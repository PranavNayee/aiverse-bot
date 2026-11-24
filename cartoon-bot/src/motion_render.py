"""Smooth, light 'motion graphics' look for the reels (VIDEO_STYLE=motion, the default).

What makes it smoother than the old dark style:
  * spring animations (elements overshoot a little and settle) instead of linear/cubic ease
  * NO snap-zoom on cuts - scenes cross-fade while the next scene's elements spring in
  * motion blur: fast-moving frames are the average of 3 time samples (only when something actually moves)
  * UI-mockup cards (chat window, code window, cards with soft shadows), cream background with a faint grid and
    slowly rotating flowers, orange serif-italic highlight words, big karaoke captions on a pill
Everything is drawn with Pillow + numpy and piped into ffmpeg - free, no extra dependencies.
Same entry point as edu_render.render_video, so lesson_main.py does not change."""
import functools, math, os, re, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import edu_render as E
from edu_render import W, H, FPS, TAU, font, clamp, prog, mix, emoji_img

CREAM, INK, MUTE = (250, 246, 238), (26, 26, 32), (126, 120, 112)
ORANGE, WHITE, LINE = (255, 107, 53), (255, 255, 255), (228, 221, 208)
GREEN, RED, BLUE, PURPLE = (34, 160, 90), (235, 77, 75), (70, 110, 235), (140, 90, 220)
SOFT, TINT = (244, 240, 232), (255, 232, 220)
STEP_COLORS = [ORANGE, BLUE, GREEN, PURPLE]
HANDLE = "@" + E.BRAND.lower()
TOP, BOTTOM, CAP_Y = 300, 1290, 1450
SAMPLES = int(os.environ.get("MOTION_BLUR_SAMPLES", "3") or 3)       # 1 = off (faster), 3 = default
XF = 0.28                                                           # cross-fade between scenes (s)


# ---------------------------------------------------------------- fonts / easing / primitives
@functools.lru_cache(maxsize=None)
def serif(size):
    """Serif italic for the highlighted words. Noto Serif Italic if present, else DejaVu/Liberation/Georgia."""
    size = int(size)
    from PIL import ImageFont
    for p in ("/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf", "/usr/share/fonts/truetype/noto/NotoSerif-BoldItalic.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
              "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return font(size)


def spring(x, f=11.0, z=8.0):
    """Damped spring, x = seconds since the element started. 0 -> overshoots ~10% -> settles at 1 in ~0.6 s."""
    return 0.0 if x <= 0 else 1 - math.exp(-z * x) * math.cos(f * x)


def fade(x, length=0.25):
    return clamp(x / length)


def smooth(p):
    p = clamp(p)
    return p * p * (3 - 2 * p)


def A(c, a=1.0):
    return (c[0], c[1], c[2], int(255 * clamp(a)))


def blit(frame, im, cx, cy, scale=1.0, alpha=1.0):
    if im is None or alpha <= 0.01 or scale <= 0.01:
        return
    if abs(scale - 1) > 0.01:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if alpha < 0.99:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    frame.paste(im, (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))), im)


def shadow(d, box, r, a):
    x0, y0, x1, y1 = box
    for g, al in ((18, .035), (10, .05), (4, .06)):
        d.rounded_rectangle((x0 - g, y0 - g + 12, x1 + g, y1 + g + 12), r + g, fill=(70, 45, 20, int(255 * al * a)))


def panel(d, box, r=40, fill=WHITE, a=1.0, outline=LINE, ow=3, sh=True):
    x0, y0, x1, y1 = box
    if x1 - x0 < 6 or y1 - y0 < 6 or a <= 0.01:
        return
    r = max(2, min(r, (x1 - x0) / 2 - 1, (y1 - y0) / 2 - 1))
    if sh:
        shadow(d, box, r, a)
    d.rounded_rectangle(box, r, fill=A(fill, a), outline=A(outline, a) if outline else None, width=ow if outline else 0)


def tag(d, cx, cy, text, a=1.0, fill=ORANGE, fg=WHITE, size=34, scale=1.0):
    f = font(int(size * scale) or 1)
    w = d.textlength(text, font=f) + 54 * scale
    h = size * 1.75 * scale
    panel(d, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), h / 2, fill, a, None, sh=False)
    d.text((cx, cy), text, font=f, fill=A(fg, a), anchor="mm")


