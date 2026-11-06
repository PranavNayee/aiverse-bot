"""'Seekho Bot' - the channel's 2D cartoon teacher, drawn entirely in code.

It blinks, bobs, lip-syncs to the narration (mouth driven by the voice loudness) and gestures
(waves on hook/cta, points up at the lesson content otherwise). Every pose is rendered once at 2x and
downscaled for smooth anti-aliased edges, then cached, so it costs almost nothing per frame."""
import functools, math
from PIL import Image, ImageDraw

SS = 2                       # supersampling factor
BW, BH = 260, 330            # base sprite size (before supersampling)
INK = (28, 32, 66, 255)
SHELL = (238, 242, 255, 255)
SHADE = (205, 212, 240, 255)
VISOR = (16, 20, 46, 255)
CHEEK = (255, 128, 170, 120)
ARM_STEPS = 24               # arm angle quantisation (keeps the cache small)


def _p(*xy):
    return [v * SS for v in xy]


def _capsule(d, a, b, width, fill, outline=INK):
    (x0, y0), (x1, y1) = a, b
    r = width / 2
    d.line(_p(x0, y0, x1, y1), fill=outline, width=int((width + 8) * SS))
    for x, y in (a, b):
        d.ellipse(_p(x - r - 4, y - r - 4, x + r + 4, y + r + 4), fill=outline)
    d.line(_p(x0, y0, x1, y1), fill=fill, width=int(width * SS))
    for x, y in (a, b):
        d.ellipse(_p(x - r, y - r, x + r, y + r), fill=fill)


def _arm(d, shoulder, angle_deg, length, accent):
    a = math.radians(angle_deg)
    hand = (shoulder[0] + length * math.cos(a), shoulder[1] - length * math.sin(a))
    _capsule(d, shoulder, hand, 20, SHADE)
    hx, hy = hand
    d.ellipse(_p(hx - 17, hy - 17, hx + 17, hy + 17), fill=INK)
    d.ellipse(_p(hx - 13, hy - 13, hx + 13, hy + 13), fill=accent)


