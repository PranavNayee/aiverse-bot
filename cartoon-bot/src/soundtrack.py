"""Builds ONE continuous audio track for the whole reel (no clicks/gaps at scene cuts):
voice clips laid end-to-end at their scene start times + an optional soft background music bed that is
synthesised in code (or taken from assets/music) and automatically ducked under the voice.
Also returns per-video-frame voice loudness, which drives the mascot's lip-sync."""
import glob, os, random, subprocess, wave
import numpy as np
from util import log

SR = 44100


def load_pcm(path, sr=SR, af=None):
    """Decode any audio file to mono float32 in [-1, 1] (optionally through an ffmpeg filter chain)."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path] + (["-af", af] if af else []) +
                       ["-f", "s16le", "-ac", "1", "-ar", str(sr), "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def write_wav(path, x, sr=SR):
    x = np.clip(np.nan_to_num(x), -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def _smooth(x, n):
    if n <= 1:
        return x
    k = np.ones(n, dtype=np.float32) / n
    return np.convolve(x, k, mode="same")


def synth_bed(seconds, sr=SR, seed=7):
    """Gentle lo-fi pad + soft plucked arpeggio (royalty-free because it is generated here)."""
    rng = random.Random(seed)
    n = int(seconds * sr)
    t = np.arange(n, dtype=np.float32) / sr
    prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]          # Am  F  C  G (MIDI)
    rng.shuffle(prog[1:])
    bar = 3.2
    hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)
    out = np.zeros(n, dtype=np.float32)
    nb = int(seconds / bar) + 2
    for b in range(nb):
        chord = prog[b % len(prog)]
        s0, s1 = int(max(0, (b * bar - 0.4) * sr)), int(min(n, ((b + 1) * bar + 0.4) * sr))
        if s0 >= n:
            break
        seg = t[s0:s1]
        L = len(seg)
        env = np.clip(np.sin(np.linspace(0, np.pi, L, dtype=np.float32)), 0, 1) ** 0.8         # soft swell per chord
        pad = np.zeros(L, dtype=np.float32)
        for m in chord:
            for det in (-0.0025, 0.0025):
                f = hz(m - 12) * (1 + det)
                pad += np.sin(2 * np.pi * f * seg) + 0.25 * np.sin(4 * np.pi * f * seg)
        out[s0:s1] += 0.035 * pad * env
        # arpeggio: 8 plucks per bar
        for k in range(8):
            st = int((b * bar + k * bar / 8) * sr)
            if st >= n:
                break
            m = chord[[0, 1, 2, 1, 0, 2, 1, 2][k]] + 12
            ln = min(int(0.6 * sr), n - st)
            tt = np.arange(ln, dtype=np.float32) / sr
            out[st:st + ln] += 0.05 * np.sin(2 * np.pi * hz(m) * tt) * np.exp(-tt * 7)
    fade = min(int(1.0 * sr), n // 4)
    if fade:
        out[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        out[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    return out


def _music(seconds, music_dir):
    files = sorted(glob.glob(os.path.join(music_dir, "*.mp3")) + glob.glob(os.path.join(music_dir, "*.wav")) +
                   glob.glob(os.path.join(music_dir, "*.m4a"))) if music_dir else []
    n = int(seconds * SR)
    if files:
        try:
            x = load_pcm(random.choice(files))
            if len(x) < n:
                x = np.tile(x, n // max(len(x), 1) + 1)
            x = x[:n]
            x = x / (np.sqrt(np.mean(x ** 2)) + 1e-6) * 0.05            # normalise to a quiet bed
            fade = min(SR, n // 4)
            x[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
            return x
        except Exception as e:
            log("Music file failed, using generated bed:", e)
    return synth_bed(seconds)


def whoosh(sr=SR, dur=0.42, seed=3):
    """Soft transition whoosh: band-limited noise with a quick swell (generated, royalty-free)."""
    rng = np.random.default_rng(seed)
    n = int(dur * sr)
    spec = np.fft.rfft(rng.standard_normal(n).astype(np.float32))
    f = np.fft.rfftfreq(n, 1 / sr)
    spec *= np.exp(-((np.log(f + 1) - np.log(1400)) ** 2) / 0.9)          # soft band around 1.4 kHz
    x = np.fft.irfft(spec, n).astype(np.float32)
    t = np.linspace(0, 1, n, dtype=np.float32)
    env = (t ** 1.6) * np.exp(-((t - 0.62) ** 2) / 0.05) / 0.62 ** 1.6
    x *= env
    return 0.11 * x / (np.max(np.abs(x)) + 1e-6)


def build(voice_clips, starts, total, out_wav, fps, music=True, music_dir=None, voice_af=None, sfx_at=()):
    """voice_clips: audio paths; starts: start second of each clip; total: reel length.
    Returns per-frame voice level array (0..1) for lip-sync."""
    n = int(round(total * SR))
    voice = np.zeros(n, dtype=np.float32)
    for path, st in zip(voice_clips, starts):
        x = load_pcm(path, af=voice_af)
        s = int(round(st * SR))
        e = min(n, s + len(x))
        if e > s:
            voice[s:e] += x[:e - s]
    mix = voice.copy()
    if music:
        bed = _music(total, music_dir)
        bed = np.pad(bed, (0, max(0, n - len(bed))))[:n]                # exact length, whatever the source
        env = _smooth(np.abs(voice), int(0.25 * SR))
        env = env / (np.percentile(env[env > 1e-4], 90) + 1e-6) if np.any(env > 1e-4) else env
        duck = 1.0 - 0.65 * np.clip(env, 0, 1)                            # music dips while the bot talks
        mix += bed * duck
    if sfx_at:
        w = whoosh()
        for st in sfx_at:                                                 # lands just before each scene cut
            a = int(max(0.0, st - 0.3) * SR)
            b = min(n, a + len(w))
            mix[a:b] += w[:b - a]
    peak = float(np.max(np.abs(mix))) or 1.0
    if peak > 0.98:
        mix *= 0.98 / peak
    write_wav(out_wav, mix)

    # per-frame loudness for the mouth
    hop = SR / fps
    frames = int(round(total * fps))
    lv = np.zeros(frames, dtype=np.float32)
    for f in range(frames):
        a, b = int(f * hop), int((f + 1) * hop)
        seg = voice[a:b]
        lv[f] = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0
    ref = np.percentile(lv[lv > 0.005], 85) if np.any(lv > 0.005) else 1.0
    lv = np.clip(lv / (ref + 1e-6), 0, 1)
    out = np.zeros_like(lv)                                               # fast attack, slower release
    for i in range(len(lv)):
        prev = out[i - 1] if i else 0.0
        out[i] = lv[i] if lv[i] > prev else prev * 0.6 + lv[i] * 0.4
    return out