def window(d, box, title, a=1.0, dark=False):
    """UI mock-up window: rounded card + title bar with the three dots."""
    x0, y0, x1, y1 = box
    panel(d, box, 38, INK if dark else WHITE, a, None if dark else LINE)
    if a > 0.05:
        bar = (42, 42, 52) if dark else (250, 247, 240)
        d.rounded_rectangle((x0 + 2, y0 + 2, x1 - 2, y0 + 78), 36, fill=A(bar, a))
        d.rectangle((x0 + 2, y0 + 44, x1 - 2, y0 + 78), fill=A(bar, a))
        for k, c in enumerate((RED, (251, 191, 36), GREEN)):
            d.ellipse((x0 + 34 + k * 40, y0 + 29, x0 + 56 + k * 40, y0 + 51), fill=A(c, a))
        d.text(((x0 + x1) / 2, y0 + 40), title, font=font(30, False), fill=A((200, 200, 210) if dark else MUTE, a), anchor="mm")


@functools.lru_cache(maxsize=256)
def _rich_layout(text, maxw, maxh, start, minimum, hl, gap):
    words = text.split()
    n = len(words)
    k = hl if hl is not None else (0 if n <= 1 else 1 if n < 4 else 2)
    hset = set(range(n - k, n))
    for size in range(start, minimum - 1, -4):
        fs, fi = font(size, True), serif(size * 1.08)
        sp = fs.getlength(" ")
        lines, cur, cw = [], [], 0.0
        for i, w in enumerate(words):
            ww = (fi if i in hset else fs).getlength(w)
            if cur and cw + sp + ww > maxw:
                lines.append((cur, cw)); cur, cw = [], 0.0
            cw += (sp if cur else 0) + ww
            cur.append((i, w, ww, i in hset))
        if cur:
            lines.append((cur, cw))
        if len(lines) * size * gap <= maxh and all(lw <= maxw for _, lw in lines):
            break
    return size, fs, fi, sp, tuple((tuple(it), lw) for it, lw in lines)


def rich(d, cx, y, text, maxw=920, maxh=400, start=100, alpha=1.0, hl=None, color=INK, t=None, t0=0.0,
         stagger=0.07, gap=1.16, minimum=44):
    """Headline: bold sans words with the LAST word(s) in orange serif italic on a soft highlight.
    With t given, words spring in one after another. Returns the y below the block."""
    size, fs, fi, sp, lines = _rich_layout(text, maxw, maxh, start, minimum, hl, gap)
    for li, (items, lw) in enumerate(lines):
        base = y + (li + 0.5) * size * gap
        x = cx - lw / 2
        for i, w, ww, h in items:
            a, yo = alpha, 0.0
            if t is not None:
                u = t - t0 - i * stagger
                a = alpha * fade(u, .18); yo = (1 - spring(u)) * 36
            if a > 0.01:
                if h:
                    d.rounded_rectangle((x - 10, base - size * .5 + yo, x + ww + 10, base + size * .45 + yo), 16, fill=A(ORANGE, .13 * a))
                d.text((x, base + size * .33 + yo), w, font=fi if h else fs, fill=A(ORANGE if h else color, a), anchor="ls")
            x += ww + sp
    return y + len(lines) * size * gap


def para(d, cx, y, text, maxw, maxh, start, minimum, color=INK, a=1.0, bold=False, align="mm", gap=1.2):
    f, lines, size = E.fit(d, text, maxw, maxh, start, minimum, bold=bold)
    for i, ln in enumerate(lines):
        d.text((cx, y + i * size * gap), ln, font=f, fill=A(color, a), anchor=align)
    return y + len(lines) * size * gap


# ---------------------------------------------------------------- background + chrome
_BG = None
def background():
    global _BG
    if _BG is None:
        y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        top, bot = np.array((252, 249, 243), np.float32), np.array((247, 241, 230), np.float32)
        arr = (top + (bot - top) * y).repeat(W, 1).astype(np.uint8)
        img = Image.fromarray(arr, "RGB")
        g = ImageDraw.Draw(img)
        for gx in range(0, W + 1, 90):
            g.line([(gx, 0), (gx, H)], fill=(238, 231, 218), width=1)
        for gy in range(0, H + 1, 90):
            g.line([(0, gy), (W, gy)], fill=(238, 231, 218), width=1)
        _BG = img
    return _BG


@functools.lru_cache(maxsize=4)
def flower(size, c1, c2):
    S = size * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    petal = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(petal).ellipse((S * .43, S * .05, S * .57, S * .42), fill=c1)
    for k in range(8):
        im.alpha_composite(petal.rotate(k * 45, resample=Image.BICUBIC, center=(S / 2, S / 2)))
    ImageDraw.Draw(im).ellipse((S * .43, S * .43, S * .57, S * .57), fill=c2)
    return im.resize((size, size), Image.LANCZOS)


