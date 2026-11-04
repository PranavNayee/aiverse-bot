"""2D cut-out animation engine: rigged characters + lip-sync + emotions + props + camera.
Frames are drawn with Pillow and streamed straight into ffmpeg (no frame files on disk)."""
import math, os, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import characters as CH

W, H, FPS = 1080, 1920, 30
FEET_Y = 1500
EMOJI_FONTS = ["/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
               "/usr/share/fonts/noto/NotoColorEmoji.ttf",
               "/usr/share/fonts/truetype/noto-color-emoji/NotoColorEmoji.ttf"]
EMOTION = {"neutral": ("neutral", "flat"), "happy": ("raised", "smile"), "surprised": ("raised", "o"),
           "angry": ("angry", "frown"), "sad": ("sad", "frown")}
BASE_SCALE = {"chintu": 0.95, "mintu": 0.88}
MOUTHS = ["closed", "small", "open", "wide"]
TAU = 2 * math.pi

# ----------------------------------------------------------------- small helpers
def ease_out_back(p):
    p = min(max(p, 0.0), 1.0) - 1
    return 1 + 2.70158 * p ** 3 + 1.70158 * p ** 2

def lerp(a, b, k):
    return a + (b - a) * k

def blit(dst, src, x, y):
    """alpha_composite that tolerates negative / out-of-range positions."""
    x, y = int(round(x)), int(round(y)); sx = sy = 0
    if x < 0: sx, x = -x, 0
    if y < 0: sy, y = -y, 0
    w = min(src.width - sx, dst.width - x); h = min(src.height - sy, dst.height - y)
    if w > 0 and h > 0:
        dst.alpha_composite(src, (x, y), (sx, sy, sx + w, sy + h))

def envelope(audio_path, nframes):
    """Loudness per video frame (0..1) used for lip-sync."""
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
        sm[i] = 0.55 * env[i] + 0.45 * sm[i - 1]
    idx = np.where(sm < 0.12, 0, np.where(sm < 0.32, 1, np.where(sm < 0.62, 2, 3)))
    med = idx.copy()
    for i in range(1, nframes - 1):
        med[i] = int(np.median(idx[i - 1:i + 2]))
    return sm, med

def load_emoji(ch, size=260):
    if not ch:
        return None
    for fp in EMOJI_FONTS:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 109)
                im = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
                ImageDraw.Draw(im).text((20, 20), ch, font=font, embedded_color=True)
                box = im.getbbox()
                if not box:
                    return None
                im = im.crop(box); k = size / max(im.size)
                return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
            except Exception:
                return None
    return None

def prep_bg(path):
    bg = Image.open(path).convert("RGB")
    k = max(int(W * 1.12) / bg.width, int(H * 1.12) / bg.height)
    bg = bg.resize((int(bg.width * k) + 1, int(bg.height * k) + 1), Image.LANCZOS)
    left, top = (bg.width - int(W * 1.12)) // 2, (bg.height - int(H * 1.12)) // 2
    bg = bg.crop((left, top, left + int(W * 1.12), top + int(H * 1.12)))
    return bg.filter(ImageFilter.GaussianBlur(1.6))      # slight blur so the characters pop

