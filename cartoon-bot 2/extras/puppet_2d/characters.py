"""Hand-built vector-style cartoon puppets (drawn with Pillow, no image AI needed).
Each character = body + 2 arms + a head whose eyes / brows / mouth are swappable layers."""
import functools
from PIL import Image, ImageDraw

S = 3                                  # supersampling for smooth edges
OUT = (40, 28, 30, 255)
WHITE = (250, 250, 250, 255)
HAIR = (30, 24, 24, 255)
MOUTH_IN = (122, 30, 38, 255)
TONGUE = (232, 110, 120, 255)

def _canvas(w, h):
    return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))

def _done(img):
    return img.resize((img.width // S, img.height // S), Image.LANCZOS)

def _b(box):
    return [int(round(v * S)) for v in box]

def ell(d, box, fill, outline=OUT, w=7):
    d.ellipse(_b(box), fill=fill, outline=outline, width=(w * S if outline else 0))

def rr(d, box, r, fill, outline=OUT, w=7):
    d.rounded_rectangle(_b(box), radius=r * S, fill=fill, outline=outline, width=(w * S if outline else 0))

def poly(d, pts, fill, outline=OUT, w=7):
    p = [(int(round(x * S)), int(round(y * S))) for x, y in pts]
    d.polygon(p, fill=fill)
    if outline:
        d.line(p + [p[0]], fill=outline, width=w * S, joint="curve")

def stroke(d, pts, color=OUT, w=10):
    p = [(int(round(x * S)), int(round(y * S))) for x, y in pts]
    d.line(p, fill=color, width=w * S, joint="curve")
    r = w * S // 2
    for x, y in (p[0], p[-1]):
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)

# ------------------------------------------------------------------ rig container
class Rig:
    def __init__(self, name, body, arm_l, arm_r, head_parts, neck, head_pivot, shoulders, arm_pivot, margins):
        self.name, self.body, self.arm_l, self.arm_r = name, body, arm_l, arm_r
        self.parts = head_parts            # dict of layer builders
        self.neck, self.head_pivot, self.shoulders, self.arm_pivot = neck, head_pivot, shoulders, arm_pivot
        self.margins = margins             # (left/right M, top MT)
        self._cache = {}

    def head(self, look, blink, brow, mouth):
        key = (look, blink, brow, mouth)
        if key not in self._cache:
            p = self.parts
            im = p["base"].copy()
            for layer in (p["eyes"][(look, blink)], p["mouth"][mouth], p["front"], p["brow"][brow]):
                im.alpha_composite(layer)
            self._cache[key] = im
        return self._cache[key]

# ------------------------------------------------------------------ shared layers
def _eye_layers(cx_list, cy, ew, eh, pr, extra_blink_y=0, look_px=9):
    layers = {}
    for look in (-1, 0, 1):
        for blink in (False, True):
            c = _canvas(460, 470); d = ImageDraw.Draw(c)
            for cx in cx_list:
                if blink:
                    stroke(d, [(cx - ew * .5, cy + extra_blink_y), (cx, cy + 8 + extra_blink_y), (cx + ew * .5, cy + extra_blink_y)], OUT, 7)
                else:
                    ell(d, (cx - ew / 2, cy - eh / 2, cx + ew / 2, cy + eh / 2), WHITE, OUT, 5)
                    px = cx + look * look_px
                    ell(d, (px - pr, cy - pr + 2, px + pr, cy + pr + 2), (28, 22, 22, 255), None)
                    ell(d, (px - pr * .35 + 4, cy - pr * .6, px + pr * .35 + 4, cy - pr * .1), WHITE, None)
            layers[(look, blink)] = _done(c)
    return layers

def _mouth_layers(cx, cy):
    out = {}
    def mk(fn):
        c = _canvas(460, 470); d = ImageDraw.Draw(c); fn(d); return _done(c)
    out["smile"] = mk(lambda d: d.arc(_b((cx - 38, cy - 24, cx + 38, cy + 22)), 15, 165, fill=OUT, width=7 * S))
    out["flat"]  = mk(lambda d: stroke(d, [(cx - 26, cy + 4), (cx + 26, cy + 4)], OUT, 7))
    out["frown"] = mk(lambda d: d.arc(_b((cx - 34, cy - 2, cx + 34, cy + 40)), 200, 340, fill=OUT, width=7 * S))
    out["o"]     = mk(lambda d: ell(d, (cx - 15, cy - 14, cx + 15, cy + 20), MOUTH_IN, OUT, 6))
    out["small"] = mk(lambda d: ell(d, (cx - 24, cy - 10, cx + 24, cy + 16), MOUTH_IN, OUT, 6))
    def opn(d):
        ell(d, (cx - 30, cy - 14, cx + 30, cy + 32), MOUTH_IN, OUT, 6)
        ell(d, (cx - 17, cy + 14, cx + 17, cy + 31), TONGUE, None)
    out["open"] = mk(opn)
    def wide(d):
        ell(d, (cx - 38, cy - 16, cx + 38, cy + 44), MOUTH_IN, OUT, 6)
        ell(d, (cx - 21, cy + 22, cx + 21, cy + 43), TONGUE, None)
    out["wide"] = mk(wide)
    return out

def _brow_layers(lx, rx, y):
    out = {}
    def mk(l, r):
        c = _canvas(460, 470); d = ImageDraw.Draw(c)
        stroke(d, l, OUT, 13); stroke(d, r, OUT, 13); return _done(c)
    out["neutral"] = mk([(lx - 34, y + 4), (lx, y - 4), (lx + 34, y + 2)], [(rx - 34, y + 2), (rx, y - 4), (rx + 34, y + 4)])
    out["raised"]  = mk([(lx - 34, y - 10), (lx, y - 24), (lx + 34, y - 14)], [(rx - 34, y - 14), (rx, y - 24), (rx + 34, y - 10)])
    out["angry"]   = mk([(lx - 36, y - 14), (lx + 34, y + 16)], [(rx - 34, y + 16), (rx + 36, y - 14)])
    out["sad"]     = mk([(lx - 34, y + 14), (lx + 34, y - 12)], [(rx - 34, y - 12), (rx + 34, y + 14)])
    return out

ARM_R = 340                                   # arm canvas is 2R x 2R, shoulder pivot at the centre

def _arm(sleeve, skin, w_sleeve=90, length=270, hand_r=42):
    R = ARM_R
    c = _canvas(2 * R, 2 * R); d = ImageDraw.Draw(c)
    hand_cy = R - 27 + length - 10
    ell(d, (R - hand_r, hand_cy - hand_r, R + hand_r, hand_cy + hand_r), skin)
    rr(d, (R - w_sleeve / 2, R - 27, R + w_sleeve / 2, R - 27 + length), 44, sleeve)
    return _done(c)

# ------------------------------------------------------------------ CHINTU (short, chubby, moustache, yellow kurta)
@functools.lru_cache(maxsize=None)
def chintu():
    SKIN, SKIN_D = (224, 160, 108, 255), (190, 122, 78, 255)
    KURTA, KURTA_D = (247, 196, 40, 255), (212, 154, 22, 255)
    # body 520x700
    c = _canvas(520, 700); d = ImageDraw.Draw(c)
    rr(d, (228, 150, 292, 250), 18, SKIN)                                   # neck
    ell(d, (118, 650, 240, 698), (110, 66, 40, 255)); ell(d, (280, 650, 402, 698), (110, 66, 40, 255))
    rr(d, (152, 520, 236, 672), 30, WHITE); rr(d, (284, 520, 368, 672), 30, WHITE)
    rr(d, (66, 215, 454, 604), 140, KURTA)
    poly(d, [(228, 215), (292, 215), (260, 292)], KURTA_D, OUT, 6)
    for y in (340, 410, 480):
        ell(d, (251, y - 9, 269, y + 9), KURTA_D, OUT, 3)
    body = _done(c)
    # head 460x470
    h = _canvas(460, 470); d = ImageDraw.Draw(h)
    ell(d, (36, 218, 112, 296), SKIN); ell(d, (348, 218, 424, 296), SKIN)         # ears
    ell(d, (60, 58, 400, 330), HAIR)
    ell(d, (68, 100, 392, 400), SKIN)                                            # face
    d.pieslice(_b((60, 58, 400, 330)), 180, 360, fill=HAIR)
    ell(d, (104, 150, 356, 330), SKIN, None)                                     # forehead curve
    ell(d, (98, 276, 168, 326), (240, 140, 128, 255), None); ell(d, (292, 276, 362, 326), (240, 140, 128, 255), None)
    ell(d, (206, 252, 254, 296), SKIN_D, OUT, 5)                                 # nose
    base = _done(h)
    f = _canvas(460, 470); d = ImageDraw.Draw(f)                                 # moustache (front)
    for box in [(128, 288, 232, 336), (228, 288, 332, 336)]:
        ell(d, box, HAIR, OUT, 4)
    ell(d, (104, 276, 150, 326), HAIR, OUT, 4); ell(d, (310, 276, 356, 326), HAIR, OUT, 4)
    front = _done(f)
    parts = {"base": base, "front": front,
             "eyes": _eye_layers((172, 288), 224, 70, 80, 17),
             "mouth": _mouth_layers(230, 352),
             "brow": _brow_layers(172, 288, 182)}
    return Rig("chintu", body, _arm(KURTA, SKIN), _arm(KURTA, SKIN).transpose(Image.FLIP_LEFT_RIGHT), parts,
               neck=(260, 240), head_pivot=(230, 395), shoulders=((112, 292), (408, 292)),
               arm_pivot=(ARM_R, ARM_R), margins=(230, 280))

# ------------------------------------------------------------------ MINTU (tall, thin, glasses, blue shirt)
@functools.lru_cache(maxsize=None)
def mintu():
    SKIN, SKIN_D = (232, 182, 138, 255), (200, 146, 104, 255)
    SHIRT, SHIRT_D = (58, 124, 216, 255), (36, 90, 170, 255)
    PANTS = (50, 62, 96, 255)
    c = _canvas(440, 900); d = ImageDraw.Draw(c)
    rr(d, (186, 180, 250, 290), 18, SKIN)                                       # neck
    ell(d, (110, 846, 212, 892), (40, 36, 44, 255)); ell(d, (228, 846, 330, 892), (40, 36, 44, 255))
    rr(d, (130, 560, 212, 866), 26, PANTS); rr(d, (228, 560, 310, 866), 26, PANTS)
    rr(d, (96, 250, 344, 640), 80, SHIRT)
    poly(d, [(194, 250), (246, 250), (220, 312)], WHITE, OUT, 6)
    for y in (350, 430, 510):
        ell(d, (211, y - 8, 229, y + 8), SHIRT_D, OUT, 3)
    body = _done(c)
    h = _canvas(460, 470); d = ImageDraw.Draw(h)
    ell(d, (84, 238, 150, 306), SKIN); ell(d, (310, 238, 376, 306), SKIN)
    for pts in ([(120, 150), (96, 70), (170, 116)], [(190, 110), (200, 30), (250, 100)], [(250, 104), (310, 44), (320, 128)], [(300, 130), (366, 100), (346, 190)]):
        poly(d, pts, HAIR, OUT, 4)
    ell(d, (96, 70, 364, 300), HAIR)
    ell(d, (104, 96, 356, 404), SKIN)
    d.pieslice(_b((96, 70, 364, 300)), 180, 360, fill=HAIR)
    ell(d, (130, 170, 330, 330), SKIN, None)
    ell(d, (212, 290, 248, 322), SKIN_D, OUT, 4)
    base = _done(h)
    f = _canvas(460, 470); d = ImageDraw.Draw(f)                                 # glasses (front)
    for cx in (172, 288):
        ell(d, (cx - 52, 192, cx + 52, 292), (255, 255, 255, 70), OUT, 8)
    stroke(d, [(224, 238), (236, 238)], OUT, 8)
    stroke(d, [(120, 232), (100, 228)], OUT, 7); stroke(d, [(340, 232), (360, 228)], OUT, 7)
    front = _done(f)
    parts = {"base": base, "front": front,
             "eyes": _eye_layers((172, 288), 242, 52, 62, 14, look_px=7),
             "mouth": _mouth_layers(230, 360),
             "brow": _brow_layers(172, 288, 180)}
    return Rig("mintu", body, _arm(SHIRT, SKIN, w_sleeve=64, length=300, hand_r=36),
               _arm(SHIRT, SKIN, w_sleeve=64, length=300, hand_r=36).transpose(Image.FLIP_LEFT_RIGHT), parts,
               neck=(220, 270), head_pivot=(230, 400), shoulders=((112, 300), (328, 300)),
               arm_pivot=(ARM_R, ARM_R), margins=(230, 280))

def get_rig(name):
    return {"chintu": chintu, "mintu": mintu}[name]()