def base_frame(c, t_abs):
    fr = background().copy()
    for (cx, cy, size, c1, spin) in ((1010, 215, 400, (255, 176, 120, 115), 7), (70, 1255, 360, (255, 214, 120, 115), -6)):
        blit(fr, flower(size, c1, (255, 140, 60, 200)).rotate(t_abs * spin, resample=Image.BICUBIC), cx, cy)
    d = ImageDraw.Draw(fr, "RGBA")
    chrome(d, c)
    return fr, d


def chrome(d, c):
    f = font(32)
    w = d.textlength(HANDLE, font=f) + 92
    panel(d, (56, 92, 56 + w, 170), 39, WHITE, 1, LINE, 2)
    d.ellipse((82, 119, 108, 145), fill=A(ORANGE))
    d.text((124, 131), HANDLE, font=f, fill=A(INK), anchor="lm")
    label = str(c.get("label", ""))
    if label and not label.startswith("Lesson"):          # 'Lesson 5/60' looks like a class -> swipe: hidden
        fb = font(30)
        bw = d.textlength(label, font=fb) + 54
        panel(d, (W - 56 - bw, 92, W - 56, 170), 39, TINT, 1, ORANGE, 2, sh=False)
        d.text((W - 56 - bw / 2, 131), label, font=fb, fill=A(ORANGE), anchor="mm")


def kicker(c, default="AI SEEKHO"):
    label = str(c.get("label", ""))
    return default if (not label or label.startswith("Lesson")) else label.upper()


# ---------------------------------------------------------------- scene drawers: (frame, d, visual, t, dur, ctx)
def s_hook(fr, d, v, t, dur, c):
    t = t + (0.2 if c["t0"] < 0.01 else 0.0)                 # first scene is already moving on frame 0 (autoplay)
    ring = (t * 0.7) % 1.0
    for k in (0, 1):
        r = 215 + 90 * ((ring + k * .5) % 1)
        d.ellipse((540 - r, 640 - r, 540 + r, 640 + r), outline=A(ORANGE, .30 * (1 - ((ring + k * .5) % 1))), width=5)
    tag(d, 540, 400, kicker(c), fade(t, .2), scale=spring(t - .05))
    s = spring(t - 0.05)
    cy = 640 + 8 * math.sin(TAU * .5 * t)
    panel(d, (540 - 170 * s, cy - 170 * s, 540 + 170 * s, cy + 170 * s), 70 * s + 4, WHITE, fade(t, .15))
    blit(fr, emoji_img(v.get("emoji") or "🤔", 230), 540, cy, s)
    rich(d, 540, 870, v.get("text", ""), 930, 360, 104, t=t, t0=0.12)


def s_bullets(fr, d, v, t, dur, c):
    items = v.get("items", [])
    rich(d, 540, 320, v.get("heading", ""), 940, 180, 72, t=t, hl=1, minimum=48)
    n = max(len(items), 1)
    step = clamp((dur - 1.3) / n, 0.6, 1.9)
    ch = min(230, (BOTTOM - 520 - (n - 1) * 34) / n)
    active = max([j for j in range(len(items)) if t >= 0.5 + j * step] or [-1])
    for i, it in enumerate(items):
        u = t - (0.5 + i * step)
        if u <= 0:
            continue
        y = 520 + i * (ch + 34)
        xo = (1 - spring(u)) * 300
        on = i == active
        panel(d, (64 + xo, y, W - 64 + xo, y + ch), 36, WHITE, fade(u, .2), ORANGE if on else LINE, 4 if on else 3)
        cy = y + ch / 2
        d.ellipse((104 + xo, cy - 42, 188 + xo, cy + 42), fill=A(ORANGE if on else (255, 190, 160), fade(u, .2)))
        d.text((146 + xo, cy), str(i + 1), font=font(48), fill=A(WHITE), anchor="mm")
        f, lines, size = E.fit(d, it, 700, ch - 30, 56, 34)
        for j, ln in enumerate(lines):
            d.text((226 + xo, cy + (j - (len(lines) - 1) / 2) * size * 1.15), ln, font=f, fill=A(INK, fade(u, .2)), anchor="lm")


