import json, re, requests
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

Return ONLY JSON:
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

Return ONLY JSON: {{"safe": true/false, "reason": "short reason"}}"""

def _clean_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)

@retry(tries=2, delay=8)
def _gemini_once(model, prompt, temperature):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    r = requests.post(url, headers={"x-goog-api-key": C.GEMINI_API_KEY(), "Content-Type": "application/json"},
                      json={"contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"responseMimeType": "application/json", "temperature": temperature}},
                      timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"Gemini {model} error {r.status_code}: {r.text[:200]}")
    return _clean_json(r.json()["candidates"][0]["content"]["parts"][0]["text"])

def gemini(prompt, temperature=1.0):
    """Try each model in GEMINI_MODELS until one works."""
    last = None
    for m in C.GEMINI_MODELS:
        try:
            return _gemini_once(m, prompt, temperature)
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
    res = gemini(REVIEW_PROMPT.format(script=script), temperature=0)
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
