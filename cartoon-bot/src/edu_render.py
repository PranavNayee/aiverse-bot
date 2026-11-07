"""Animated lesson scenes drawn entirely by code (faceless, crisp, consistent, no AI images).
Every scene kind shows the lesson's REAL content. Frames stream straight into ffmpeg together with the scene's own audio,
so picture and voice can never drift apart."""
import functools, math, os, re, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
TAU = 2 * math.pi
FONT_DIR = "/usr/share/fonts/truetype/noto/"
FONT_FALLBACK = "/usr/share/fonts/truetype/dejavu/"
EMOJI_FONTS = [(FONT_DIR + "NotoColorEmoji.ttf", 109), ("/usr/share/fonts/noto/NotoColorEmoji.ttf", 109),
               ("/System/Library/Fonts/Apple Color Emoji.ttc", 160)]

TEXT, MUTED, DARK = (244, 246, 255), (156, 166, 196), (12, 14, 34)
LEVEL_COLOR = {"basics": (45, 212, 191), "intermediate": (251, 191, 36), "advanced": (244, 114, 182),
               "weekend": (167, 139, 250), "trick": (251, 146, 60)}
INDIGO, GREEN, RED = (129, 140, 248), (74, 222, 128), (251, 113, 133)
EN = os.environ.get("LANGUAGE_MODE", "hinglish") == "english_only"
BRAND = (os.environ.get("SERIES_NAME") or "AIVerse").upper()[:14]
UI = {"remember": "REMEMBER" if EN else "YAAD RAKHO", "next": "NEXT LESSON",
      "daily": "A new AI video every day" if EN else "Roz ek naya AI video"}
TOP, BOTTOM = 270, 1290            # safe content band (captions live below, phone UI covers the very top/bottom)

# ---------------------------------------------------------------- helpers
_MAC = "/System/Library/Fonts/"
@functools.lru_cache(maxsize=None)
def font(size, bold=True, mono=False):
    size = int(size)
    names = ([("NotoSansMono-Bold.ttf" if bold else "NotoSansMono-Regular.ttf")] if mono else
             [("NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf")])
    paths = [base + n for base in (FONT_DIR, FONT_FALLBACK)
             for n in names + ["DejaVuSansMono-Bold.ttf" if mono else "DejaVuSans-Bold.ttf"]]
    # macOS fallbacks (local previews only; GitHub runners use the Noto fonts above)
    paths += ([_MAC + "Menlo.ttc"] if mono else
              [_MAC + "Supplemental/Arial Bold.ttf" if bold else _MAC + "Supplemental/Arial.ttf"])
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def prog(t, start, length):
    return clamp((t - start) / max(length, 1e-6))

def ease_out(p):
    return 1 - (1 - p) ** 3

def ease_back(p):
    p = clamp(p) - 1
    return 1 + 2.70158 * p ** 3 + 1.70158 * p ** 2

def mix(c1, c2, k):
    return tuple(int(a + (b - a) * k) for a, b in zip(c1, c2))

def rgba(c, a=1.0):
    return (c[0], c[1], c[2], int(255 * clamp(a)))

@functools.lru_cache(maxsize=None)
def emoji_img(ch, size):
    if not ch:
        return None
    for fp, fsize in EMOJI_FONTS:
        if os.path.exists(fp):
            try:
                im = Image.new("RGBA", (fsize * 2, fsize * 2), (0, 0, 0, 0))
                ImageDraw.Draw(im).text((20, 20), ch, font=ImageFont.truetype(fp, fsize), embedded_color=True)
                box = im.getbbox()
                if box:
                    im = im.crop(box)
                    k = size / max(im.size)
                    return im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
            except Exception:
                return None
    return None

def put(frame, im, cx, cy, scale=1.0, alpha=1.0):
    """Paste an RGBA sprite centred at (cx, cy) with scale and opacity."""
    if im is None or alpha <= 0.01 or scale <= 0.01:
        return
    # Safety checks for coordinates and scale
    if not (0 <= cx <= W and 0 <= cy <= H):
        return  # Skip if outside frame
    scale = max(0.01, min(scale, 10.0))  # Clamp scale to reasonable range
    alpha = clamp(alpha, 0, 1)
    
    if abs(scale - 1) > 0.01:
        new_w = max(1, int(im.width * scale))
        new_h = max(1, int(im.height * scale))
        try:
            im = im.resize((new_w, new_h), Image.BILINEAR)
        except Exception:
            return  # Skip if resize fails
    if alpha < 0.99:
        im = im.copy()
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im.putalpha(a)
    
    # Calculate paste position
    paste_x = int(cx - im.width / 2)
    paste_y = int(cy - im.height / 2)
    
    # Check if image is within frame bounds
    if paste_x + im.width < 0 or paste_x > W or paste_y + im.height < 0 or paste_y > H:
        return  # Completely outside frame
    
    try:
        frame.paste(im, (paste_x, paste_y), im)     # frames are RGB: the sprite's alpha is the blend mask
    except Exception:
        pass  # Silently skip if paste fails

