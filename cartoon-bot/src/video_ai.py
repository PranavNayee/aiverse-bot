"""AI video clip generation via Hugging Face Inference API (free tier).
Uses LTX-Video — open source, no billing required, just a free HF token."""
import os, time, requests, base64
from util import log

HF_TOKEN = lambda: os.environ.get("HF_TOKEN", "")

# LTX-Video on HF Inference API — free with a HF account
HF_API_URL = "https://api-inference.huggingface.co/models/Lightricks/LTX-Video"


def _hf_headers():
    return {"Authorization": f"Bearer {HF_TOKEN()}", "Content-Type": "application/json"}


def build_video_prompt(scene, narration, hook=None, is_first=False):
    """Build a cinematic video prompt for the scene."""
    style = ("vibrant 2D cartoon animation, bold bright colors, expressive characters, "
             "Indian setting, comedic, smooth fluid motion, vertical 9:16 portrait frame, "
             "high quality, detailed")

    char_desc = ""
    chars = scene.get("characters", [])
    if "chintu" in chars:
        char_desc += "short chubby Indian man with big black moustache in yellow kurta, "
    if "mintu" in chars:
        char_desc += "tall thin Indian man with round glasses in blue shirt, "

    scene_desc = scene.get("image_prompt", "")
    hook_text = f'text overlay showing "{hook}" at start, ' if hook and is_first else ""

    prompt = f"{style}, {char_desc}{scene_desc}, {hook_text}dynamic camera movement"
    return prompt[:500]


def _generate_hf(prompt, duration):
    """Call HF Inference API for LTX-Video."""
    payload = {
        "inputs": prompt,
        "parameters": {
            "num_frames": min(int(duration * 8), 80),   # LTX runs at ~8fps
            "num_inference_steps": 30,
            "guidance_scale": 3.0,
            "height": 480,
            "width": 272,   # 9:16 at 272x480
        }
    }
    for attempt in range(4):
        r = requests.post(HF_API_URL, headers=_hf_headers(), json=payload, timeout=300)
        if r.status_code == 200:
            return r.content   # raw video bytes
        if r.status_code == 503:
            # Model loading, wait and retry
            wait = 30 * (attempt + 1)
            log(f"  HF model loading, waiting {wait}s...")
            time.sleep(wait)
            continue
        raise RuntimeError(f"HF API error {r.status_code}: {r.text[:200]}")
    raise RuntimeError("HF model failed to load after 4 attempts")


def make_video_clip(scene, narration, duration, out_path, hook=None, is_first=False, idx=0):
    """Generate an AI video clip. Returns out_path on success."""
    if not HF_TOKEN():
        raise RuntimeError("HF_TOKEN not set")

    prompt = build_video_prompt(scene, narration, hook=hook, is_first=is_first)
    log(f"  Generating AI video via HuggingFace LTX-Video...")
    log(f"  Prompt: {prompt[:80]}...")

    video_bytes = _generate_hf(prompt, duration)
    with open(out_path, "wb") as f:
        f.write(video_bytes)
    log(f"  AI video saved ({len(video_bytes)//1024} KB)")
    return out_path