# ----------------------------------------------------------------- actor
class Actor:
    def __init__(self, name, x, dur, seed, scale_mult=1.0):
        self.name, self.rig, self.x = name, CH.get_rig(name), x
        self.scale = BASE_SCALE[name] * scale_mult
        r = random.Random(seed)
        self.ph = r.random() * TAU
        self.blinks, t = [], r.uniform(0.9, 2.2)
        while t < dur:
            self.blinks.append(t); t += r.uniform(2.0, 3.8)

    def draw(self, t, st):
        """st: dict(speaking, e, mouth, emotion, k (reaction 0..1), kind, look, dx, dy, ent)"""
        rig, ph = self.rig, self.ph
        M, MT = rig.margins
        bw, bh = rig.body.size
        cw, chh = bw + 2 * M, bh + MT + 30
        cv = Image.new("RGBA", (cw, chh), (0, 0, 0, 0))
        e = st["e"] if st["speaking"] else 0.0
        k, kind = st["k"], st["kind"]
        brow, closed = EMOTION.get(st["emotion"], EMOTION["neutral"])
        if kind == "shake" and k > 0: brow, closed = "angry", "frown"
        if kind == "jump" and k > 0:  brow, closed = "raised", "smile"
        if kind == "shock" and k > 0: brow, closed = "raised", "o"
        mouth = closed
        if st["speaking"] and st["mouth"] > 0:
            mouth = MOUTHS[st["mouth"]]
        if kind == "shock" and k > 0.3 and not st["speaking"]:
            mouth = "open"

        blit(cv, rig.body, M, MT)
        # arms: idle sway + speech gestures + reactions
        idle = 7 + 3 * math.sin(TAU * 0.7 * t + ph)
        gest = e * (24 + 26 * math.sin(TAU * 1.6 * t + ph))
        angL = -(idle + max(gest, 0) * (0.6 + 0.4 * math.sin(TAU * 1.2 * t + ph + 1)))
        angR = idle + max(gest, 0) * (0.6 + 0.4 * math.sin(TAU * 1.1 * t + ph))
        if kind in ("jump", "shock") and k > 0:
            up = 150 if kind == "jump" else 70
            angL, angR = lerp(angL, -up, k), lerp(angR, up, k)
        if kind == "shake" and k > 0:
            angL, angR = lerp(angL, -35, k), lerp(angR, 35, k)
        for im, ang, (sx, sy) in ((rig.arm_l, angL, rig.shoulders[0]), (rig.arm_r, angR, rig.shoulders[1])):
            a = im.rotate(ang, Image.BILINEAR, center=rig.arm_pivot)
            blit(cv, a, M + sx - rig.arm_pivot[0], MT + sy - rig.arm_pivot[1])
        # head
        ha = 2.2 * math.sin(TAU * 0.45 * t + ph) + e * 4.5 * math.sin(TAU * 2.4 * t + ph)
        if kind == "shake" and k > 0: ha += 7 * math.sin(TAU * 12 * t) * k
        blink = any(b <= t < b + 0.14 for b in self.blinks)
        head = rig.head(st["look"], blink, brow, mouth).rotate(ha, Image.BILINEAR, center=rig.head_pivot)
        hy = 3 * math.sin(TAU * 0.8 * t + ph) - e * 5
        blit(cv, head, M + rig.neck[0] - rig.head_pivot[0], MT + rig.neck[1] - rig.head_pivot[1] + hy)

        breath = 0.012 * math.sin(TAU * 0.8 * t + ph)
        pop = 1 + (0.10 * k if kind == "shock" else 0)
        ent = st["ent"]
        sx_ = self.scale * (1 - breath * 0.5) * pop * (0.65 + 0.35 * ent)
        sy_ = self.scale * (1 + breath) * pop * (0.65 + 0.35 * ent)
        out = cv.resize((max(1, int(cw * sx_)), max(1, int(chh * sy_))), Image.BILINEAR)
        ax, ay = (M + bw / 2) * sx_, (MT + bh) * sy_
        return out, self.x + st["dx"] - ax, FEET_Y + st["dy"] + (1 - ent) * 320 - ay, sx_