def wrap(d, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=fnt) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines

def fit(d, text, maxw, maxh, start=96, minimum=40, bold=True, line_gap=1.18):
    for size in range(start, minimum - 1, -4):
        f = font(size, bold)
        lines = wrap(d, text, f, maxw)
        if len(lines) * size * line_gap <= maxh and all(d.textlength(l, font=f) <= maxw for l in lines):
            return f, lines, size
    f = font(minimum, bold)
    return f, wrap(d, text, f, maxw), minimum

def ctext(d, x, y, text, fnt, fill):
    d.text((x, y), text, font=fnt, fill=fill, anchor="mm")

def card(d, box, radius=36, fill=(255, 255, 255, 22), outline=None, width=3):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width if outline else 0)

def glow_sprite(size, color, strength=0.9):
    s = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(s).ellipse((size * .2, size * .2, size * .8, size * .8), fill=rgba(color, strength))
    return s.filter(ImageFilter.GaussianBlur(size * 0.14))

_GRAD = None
def base_gradient():
    global _GRAD
    if _GRAD is None:
        y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
        top, bot = np.array((13, 15, 38), np.float32), np.array((34, 22, 74), np.float32)
        arr = (top + (bot - top) * y)[:, None, :].repeat(W, 1)
        img = Image.fromarray(arr.astype(np.uint8), "RGB")   # RGB on purpose: RGBA ink then BLENDS (on RGBA it overwrites)
        d = ImageDraw.Draw(img, "RGBA")
        for gx in range(0, W + 1, 90):                      # faint blueprint grid
            d.line([(gx, 0), (gx, H)], fill=(255, 255, 255, 8), width=1)
        for gy in range(0, H + 1, 90):
            d.line([(0, gy), (W, gy)], fill=(255, 255, 255, 8), width=1)
        _GRAD = img
    return _GRAD

@functools.lru_cache(maxsize=None)
def _orb(color, size):
    return glow_sprite(size, color, 0.55)

# ---------------------------------------------------------------- common chrome (brand bar, progress, drifting glow)
def chrome(frame, ctx, t):
    acc = ctx["accent"]
    for i, (cx, cy, r, col) in enumerate(((220, 520, 760, acc), (880, 1180, 820, INDIGO), (500, 1700, 700, mix(acc, INDIGO, .5)))):
        put(frame, _orb(col, r), cx + 40 * math.sin(TAU * 0.04 * (ctx["t0"] + t) + i), cy + 50 * math.cos(TAU * 0.03 * (ctx["t0"] + t) + i), 1.0, 0.33)
    d = ImageDraw.Draw(frame, "RGBA")
    # brand pill (top-left) and lesson badge (top-right)
    card(d, (60, 92, 372, 168), 38, (255, 255, 255, 28), rgba(acc, .8), 2)
    d.ellipse((84, 119, 108, 143), fill=rgba(acc))
    d.text((124, 130), BRAND, font=font(36 if len(BRAND) <= 10 else 30), fill=TEXT, anchor="lm")
    badge = ctx["label"]
    bw = d.textlength(badge, font=font(32)) + 54
    card(d, (W - 60 - bw, 92, W - 60, 168), 38, rgba(acc, .22), rgba(acc, .9), 2)
    d.text((W - 60 - bw / 2, 130), badge, font=font(32), fill=rgba(acc), anchor="mm")
    # lesson progress (whole video)
    p = clamp((ctx["t0"] + t) / ctx["total"])
    d.rounded_rectangle((60, 206, W - 60, 220), radius=7, fill=(255, 255, 255, 40))
    if p > 0:
        d.rounded_rectangle((60, 206, 60 + (W - 120) * p, 220), radius=7, fill=rgba(acc))

