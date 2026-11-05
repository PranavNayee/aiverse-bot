"""One place for all AI text calls. Free providers: Groq and Gemini. Model names are DISCOVERED live
(providers retire names often), with static fallbacks. Returns parsed JSON."""
import json, os, re, time, requests
from util import log

GROQ_URL = "https://api.groq.com/openai/v1"
GEM_URL = "https://generativelanguage.googleapis.com/v1beta"
GROQ_PREFS = [r"llama-3\.3-70b", r"gpt-oss-120b", r"llama-4-maverick", r"llama-4-scout", r"qwen", r"kimi", r"gpt-oss-20b", r"llama-3\.1-8b"]
GROQ_FALLBACK = ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "llama-3.1-8b-instant"]
GEM_FALLBACK = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3-flash-preview"]
_EXCL = re.compile(r"whisper|guard|tts|playai|embed|distil|vision|safeguard|orpheus|allam|compound", re.I)
_cache = {}
LAST = ""

def extract_json(text):
    text = re.sub(r"^```(?:json)?", "", (text or "").strip()).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except ValueError:
        a, b = text.find("{"), text.rfind("}")
        if a >= 0 and b > a:
            return json.loads(text[a:b + 1])
        raise

# ---------------- Groq ----------------
def groq_models():
    if "groq" in _cache:
        return _cache["groq"]
    ranked = []
    try:
        r = requests.get(f"{GROQ_URL}/models", headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"}, timeout=30)
        ids = [m["id"] for m in r.json().get("data", []) if not _EXCL.search(m["id"]) and m.get("active", True)] if r.status_code == 200 else []
        for pat in GROQ_PREFS:
            ranked += [i for i in ids if re.search(pat, i) and i not in ranked]
    except Exception as e:
        log("Groq model discovery failed:", e)
    _cache["groq"] = ranked[:4] or GROQ_FALLBACK
    log("Groq models:", _cache["groq"])
    return _cache["groq"]

def _groq_call(model, prompt, temperature):
    key = os.environ["GROQ_API_KEY"]
    for json_mode in (True, False):
        body = {"model": model, "temperature": temperature,
                "messages": [{"role": "system", "content": "You reply with one valid JSON object and nothing else."},
                             {"role": "user", "content": prompt}]}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        r = requests.post(f"{GROQ_URL}/chat/completions", headers={"Authorization": f"Bearer {key}"}, json=body, timeout=90)
        if r.status_code == 200:
            return extract_json(r.json()["choices"][0]["message"]["content"])
        if r.status_code == 429:
            time.sleep(min(float(r.headers.get("retry-after", 8)), 20)); raise RuntimeError(f"Groq {model} rate limited")
        if r.status_code == 400 and json_mode:
            continue                                                   # this model may not support JSON mode
        raise RuntimeError(f"Groq {model} {r.status_code}: {r.text[:150]}")
    raise RuntimeError(f"Groq {model} failed")

# ---------------- Gemini ----------------
def _rank_gemini(names):
    good = []
    for n in names:
        m = re.match(r"^gemini-(\d+(?:\.\d+)?)-flash(-lite)?(-preview[\w.-]*|-\d+)?$", n)
        if m:
            good.append((-float(m.group(1)), bool(m.group(3)) and "preview" in m.group(3), bool(m.group(2)), n))
    return [g[3] for g in sorted(good)]

def gemini_models():
    if "gem" in _cache:
        return _cache["gem"]
    names = []
    try:
        r = requests.get(f"{GEM_URL}/models", headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, params={"pageSize": 200}, timeout=30)
        if r.status_code == 200:
            names = [m["name"].split("/")[-1] for m in r.json().get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
    except Exception as e:
        log("Gemini model discovery failed:", e)
    forced = [m.strip() for m in os.environ.get("GEMINI_MODELS", "").split(",") if m.strip()]
    _cache["gem"] = forced or _rank_gemini(names)[:4] or GEM_FALLBACK
    log("Gemini models:", _cache["gem"])
    return _cache["gem"]

def _gemini_call(model, prompt, temperature):
    for _ in range(2):
        r = requests.post(f"{GEM_URL}/models/{model}:generateContent",
                          headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"], "Content-Type": "application/json"},
                          json={"contents": [{"parts": [{"text": prompt}]}],
                                "generationConfig": {"responseMimeType": "application/json", "temperature": temperature}}, timeout=120)
        if r.status_code == 200:
            parts = r.json()["candidates"][0]["content"]["parts"]
            return extract_json("".join(p.get("text", "") for p in parts if not p.get("thought")))
        if r.status_code not in (429, 500, 502, 503, 504):
            break
        time.sleep(8)
    raise RuntimeError(f"Gemini {model} {r.status_code}: {r.text[:150]}")

# ---------------- public ----------------
def generate_json(prompt, temperature=0.7, order=("gemini", "groq")):
    """Try providers/models in order until one returns valid JSON. Raises if all fail (never returns junk)."""
    global LAST
    errors = []
    for prov in order:
        if prov == "groq" and os.environ.get("GROQ_API_KEY"):
            models, call = groq_models(), _groq_call
        elif prov == "gemini" and os.environ.get("GEMINI_API_KEY"):
            models, call = gemini_models(), _gemini_call
        else:
            continue
        for m in models:
            try:
                out = call(m, prompt, temperature)
                if isinstance(out, dict):
                    LAST = f"{prov}:{m}"
                    return out
                errors.append(f"{prov}:{m} returned {type(out).__name__}, expected object")
            except Exception as e:
                errors.append(f"{prov}:{m}: {str(e)[:120]}"); log(f"  {prov} {m} failed: {str(e)[:120]}")
    raise RuntimeError("No AI provider produced a valid answer. " + " | ".join(errors[-4:]) if errors else
                       "No AI key configured (set GEMINI_API_KEY and/or GROQ_API_KEY)")
