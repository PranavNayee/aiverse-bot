"""AI video clip generation via fal.ai (MiniMax H3 / Hailuo).
Each scene becomes a real animated video clip instead of a zoomed still image."""
import os, time, requests
from util import log

FAL_KEY = lambda: os.environ.get("FAL_API_KEY", "")
BASE = "https://queue.fal.run"

# Model priority: best quality first, cheaper fallback second
MODELS = [
    "fal-ai/minimax/hailuo-02/standard/text-to-video",   # Hailuo 02 standard
    "fal-ai/minimax/video-01",                            # fallback
]

HEADERS = lambda: {"Authorization": f"Key {FAL_KEY()}", "Content-Type": "application/json"}


def _submit(model, payload):
    r = requests.post(f"{BASE}/{model}", headers=HEADERS(), json=payload, timeout=60)
    if r.status_code not in (200, 201, 202):
        raise RuntimeError(f"fal submit error {r.status_code}: {r.text[:300]}")
    return r.json()["request_id"]


def _poll(model, request_id, timeout=600):
    status_url = f"{BASE}/{model}/requests/{request_id}/status"
    result_url = f"{BASE}/{model}/requests/{request_id}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(8)
        r = requests.get(status_url, headers=HEADERS(), timeout=30)
        if r.status_code != 200:
            continue
        data = r.json()
        status = data.get("status", "")
        log(f"  fal status: {status}")
        if status in ("COMPLETED", "OK"):
            # fetch actual result
            r2 = requests.get(result_url, headers=HEADERS(), timeout=30)
            result = r2.json()
            # result shape: {"video": {"url": "..."}} or {"video_url": "..."}
            url = (result.get("video") or {}).get("url") or result.get("video_url")
            if url:
                return url
            raise RuntimeError(f"fal result has no video URL: {result}")
        if status == "FAILED":
            raise RuntimeError(f"fal job failed: {data}")
    raise RuntimeError(f"fal job timed out after {timeout}s")


def _download(url, out_path):
    r = requests.get(url, timeout=300, stream=True)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
            f.write(chunk)


def build_video_prompt(scene, narration, hook=None, is_first=False):
    """Build a cinematic video prompt for the scene."""
    # Style prefix for viral cartoon-style reels
    style = ("Vibrant 2D cartoon animation style, bold colors, expressive characters, "
             "Indian setting, comedic, smooth motion, vertical 9:16 frame. ")

    char_desc = ""
    chars = scene.get("characters", [])
    if "chintu" in chars:
        char_desc += "Chintu: short chubby Indian man, big black moustache, yellow kurta. "
    if "mintu" in chars:
        char_desc += "Mintu: tall thin Indian man, round glasses, blue shirt. "

    scene_desc = scene.get("image_prompt", "")
    action = f"Scene: {scene_desc}. "

    # Add narration as audio hint
    audio = f'Audio: Hindi voiceover saying "{narration}". '

    # Hook for first scene
    hook_text = f'Show on screen: "{hook}" at the start. ' if hook and is_first else ""

    # Camera movement hint for dynamism
    camera = "Camera: gentle push-in or slow pan, dynamic and engaging. "

    full = style + char_desc + action + camera + audio + hook_text
    return full[:2000]  # fal has a 2000 char limit


def make_video_clip(scene, narration, duration, out_path, hook=None, is_first=False, idx=0):
    """Generate a real AI video clip for one scene. Returns out_path on success."""
    if not FAL_KEY():
        raise RuntimeError("FAL_API_KEY not set")

    prompt = build_video_prompt(scene, narration, hook=hook, is_first=is_first)
    # Clamp duration: fal supports 3-10s per clip
    clip_dur = max(3, min(10, int(round(duration))))

    payload = {
        "prompt": prompt,
        "duration": clip_dur,
        "resolution": "768P",
        "aspect_ratio": "9:16",
        "prompt_expansion_mode": "balanced",
    }

    last_err = None
    for model in MODELS:
        try:
            log(f"  Submitting scene to fal.ai ({model})...")
            request_id = _submit(model, payload)
            log(f"  fal request_id: {request_id}")
            video_url = _poll(model, request_id)
            log(f"  fal video ready: {video_url[:80]}...")
            _download(video_url, out_path)
            log(f"  downloaded to {out_path}")
            return out_path
        except Exception as e:
            last_err = e
            log(f"  fal model {model} failed: {e}")

    raise RuntimeError(f"All fal models failed: {last_err}")
