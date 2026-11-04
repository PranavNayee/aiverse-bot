import json, re, time, requests, os
import config as C, safety
from util import log, retry

PROMPT = """You write short, funny Hindi cartoon Reels for ALL ages (clean, family-safe humour).
The channel is a vlog-style comedy series called "{series}", episode {ep}. Each episode takes ONE trending topic
and shows the hero reacting to it like a vlogger.

HERO: {hero}
SIDEKICK (optional): {side}

SAFE TRENDING TOPICS TODAY (India):
{trends}

ALREADY USED RECENTLY (do not repeat): {used}
{hints}
{feedback}
RULES
1. Pick ONE topic that can be joked about lightly (cricket, movies/OTT, gadgets, food, festivals, weather, viral memes,
   tech, shopping, school/office life). NEVER touch politics, religion, caste, communities, wars, crime, accidents,
   deaths, illness, or mocking any real person. If nothing fits, use a relatable everyday-life situation.
2. Exactly {n} scenes. Each scene is ONE shot (one picture). Scene 1: the hero greets the camera like a vlogger and
   sets up the topic. Middle: escalation. Last scene: punchline.
3. Speakers: bablu (hero, most lines), chiku (sidekick, a few roasting lines), narrator (at most 1 scene).
4. "narration": Hindi in Devanagari, spoken style, 6-18 words.
5. "visual": English. Describe what we SEE: the character(s), their expression/pose, and the funny setting related to
   the topic. The speaking character must be big in frame, face clearly visible, looking at camera. No text or signs.
   Never depict real people.
6. "with_sidekick": true only if Chiku is visible. If speaker is chiku it must be true.
7. "camera": push (slow zoom in), orbit (circular move), pull (zoom out), shake (handheld), spiral (dramatic zoom+orbit),
   dolly_zoom (vertigo effect), crane (vertical rise), drift (floating lateral). Match camera to emotion: spiral/crane for
   dramatic moments, shake for chaos, drift for dreamy, push for normal, dolly_zoom for shock/realization.
8. "reaction": none, zoom or shake (use zoom/shake on the punchline).
9. "sticker": one emoji to pop on screen for emphasis, or "".
10. "hook": Use viral hook templates to grab attention:
    - Curiosity: "क्या आप जानते हैं...", "इसके बारे में कोई नहीं बताता..."
    - Question: "अगर [topic] हो जाए तो?", "क्यों होता है [topic]?"
    - Shock: "यह आपको चौंका देगा!", "आप यकीन नहीं करोगे..."
    - Relatable: "हर किसी के साथ होता है...", "सच में ऐसा होता है!"
    Make it 3-6 words, intriguing, related to topic.

Return ONLY JSON:
{{"topic": "...", "title": "...", "hook": "...", "caption": "Hindi caption, 1-2 lines, emojis ok",
 "hashtags": ["#..."],
 "scenes": [{{"speaker": "bablu|chiku|narrator", "narration": "...", "visual": "...", "with_sidekick": false,
              "camera": "push", "reaction": "none", "sticker": ""}}]}}"""

# Viral hook templates for maximum engagement (used by AI as examples)
VIRAL_HOOKS = {
    "curiosity": [
        "क्या आप जानते हैं {topic}?",
        "इसके बारे में कोई नहीं बताता",
        "यह राज़ छुपा है",
        "इसका जवाब 99% नहीं जानते",
    ],
    "question": [
        "अगर {topic} हो जाए तो?",
        "क्यों होता है {topic}?",
        "कैसे बचें {topic} से?",
        "{topic} का सच क्या है?",
    ],
    "shock": [
        "यह आपको चौंका देगा!",
        "आप यकीन नहीं करोगे!",
        "यह {topic} बदल देगा सब कुछ!",
        "अभी तक नहीं बताया गया",
    ],
    "relatable": [
        "हर किसी के साथ होता है",
        "सच में ऐसा होता है!",
        "आपके साथ भी होगा",
        "यह बात समझो",
    ],
    "emotional": [
        "यह दिल छू लेगा",
        "आंसू रोक नहीं पाओगे",
        "सच्ची कहानी है यह",
        "बहुत खास है यह",
    ],
}