# ---------------------------------------------------------------- scene drawers (each draws ONE frame at scene-time t)
def s_hook(frame, d, v, t, dur, ctx):
    acc = ctx["accent"]
    e = emoji_img(v.get("emoji") or "🤔", 300)
    pop = ease_back(prog(t, 0.05, 0.6))
    ring = 0.5 + 0.5 * math.sin(TAU * 0.7 * t)
    for k in (0, 1):                                   # pulsing rings behind the emoji
        r = 250 + 55 * ((ring + k * .5) % 1)
        r = max(r, 10)  # Safety: ensure positive radius
        alpha_val = .35 * (1 - ((ring + k * .5) % 1))
        if alpha_val > 0.01:  # Only draw if visible
            d.ellipse((540 - r, 600 - r, 540 + r, 600 + r), outline=rgba(acc, alpha_val), width=5)
    if e and pop > 0:  # Only draw emoji if it exists and is visible
        put(frame, e, 540, 600 + 10 * math.sin(TAU * 0.6 * t), pop)
    f, lines, size = fit(d, v["text"], 900, 400, 100, 56)
    y0 = 960
    for i, ln in enumerate(lines):
        p = ease_out(prog(t, 0.35 + 0.18 * i, 0.5))
        if p > 0:  # Only draw if visible
            ctext(d, 540, y0 + i * size * 1.2 + (1 - p) * 50, ln, f, rgba(TEXT, p))
    wbar = 560 * ease_out(prog(t, 0.9, 0.7))
    if wbar > 2:  # Only draw bar if it's visible
        d.rounded_rectangle((540 - wbar / 2, y0 + len(lines) * size * 1.2 + 20, 540 + wbar / 2, y0 + len(lines) * size * 1.2 + 32), 6, fill=rgba(acc))

def s_bullets(frame, d, v, t, dur, ctx):
    acc, items = ctx["accent"], v["items"]
    ctext(d, 540, 350, v.get("heading", ""), font(68), rgba(acc, ease_out(prog(t, 0.0, 0.5))))
    n = len(items)
    step = clamp((dur - 1.3) / n, 0.6, 1.9)
    ch = min(190, (BOTTOM - 440 - (n - 1) * 34) / n)
    for i, it in enumerate(items):
        p = prog(t, 0.55 + i * step, 0.55)
        if p <= 0:
            continue
        y = 440 + i * (ch + 34)
        e = ease_out(p); xo = (1 - e) * 140
        active = i == max(j for j in range(n) if t >= 0.55 + j * step)
        card(d, (70 + xo, y, W - 70 + xo, y + ch), 34, rgba((255, 255, 255), .10 if not active else .20), rgba(acc, e if active else .25), 3)
        d.ellipse((110 + xo, y + ch / 2 - 40, 190 + xo, y + ch / 2 + 40), fill=rgba(acc, e))
        d.text((150 + xo, y + ch / 2), str(i + 1), font=font(48), fill=DARK, anchor="mm")
        f, lines, size = fit(d, it, 700, ch - 30, 56, 36)
        for j, ln in enumerate(lines):
            d.text((230 + xo, y + ch / 2 + (j - (len(lines) - 1) / 2) * size * 1.15), ln, font=f, fill=rgba(TEXT, e), anchor="lm")

def s_flow(frame, d, v, t, dur, ctx):
    acc, steps = ctx["accent"], v["steps"]
    top = TOP + 40
    if v.get("heading"):
        ctext(d, 540, 340, v["heading"], font(62), rgba(acc, ease_out(prog(t, 0, .5)))); top = 420
    n, gap = len(steps), 78
    avail = BOTTOM - top - (70 if v.get("caption") else 0)
    bh = min(170, (avail - (n - 1) * gap) / n)
    step = clamp((dur - 1.0) / n, 0.5, 1.5)
    for i, st in enumerate(steps):
        y = top + i * (bh + gap)
        p = prog(t, 0.3 + i * step, 0.55)
        if p > 0:
            s = ease_back(p)
            cx, cy = 540, y + bh / 2
            x0, x1, y0, y1 = 540 - 400 * s, 540 + 400 * s, cy - bh / 2 * s, cy + bh / 2 * s
            card(d, (x0, y0, x1, y1), 36, rgba(mix(acc, INDIGO, i / max(n - 1, 1)), .30), rgba(mix(acc, INDIGO, i / max(n - 1, 1)), .95), 4)
            put(frame, emoji_img(st.get("emoji", ""), int(bh * .55)), 200, cy, s)
            f, lines, size = fit(d, st["label"], 500, bh - 30, 58, 34)
            for j, ln in enumerate(lines):
                ctext(d, 600, cy + (j - (len(lines) - 1) / 2) * size * 1.12, ln, f, rgba(TEXT, clamp(p * 1.6)))
        if i < n - 1:                                      # arrow + travelling dot to the next step
            pa = prog(t, 0.3 + (i + 1) * step - 0.25, 0.4)
            if pa > 0:
                ay0, ay1 = y + bh + 8, y + bh + gap - 8
                d.line([(540, ay0), (540, ay0 + (ay1 - ay0) * pa)], fill=rgba(acc, .9), width=7)
                if pa >= 1:
                    d.polygon([(540, ay1 + 4), (516, ay1 - 28), (564, ay1 - 28)], fill=rgba(acc))
                    k = (t * 0.9 + i * .3) % 1
                    d.ellipse((540 - 11, ay0 + (ay1 - ay0 - 20) * k - 11 + 10, 540 + 11, ay0 + (ay1 - ay0 - 20) * k + 11 + 10), fill=rgba(TEXT, .9))
    if v.get("caption"):
        ctext(d, 540, BOTTOM - 20, v["caption"], font(44, False), rgba(MUTED, ease_out(prog(t, dur * .5, .6))))

