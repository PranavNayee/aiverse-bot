"""Human-sounding narration. Providers, best first (TTS_PROVIDER=auto picks the first one configured):

  elevenlabs - most human (paid; set ELEVENLABS_API_KEY, optional ELEVENLABS_VOICE_ID). Exact word timings.
  gemini     - natural, expressive, directed like an actor (free with GEMINI_API_KEY). Timings from pauses.
  edge       - Microsoft neural voices (free, always works) - the safety net.

A reel is voiced by ONE provider from start to finish: if any scene fails, the whole reel falls back to the
next provider, so the voice never changes mid-video.
Each scene returns (audio_path, seconds, [(start, end, caption_word)]) - captions always show the
script's own words (Roman Hinglish / English) even when the voice reads a Devanagari copy."""
import base64, concurrent.futures, os, re, time, requests
import numpy as np
import config as C, voice, soundtrack
from util import log

GEM_URL = "https://generativelanguage.googleapis.com/v1beta"
EL_URL = "https://api.elevenlabs.io/v1"
LAST = ""


# ---------------------------------------------------------------- timing helpers
def _trim(x, sr, lead=0.12, tail=0.3, thr=0.012):
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx):
        return x
    a = max(0, idx[0] - int(lead * sr)); b = min(len(x), idx[-1] + int(tail * sr))
    return x[a:b]


def pause_words(text, x, sr):
    """Word timings without TTS timestamps: split the text into phrases at punctuation, find the matching
    pauses in the audio, then spread each phrase's words over its own speech span by word length."""
    words = text.split()
    if not words:
        return []
    dur = len(x) / sr
    hop = int(0.01 * sr)
    env = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, max(len(x) - hop, 1), hop)])
    thr = max(0.02 * float(env.max() or 1), 0.004)
    voiced = env > thr
    vi = np.where(voiced)[0]
    if not len(vi):
        return voice.estimate_words(text, dur)
    s0, s1 = vi[0] * 0.01, (vi[-1] + 1) * 0.01
    # silent gaps inside the speech span (>= 0.14 s)
    gaps, run = [], None
    for i in range(vi[0], vi[-1] + 1):
        if not voiced[i]:
            run = i if run is None else run
        elif run is not None:
            if (i - run) * 0.01 >= 0.14:
                gaps.append((run * 0.01, i * 0.01))
            run = None
    # phrases at punctuation
    phrases, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[,.?!;:।]$", w):
            phrases.append(cur); cur = []
    if cur:
        phrases.append(cur)
    k = len(phrases) - 1
    cuts = sorted(sorted(gaps, key=lambda g: g[1] - g[0], reverse=True)[:k]) if k and len(gaps) >= k else []
    if len(cuts) != k:                                  # can't match phrases to pauses: one span for all
        phrases, cuts = [words], []
    spans, st = [], s0
    for g in cuts:
        spans.append((st, g[0])); st = g[1]
    spans.append((st, s1))
    out = []
    for ph, (a, b) in zip(phrases, spans):
        wts = [len(w) + 2 for w in ph]
        tot, t = float(sum(wts)), a
        for w, k2 in zip(ph, wts):
            d = (b - a) * k2 / tot
            out.append((t, t + d * 0.92, w)); t += d
    return out


def _save(x, sr, path):
    soundtrack.write_wav(path, x, sr)
    return path, len(x) / sr


# ---------------------------------------------------------------- Gemini TTS
_gem_models = None
def gemini_tts_models():
    global _gem_models
    if _gem_models is not None:
        return _gem_models
    forced = [m.strip() for m in os.environ.get("GEMINI_TTS_MODELS", "").split(",") if m.strip()]
    names = []
    try:
        r = requests.get(f"{GEM_URL}/models", headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
                         params={"pageSize": 200}, timeout=30)
        if r.status_code == 200:
            names = [m["name"].split("/")[-1] for m in r.json().get("models", [])
                     if "tts" in m["name"].lower() and "generateContent" in m.get("supportedGenerationMethods", [])]
    except Exception as e:
        log("Gemini TTS model discovery failed:", e)

    def rank(n):                                        # newest version first, flash before pro (quota)
        v = re.search(r"(\d+(?:\.\d+)?)", n)
        return (-(float(v.group(1)) if v else 0), "lite" in n, "pro" in n, "preview" in n, n)
    ranked = sorted(names, key=rank)
    full = [n for n in ranked if "lite" not in n]
    _gem_models = forced or (full or ranked)[:3] or ["gemini-2.5-flash-preview-tts"]
    log("Gemini TTS models:", _gem_models)
    return _gem_models