def s_flow(fr, d, v, t, dur, c):
    steps = v.get("steps", [])
    top = TOP + 20
    if v.get("heading"):
        rich(d, 540, 320, v["heading"], 940, 120, 66, t=t, hl=1, minimum=46); top = 450
    n, gap = max(len(steps), 1), 84
    bh = min(215, (BOTTOM - top - (70 if v.get("caption") else 0) - (n - 1) * gap) / n)
    step = clamp((dur - 1.0) / n, 0.5, 1.5)
    for i, st in enumerate(steps):
        col = STEP_COLORS[i % 4]
        u = t - (0.3 + i * step)
        y = top + i * (bh + gap)
        cy = y + bh / 2
        if u > 0:
            s = spring(u)
            panel(d, (540 - 420 * s, cy - bh / 2 * s, 540 + 420 * s, cy + bh / 2 * s), 38, WHITE, fade(u, .2), col, 4)
            if s > .4:
                ex = 120 + bh * .62
                d.ellipse((ex - bh * .36, cy - bh * .36, ex + bh * .36, cy + bh * .36), fill=A(col, .14 * fade(u, .2)))
                blit(fr, emoji_img(st.get("emoji", ""), int(bh * .46)), ex, cy, s, fade(u, .2))
                f, lines, size = E.fit(d, st.get("label", ""), 520, bh - 28, 60, 34)
                for j, ln in enumerate(lines):
                    d.text((120 + bh * 1.05, cy + (j - (len(lines) - 1) / 2) * size * 1.12), ln, font=f, fill=A(INK, fade(u, .2)), anchor="lm")
        if i < n - 1:
            pa = smooth((t - (0.3 + (i + 1) * step - 0.3)) / 0.4)
            if pa > 0:
                a0, a1 = y + bh + 8, y + bh + gap - 8
                d.line([(540, a0), (540, a0 + (a1 - a0) * pa)], fill=A(col, .9), width=7)
                if pa >= 1:
                    d.polygon([(540, a1 + 4), (516, a1 - 26), (564, a1 - 26)], fill=A(col))
                    k = (t * .9 + i * .3) % 1
                    yy = a0 + (a1 - a0 - 24) * k + 10
                    d.ellipse((529, yy - 11, 551, yy + 11), fill=A(INK, .8))
    if v.get("caption"):
        d.text((540, BOTTOM - 14), v["caption"], font=font(42, False), fill=A(MUTE, fade(t - dur * .45, .5)), anchor="mm")


def s_compare(fr, d, v, t, dur, c):
    cols = [(64, 520, v.get("left_title", ""), v.get("left", []), RED, 0.25),
            (560, 1016, v.get("right_title", ""), v.get("right", []), GREEN, 0.25 + max(dur * .3, 1.0))]
    for x0, x1, title, items, col, st in cols:
        u = t - st
        if u <= 0:
            continue
        yo = (1 - spring(u)) * 120
        a = fade(u, .2)
        panel(d, (x0, 380 + yo, x1, 1190 + yo), 44, WHITE, a, col, 4)
        d.rounded_rectangle((x0 + 24, 410 + yo, x1 - 24, 520 + yo), 30, fill=A(col, a))
        f, lines, size = E.fit(d, title, 380, 90, 50, 30)
        d.text(((x0 + x1) / 2, 465 + yo), " ".join(lines), font=f, fill=A(WHITE, a), anchor="mm")
        for i, it in enumerate(items):
            ui = u - .45 - i * .5
            if ui <= 0:
                continue
            f2, l2, s2 = E.fit(d, it, 340, 190, 46, 30, bold=False)
            cy = 650 + i * 170 + yo + (1 - spring(ui)) * 40
            d.ellipse((x0 + 30, cy - 13, x0 + 56, cy + 13), fill=A(col, fade(ui, .2)))
            for j, ln in enumerate(l2):
                d.text((x0 + 76, cy + (j - (len(l2) - 1) / 2) * s2 * 1.15), ln, font=f2, fill=A(INK, fade(ui, .2)), anchor="lm")
    s = spring(t - .8)
    if s > 0:
        r = max(2, 54 * s)
        d.ellipse((540 - r, 780 - r, 540 + r, 780 + r), fill=A(INK), outline=A(WHITE), width=6)
        d.text((540, 780), "VS", font=font(int(44 * s) + 1), fill=A(WHITE), anchor="mm")


