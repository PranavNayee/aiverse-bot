import base64, time, requests
from urllib.parse import quote
from PIL import Image
import config as C
from util import log

def _ext(data):
    if data[:3] == b"\xff\xd8\xff": return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n": return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP": return "webp"
    return None

def build_prompt(scene):
    chars = " ".join(C.CHARACTERS[c] for c in scene.get("characters", []) if c in C.CHARACTERS)
    who = f"Characters: {chars}. " if chars else ""
    return f"{C.STYLE}. {who}Scene: {scene['image_prompt']}. No text, no letters, no logos, no watermark."

def _pollinations(prompt, seed):
    """Try Pollinations up to 6 times with growing delays and seed variation on failure."""
    url_base = "https://image.pollinations.ai/prompt/"
    last = None
    for attempt in range(6):
        try:
            s = seed + attempt * 7   # vary seed slightly on retries
            url = (f"{url_base}{quote(prompt)}"
                   f"?width=768&height=1344&model=flux&nologo=true&seed={s}")
            r = requests.get(url, timeout=240)
            if r.status_code == 200 and _ext(r.content) and len(r.content) > 15000:
                return r.content
            last = f"status {r.status_code}, {len(r.content)} bytes"
        except Exception as e:
            last = str(e)
        wait = 15 * (attempt + 1)
        log(f"  Pollinations attempt {attempt+1}/6 failed ({last}), retrying in {wait}s...")
        time.sleep(wait)
    raise RuntimeError(f"Pollinations failed after 6 attempts: {last}")

def _cloudflare(prompt, seed):
    r = requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{C.CF_ACCOUNT_ID()}/ai/run/@cf/black-forest-labs/flux-1-schnell",
        headers={"Authorization": f"Bearer {C.CF_API_TOKEN()}"},
        json={"prompt": prompt[:2000], "steps": 6, "seed": seed}, timeout=180)
    if r.status_code != 200:
        raise RuntimeError(f"Cloudflare AI {r.status_code}: {r.text[:200]}")
    data = base64.b64decode(r.json()["result"]["image"])
    if not _ext(data):
        raise RuntimeError("Cloudflare returned an unknown image format")
    return data

def _puppet_composite(scene, out_path, seed):
    """Render a scene using the vector puppet system (characters.py) composited over
    an AI-generated background. Falls back to AI-only if characters module fails."""
    try:
        import characters as CH
        char_names = [c for c in scene.get("characters", []) if c in ("chintu", "mintu")]
        if not char_names:
            return None   # no characters in this scene, use plain AI image

        # Build background prompt without character descriptions (just the scene)
        bg_prompt = (f"{C.STYLE}. Scene background only, no people: "
                     f"{scene['image_prompt']}. No text, no letters, no logos, no watermark.")
        providers = [("pollinations", _pollinations)]
        if C.CF_API_TOKEN() and C.CF_ACCOUNT_ID():
            providers.append(("cloudflare", _cloudflare))

        bg_data = None
        for name, fn in providers:
            try:
                bg_data = fn(bg_prompt, seed)
                log(f"  background ok via {name}")
                break
            except Exception as e:
                log(f"  background provider {name} failed: {e}")
        if not bg_data:
            return None

        # Load background and resize to 9:16 portrait
        import io
        bg = Image.open(io.BytesIO(bg_data)).convert("RGBA")
        W, H = 768, 1344
        bg = bg.resize((W, H), Image.LANCZOS)

        # Composite each character
        n = len(char_names)
        for i, cname in enumerate(char_names):
            rig = CH.get_rig(cname)
            # Pick expression based on position in story (random-ish from seed)
            expressions = [
                ("smile", "neutral", False),
                ("o", "raised", False),
                ("flat", "neutral", False),
                ("wide", "raised", True),
            ]
            look, brow, blink = expressions[(seed + i) % len(expressions)]
            head = rig.head(look=0, blink=blink, brow=brow, mouth=look)

            # Compose body + head into a full character image
            body = rig.body.convert("RGBA")
            bw, bh = body.size
            hw, hh = head.size
            hx = rig.head_pivot[0] - hw // 2
            hy = rig.head_pivot[1] - hh
            char_img = Image.new("RGBA", (max(bw, hx + hw), bh + max(0, -hy)), (0, 0, 0, 0))
            char_img.paste(body, (0, max(0, -hy) if hy < 0 else 0), body)
            char_img.alpha_composite(head, (hx, max(0, hy)))

            # Scale character to fit nicely in frame
            target_h = int(H * (0.72 if bh > 700 else 0.60))
            scale = target_h / char_img.height
            cw = int(char_img.width * scale)
            char_img = char_img.resize((cw, target_h), Image.LANCZOS)

            # Position: single char = center, two chars = left/right
            if n == 1:
                cx = (W - cw) // 2
            else:
                cx = int(W * 0.08) if i == 0 else int(W * 0.92) - cw
            cy = H - target_h - 20
            bg.alpha_composite(char_img, (cx, cy))

        # Save as PNG
        bg.convert("RGB").save(out_path, "PNG")
        log(f"  image ok via puppet composite ({len(char_names)} chars)")
        return out_path
    except Exception as e:
        log(f"  puppet composite failed, falling back to AI image: {e}")
        return None

def make_image(scene, out_base, seed=None):
    """Tries puppet composite first (vector characters + AI background),
    then plain AI image (Pollinations → Cloudflare). Returns the saved file path."""
    seed = seed or C.IMG_SEED

    # Try puppet composite for scenes with characters
    puppet_path = out_base + ".png"
    result = _puppet_composite(scene, puppet_path, seed)
    if result:
        return result

    # Plain AI image fallback
    prompt = build_prompt(scene)
    providers = [("pollinations", _pollinations)]
    if C.CF_API_TOKEN() and C.CF_ACCOUNT_ID():
        providers.append(("cloudflare", _cloudflare))
    errors = []
    for name, fn in providers:
        try:
            data = fn(prompt, seed)
            path = f"{out_base}.{_ext(data)}"
            open(path, "wb").write(data)
            log(f"  image ok via {name}")
            return path
        except Exception as e:
            errors.append(str(e)); log(f"  image provider {name} failed: {e}")
    raise RuntimeError("All image providers failed: " + " | ".join(errors))