# ----------------------------------------------------------------- scene renderer
def render_scene(spec, out_path, snapshot=None):
    """spec keys: bg, audio, dur, present[list], speaker, emotions{}, prop, reaction, idx
    snapshot: (jpg_path, fraction_of_scene) to save one frame (used as the Instagram cover)."""
    dur, idx = float(spec["dur"]), int(spec.get("idx", 0))
    nframes = max(2, int(round(dur * FPS)))
    sm, mouth_idx = envelope(spec["audio"], nframes)
    bg = prep_bg(spec["bg"])
    bgw, bgh = bg.size
    present = [n for n in ("chintu", "mintu") if n in spec["present"]] or ["chintu", "mintu"]
    xs = {"chintu": 310, "mintu": 790} if len(present) == 2 else {present[0]: 540}
    mult = 1.0 if len(present) == 2 else 1.15
    actors = {n: Actor(n, xs[n], dur, seed=idx * 31 + len(n), scale_mult=mult) for n in present}
    prop = load_emoji(spec.get("prop", ""))
    kind = spec.get("reaction", "none")
    tr = min(max(dur - 0.9, 0.2), max(0.8, 0.55 * dur))
    shadow = Image.new("RGBA", (460, 80), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse((10, 10, 450, 70), fill=(0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", spec["audio"], "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
           "-af", "apad", "-t", f"{dur:.3f}", "-c:a", "aac", "-ar", "44100", "-ac", "2", out_path]
    errf = open(out_path + ".err", "wb")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=errf)
    snap_frame = int(snapshot[1] * nframes) if snapshot else -1
    try:
        for f in range(nframes):
            t = f / FPS
            # background with slow zoom + drift
            z = 1 + 0.05 * (t / dur)
            cx = bgw / 2 + 30 * math.sin(TAU * 0.05 * t + idx)
            cy = bgh / 2
            box = (cx - W / (2 * z), cy - H / (2 * z), cx + W / (2 * z), cy + H / (2 * z))
            frame = bg.resize((W, H), Image.BILINEAR, box=box).convert("RGBA")

            kk = 0.0
            if kind != "none" and tr <= t <= tr + 0.9:
                kk = math.sin(math.pi * (t - tr) / 0.9)
            ent = ease_out_back(t / 0.45)
            drawn = []
            for n, a in actors.items():
                speaking = (spec["speaker"] == n)
                other = [o for o in present if o != n]
                look = 0 if not other else (1 if xs[other[0]] > xs[n] else -1)
                if int(t * 0.35 + a.ph) % 3 == 2 and (t * 0.35 + a.ph) % 1 < 0.2:
                    look = 0                                         # occasional glance at camera
                st = {"speaking": speaking, "e": float(sm[f]), "mouth": int(mouth_idx[f]),
                      "emotion": spec.get("emotions", {}).get(n, "neutral"), "k": kk, "kind": kind,
                      "look": look, "ent": ent, "dx": 0.0, "dy": 0.0}
                if kind == "jump":  st["dy"] = -170 * kk
                if kind == "shake": st["dx"] = 14 * math.sin(TAU * 15 * t) * kk
                if speaking:        st["dy"] -= float(sm[f]) * 10
                drawn.append(a.draw(t, st))
            for (img, px, py, s) in drawn:                            # shadows first
                sh = shadow.resize((int(460 * s * 0.85), int(80 * s * 0.85)), Image.BILINEAR)
                blit(frame, sh, px + img.width / 2 - sh.width / 2, FEET_Y - sh.height / 2 + 14)
            for (img, px, py, s) in drawn:
                blit(frame, img, px, py)
            if prop is not None and t > 0.35:                         # emoji prop pops in above the scene
                p = ease_out_back((t - 0.35) / 0.5)
                size = max(8, int(prop.width * (0.2 + 0.8 * p)))
                pim = prop.resize((size, max(8, int(prop.height * size / prop.width))), Image.BILINEAR)
                pim = pim.rotate(8 * math.sin(TAU * 1.1 * t), Image.BILINEAR, expand=True)
                blit(frame, pim, 540 - pim.width / 2, 470 - pim.height / 2 + 14 * math.sin(TAU * 0.8 * t))
            # camera: punch-in on reactions, shake on angry
            zc = 1.0 + (0.07 * kk if kind in ("shock", "jump") else 0.0)
            shx = (10 * math.sin(TAU * 18 * t) * kk) if kind == "shake" else 0.0
            if zc > 1.002 or shx:
                bx0 = W / 2 - W / (2 * zc) + shx; by0 = H / 2 - H / (2 * zc)
                frame = frame.resize((W, H), Image.BILINEAR, box=(bx0, by0, bx0 + W / zc, by0 + H / zc))
            rgb = frame.convert("RGB")
            if f == snap_frame:
                rgb.save(snapshot[0], quality=90)
            proc.stdin.write(rgb.tobytes())
        proc.stdin.close()
        rc = proc.wait()
    except BrokenPipeError:
        rc = proc.wait()
    finally:
        errf.close()
    if rc != 0:
        raise RuntimeError("ffmpeg (animation) failed: " + open(out_path + ".err", errors="ignore").read()[-1200:])
    os.remove(out_path + ".err")