def s_network(fr, d, v, t, dur, c):
    layers = v.get("layers") or [3, 4, 2]
    if len(layers) < 2:
        layers = [3, 4, 2]
    rich(d, 540, 320, v.get("heading", ""), 940, 120, 66, t=t, hl=1, minimum=46)
    wa = fade(t, .3)
    window(d, (64, 470, W - 64, 1230), "neural_network.ai", wa)
    xs = np.linspace(190, W - 190, len(layers))
    cy, sp = 820, min(130, 520 / max(max(layers), 1))
    pos = [[(xs[i], cy + (j - (n - 1) / 2) * sp) for j in range(n)] for i, n in enumerate(layers)]
    rev = [t - (0.4 + i * .45) for i in range(len(layers))]
    wave = (t * .55) % 1.0
    for i in range(len(layers) - 1):
        pe = clamp(min(rev[i], rev[i + 1]) / .4)
        if pe > 0:
            for a in pos[i]:
                for b in pos[i + 1]:
                    d.line([a, b], fill=A((200, 190, 175), pe), width=2)
        if pe >= 1:
            k = clamp(wave * (len(layers) - 1) - i)
            if 0 < k < 1:
                for a in pos[i]:
                    for b in pos[i + 1]:
                        x, y = a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
                        d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=A(ORANGE))
    done = rev[-1] > .4
    for i, layer in enumerate(pos):
        glow = clamp(1 - abs(wave * (len(layers) - 1) - i)) if done else 0
        for (x, y) in layer:
            r = 36 * spring(rev[i])
            if r < 2:
                continue
            if glow > .2:
                d.ellipse((x - r - 14, y - r - 14, x + r + 14, y + r + 14), fill=A(ORANGE, .22 * glow))
            d.ellipse((x - r, y - r, x + r, y + r), fill=A(mix(WHITE, (255, 214, 190), glow)), outline=A(ORANGE if glow > .3 else INK), width=4)
    labels = v.get("labels") or (["Input"] + ["Hidden"] * (len(layers) - 2) + ["Output"])
    for i in range(len(layers)):
        d.text((xs[i], cy + max(layers) * sp / 2 + 64), labels[i] if i < len(labels) else "", font=font(36, False),
               fill=A(MUTE, fade(rev[i], .3)), anchor="mm")


_KW = E.KEYWORDS
def _tok(line):
    out = []
    for s, col in E._tokens(line):
        if col == E.MUTED:
            col = (120, 130, 150)
        elif col == E.GREEN:
            col = (110, 231, 160)
        elif col == E.TEXT:
            col = (235, 238, 250)
        out.append((s, col))
    return out


def s_code(fr, d, v, t, dur, c):
    lines = v.get("lines", [])
    rich(d, 540, 320, v.get("heading", ""), 940, 120, 66, t=t, hl=1, minimum=46)
    u = t - .1
    yo = (1 - spring(u)) * 120
    top = 470 + yo
    window(d, (56, top, W - 56, top + 150 + len(lines) * 84 + 40), "main.py", fade(u, .25), dark=True)
    f = font(40, False, True)
    total = sum(len(l) for l in lines)
    left = int(total * smooth((t - .6) / max(dur * .65, 1.5)))
    for i, ln in enumerate(lines):
        x, y = 96, top + 130 + i * 84 + 20
        n = min(len(ln), max(left, 0))
        used = 0
        for s, col in _tok(ln):
            if used >= n:
                break
            seg = s[:n - used]
            d.text((x, y), seg, font=f, fill=A(col), anchor="lm")
            x += d.textlength(seg, font=f); used += len(seg)
        if 0 < left <= len(ln) and int(t * 2.2) % 2 == 0:
            d.rectangle((x + 4, y - 26, x + 20, y + 26), fill=A(ORANGE))
        left -= len(ln)


def s_stat(fr, d, v, t, dur, c):
    big = str(v.get("big", ""))
    s = spring(t - .05)
    blit(fr, emoji_img(v.get("emoji", ""), 230), 540, 520 + 8 * math.sin(TAU * .6 * t), s)
    shown = big
    m = re.fullmatch(r"(\D*)(\d+)(\D*)", big)
    if m and not (1900 <= int(m.group(2)) <= 2100 and not m.group(1) and not m.group(3)):
        shown = f"{m.group(1)}{int(int(m.group(2)) * smooth((t - .3) / 1.2))}{m.group(3)}"
    f, lines, size = E.fit(d, big, 940, 260, 230, 90)
    for k in (3, 2, 1):                                          # soft orange glow behind the number
        d.ellipse((540 - 330 - k * 30, 860 - 130 - k * 24, 540 + 330 + k * 30, 860 + 130 + k * 24), fill=A(ORANGE, .035 * fade(t - .2, .6)))
    d.text((540, 860 + (1 - spring(t - .2)) * 60), shown, font=f, fill=A(ORANGE, fade(t - .2, .2)), anchor="mm")
    para(d, 540, 1050, v.get("caption", ""), 880, 300, 64, 40, INK, fade(t - .8, .5))


def s_formula(fr, d, v, t, dur, c):
    lines = v.get("lines", [])
    rich(d, 540, 320, v.get("heading", ""), 940, 120, 66, t=t, hl=1, minimum=46)
    u = t - .2
    s = spring(u)
    h = 150 + 150 * len(lines)
    y0 = 790 - h / 2
    panel(d, (64, y0 + (1 - s) * 80, W - 64, y0 + h + (1 - s) * 80), 48, WHITE, fade(u, .2), ORANGE, 4)
    d.rounded_rectangle((64, y0 + (1 - s) * 80 + 30, 82, y0 + h + (1 - s) * 80 - 30), 9, fill=A(ORANGE, fade(u, .2)))
    for i, ln in enumerate(lines):
        ui = t - (.5 + i * .6)
        f, ls, size = E.fit(d, ln, 840, 130, 92, 44)
        col = ORANGE if i == len(lines) - 1 and len(lines) > 1 else INK
        d.text((540, y0 + 105 + i * 150 + (1 - spring(ui)) * 40), " ".join(ls), font=f, fill=A(col, fade(ui, .25)), anchor="mm")
    if v.get("note"):
        para(d, 540, y0 + h + 110, v["note"], 900, 200, 52, 36, MUTE, fade(t - 1.4, .5), gap=1.25)


