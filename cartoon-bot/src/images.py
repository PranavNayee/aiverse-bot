import base64, time, requests
from urllib.parse import quote
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
            # Vary seed slightly on retries so we don't hit the same cached failure
            s = seed + attempt * 7
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

def make_image(scene, out_base, seed=None):
    """Tries Pollinations first (with retries), then Cloudflare Workers AI (if CF_API_TOKEN is set).
    Returns the saved file path."""
    seed = seed or C.IMG_SEED
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