def s_compare(frame, d, v, t, dur, ctx):
    cols = [(70, 520, v["left_title"], v["left"], RED, 0.3), (560, 1010, v["right_title"], v["right"], GREEN, 0.3 + max(dur * .3, 1.0))]
    for x0, x1, title, items, col, st in cols:
        p = ease_out(prog(t, st, 0.6))
        if p <= 0:
            continue
        yo = (1 - p) * 60
        card(d, (x0, 400 + yo, x1, 1180 + yo), 40, rgba(col, .12), rgba(col, p), 4)
        card(d, (x0 + 24, 430 + yo, x1 - 24, 540 + yo), 28, rgba(col, .85 * p))
        f, lines, size = fit(d, title, 360, 90, 48, 30)
        ctext(d, (x0 + x1) / 2, 485 + yo, " ".join(lines), f, rgba(DARK, p))
        for i, it in enumerate(items):
            pi = ease_out(prog(t, st + .5 + i * .55, .5))
            f2, l2, s2 = fit(d, it, 360, 190, 46, 32, bold=False)
            cy = 680 + i * 170 + yo
            d.ellipse((x0 + 34, cy - 12, x0 + 58, cy + 12), fill=rgba(col, pi))
            for j, ln in enumerate(l2):
                d.text((x0 + 76, cy + (j - (len(l2) - 1) / 2) * s2 * 1.15), ln, font=f2, fill=rgba(TEXT, pi), anchor="lm")
    pv = ease_back(prog(t, 0.9, 0.5))
    if pv > 0:
        r = max(1, 52 * pv + 4 * math.sin(TAU * t))  # Ensure r is always positive
        d.ellipse((540 - r, 790 - r, 540 + r, 790 + r), fill=rgba(DARK), outline=rgba(ctx["accent"]), width=5)
        ctext(d, 540, 790, "VS", font(int(46 * pv) + 1), rgba(TEXT))

def s_network(frame, d, v, t, dur, ctx):
    acc, layers = ctx["accent"], v["layers"]
    if v.get("heading"):
        ctext(d, 540, 340, v["heading"], font(62), rgba(acc, ease_out(prog(t, 0, .5))))
    
    # Safety check for layers
    if not layers or len(layers) < 2:
        layers = [3, 4, 2]  # Default safe network
    
    xs = np.linspace(170, W - 170, len(layers))
    cy, sp = 790, min(140, 620 / max(max(layers), 1))
    pos = [[(xs[i], cy + (j - (n - 1) / 2) * sp) for j in range(n)] for i, n in enumerate(layers)]
    reveal = [prog(t, 0.3 + i * 0.5, 0.5) for i in range(len(layers))]
    wave = (t * 0.55) % 1.0
    for i in range(len(layers) - 1):
        pe = min(reveal[i], reveal[i + 1])
        if pe > 0:  # Only draw if visible
            for a in pos[i]:
                for b in pos[i + 1]:
                    d.line([a, b], fill=rgba(INDIGO, .28 * pe), width=2)
        if pe >= 1:                                      # signal pulses travelling forward
            k = clamp(wave * (len(layers) - 1) - i, 0, 1)
            if 0 < k < 1:
                for a in pos[i]:
                    for b in pos[i + 1]:
                        x, y = a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
                        d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=rgba(acc, .9))
    for i, layer in enumerate(pos):
        glowk = 1 - abs(((wave * (len(layers) - 1)) - i)) if reveal[-1] >= 1 else 0
        for (x, y) in layer:
            r = 36 * ease_back(reveal[i])
            if r < 2:  # Skip tiny/negative circles
                continue
            col = mix(MUTED, acc, clamp(glowk))
            if glowk > 0.2:
                # Safety check for glow radius
                glow_r = max(r + 14, 2)
                d.ellipse((x - glow_r, y - glow_r, x + glow_r, y + glow_r), fill=rgba(acc, .25 * glowk))
            # Safety check for node radius
            node_r = max(r, 2)
            d.ellipse((x - node_r, y - node_r, x + node_r, y + node_r), fill=rgba(col), outline=rgba(TEXT, .9), width=3)
    labels = v.get("labels") or []
    if not labels:
        labels = ["Input"] + ["Hidden"] * (len(layers) - 2) + ["Output"]
    for i in range(len(layers)):
        lab = labels[i] if i < len(labels) else ""
        ctext(d, xs[i], cy + max(layers) * sp / 2 + 70, lab, font(38, False), rgba(MUTED, reveal[i]))