def _direction(text, minimal=False, paragraphs=False):
    """Gemini TTS speaks the TRANSCRIPT only; the notes above it steer the performance."""
    if minimal:
        return f"Say naturally, like a friendly human teacher: {text}"
    if C.LANGUAGE_MODE == "english_only":
        accent = "Natural Indian-English accent, crisp and clear."
    else:
        accent = ("Natural Hinglish exactly as spoken in Delhi or Mumbai: Hindi words with perfect Hindi pronunciation, "
                  "English tech words in Indian English.")
    return ("Read ONLY the text under TRANSCRIPT aloud. Never read these notes.\n"
            "# AUDIO PROFILE: a warm, confident young Indian male tech teacher making an Instagram reel.\n"
            f"# DIRECTOR'S NOTES\nStyle: real human, conversational, expressive, energetic but clear, smiling. "
            f"Never robotic.\nAccent: {accent}\nPace: natural, short pauses at commas and full stops."
            + (" Leave a clear pause of about one second between paragraphs." if paragraphs else "") + "\n"
            f"# TRANSCRIPT\n{text}")


def _max_secs(text):
    return 2.0 + 0.5 * len(text.split())           # natural speech is ~0.35 s/word; reading the notes is ~3x longer


def _gemini_one(text, path, max_secs=None, paragraphs=False):
    last = None
    for model in gemini_tts_models():
        for attempt in range(3):
            try:
                r = requests.post(f"{GEM_URL}/models/{model}:generateContent",
                                  headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, timeout=(10, 90),
                                  json={"contents": [{"parts": [{"text": _direction(text, minimal=attempt == 2 and not paragraphs, paragraphs=paragraphs)}]}],
                                        "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {
                                            "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": C.GEMINI_VOICE}}}}})
            except requests.exceptions.RequestException as e:
                last = e; time.sleep(5); continue
            if r.status_code == 200:
                part = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
                rate = int((re.search(r"rate=(\d+)", part.get("mimeType", "")) or [0, 24000])[1])
                pcm = np.frombuffer(base64.b64decode(part["data"]), dtype=np.int16).astype(np.float32) / 32768.0
                if len(pcm) < rate * 0.4:
                    last = "empty audio"; continue
                pcm = _trim(pcm, rate)
                if len(pcm) / rate > (max_secs or _max_secs(text)):         # it read the director's notes too
                    last = f"audio too long ({len(pcm) / rate:.1f}s for {len(text.split())} words)"
                    log(f"  Gemini TTS {model}: {last} - retrying")
                    continue
                return model, pcm, rate
            last = f"{model} {r.status_code}: {r.text[:160]}"
            if r.status_code == 429:
                m = re.search(r'"retryDelay":\s*"(\d+)', r.text)
                wait = int(m.group(1)) + 2 if m else 20 * (attempt + 1)
                if wait > 70:                           # daily quota gone: try the next model
                    break
                time.sleep(wait); continue
            if r.status_code >= 500:
                time.sleep(6 * (attempt + 1)); continue
            break                                       # 400/403/404: this model can't be used
    raise RuntimeError(f"Gemini TTS failed: {last}")


def _gemini_scene(i, sc):
    path = f"work/voice_{i}.wav"
    text = sc.get("speech") if C.GEMINI_SPEAK_DEVANAGARI and sc.get("speech") else sc["narration"]
    model, x, sr = _gemini_one(voice.clean_for_tts(text), path)
    p, d = _save(x, sr, path)
    words = voice.align(sc["narration"], pause_words(text, x, sr), d) if text != sc["narration"] else \
        pause_words(sc["narration"], x, sr)
    return p, d, words