REVIEW_PROMPT = """You are a strict brand-safety editor for a family-friendly Indian comedy channel.
Reject the script if it contains or implies: politics or politicians, religion, caste or community jokes, violence,
crime, death, illness, tragedy, sexual content, abuse, harassment of or insults to any real person or group,
misleading news claims, or anything a brand would not want next to its ad. Also reject if it is not funny or unclear.

SCRIPT:
{script}

Return ONLY JSON: {{"safe": true/false, "reason": "short reason"}}"""

CAMERAS = ("push", "orbit", "pull", "shake", "spiral", "dolly_zoom", "crane", "drift")
REACTIONS = ("none", "zoom", "shake")

def _clean_json(text):
    text = re.sub(r"^```(?:json)?", "", text.strip()).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta"
HF_API_URL = "https://api-inference.huggingface.co/models"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

HF_MODELS = [
    "Qwen/Qwen2.5-72B-Instruct",
    "meta-llama/Llama-3.3-70B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3"
]

GROQ_MODELS = [
    "llama-3.3-70b-versatile",      # Fastest, most versatile
    "llama-3.1-70b-versatile",      # Backup
    "mixtral-8x7b-32768"            # Alternative
]

LAST_MODEL = ""
_cands = None

def _rank(names):
    """Newest Flash models first (stable before preview, full Flash before Flash-Lite). Pure function, easy to test."""
    good = []
    for n in names:
        m = re.match(r"^gemini-(\d+(?:\.\d+)?)-flash(-lite)?(-preview[\w.-]*|-\d+)?$", n)
        if m:
            good.append((-float(m.group(1)), bool(m.group(3)) and "preview" in m.group(3), bool(m.group(2)), n))
    return [g[3] for g in sorted(good)]

def model_candidates():
    """Models to try, best first. Uses GEMINI_MODELS if you set it, else asks Google what exists today."""
    global _cands
    if C.GEMINI_MODELS:
        return C.GEMINI_MODELS
    if _cands:
        return _cands
    names, token = [], None
    try:
        for _ in range(3):
            r = requests.get(f"{GEMINI_URL}/models", headers={"x-goog-api-key": C.GEMINI_API_KEY()},
                             params={"pageSize": 200, **({"pageToken": token} if token else {})}, timeout=30)
            if r.status_code != 200:
                break
            j = r.json()
            names += [m["name"].split("/")[-1] for m in j.get("models", [])
                      if "generateContent" in m.get("supportedGenerationMethods", [])]
            token = j.get("nextPageToken")
            if not token:
                break
    except Exception as e:
        log("Model discovery failed:", e)
    ranked = _rank(names)[:5]
    _cands = ranked or C.GEMINI_FALLBACK_MODELS
    log("Gemini models to try:", _cands)
    return _cands

