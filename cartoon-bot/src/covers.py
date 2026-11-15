"""Designed covers: Instagram reel cover (1080x1920, grid-safe centre) + YouTube thumbnail (1280x720).
Big outlined text with the key word in yellow, over the AI result image or the brand gradient."""
import re
from PIL import Image, ImageDraw, ImageFilter
import edu_render as E

YEL, WHITE, BLACK = (255, 214, 10), (255, 255, 255), (0, 0, 0)
_EMOJI = re.compile(r"[^\w\s\-?!.,:'&%/₹#+]", re.U)


def _text(raw, maxlen=46):
    t = _EMOJI.sub("", raw or "").strip(" -|:")
    t = re.sub(r"\s+", " ", t)
    return (t[:maxlen].rsplit(" ", 1)[0] + "…") if len(t) > maxlen else t


def _bg(size, image_path, accent):
    w, h = size
    if image_path:
        try:
            src = Image.open(image_path).convert("RGB")
            k = max(w / src.width, h / src.height)
            im = src.resize((int(src.width * k) + 1, int(src.height * k) + 1), Image.LANCZOS)
            im = im.crop(((im.width - w) // 2, (im.height - h) // 2, (im.width - w) // 2 + w, (im.height - h) // 2 + h))
            shade = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(shade).rectangle((0, int(h * 0.45), w, h), fill=(0, 0, 0, 150))
            return Image.alpha_composite(im.convert("RGBA"), shade.filter(ImageFilter.GaussianBlur(60))).convert("RGB")
        except Exception:
            pass
    base = E.base_gradient().resize((w, h)) if (w, h) != (E.W, E.H) else E.base_gradient().copy()
    g = E.glow_sprite(int(w * 1.1), accent, 0.5)
    base.paste(g, (w // 2 - g.width // 2, h // 3 - g.height // 2), g)
    return base


def _draw_words(d, words, cx, cy, maxw, start, hl):
    for size in range(start, 40, -6):
        f = E.font(size)
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if d.textlength(trial, font=f) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur); cur = w
        lines.append(cur)
        if len(lines) <= 3:
            break
    sw = max(6, size // 11)
    y0 = cy - (len(lines) - 1) * size * 0.56
    for i, ln in enumerate(lines):
        y = y0 + i * size * 1.12
        x = cx - d.textlength(ln, font=f) / 2
        for w in ln.split(" "):
            col = YEL if w.lower().strip("?!.,") in hl else WHITE
            d.text((x, y), w, font=f, fill=col, anchor="lm", stroke_width=sw, stroke_fill=BLACK)
            x += d.textlength(w + " ", font=f)


def make(text, out_reel, out_thumb, accent=(45, 212, 191), image_path=None, emoji=None, tag=None):
    words = _text(text).upper().split()
    hl = {max(words, key=len).lower().strip("?!.,")} if words else set()       # highlight the longest word
    # reel cover 1080x1920 - text kept inside the centre 1080x1440 that the profile grid shows
    im = _bg((1080, 1920), image_path, accent)
    d = ImageDraw.Draw(im, "RGBA")
    if emoji and not image_path:
        e = E.emoji_img(emoji, 300)
        if e:
            im.paste(e, (540 - e.width // 2, 520 - e.height // 2), e)
    if tag:
        f = E.font(44); tw = d.textlength(tag, font=f)
        d.rounded_rectangle((540 - tw / 2 - 30, 300, 540 + tw / 2 + 30, 370), 35, fill=accent + (240,))
        d.text((540, 335), tag, font=f, fill=(12, 14, 34), anchor="mm")
    _draw_words(d, words, 540, 1150, 960, 120, hl)
    im.save(out_reel, quality=92)
    # YouTube thumbnail 1280x720
    th = _bg((1280, 720), image_path, accent)
    d = ImageDraw.Draw(th, "RGBA")
    if emoji and not image_path:
        e = E.emoji_img(emoji, 220)
        if e:
            th.paste(e, (1110 - e.width // 2, 360 - e.height // 2), e)
    side = bool(emoji and not image_path)
    _draw_words(d, words, 500 if side else 640, 380, 820 if side else 1080, 110, hl)
    th.save(out_thumb, quality=92)
    return out_reel, out_thumb
