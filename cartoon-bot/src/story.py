import json, re, time, requests
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
7. "camera": one of push, orbit, pull, shake. "reaction": none, zoom or shake (use zoom/shake on the punchline).
8. "sticker": one emoji to pop on screen for emphasis, or "".
9. "hook": 3-6 word Hindi curiosity line shown at the start.

Return ONLY JSON:
{{"topic": "...", "title": "...", "hook": "...", "caption": "Hindi caption, 1-2 lines, emojis ok",
 "hashtags": ["#..."],
 "scenes": [{{"speaker": "bablu|chiku|narrator", "narration": "...", "visual": "...", "with_sidekick": false,
              "camera": "push", "reaction": "none", "sticker": ""}}]}}"""

REVIEW_PROMPT = """You are a strict brand-safety editor for a family-friendly Indian comedy channel.
Reject the script if it contains or implies: politics or politicians, religion, caste or community jokes, violence,
crime, death, illness, tragedy, sexual content, abuse, harassment of or insults to any real person or group,
misleading news claims, or anything a brand would not want next to its ad. Also reject if it is not funny or unclear.

SCRIPT:
{script}

Return ONLY JSON: {{"safe": true/false, "reason": "short reason"}}"""

CAMERAS = ("push", "orbit", "pull", "shake")
REACTIONS = ("none", "zoom", "shake")

def _clean_json(text):
    text = re.sub(r"^```(?:json)?", "", text.strip()).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta"
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

def _devanagari_ratio(text):
    letters = [c for c in text if c.isalpha()]
    return sum("\u0900" <= c <= "\u097F" for c in letters) / len(letters) if letters else 0

def validate(st):
    """Fix small problems, raise ValueError for big ones."""
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
    res = gemini(REVIEW_PROMPT.format(script=f"Topic: {st['topic']}\nCaption: {st['caption']}\n{script}"), temperature=0)
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
            st = validate(gemini(prompt))
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
