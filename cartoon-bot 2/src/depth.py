"""Depth map for each image (near = bright). Used to make a flat picture move like real 3D.
Uses a free AI depth model on CPU; if it can't load, falls back to a simple centre-weighted depth so the video still renders."""
import numpy as np
import config as C
from util import log

_pipe = None
_tried = False

def _load():
    global _pipe, _tried
    if _tried:
        return _pipe
    _tried = True
    try:
        from transformers import pipeline
    except Exception as e:
        log("  depth: transformers/torch not installed -> pseudo depth:", e); return None
    for m in C.DEPTH_MODELS:
        try:
            _pipe = pipeline("depth-estimation", model=m, device=-1)
            log("  depth model loaded:", m)
            return _pipe
        except Exception as e:
            log(f"  depth model {m} failed: {str(e)[:120]}")
    return None

def pseudo_depth(w, h):
    """Subject-in-the-middle guess: centre and lower area are closer."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx / w - 0.5) / 0.42) ** 2 + ((yy / h - 0.52) / 0.40) ** 2)
    d = np.clip(1.0 - r, 0, 1) * 0.8 + (yy / h) * 0.2
    return d.astype(np.float32)

def estimate(img_path, out_npy):
    """Saves a float32 depth map (0..1, near=1) and returns (path, is_real)."""
    from PIL import Image
    im = Image.open(img_path).convert("RGB")
    d, real = None, False
    pipe = _load()
    if pipe is not None:
        try:
            out = pipe(im)["depth"]
            d = np.asarray(out, dtype=np.float32)
            d = (d - d.min()) / max(float(d.max() - d.min()), 1e-6)
            real = True
        except Exception as e:
            log("  depth inference failed -> pseudo depth:", e)
    if d is None:
        d = pseudo_depth(im.width, im.height)
    np.save(out_npy, d)
    return out_npy, real