KEYWORDS = {"def", "return", "import", "from", "for", "in", "if", "else", "elif", "print", "class", "while", "lambda", "True", "False", "None", "and", "or", "not", "as", "with"}
def _tokens(line):
    out = []
    for m in re.finditer(r"(#.*$)|(\".*?\"|'.*?')|(\b\d+\.?\d*\b)|(\b[A-Za-z_]\w*\b)|(\s+|.)", line):
        s = m.group(0)
        col = (MUTED if m.group(1) else GREEN if m.group(2) else (251, 191, 36) if m.group(3) else
               (244, 114, 182) if (m.group(4) and s in KEYWORDS) else TEXT)
        out.append((s, col))
    return out

def s_code(frame, d, v, t, dur, ctx):
    acc, lines = ctx["accent"], v["lines"]
    if v.get("heading"):
        ctext(d, 540, 340, v["heading"], font(62), rgba(acc, ease_out(prog(t, 0, .5))))
    p = ease_out(prog(t, 0.1, 0.5))
    top = 430
    card(d, (60, top, W - 60, top + 120 + len(lines) * 84 + 40), 30, (8, 10, 26, int(235 * p)), rgba(acc, .7 * p), 3)
    for k, c in enumerate(((251, 113, 133), (251, 191, 36), (74, 222, 128))):
        d.ellipse((96 + k * 44, top + 38, 120 + k * 44, top + 62), fill=rgba(c, p))
    f = font(42, False, True)
    total = sum(len(l) for l in lines)
    shown = int(total * ease_out(prog(t, 0.6, max(dur * 0.65, 1.5))) ) if True else total
    left = shown
    for i, ln in enumerate(lines):
        x, y = 100, top + 130 + i * 84
        n = min(len(ln), max(left, 0))
        used = 0
        for s, col in _tokens(ln):
            if used >= n:
                break
            seg = s[:n - used]
            d.text((x, y), seg, font=f, fill=rgba(col), anchor="lm")
            x += d.textlength(seg, font=f); used += len(seg)
        if 0 < left <= len(ln) or (left <= 0 and i == 0 and False):
            if int(t * 2.2) % 2 == 0:
                d.rectangle((x + 4, y - 26, x + 22, y + 26), fill=rgba(acc, .9))
        left -= len(ln)

def s_stat(frame, d, v, t, dur, ctx):
    acc = ctx["accent"]
    e = emoji_img(v.get("emoji", ""), 230)
    put(frame, e, 540, 520 + 8 * math.sin(TAU * .6 * t), ease_back(prog(t, .05, .6)))
    big = v["big"]
    shown = big
    m = re.fullmatch(r"(\D*)(\d+)(\D*)", big)
    if m and not (1900 <= int(m.group(2)) <= 2100 and not m.group(1) and not m.group(3)):
        shown = f"{m.group(1)}{int(int(m.group(2)) * ease_out(prog(t, .3, 1.2)))}{m.group(3)}"
    f, lines, size = fit(d, shown if m else big, 940, 260, 230, 90)
    sc = ease_back(prog(t, .2, .6))
    put(frame, glow_sprite(900, acc, .55), 540, 860, 1.0, ease_out(prog(t, .2, .6)) * .7)
    ctext(d, 540, 860, big if not m else shown, f, rgba(mix(TEXT, acc, .35), clamp(sc)))
    f2, l2, s2 = fit(d, v["caption"], 880, 300, 64, 40, bold=False)
    for i, ln in enumerate(l2):
        ctext(d, 540, 1050 + i * s2 * 1.2, ln, f2, rgba(TEXT, ease_out(prog(t, .8 + .15 * i, .5))))

def s_formula(frame, d, v, t, dur, ctx):
    acc = ctx["accent"]
    if v.get("heading"):
        ctext(d, 540, 340, v["heading"], font(62), rgba(acc, ease_out(prog(t, 0, .5))))
    p = ease_back(prog(t, .2, .6))
    h = 150 + 150 * len(v["lines"])
    y0 = 760 - h / 2
    card(d, (70, y0 * (0.5 + 0.5 * p), W - 70, y0 + h), 44, rgba(acc, .16), rgba(acc, clamp(p)), 4)
    for i, ln in enumerate(v["lines"]):
        f, ls, s = fit(d, ln, 880, 130, 92, 44)
        pi = ease_out(prog(t, .5 + i * .6, .6))
        ctext(d, 540, y0 + 105 + i * 150 + (1 - pi) * 30, " ".join(ls), f, rgba(TEXT, pi))
    sweep = (t * 0.45) % 1.4 - 0.2                      # shimmer sweep
    d.rectangle((70 + 940 * sweep, y0 + 20, 70 + 940 * sweep + 40, y0 + h - 20), fill=(255, 255, 255, 22))
    if v.get("note"):
        f, ls, s = fit(d, v["note"], 900, 200, 52, 36, bold=False)
        for i, ln in enumerate(ls):
            ctext(d, 540, y0 + h + 90 + i * s * 1.2, ln, f, rgba(MUTED, ease_out(prog(t, 1.4, .6))))