def s_takeaway(fr, d, v, t, dur, c):
    u = t - .1
    s = spring(u)
    panel(d, (64, 440 + (1 - s) * 90, W - 64, 1040 + (1 - s) * 90), 54, WHITE, fade(u, .2), GREEN, 4)
    tag(d, 330, 440 + (1 - s) * 90, "YAAD RAKHO" if not E.EN else "REMEMBER", fade(u, .2), fill=GREEN, size=38)
    r = 54 * s
    if r > 2:
        d.ellipse((540 - r, 610 - r, 540 + r, 610 + r), fill=A(GREEN))
        if s > .6:
            d.line([(540 - 24, 612), (540 - 6, 634), (540 + 30, 588)], fill=A(WHITE), width=12, joint="curve")
    rich(d, 540, 700, v.get("text", ""), 860, 300, 70, t=t, t0=.45, minimum=42)
    terms = v.get("terms", [])
    for size in range(40, 25, -2):
        fw = font(size)
        widths = [fw.getlength(tm) + 56 for tm in terms]
        if sum(widths) + 22 * (len(terms) - 1) <= W - 120:
            break
    x = 540 - (sum(widths) + 22 * max(len(terms) - 1, 0)) / 2
    for i, (term, w) in enumerate(zip(terms, widths)):
        ui = t - (1.0 + i * .3)
        cx = x + w / 2; x += w + 22
        if ui <= 0:
            continue
        k = spring(ui)
        panel(d, (cx - w / 2 * k, 1160 - 42 * k, cx + w / 2 * k, 1160 + 42 * k), 42, TINT, fade(ui, .2), ORANGE, 3, sh=False)
        d.text((cx, 1160), term, font=fw, fill=A(INK, fade(ui, .2)), anchor="mm")


def _cursor(d, x, y, a=1.0):
    pts = [(0, 0), (0, 40), (10, 31), (18, 49), (27, 45), (19, 28), (32, 28)]
    d.polygon([(x + px + 3, y + py + 4) for px, py in pts], fill=(0, 0, 0, int(60 * a)))
    d.polygon([(x + px, y + py) for px, py in pts], fill=A(WHITE, a), outline=A(INK, a), width=3)


def s_cta(fr, d, v, t, dur, c):
    nxt = E.UI["next"] if str(c.get("label", "")).startswith("Lesson") else "NEXT VIDEO"
    tag(d, 540, 450, nxt, fade(t, .2), scale=spring(t))
    rich(d, 540, 540, v.get("text", ""), 920, 380, 86, t=t, t0=.15, minimum=48)
    u = t - .8
    s = spring(u)
    click = t - 1.9
    pulse = 1 + 0.04 * math.sin(TAU * 1.3 * t) if click > 0 else 1.0
    press = 0.94 if 0 < click < .12 else 1.0
    if s > 0:
        w, h = 540 * s * pulse * press, 132 * s * pulse * press
        panel(d, (540 - w / 2, 1010 - h / 2, 540 + w / 2, 1010 + h / 2), 66, ORANGE, fade(u, .2), None)
        if s > .5:
            d.text((565, 1010), "FOLLOW", font=font(int(58 * min(s, 1.1))), fill=A(WHITE), anchor="mm")
            blit(fr, emoji_img("🔔", 74), 540 - w / 2 + 78, 1010, 1 + 0.1 * math.sin(TAU * 3 * t))
    if click > 0:                                              # click ripple
        r = 40 + 150 * smooth(click / .6)
        d.ellipse((600 - r, 1020 - r, 600 + r, 1020 + r), outline=A(ORANGE, .5 * (1 - smooth(click / .6))), width=6)
    cp = smooth((t - 1.1) / .8)                                 # cursor glides in from the lower right
    if cp > 0 and t < 3.4:
        _cursor(d, 840 + (590 - 840) * cp + 6 * math.sin(cp * 3), 1180 + (1020 - 1180) * cp, 1.0)
    d.text((540, 1180), HANDLE, font=font(46), fill=A(INK, fade(t - 1.2, .5)), anchor="mm")
    d.text((540, 1245), E.UI["daily"], font=font(40, False), fill=A(MUTE, fade(t - 1.4, .5)), anchor="mm")


