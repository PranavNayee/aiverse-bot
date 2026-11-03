import json, os, re, requests
import config as C, safety
from util import log, retry

PROMPT = """You write short, funny Hindi cartoon Reels for an Indian audience of ALL ages (clean humour, family-safe).

SAFE TRENDING TOPICS TODAY (India):
{trends}

ALREADY USED RECENTLY (do not repeat): {used}
{hints}
{feedback}
TASK
1. Pick ONE topic that can be joked about lightly (cricket, movies/OTT, gadgets, food, festivals, weather, viral memes,
   tech, shopping sales, school/office life). NEVER touch politics, religion, caste, communities, wars, crime,
   accidents, deaths, illness, or mocking any real person. If no topic is suitable, write a relatable everyday-life joke.
2. Write exactly {n} scenes: scene 1 = strong hook/setup, middle = escalation, last scene = punchline.
3. Main characters (reuse them): {chars}
4. Speakers allowed: narrator, chintu, mintu.
5. "narration": Hindi in Devanagari, natural spoken style, 6-18 words per scene.
6. "image_prompt": English, describes the visual scene and actions only. No text/letters/signs in the image.
   Never depict real people; express the topic through objects and situations.
7. "characters": which of chintu/mintu are visible in that scene (can be empty).
8. "hook": 3-6 word Hindi curiosity line shown on screen at the start.

Return ONLY valid JSON (no markdown, no explanation):
{{"topic": "...", "title": "...", "hook": "...", "caption": "Hindi caption, 1-2 lines, emojis ok",
 "hashtags": ["#..."],
 "scenes": [{{"speaker": "narrator|chintu|mintu", "narration": "...", "image_prompt": "...", "characters": ["chintu","mintu"]}}]}}"""

REVIEW_PROMPT = """You are a strict brand-safety editor for a family-friendly Indian comedy channel.
Review this cartoon script. Reject it if it contains or implies: politics or politicians, religion, caste or
community jokes, violence, crime, death, illness, tragedy, sexual content, abuse, harassment of or insults to any real
person or group, misleading news claims, or anything a brand would not want next to its ad.
Also reject if it is not actually funny or not understandable.

SCRIPT:
{script}

Return ONLY valid JSON (no markdown): {{"safe": true/false, "reason": "short reason"}}"""

def _clean_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    # Extract first JSON object if there's extra text
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        text = m.group(0)
    return json.loads(text)

# ── HuggingFace Inference API (free) ────────────────────────────────────────
HF_MODELS = [
    "Qwen/Qwen2.5-72B-Instruct",
    "meta-llama/Llama-3.3-70B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
]

@retry(tries=2, delay=10)
def _hf_once(model, prompt, temperature):
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        raise RuntimeError("HF_TOKEN not set")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
        "temperature": max(0.01, temperature),
        "stream": False,
    }
    r = requests.post(
        "https://api-inference.huggingface.co/v1/chat/completions",
        headers=headers, json=payload, timeout=120
    )
    if r.status_code == 429:
        raise RuntimeError(f"HF rate limit on {model}")
    if r.status_code != 200:
        raise RuntimeError(f"HF {model} error {r.status_code}: {r.text[:200]}")
    content = r.json()["choices"][0]["message"]["content"]
    return _clean_json(content)

def _hf_generate(prompt, temperature=1.0):
    """Try each HF model until one works."""
    last = None
    for m in HF_MODELS:
        try:
            result = _hf_once(m, prompt, temperature)
            log(f"  HF model {m} succeeded")
            return result
        except Exception as e:
            last = e
            log(f"  HF model {m} failed: {e}")
    raise RuntimeError(f"All HF models failed: {last}")

# ── Gemini fallback ──────────────────────────────────────────────────────────
@retry(tries=3, delay=20)
def _gemini_once(model, prompt, temperature):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    r = requests.post(url,
                      headers={"x-goog-api-key": C.GEMINI_API_KEY(),
                                "Content-Type": "application/json"},
                      json={"contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"responseMimeType": "application/json",
                                                  "temperature": temperature}},
                      timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"Gemini {model} error {r.status_code}: {r.text[:200]}")
    return _clean_json(r.json()["candidates"][0]["content"]["parts"][0]["text"])

def _gemini_generate(prompt, temperature=1.0):
    last = None
    for m in C.GEMINI_MODELS:
        try:
            return _gemini_once(m, prompt, temperature)
        except Exception as e:
            last = e
            log(f"  Gemini {m} failed: {e}")
    raise RuntimeError(f"All Gemini models failed: {last}")

# ── unified generate: HF first, Gemini fallback ──────────────────────────────
def generate(prompt, temperature=1.0):
    """Try HuggingFace free models first, fall back to Gemini."""
    # Try HF if token is available
    if os.environ.get("HF_TOKEN"):
        try:
            return _hf_generate(prompt, temperature)
        except Exception as e:
            log(f"HF failed, trying Gemini: {e}")
    # Gemini fallback
    return _gemini_generate(prompt, temperature)

# Keep 'gemini' as an alias so check.py still works
gemini = generate

# ── validation & story generation ───────────────────────────────────────────
def _devanagari_ratio(text):
    letters = [c for c in text if c.isalpha()]
    return sum("\u0900" <= c <= "\u097F" for c in letters) / len(letters) if letters else 0

def validate(st):
    for k in ("topic", "caption"):
        if not str(st.get(k, "")).strip():
            raise ValueError(f"missing {k}")
    scenes = st.get("scenes") or []
    if not (max(4, C.NUM_SCENES - 2) <= len(scenes) <= C.NUM_SCENES + 2):
        raise ValueError(f"expected about {C.NUM_SCENES} scenes, got {len(scenes)}")
    for i, s in enumerate(scenes, 1):
        nar = str(s.get("narration", "")).strip()
        if not nar or not str(s.get("image_prompt", "")).strip():
            raise ValueError(f"scene {i} incomplete")
        if len(nar.split()) > 28:
            raise ValueError(f"scene {i} narration too long")
        if _devanagari_ratio(nar) < 0.6:
            raise ValueError(f"scene {i} narration is not Hindi (Devanagari)")
        if s.get("speaker") not in C.VOICES:
            s["speaker"] = "narrator"
        s["characters"] = [c for c in (s.get("characters") or []) if c in C.CHARACTERS]
    st["hook"] = " ".join(str(st.get("hook", "")).split()[:8])
    st["hashtags"] = [h if h.startswith("#") else "#" + h for h in st.get("hashtags", []) if h]
    return st

def review(st):
    script = "\n".join(f"[{s['speaker']}] {s['narration']}" for s in st["scenes"])
    script = f"Topic: {st['topic']}\nCaption: {st['caption']}\n{script}"
    res = generate(REVIEW_PROMPT.format(script=script), temperature=0)
    return bool(res.get("safe")), str(res.get("reason", ""))

def make_story(trends, used, hints=""):
    feedback = ""
    for attempt in range(1, 4):
        prompt = PROMPT.format(
            trends="\n".join(f"- {t}" for t in trends) or "- (none available; use an everyday-life joke)",
            used=", ".join(used) or "none", n=C.NUM_SCENES,
            chars="; ".join(C.CHARACTERS.values()),
            hints=f"PERFORMANCE HINTS: {hints}\n" if hints else "",
            feedback=f"PREVIOUS ATTEMPT WAS REJECTED: {feedback}. Fix this.\n" if feedback else "")
        try:
            st = validate(generate(prompt))
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
