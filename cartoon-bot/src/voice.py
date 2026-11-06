"""Text-to-speech with Microsoft Edge neural voices (free). Also returns WORD TIMINGS so the on-screen
captions highlight each word exactly when it is spoken."""
import asyncio, re, subprocess, time, edge_tts
import config as C
from util import log


def clean_for_tts(text):
    text = re.sub(r"[^ऀ-ॿ\w\s,.?!।'\-:;]", " ", text)   # drop emojis / odd symbols
    return re.sub(r"\s+", " ", text).strip()


async def _tts(text, cfg, out):
    try:
        com = edge_tts.Communicate(text, cfg["voice"], rate=cfg["rate"], pitch=cfg["pitch"], boundary="WordBoundary")
    except TypeError:                                   # edge-tts < 7 always sends word boundaries
        com = edge_tts.Communicate(text, cfg["voice"], rate=cfg["rate"], pitch=cfg["pitch"])
    words = []
    with open(out, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                st = ch["offset"] / 1e7
                words.append((st, st + ch["duration"] / 1e7, ch["text"]))
    return words


def estimate_words(text, dur):
    """Fallback timing when the TTS gives no word boundaries: spread words by their length."""
    ws = text.split()
    if not ws:
        return []
    lead, tail = 0.1, 0.25
    span = max(dur - lead - tail, 0.5)
    weights = [len(w) + 2 for w in ws]
    tot, t, out = sum(weights), lead, []
    for w, k in zip(ws, weights):
        d = span * k / tot
        out.append((t, t + d * 0.9, w)); t += d
    return out


def synth(text, speaker, out):
    """Writes the mp3 to `out` and returns a list of (start_s, end_s, word)."""
    cfg = C.VOICES.get(speaker, C.VOICES["narrator"])
    text = clean_for_tts(text)
    last = None
    for attempt in range(4):
        try:
            words = asyncio.run(_tts(text, cfg, out))
            d = duration(out)
            if d > 0.3:
                return words or estimate_words(text, d)
            last = "empty audio"
        except Exception as e:
            last = e
        log(f"  TTS retry {attempt+1}: {last}")
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"Voice generation failed: {last}")


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())