def s_takeaway(frame, d, v, t, dur, ctx):
    acc = ctx["accent"]
    p = ease_back(prog(t, .1, .6))
    card(d, (70, 420, W - 70, 1010), 50, rgba(acc, .17), rgba(acc, clamp(p)), 4)
    card(d, (110, 380, 520, 470), 40, rgba(acc, clamp(p)))
    ctext(d, 315, 425, UI["remember"], font(44), rgba(DARK, clamp(p)))
    r = 52 * p
    d.ellipse((540 - r, 590 - r, 540 + r, 590 + r), fill=rgba(GREEN, clamp(p)))
    if p > .5:
        d.line([(540 - 22, 592), (540 - 4, 612), (540 + 28, 570)], fill=rgba(DARK), width=11, joint="curve")
    f, lines, size = fit(d, v["text"], 860, 330, 72, 42)
    for i, ln in enumerate(lines):
        ctext(d, 540, 760 + i * size * 1.2, ln, f, rgba(TEXT, ease_out(prog(t, .5 + .15 * i, .5))))
    terms = v["terms"]
    for size in range(40, 25, -2):                       # shrink until all pills fit on one row
        fw = font(size)
        widths = [d.textlength(tm, font=fw) + 56 for tm in terms]
        if sum(widths) + 22 * (len(terms) - 1) <= W - 120:
            break
    x = 540 - (sum(widths) + 22 * (len(terms) - 1)) / 2
    for i, (term, w) in enumerate(zip(terms, widths)):
        pi = ease_back(prog(t, 1.0 + i * .35, .5))
        cx = x + w / 2; x += w + 22
        if pi <= 0:
            continue
        cy = 1130
        card(d, (cx - w / 2 * pi, cy - 40 * pi, cx + w / 2 * pi, cy + 40 * pi), 40, rgba(INDIGO, .35), rgba(INDIGO, 1), 3)
        ctext(d, cx, cy, term, fw, rgba(TEXT, clamp(pi)))

def s_cta(frame, d, v, t, dur, ctx):
    acc = ctx["accent"]
    nxt = UI["next"] if str(ctx.get("label", "")).startswith("Lesson") else "NEXT VIDEO"
    ctext(d, 540, 450, nxt, font(46), rgba(acc, ease_out(prog(t, 0, .4))))
    f, lines, size = fit(d, v["text"], 900, 380, 84, 48)
    for i, ln in enumerate(lines):
        ctext(d, 540, 600 + i * size * 1.2, ln, f, rgba(TEXT, ease_out(prog(t, .3 + .15 * i, .5))))
    pb = ease_back(prog(t, .9, .6))
    pulse = 1 + 0.05 * math.sin(TAU * 1.2 * t)
    if pb > 0:
        w, h = 520 * pb * pulse, 130 * pb * pulse
        card(d, (540 - w / 2, 980 - h / 2, 540 + w / 2, 980 + h / 2), 65, rgba(acc))
        ctext(d, 560, 980, "FOLLOW", font(int(58 * pb) + 1), rgba(DARK))
        put(frame, emoji_img("🔔", 74), 540 - w / 2 + 70, 980, pb * (1 + 0.1 * math.sin(TAU * 3 * t)))
    ctext(d, 540, 1160, UI["daily"], font(46, False), rgba(MUTED, ease_out(prog(t, 1.3, .6))))

def _bubble_lines(d, text, f, maxw):
    lines = wrap(d, text, f, maxw)
    return lines, max([d.textlength(l, font=f) for l in lines] + [10])


