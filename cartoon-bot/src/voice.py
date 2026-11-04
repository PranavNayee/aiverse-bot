import asyncio, re, subprocess, time, edge_tts
import config as C
from util import log

def clean_for_tts(text):
    text = re.sub(r"[^\u0900-\u097F\w\s,.?!।'\-:;]", " ", text)   # drop emojis / odd symbols
    return re.sub(r"\s+", " ", text).strip()

async def _tts(text, cfg, out):
    await edge_tts.Communicate(text, cfg["voice"], rate=cfg["rate"], pitch=cfg["pitch"]).save(out)

def synth(text, speaker, out):
    cfg = C.VOICES.get(speaker, C.VOICES["narrator"])
    text = clean_for_tts(text)
    last = None
    for attempt in range(4):
        try:
            asyncio.run(_tts(text, cfg, out))
            if duration(out) > 0.3:
                return
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

def generate_silence(output_path, duration_seconds):
    """Generate silent audio file of specified duration"""
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={duration_seconds}",
        "-c:a", "aac", output_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    log(f"Generated {duration_seconds}s silence: {output_path}")