def extract_text(resp_json):
    parts = resp_json["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts if not p.get("thought"))

def _gemini_once(model, prompt, temperature):
    """Returns parsed JSON. Retries only temporary problems (429 / 5xx); a retired model moves on immediately."""
    last = None
    for attempt in range(2):
        r = requests.post(f"{GEMINI_URL}/models/{model}:generateContent",
                          headers={"x-goog-api-key": C.GEMINI_API_KEY(), "Content-Type": "application/json"},
                          json={"contents": [{"parts": [{"text": prompt}]}],
                                "generationConfig": {"responseMimeType": "application/json", "temperature": temperature}},
                          timeout=120)
        if r.status_code == 200:
            return _clean_json(extract_text(r.json()))
        last = RuntimeError(f"Gemini {model} error {r.status_code}: {r.text[:200]}")
        if r.status_code not in (429, 500, 502, 503, 504):
            break
        time.sleep(8)
    raise last

def gemini(prompt, temperature=1.0):
    """Try each available model until one works."""
    global LAST_MODEL
    last = None
    for m in model_candidates():
        try:
            out = _gemini_once(m, prompt, temperature)
            LAST_MODEL = m
            return out
        except Exception as e:
            last = e
            log(f"Model {m} failed, trying next: {e}")
    raise RuntimeError(f"All Gemini models failed: {last}")

def _huggingface_once(model, prompt, temperature):
    """Call HuggingFace Inference API with JSON parsing."""
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN not set")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Format prompt for chat models
    messages = [{"role": "user", "content": prompt}]
    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": temperature,
            "max_new_tokens": 2000,
            "return_full_text": False
        }
    }
    
    for attempt in range(2):
        r = requests.post(f"{HF_API_URL}/{model}", headers=headers, json=payload, timeout=120)
        if r.status_code == 200:
            try:
                result = r.json()
                # HF returns different formats depending on model
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    text = result.get("generated_text", "") or result.get("text", "")
                else:
                    text = str(result)
                
                # Extract JSON from response
                return _clean_json(text)
            except json.JSONDecodeError:
                # Try to find JSON in the response
                json_match = re.search(r'\{.*\}', r.text, re.DOTALL)
                if json_match:
                    return _clean_json(json_match.group(0))
                raise RuntimeError(f"HuggingFace {model} returned non-JSON: {r.text[:200]}")
        
        if r.status_code == 503:  # Model loading
            log(f"HuggingFace {model} loading, waiting...")
            time.sleep(20)
            continue
        
        raise RuntimeError(f"HuggingFace {model} error {r.status_code}: {r.text[:200]}")
    
    raise RuntimeError(f"HuggingFace {model} timed out (model loading)")

def huggingface(prompt, temperature=1.0):
    """Try HuggingFace models."""
    global LAST_MODEL
    last = None
    for model in HF_MODELS:
        try:
            out = _huggingface_once(model, prompt, temperature)
            LAST_MODEL = f"HF:{model}"
            return out
        except Exception as e:
            last = e
            log(f"HuggingFace {model} failed: {e}")
    raise RuntimeError(f"All HuggingFace models failed: {last}")