def s_chat(frame, d, v, t, dur, ctx):
    """ChatGPT-style demo: the prompt types itself, the AI 'thinks', then the answer streams in."""
    acc = ctx["accent"]
    p = ease_out(prog(t, 0, .45))
    card(d, (70, 330, W - 70, BOTTOM - 10), 44, (10, 12, 30, int(215 * p)), rgba(acc, .55 * p), 3)
    d.ellipse((110, 372, 150, 412), fill=rgba(acc, p))
    d.text((170, 392), "AI Chat", font=font(40), fill=rgba(TEXT, p), anchor="lm")
    d.line([(110, 440), (W - 110, 440)], fill=rgba(TEXT, .12 * p), width=2)
    fu, fa = font(44), font(42, False)
    t_user = (0.35, max(1.2, dur * 0.32))                      # typing window for the prompt
    t_think = t_user[0] + t_user[1] + 0.15
    t_ai = (t_think + 0.6, max(1.2, dur - (t_think + 0.6) - 0.6))
    # user bubble (right)
    k = prog(t, *t_user)
    if k > 0:
        txt = v["user"][:max(1, int(len(v["user"]) * k))]
        lines, lw = _bubble_lines(d, v["user"], fu, 680)
        shown, left = [], len(txt)
        for ln in lines:
            shown.append(ln[:max(0, left)]); left -= len(ln) + 1
        bw, bh = lw + 70, len(lines) * 58 + 46
        x1, y0 = W - 110, 480
        card(d, (x1 - bw, y0, x1, y0 + bh), 34, rgba(acc, .92))
        for i, ln in enumerate(shown):
            d.text((x1 - bw + 35, y0 + 23 + i * 58 + 29), ln, font=fu, fill=DARK, anchor="lm")
        y_next = y0 + bh + 40
    else:
        y_next = 480
    # thinking dots
    if t_think <= t < t_ai[0]:
        for i in range(3):
            a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(TAU * (t * 2.2 - i * 0.25)))
            d.ellipse((130 + i * 46, y_next + 20, 156 + i * 46, y_next + 46), fill=rgba(TEXT, a))
    # AI bubble (left), streams word by word
    ka = prog(t, *t_ai)
    if ka > 0:
        words = v["ai"].split()
        txt = " ".join(words[:max(1, int(math.ceil(len(words) * ka)))])
        lines, lw = _bubble_lines(d, v["ai"], fa, 700)
        shown_lines = wrap(d, txt, fa, 700)
        bw, bh = lw + 70, len(lines) * 56 + 46
        card(d, (110, y_next, 110 + bw, y_next + bh), 34, (255, 255, 255, 30), rgba(TEXT, .25), 2)
        for i, ln in enumerate(shown_lines[:len(lines)]):
            d.text((145, y_next + 23 + i * 56 + 28), ln, font=fa, fill=TEXT, anchor="lm")


DRAWERS = {"hook": s_hook, "bullets": s_bullets, "flow": s_flow, "compare": s_compare, "network": s_network,
           "code": s_code, "stat": s_stat, "formula": s_formula, "takeaway": s_takeaway, "chat": s_chat, "cta": s_cta}

# ---------------------------------------------------------------- captions (speech bubble, word-by-word karaoke)
BUBBLE = (335, 1318, 950, 1572)            # x0, y0, x1, y1 - left of Instagram's right-side buttons, above its caption
MASCOT_XY = (182, 1452)
XFADE = 0.28                                # crossfade length between scenes (s)


def make_chunks(words, max_words=4, max_chars=24, gap=0.35):
    """words: [(start, end, text)] in GLOBAL seconds -> [{'start','end','words':[...]}] caption chunks."""
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or len(" ".join(x[2] for x in cur + [w])) > max_chars
                    or w[0] - cur[-1][1] > gap):
            chunks.append(cur); cur = []
        cur.append(w)
        if re.search(r"[.?!,]$", w[2]) and len(cur) >= 2:
            chunks.append(cur); cur = []
    if cur:
        chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        nxt = chunks[i + 1][0][0] if i + 1 < len(chunks) else c[-1][1] + 0.6
        out.append({"start": c[0][0] - 0.06, "end": min(nxt - 0.02, c[-1][1] + 0.7), "words": c})
    return out


@functools.lru_cache(maxsize=512)
def _bubble_layout(texts):
    """Lay out the chunk's words in <=2 centred lines inside the bubble. Returns (font, [(x, y, word_index)])."""
    d = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    x0, y0, x1, y1 = BUBBLE
    maxw, maxh = x1 - x0 - 70, y1 - y0 - 50
    for size in range(66, 37, -4):
        f = font(size)
        sp = d.textlength(" ", font=f)
        lines, cur, curw = [], [], 0.0
        for i, w in enumerate(texts):
            ww = d.textlength(w, font=f)
            if cur and curw + sp + ww > maxw:
                lines.append((cur, curw)); cur, curw = [], 0.0
            curw = curw + (sp if cur else 0) + ww
            cur.append((i, w, ww))
        if cur:
            lines.append((cur, curw))
        if len(lines) <= 2 and len(lines) * size * 1.25 <= maxh and all(lw <= maxw for _, lw in lines):
            break
    cy = (y0 + y1) / 2
    placed = []
    for li, (items, lw) in enumerate(lines):
        y = cy + (li - (len(lines) - 1) / 2) * size * 1.25
        x = (x0 + x1) / 2 - lw / 2
        for i, w, ww in items:
            placed.append((x, y, i)); x += ww + sp
    return f, tuple(placed)