# ---------------------------------------------------------------- ElevenLabs
_el_voice = None
def _el_voice_id():
    global _el_voice
    if _el_voice:
        return _el_voice
    _el_voice = os.environ.get("ELEVENLABS_VOICE_ID", "").strip()
    if not _el_voice:
        r = requests.get(f"{EL_URL}/voices", headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}, timeout=30)
        vs = r.json().get("voices", []) if r.status_code == 200 else []
        male = [v for v in vs if (v.get("labels") or {}).get("gender") == "male"]
        _el_voice = (male or vs or [{}])[0].get("voice_id")
        if not _el_voice:
            raise RuntimeError(f"ElevenLabs: no voice available ({r.status_code} {r.text[:120]})")
        log("ElevenLabs voice:", (male or vs)[0].get("name"), _el_voice)
    return _el_voice


def _el_scene(i, sc):
    text = sc.get("speech") or sc["narration"]
    text = voice.clean_for_tts(text)
    for attempt in range(3):
        r = requests.post(f"{EL_URL}/text-to-speech/{_el_voice_id()}/with-timestamps",
                          params={"output_format": "mp3_44100_128"}, timeout=(10, 120),
                          headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
                          json={"text": text, "model_id": C.ELEVENLABS_MODEL,
                                "voice_settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.35,
                                                   "use_speaker_boost": True}})
        if r.status_code == 200:
            break
        if r.status_code in (429, 500, 502, 503) and attempt < 2:
            time.sleep(8 * (attempt + 1)); continue
        raise RuntimeError(f"ElevenLabs {r.status_code}: {r.text[:200]}")
    j = r.json()
    path = f"work/voice_{i}.mp3"
    with open(path, "wb") as f:
        f.write(base64.b64decode(j["audio_base64"]))
    al = j.get("alignment") or {}
    spoken, cur, st = [], "", None
    for ch, a, b in zip(al.get("characters", []), al.get("character_start_times_seconds", []),
                        al.get("character_end_times_seconds", [])):
        if ch.isspace():
            if cur:
                spoken.append((st, prev_end, cur)); cur = ""
            continue
        if not cur:
            st = a
        cur += ch; prev_end = b
    if cur:
        spoken.append((st, prev_end, cur))
    d = voice.duration(path)
    return path, d, voice.align(sc["narration"], spoken, d)


# ---------------------------------------------------------------- Edge (safety net)
def _edge_scene(i, sc):
    path = f"work/voice_{i}.mp3"
    if sc.get("speech") and C.SPEAK_DEVANAGARI:
        spoken = voice.synth(sc["speech"], C.DEFAULT_LESSON_VOICE, path)
    else:
        spk = "hinglish_roman" if C.SPEAK_DEVANAGARI else C.DEFAULT_LESSON_VOICE
        spoken = voice.synth(sc["narration"], spk, path)
    d = voice.duration(path)
    return path, d, voice.align(sc["narration"], spoken, d)


PROVIDERS = {"elevenlabs": (_el_scene, 3), "gemini": (_gemini_scene, 2), "edge": (_edge_scene, 6)}


def order():
    want = C.TTS_PROVIDER
    avail = [p for p, ok in (("elevenlabs", bool(os.environ.get("ELEVENLABS_API_KEY"))),
                             ("gemini", bool(os.environ.get("GEMINI_API_KEY"))), ("edge", True)) if ok]
    if want in avail:
        avail.remove(want); avail.insert(0, want)
    return avail


def _gaps(x, sr, min_gap=0.32):
    hop = int(0.01 * sr)
    env = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, max(len(x) - hop, 1), hop)])
    voiced = env > max(0.02 * float(env.max() or 1), 0.004)
    gaps, run = [], None
    for i, v in enumerate(voiced):
        if not v:
            run = i if run is None else run
        elif run is not None:
            if (i - run) * 0.01 >= min_gap:
                gaps.append((run * 0.01, i * 0.01))
            run = None
    return gaps


