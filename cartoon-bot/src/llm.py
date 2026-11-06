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
_DEAD = {}          # model -> failure count this run (overloaded / timing out): skipped after 2 strikes
_GOOD = {}          # provider -> model that last worked: tried first next time


class _Overloaded(RuntimeError):
    """Temporary provider trouble (timeout, 429, 5xx): don't keep hammering this model."""

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
        try:
            r = requests.post(f"{GROQ_URL}/chat/completions", headers={"Authorization": f"Bearer {key}"}, json=body,
                              timeout=(10, 60))
        except requests.exceptions.RequestException as e:
            raise _Overloaded(f"Groq {model}: {e}")
        if r.status_code == 200:
            try:
                return extract_json(r.json()["choices"][0]["message"]["content"])
            except (ValueError, KeyError, IndexError, TypeError):
                if json_mode:
                    continue                                           # broken/empty JSON: one more try
                raise
        if r.status_code == 429:
            time.sleep(min(float(r.headers.get("retry-after", 8)), 20)); raise _Overloaded(f"Groq {model} rate limited")
        if r.status_code == 400 and json_mode:
            continue                                                   # this model may not support JSON mode
        if r.status_code >= 500:
            raise _Overloaded(f"Groq {model} {r.status_code}: {r.text[:150]}")
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
    try:
        r = requests.post(f"{GEM_URL}/models/{model}:generateContent",
                          headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"], "Content-Type": "application/json"},
                          json={"contents": [{"parts": [{"text": prompt}]}],
                                "generationConfig": {"responseMimeType": "application/json", "temperature": temperature}},
                          timeout=(10, 75))
    except requests.exceptions.RequestException as e:
        raise _Overloaded(f"Gemini {model}: {e}")
    if r.status_code == 200:
        parts = r.json()["candidates"][0]["content"]["parts"]
        return extract_json("".join(p.get("text", "") for p in parts if not p.get("thought")))
    if r.status_code in (429, 500, 502, 503, 504):
        raise _Overloaded(f"Gemini {model} {r.status_code}: {r.text[:150]}")
    raise RuntimeError(f"Gemini {model} {r.status_code}: {r.text[:150]}")

# ---------------- public ----------------
ROUND_WAITS = (20, 60, 120)     # when EVERY model fails (provider outages), wait and try all of them again


def generate_json(prompt, temperature=0.7, order=("gemini", "groq")):
    """Try providers/models in order until one returns valid JSON. If every model fails (both providers busy,
    rate limits, broken JSON) wait and retry the whole set a few times. Raises if all rounds fail."""
    for i, wait in enumerate((0,) + ROUND_WAITS):
        if wait:
            log(f"  all AI models failed - waiting {wait}s, then retrying (round {i + 1}/{len(ROUND_WAITS) + 1})")
            time.sleep(wait)
            _DEAD.clear()                       # give benched models another chance
        try:
            return _one_pass(prompt, temperature, order)
        except _NoKeys:
            raise
        except RuntimeError as e:
            last = e
    raise last


class _NoKeys(RuntimeError):
    pass


def _one_pass(prompt, temperature=0.7, order=("gemini", "groq"), _retry=False):
    global LAST
    errors = []
    for prov in order:
        if prov == "groq" and os.environ.get("GROQ_API_KEY"):
            models, call = groq_models(), _groq_call
        elif prov == "gemini" and os.environ.get("GEMINI_API_KEY"):
            models, call = gemini_models(), _gemini_call
        else:
            continue
        good = _GOOD.get(prov)
        models = ([good] if good in models else []) + [m for m in models if m != good]
        for m in models:
            if _DEAD.get(m, 0) >= 2:
                continue
            try:
                out = call(m, prompt, temperature)
                if isinstance(out, dict):
                    LAST = f"{prov}:{m}"
                    _GOOD[prov] = m
                    _DEAD.pop(m, None)
                    return out
                errors.append(f"{prov}:{m} returned {type(out).__name__}, expected object")
            except _Overloaded as e:
                _DEAD[m] = _DEAD.get(m, 0) + 1
                if _GOOD.get(prov) == m:
                    _GOOD.pop(prov)
                errors.append(f"{prov}:{m}: {str(e)[:120]}"); log(f"  {prov} {m} busy: {str(e)[:120]}")
            except Exception as e:
                errors.append(f"{prov}:{m}: {str(e)[:120]}"); log(f"  {prov} {m} failed: {str(e)[:120]}")
    if not errors:
        if _DEAD and not _retry:                    # every model was benched earlier this run: give them one more go
            _DEAD.clear()
            return _one_pass(prompt, temperature, order, _retry=True)
        raise _NoKeys("No AI key configured (set GEMINI_API_KEY and/or GROQ_API_KEY)")
    raise RuntimeError("No AI provider produced a valid answer. " + " | ".join(errors[-4:]))
