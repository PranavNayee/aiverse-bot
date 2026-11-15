"""Free AI image generation for 'AI Photo Prompt' reels: the reel opens on the real result.
Order: Gemini image models (your free GEMINI_API_KEY) -> Pollinations.ai (free, no key; its corner watermark is cropped).
Safety: prompts never name real people/celebrities; the script writer is told the same."""
import base64, io, os, re, time, urllib.parse
import requests
from PIL import Image
from util import log

GEM_URL = "https://generativelanguage.googleapis.com/v1beta"
BANNED = re.compile(r"\b(nude|naked|sexy|nsfw|gore|blood|weapon|gun|celebrity|modi|shah ?rukh|salman|virat|dhoni)\b", re.I)
_models = None
LAST = ""


def _gemini_models():
    global _models
    if _models is not None:
        return _models
    forced = [m.strip() for m in os.environ.get("GEMINI_IMAGE_MODELS", "").split(",") if m.strip()]
    names = []
    try:
        r = requests.get(f"{GEM_URL}/models", headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
                         params={"pageSize": 200}, timeout=30)
        names = [m["name"].split("/")[-1] for m in r.json().get("models", [])
                 if "image" in m["name"].lower() and "generateContent" in m.get("supportedGenerationMethods", [])]
    except Exception as e:
        log("Gemini image model discovery failed:", e)
    rank = lambda n: (-(float((re.search(r"(\d+(?:\.\d+)?)", n) or [0, 0])[1])), "preview" in n, n)
    _models = forced or sorted(names, key=rank)[:3]
    log("Gemini image models:", _models)
    return _models


def _gemini(prompt):
    last = None
    for m in _gemini_models():
        for attempt in range(2):
            try:
                r = requests.post(f"{GEM_URL}/models/{m}:generateContent", timeout=(10, 120),
                                  headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
                                  json={"contents": [{"parts": [{"text": prompt + "\nVertical 4:5 image, no text, no watermark."}]}],
                                        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}})
            except requests.RequestException as e:
                last = e; continue
            if r.status_code == 200:
                for part in (r.json().get("candidates") or [{}])[0].get("content", {}).get("parts", []):
                    data = (part.get("inlineData") or {}).get("data")
                    if data:
                        return Image.open(io.BytesIO(base64.b64decode(data))).convert("RGB"), m
                last = "no image in reply"
            else:
                last = f"{m} {r.status_code}: {r.text[:150]}"
                if r.status_code in (400, 403, 404):
                    break
                time.sleep(6)
    raise RuntimeError(f"Gemini image failed: {last}")


def _huggingface(prompt, seed):
    """FLUX.1-schnell on Hugging Face (free monthly credits with HF_TOKEN)."""
    model = os.environ.get("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
    r = requests.post(f"https://router.huggingface.co/hf-inference/models/{model}", timeout=(10, 180),
                      headers={"Authorization": f"Bearer {os.environ['HF_TOKEN']}", "Accept": "image/jpeg"},
                      json={"inputs": prompt, "parameters": {"width": 896, "height": 1120, "seed": seed}})
    if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image"):
        raise RuntimeError(f"HuggingFace {r.status_code}: {r.text[:150]}")
    return Image.open(io.BytesIO(r.content)).convert("RGB"), "huggingface-flux"


def _pollinations(prompt, seed):
    q = urllib.parse.quote(prompt[:600])
    r = requests.get(f"https://image.pollinations.ai/prompt/{q}", timeout=120,
                     params={"width": 1024, "height": 1280, "nologo": "true", "seed": seed, "model": "flux"})
    if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image"):
        raise RuntimeError(f"Pollinations {r.status_code}")
    im = Image.open(io.BytesIO(r.content)).convert("RGB")
    w, h = im.size
    return im.crop((0, 0, w, int(h * 0.93))), "pollinations"      # drop the bottom-right watermark strip


def generate(prompt, out_path, seed=7):
    """Writes a JPG to out_path and returns it. Raises if every provider fails."""
    global LAST
    if BANNED.search(prompt):
        raise RuntimeError("image prompt rejected by safety filter")
    errors = []
    for fn in ((lambda: _gemini(prompt)) if os.environ.get("GEMINI_API_KEY") else None,
               (lambda: _huggingface(prompt, seed)) if os.environ.get("HF_TOKEN") else None,
               lambda: _pollinations(prompt, seed)):
        if fn is None:
            continue
        try:
            im, LAST = fn()
            im.save(out_path, quality=92)
            log(f"🖼️ AI image via {LAST}: {im.size}")
            return out_path
        except Exception as e:
            errors.append(str(e)[:160]); log("Image provider failed:", str(e)[:160])
    raise RuntimeError("All image providers failed: " + " | ".join(errors))


if __name__ == "__main__":                                   # quick test: python images.py "prompt"
    import sys
    os.makedirs("test_work", exist_ok=True)
    generate(sys.argv[1] if len(sys.argv) > 1 else "a cute robot reading a book in a cosy Indian library, warm light",
             "test_work/ai_image.jpg")