@functools.lru_cache(maxsize=2048)
def sprite(accent, mouth=0, blink=False, expr="normal", arm_q=0, size=1.0):
    """accent: RGB tuple; mouth: 0..4 openness; expr: normal|happy|surprised; arm_q: 0..ARM_STEPS-1."""
    acc = tuple(accent[:3]) + (255,)
    im = Image.new("RGBA", (BW * SS, BH * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # soft floor shadow
    d.ellipse(_p(60, 312, 200, 328), fill=(0, 0, 0, 70))

    # left arm (resting) is behind the body
    _arm(d, (70, 222), 245, 72, acc)

    # body + chest screen
    d.rounded_rectangle(_p(58, 192, 202, 312), radius=40 * SS, fill=SHELL, outline=INK, width=5 * SS)
    d.rounded_rectangle(_p(70, 286, 190, 306), radius=10 * SS, fill=SHADE)
    d.rounded_rectangle(_p(94, 214, 166, 266), radius=14 * SS, fill=VISOR)
    d.text((130 * SS, 240 * SS), "AI", fill=acc, anchor="mm", font=_font(30 * SS))

    # right arm (gesturing) in front: angle mapped from arm_q
    ang = -60 + 200 * (arm_q / (ARM_STEPS - 1))          # -60 (down) .. 140 (up/over head)
    _arm(d, (192, 222), ang, 82, acc)

    # neck
    d.rounded_rectangle(_p(110, 178, 150, 200), radius=8 * SS, fill=SHADE, outline=INK, width=4 * SS)

    # antenna
    d.line(_p(130, 60, 130, 26), fill=INK, width=6 * SS)
    d.ellipse(_p(116, 8, 144, 36), fill=INK)
    d.ellipse(_p(120, 12, 140, 32), fill=acc)

    # ears
    for x0 in (24, 216):
        d.rounded_rectangle(_p(x0, 96, x0 + 20, 146), radius=8 * SS, fill=acc, outline=INK, width=4 * SS)

    # head + visor
    d.rounded_rectangle(_p(36, 54, 224, 188), radius=46 * SS, fill=SHELL, outline=INK, width=5 * SS)
    d.rounded_rectangle(_p(56, 74, 204, 166), radius=32 * SS, fill=VISOR)
    d.ellipse(_p(66, 80, 96, 96), fill=(255, 255, 255, 40))       # visor glint

    # eyes
    for ex in (100, 160):
        ey = 112
        if blink:
            d.rounded_rectangle(_p(ex - 14, ey - 3, ex + 14, ey + 3), radius=3 * SS, fill=acc)
        elif expr == "happy":
            d.arc(_p(ex - 16, ey - 12, ex + 16, ey + 18), 200, 340, fill=acc, width=7 * SS)
        elif expr == "surprised":
            d.ellipse(_p(ex - 17, ey - 19, ex + 17, ey + 19), fill=acc)
            d.ellipse(_p(ex - 6, ey - 12, ex + 4, ey - 2), fill=(255, 255, 255, 230))
        else:
            d.rounded_rectangle(_p(ex - 12, ey - 16, ex + 12, ey + 16), radius=12 * SS, fill=acc)
            d.ellipse(_p(ex - 6, ey - 11, ex + 2, ey - 3), fill=(255, 255, 255, 220))

    # cheeks
    d.ellipse(_p(64, 136, 86, 148), fill=CHEEK)
    d.ellipse(_p(174, 136, 196, 148), fill=CHEEK)

    # mouth: closed = smile, open = rounded box that grows with the voice
    if mouth <= 0:
        d.arc(_p(114, 132, 146, 156), 20, 160, fill=acc, width=5 * SS)
    else:
        h = 5 + mouth * 5
        w = 22 + mouth * 3
        d.rounded_rectangle(_p(130 - w / 2, 148 - h / 2, 130 + w / 2, 148 + h / 2), radius=min(h, w) / 2 * SS,
                            fill=(255, 120, 150, 255), outline=acc, width=3 * SS)

    out = im.resize((int(BW * size), int(BH * size)), Image.LANCZOS)
    return out


@functools.lru_cache(maxsize=None)
def _font(size):
    from edu_render import font
    return font(size)


def _blink(t):
    """Deterministic natural-looking blinks (~every 3-4 s, sometimes a double blink)."""
    period = 3.4
    k = t % period
    n = int(t // period)
    if k < 0.12:
        return True
    return n % 3 == 1 and 0.28 < k < 0.38


def pose(kind, t, scene_t, talk):
    """Returns (expr, arm_q, bob_px) for global time t, time inside the scene, and voice level 0..1."""
    if kind == "cta" or (kind == "hook" and scene_t < 1.6):
        swing = 0.5 + 0.5 * math.sin(math.tau * 1.6 * t)            # friendly wave
        arm = 0.78 + 0.2 * swing
    else:
        arm = 0.62 + 0.06 * math.sin(math.tau * 0.5 * t) + 0.08 * talk  # pointing up at the content
    expr = "happy" if kind in ("cta", "takeaway") else "surprised" if (kind == "hook" and scene_t < 1.0) else "normal"
    bob = 7 * math.sin(math.tau * 0.85 * t) + 4 * talk
    arm_q = max(0, min(ARM_STEPS - 1, int(round(arm * (ARM_STEPS - 1)))))
    return expr, arm_q, bob


def draw(frame, accent, kind, t, scene_t, talk, cx, cy, size=1.0, alpha=1.0):
    """Composite the mascot onto `frame` (RGBA) centred at (cx, cy). talk: 0..1 voice loudness."""
    expr, arm_q, bob = pose(kind, t, scene_t, talk)
    mouth = 0 if talk < 0.08 else min(4, 1 + int(talk * 4))
    im = sprite(tuple(accent[:3]), mouth, _blink(t), expr, arm_q, size)
    if alpha < 0.99:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    x, y = int(cx - im.width / 2), int(cy - im.height / 2 - bob)
    frame.paste(im, (x, y), im)
    return im.width, im.height