def _groq_once(model, prompt, temperature):
    """Call Groq API with JSON mode."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that responds only with valid JSON. Never include markdown, explanations, or any text outside the JSON object."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": 2000,
        "response_format": {"type": "json_object"}  # Force JSON output
    }
    
    for attempt in range(2):
        r = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            result = r.json()
            content = result["choices"][0]["message"]["content"]
            return _clean_json(content)
        
        if r.status_code == 429:  # Rate limit
            log(f"Groq rate limit, waiting...")
            time.sleep(5)
            continue
        
        raise RuntimeError(f"Groq {model} error {r.status_code}: {r.text[:200]}")
    
    raise RuntimeError(f"Groq {model} rate limited")

def groq(prompt, temperature=1.0):
    """Try Groq models (fastest!)."""
    global LAST_MODEL
    last = None
    for model in GROQ_MODELS:
        try:
            out = _groq_once(model, prompt, temperature)
            LAST_MODEL = f"Groq:{model}"
            return out
        except Exception as e:
            last = e
            log(f"Groq {model} failed: {e}")
    raise RuntimeError(f"All Groq models failed: {last}")

def generate_story(prompt, temperature=1.0):
    """Try Groq first (fastest), then HuggingFace, then Gemini fallback."""
    # Try Groq first (super fast!)
    if os.environ.get("GROQ_API_KEY"):
        try:
            log("Trying Groq models (fastest)...")
            return groq(prompt, temperature)
        except Exception as e:
            log(f"Groq failed, trying HuggingFace: {e}")
    
    # Try HuggingFace if token is available
    if os.environ.get("HF_TOKEN"):
        try:
            log("Trying HuggingFace models...")
            return huggingface(prompt, temperature)
        except Exception as e:
            log(f"HuggingFace failed, falling back to Gemini: {e}")
    
    # Fall back to Gemini
    log("Using Gemini...")
    return gemini(prompt, temperature)

def _devanagari_ratio(text):
    letters = [c for c in text if c.isalpha()]
    return sum("\u0900" <= c <= "\u097F" for c in letters) / len(letters) if letters else 0

def validate(st):
    """Fix small problems, raise ValueError for big ones."""
    # Ensure st is a dict, not a list or other type
    if not isinstance(st, dict):
        raise ValueError(f"Expected JSON object (dict), got {type(st).__name__}")
    
    for k in ("topic", "caption"):
        if not str(st.get(k, "")).strip():
            raise ValueError(f"missing {k}")
    scenes = st.get("scenes") or []
    if not (max(4, C.NUM_SCENES - 2) <= len(scenes) <= C.NUM_SCENES + 2):
        raise ValueError(f"expected about {C.NUM_SCENES} scenes, got {len(scenes)}")
    narrators = 0
    for i, s in enumerate(scenes, 1):
        nar = str(s.get("narration", "")).strip()
        if not nar or not str(s.get("visual", "")).strip():
            raise ValueError(f"scene {i} incomplete")
        if len(nar.split()) > 28:
            raise ValueError(f"scene {i} narration too long")
        if _devanagari_ratio(nar) < 0.6:
            raise ValueError(f"scene {i} narration is not Hindi (Devanagari)")
        if s.get("speaker") not in C.VOICES:
            s["speaker"] = "bablu"
        narrators += s["speaker"] == "narrator"
        s["with_sidekick"] = bool(s.get("with_sidekick")) or s["speaker"] == "chiku"
        s["camera"] = s.get("camera") if s.get("camera") in CAMERAS else "push"
        s["reaction"] = s.get("reaction") if s.get("reaction") in REACTIONS else "none"
        st_ = str(s.get("sticker") or "").strip()
        s["sticker"] = st_ if 0 < len(st_) <= 4 and not st_.isascii() else ""
    if narrators > 2:
        raise ValueError("too many narrator scenes; the hero should speak")
    st["hook"] = " ".join(str(st.get("hook", "")).split()[:8])
    st["hashtags"] = [h if h.startswith("#") else "#" + h for h in st.get("hashtags", []) if h]
    return st

def review(st):
    script = "\n".join(f"[{s['speaker']}] {s['narration']}  (visual: {s['visual']})" for s in st["scenes"])
    res = generate_story(REVIEW_PROMPT.format(script=f"Topic: {st['topic']}\nCaption: {st['caption']}\n{script}"), temperature=0)
    return bool(res.get("safe")), str(res.get("reason", ""))

def make_story(trends, used, hints="", episode=1):
    feedback = ""
    for attempt in range(1, 4):
        prompt = PROMPT.format(
            series=C.SERIES_NAME, ep=episode,
            hero=f"{C.CHARACTERS['bablu']['look']} — {C.CHARACTERS['bablu']['persona']}",
            side=f"{C.CHARACTERS['chiku']['look']} — {C.CHARACTERS['chiku']['persona']}",
            trends="\n".join(f"- {t}" for t in trends) or "- (none available; use an everyday-life joke)",
            used=", ".join(used) or "none", n=C.NUM_SCENES,
            hints=f"PERFORMANCE HINTS: {hints}\n" if hints else "",
            feedback=f"PREVIOUS ATTEMPT WAS REJECTED: {feedback}. Fix this.\n" if feedback else "")
        try:
            st = validate(generate_story(prompt))
            ok, why = safety.local_check(st)
            if not ok:
                feedback = why; log("Rejected (blocklist):", why); continue
            ok, why = review(st)
            if not ok:
                feedback = why; log("Rejected (reviewer):", why); continue
            log(f"Story accepted on attempt {attempt}: {st['topic']}")
            return st
        except ValueError as e:
            feedback = str(e); log("Rejected (validation):", e)
    raise RuntimeError(f"Could not produce a safe, valid story after 3 attempts. Last issue: {feedback}")