def _gemini_reel(scenes):
    """ONE request for the whole reel (saves free quota ~7x and gives one continuous, consistent performance),
    then split into scenes at the paragraph pauses. Raises if the split doesn't match the script."""
    texts = [voice.clean_for_tts(sc.get("speech") if C.GEMINI_SPEAK_DEVANAGARI and sc.get("speech") else sc["narration"])
             for sc in scenes]
    words = [len(t.split()) for t in texts]
    model, x, sr = _gemini_one("\n\n".join(texts), "reel", paragraphs=True,
                               max_secs=2.0 + 0.5 * sum(words) + 1.5 * len(scenes))
    n = len(scenes)
    gaps = [g for g in _gaps(x, sr) if g[0] > 0.3 and g[1] < len(x) / sr - 0.3]
    if len(gaps) < n - 1:
        raise RuntimeError(f"whole-reel voice: found {len(gaps)} pauses for {n} scenes")
    cuts = sorted(sorted(gaps, key=lambda g: g[1] - g[0], reverse=True)[:n - 1])
    bounds = [0.0] + [(a + b) / 2 for a, b in cuts] + [len(x) / sr]
    total, tw = len(x) / sr, float(sum(words))
    for i in range(n):                                   # each piece must roughly match its scene's length
        ratio = (bounds[i + 1] - bounds[i]) / (total * words[i] / tw)
        if not 0.45 <= ratio <= 2.2:
            raise RuntimeError(f"whole-reel voice: scene {i} split looks wrong (ratio {ratio:.2f})")
    out = []
    for i, sc in enumerate(scenes):
        seg = _trim(x[int(bounds[i] * sr):int(bounds[i + 1] * sr)], sr, lead=0.08, tail=0.25)
        path, d = _save(seg, sr, f"work/voice_{i}.wav")
        ws = pause_words(texts[i], seg, sr)
        out.append((path, d, voice.align(sc["narration"], ws, d)))
    log(f"  whole-reel voice OK ({model}, 1 request)")
    return out


def speak_scenes(scenes):
    """Voice every scene with the best provider that can do ALL of them. Returns [(path, secs, words)].
    STRICT_VOICE=true: never fall back to the robotic Edge voice - fail instead."""
    global LAST
    errors = []
    provs = order()
    if os.environ.get("STRICT_VOICE", "false").lower() == "true" and len(provs) > 1:
        provs = [p for p in provs if p != "edge"]
    for prov in provs:
        fn, workers = PROVIDERS[prov]
        log(f"🎙️ Voicing {len(scenes)} scenes with {prov}...")
        if prov == "gemini":
            try:
                res = _gemini_reel(scenes)
                for i, (p, d, _) in enumerate(res):
                    log(f"  Scene {i}: {d:.1f}s - {scenes[i]['narration'][:50]}...")
                LAST = prov
                return res
            except Exception as e:
                log(f"  whole-reel voice failed ({str(e)[:160]}) - voicing scene by scene")
                if "429" in str(e) and "quota" in str(e).lower():
                    errors.append(f"gemini: {str(e)[:200]}")
                    log("  ⚠️ gemini daily quota used up")
                    continue
            workers = 1                                  # gentle on per-minute limits
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
                res = list(ex.map(lambda a: fn(*a), enumerate(scenes)))
            for i, (p, d, _) in enumerate(res):
                log(f"  Scene {i}: {d:.1f}s - {scenes[i]['narration'][:50]}...")
            LAST = prov
            return res
        except Exception as e:
            errors.append(f"{prov}: {str(e)[:200]}")
            log(f"  ⚠️ {prov} voice failed, trying the next provider: {str(e)[:200]}")
    raise RuntimeError("No human-like voice available (STRICT_VOICE): " + " | ".join(errors)
                       if os.environ.get("STRICT_VOICE", "false").lower() == "true" else
                       "All voice providers failed: " + " | ".join(errors))


def needs_devanagari():
    """Hinglish: is a Devanagari copy of the script needed by any provider we may use?"""
    first = order()[0]
    return first == "elevenlabs" or (first == "gemini" and C.GEMINI_SPEAK_DEVANAGARI) or C.SPEAK_DEVANAGARI
