import math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 30
TAU = 2 * math.pi
EMOJI_FONTS = ["/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", "/usr/share/fonts/noto/NotoColorEmoji.ttf",
               "/usr/share/fonts/truetype/noto-color-emoji/NotoColorEmoji.ttf"]

def ease_out_back(p):
    p = min(max(p, 0.0), 1.0) - 1
    return 1 + 2.70158 * p ** 3 + 1.70158 * p ** 2

def envelope(audio_path, nframes):
    """Voice loudness per video frame, 0..1 (smoothed). Drives the mouth and the 'beat' zoom."""
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", audio_path, "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                       capture_output=True)
    x = np.frombuffer(p.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    n = 16000 // FPS
    env = np.zeros(nframes, dtype=np.float32)
    for i in range(nframes):
        seg = x[i * n:(i + 1) * n]
        if len(seg):
            env[i] = float(np.sqrt(np.mean(seg * seg)))
    voiced = env[env > 0.01]
    ref = float(np.percentile(voiced, 85)) if len(voiced) else 1.0
    env = np.clip(env / max(ref, 1e-4), 0, 1.0)
    sm = env.copy()
    for i in range(1, nframes):
        sm[i] = 0.6 * env[i] + 0.4 * sm[i - 1]
    return sm

def load_emoji(ch, size=300):
    """Colour emoji as an RGBA numpy array (BGR order handled by caller), or None if no emoji font."""
    if not ch:
        return None
    for fp in EMOJI_FONTS:
        if os.path.exists(fp):
            try:
                im = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
                ImageDraw.Draw(im).text((20, 20), ch, font=ImageFont.truetype(fp, 109), embedded_color=True)
                box = im.getbbox()
                if not box:
                    return None
                im = im.crop(box); k = size / max(im.size)
                im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
                return np.asarray(im)           # H x W x 4 (RGBA)
            except Exception:
                return None
    return None