def s_chat(fr, d, v, t, dur, c):
    u = t
    yo = (1 - spring(u)) * 100
    a = fade(u, .25)
    window(d, (56, 330 + yo, W - 56, 1260 + yo), "AI Chat", a)
    fu, fa = font(44), font(42, False)
    t_user = (0.1, max(0.6, dur * .28))
    t_think = t_user[0] + t_user[1] + .05
    t_ai = (t_think + min(.4, dur * .1), max(.6, dur * .35))
    y_next = 470 + yo
    k = prog(t, *t_user)
    if k > 0:
        txt = v.get("user", "")[:max(1, int(len(v.get("user", "")) * k))]
        lines, lw = _bl(d, v.get("user", ""), fu, 680)
        shown, left = [], len(txt)
        for ln in lines:
            shown.append(ln[:max(0, left)]); left -= len(ln) + 1
        bw, bh = lw + 70, len(lines) * 58 + 46
        x1, y0 = W - 100, 470 + yo
        panel(d, (x1 - bw, y0, x1, y0 + bh), 34, ORANGE, 1, None, sh=False)
        for i, ln in enumerate(shown):
            d.text((x1 - bw + 35, y0 + 52 + i * 58), ln, font=fu, fill=A(WHITE), anchor="lm")
        y_next = y0 + bh + 40
    if t_think <= t < t_ai[0]:
        for i in range(3):
            aa = .3 + .7 * (.5 + .5 * math.sin(TAU * (t * 2.2 - i * .25)))
            d.ellipse((130 + i * 46, y_next + 20, 156 + i * 46, y_next + 46), fill=A(MUTE, aa))
    ka = prog(t, *t_ai)
    if ka > 0:
        words = v.get("ai", "").split()
        shown_txt = " ".join(words[:max(1, int(math.ceil(len(words) * ka)))])
        lines, lw = _bl(d, v.get("ai", ""), fa, 700)
        sl = E.wrap(d, shown_txt, fa, 700)
        bw, bh = lw + 70, len(lines) * 56 + 46
        panel(d, (100, y_next, 100 + bw, y_next + bh), 34, SOFT, 1, LINE, 2, sh=False)
        for i, ln in enumerate(sl[:len(lines)]):
            d.text((135, y_next + 51 + i * 56), ln, font=fa, fill=A(INK), anchor="lm")


def _bl(d, text, f, maxw):
    lines = E.wrap(d, text, f, maxw)
    return lines, max([d.textlength(l, font=f) for l in lines] + [10])


def s_image(fr, d, v, t, dur, c):
    path = v.get("path")
    if not path or not os.path.exists(path):
        blit(fr, emoji_img("🖼️", 320), 540, 700)
        return
    bgi, fg = E._image_layers(path)
    cream = Image.blend(bgi, Image.new("RGB", (W, H), CREAM), .72)
    fr.paste(cream, (0, 0))
    d2 = ImageDraw.Draw(fr, "RGBA")
    chrome(d2, c)
    s = 0.94 + 0.06 * spring(t) + 0.02 * smooth(t / max(dur, 1))
    x, y = (W - fg.width * s) / 2, 230 + (1 - spring(t)) * 70
    box = (x - 10, y - 10, x + fg.width * s + 10, y + fg.height * s + 10)
    panel(d2, box, 56, WHITE, fade(t, .2), None)
    blit(fr, fg, x + fg.width * s / 2, y + fg.height * s / 2, s, fade(t, .25))
    d2 = ImageDraw.Draw(fr, "RGBA")
    tag(d2, x + 150, y + 50, "AI GENERATED", fade(t - .3, .3), fill=INK, size=28)
    if v.get("caption"):
        f = font(46)
        tw = d2.textlength(v["caption"], font=f)
        cy = y + fg.height * s - 70
        panel(d2, (540 - tw / 2 - 36, cy - 44, 540 + tw / 2 + 36, cy + 44), 44, ORANGE, fade(t - .5, .3), None, sh=False)
        d2.text((540, cy), v["caption"], font=f, fill=A(WHITE, fade(t - .5, .3)), anchor="mm")


DRAWERS = {"hook": s_hook, "bullets": s_bullets, "flow": s_flow, "compare": s_compare, "network": s_network,
           "code": s_code, "stat": s_stat, "formula": s_formula, "takeaway": s_takeaway, "chat": s_chat,
           "image": s_image, "cta": s_cta}