def draw_bubble(frame, chunk, t, acc):
    if not chunk:
        return
    d = ImageDraw.Draw(frame, "RGBA")
    age = t - chunk["start"]
    pop = ease_back(clamp(age / 0.16))
    yo = (1 - pop) * 14
    x0, y0, x1, y1 = BUBBLE
    card(d, (x0, y0 + yo, x1, y1 + yo), 46, (10, 12, 32, 225), rgba(acc, .95), 4)
    ty = (y0 + y1) / 2 + yo - 20                                  # tail pointing at the bot's face
    d.polygon([(x0 + 2, ty - 26), (x0 + 2, ty + 26), (x0 - 40, ty + 34)], fill=(10, 12, 32, 225))
    d.line([(x0 + 1, ty + 26), (x0 - 40, ty + 34), (x0 + 1, ty - 26)], fill=rgba(acc, .95), width=4)
    texts = tuple(w[2] for w in chunk["words"])
    f, placed = _bubble_layout(texts)
    for x, y, i in placed:
        ws, we, txt = chunk["words"][i]
        if t >= we:
            col = TEXT
        elif t >= ws:
            col = rgba(acc)                                      # word being spoken right now
        else:
            col = rgba(TEXT, .45)
        d.text((x, y + yo), txt, font=f, fill=col, anchor="lm")


# ---------------------------------------------------------------- whole reel -> one mp4 (single pass, no cut glitches)
def draw_content(spec, t, dur, ctx):
    frame = base_gradient().copy()
    chrome(frame, ctx, t)
    d = ImageDraw.Draw(frame, "RGBA")
    DRAWERS[spec["kind"]](frame, d, spec["visual"], t, dur, ctx)
    return frame


def render_video(scenes, audio_wav, levels, out_path, label, level="basics", words=None, mascot_on=True,
                 snapshot=None):
    """scenes: [{kind, visual, start, dur}] (start/dur in seconds, contiguous).
    levels: per-frame voice loudness 0..1 (lip-sync). words: [(start, end, word)] global timings for captions.
    snapshot: optional (jpg_path, second) to save a cover frame."""
    import mascot
    total = scenes[-1]["start"] + scenes[-1]["dur"]
    n = int(round(total * FPS))
    acc = LEVEL_COLOR.get(level, LEVEL_COLOR["basics"])
    chunks = make_chunks(words or [])
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", audio_wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart",
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100", "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
           "-ac", "2", "-t", f"{total:.3f}", out_path]
    errf = open(out_path + ".err", "wb")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=errf)
    si, ci = 0, 0
    prev_content, xfade_src = None, None
    snap_f = int(snapshot[1] * FPS) if snapshot else -1
    rc = -1
    try:
        for f in range(n):
            t = f / FPS
            while si + 1 < len(scenes) and t >= scenes[si + 1]["start"]:
                si += 1
                xfade_src = prev_content
            sc = scenes[si]
            st = t - sc["start"]
            ctx = {"accent": acc, "label": label, "t0": sc["start"], "total": total}
            content = draw_content(sc, st, sc["dur"], ctx)
            prev_content = content
            frame = content
            if xfade_src is not None and st < XFADE and si > 0:
                frame = Image.blend(xfade_src, content, ease_out(st / XFADE))
            elif st >= XFADE:
                xfade_src = None
            frame = frame.copy() if frame is content else frame
            if mascot_on:
                talk = float(levels[f]) if f < len(levels) else 0.0
                mascot.draw(frame, acc, sc["kind"], t, st, talk, *MASCOT_XY)
            if f == snap_f:                                  # clean cover: no half-sentence caption bubble
                frame.save(snapshot[0], quality=92)
            while ci < len(chunks) and t > chunks[ci]["end"]:
                ci += 1
            if ci < len(chunks) and chunks[ci]["start"] <= t:
                draw_bubble(frame, chunks[ci], t, acc)
            im = frame
            proc.stdin.write(im.tobytes())
        proc.stdin.close(); rc = proc.wait()
    except BrokenPipeError:
        rc = proc.wait()
    finally:
        errf.close()
    if rc != 0:
        raise RuntimeError("ffmpeg (reel render) failed: " + open(out_path + ".err", errors="ignore").read()[-1000:])
    os.remove(out_path + ".err")
    return total