# ---------------------------------------------------------------- captions: big word-by-word karaoke on a pill
def draw_caption(fr, chunk, t, cy=CAP_Y):
    if not chunk:
        return
    d = ImageDraw.Draw(fr, "RGBA")
    texts = tuple(w[2] for w in chunk["words"])
    f, size, sp, lines = E._cap_layout(texts, False)
    age = t - chunk["start"]
    yo = (1 - spring(age, 13, 9)) * 26
    a = fade(age, .09)
    mw = max(lw for _, lw in lines)
    hh = len(lines) * size * 1.14
    panel(d, (540 - mw / 2 - 48, cy - hh / 2 - 30 + yo, 540 + mw / 2 + 48, cy + hh / 2 + 30 + yo), 52, WHITE, a * .96, LINE, 2)
    for li, (items, lw) in enumerate(lines):
        y = cy + (li - (len(lines) - 1) / 2) * size * 1.14 + yo
        x = 540 - lw / 2
        for i, w, ww in items:
            ws, we, _ = chunk["words"][i]
            if ws <= t < we + 0.05:
                col = ORANGE
            elif t >= we:
                col = INK
            else:
                col = (150, 144, 136)
            d.text((x, y), w, font=f, fill=A(col, a), anchor="lm")
            x += ww + sp


# ---------------------------------------------------------------- whole reel -> one mp4
_warned = False
def _scene_img(scenes, si, t_abs, c):
    global _warned
    sc = scenes[si]
    cc = dict(c, t0=sc["start"])
    fr, d = base_frame(cc, t_abs)
    try:
        DRAWERS[sc["kind"]](fr, d, sc["visual"], max(t_abs - sc["start"], 0.0), sc["dur"], cc)
    except Exception as e:                      # one bad frame must never kill the whole reel
        if not _warned:
            print(f"[motion_render] {sc['kind']} frame skipped: {e}", flush=True); _warned = True
    return fr


def _comp(scenes, si, t_abs, c):
    img = _scene_img(scenes, si, t_abs, c)
    st = t_abs - scenes[si]["start"]
    if si > 0 and st < XF:
        prev = _scene_img(scenes, si - 1, t_abs, c)          # previous scene keeps animating while it fades out
        img = Image.blend(prev, img, smooth(st / XF))
    return img


def render_video(scenes, audio_wav, levels, out_path, label, level="basics", words=None, mascot_on=True, snapshot=None):
    """Same signature as edu_render.render_video. levels/mascot_on/level are unused (faceless, light look)."""
    total = scenes[-1]["start"] + scenes[-1]["dur"]
    n = int(round(total * FPS))
    chunks = E.make_chunks(words or [], max_words=3, max_chars=18)
    c = {"label": label, "total": total}
    preset, crf = os.environ.get("VIDEO_PRESET", "medium"), os.environ.get("VIDEO_CRF", "17")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", audio_wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", preset, "-crf", crf,
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart",
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100", "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
           "-ac", "2", "-t", f"{total:.3f}", out_path]
    errf = open(out_path + ".err", "wb")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=errf)
    si, ci, rc = 0, 0, -1
    snap_f = int(snapshot[1] * FPS) if snapshot else -1
    dt = 0.4 / FPS
    try:
        for f in range(n):
            t = f / FPS
            while si + 1 < len(scenes) and t >= scenes[si + 1]["start"]:
                si += 1
            if SAMPLES <= 1:
                img = _comp(scenes, si, t, c)
            else:                                            # motion blur, only when something is really moving
                a, b = _comp(scenes, si, t - dt, c), _comp(scenes, si, t + dt, c)
                aa, bb = np.asarray(a, dtype=np.int16), np.asarray(b, dtype=np.int16)
                if np.abs(aa[::6, ::6] - bb[::6, ::6]).mean() > 0.12:
                    m = np.asarray(_comp(scenes, si, t, c), dtype=np.int16)
                    img = Image.fromarray(((aa + bb + m) // 3).astype(np.uint8))
                else:
                    img = b
            while ci < len(chunks) and t > chunks[ci]["end"]:
                ci += 1
            cur = chunks[ci] if ci < len(chunks) and chunks[ci]["start"] <= t else None
            if cur is None and si == 0 and ci < len(chunks):
                cur = chunks[ci]                              # frame 0: show the first words immediately
            draw_caption(img, cur, t)
            if f == snap_f:
                img.save(snapshot[0], quality=92)
            proc.stdin.write(img.tobytes())
        proc.stdin.close(); rc = proc.wait()
    except BrokenPipeError:
        rc = proc.wait()
    finally:
        errf.close()
    if rc != 0:
        raise RuntimeError("ffmpeg (reel render) failed: " + open(out_path + ".err", errors="ignore").read()[-1000:])
    os.remove(out_path + ".err")
    return total
