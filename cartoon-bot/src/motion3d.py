"""Turns one still 3D-style picture into a moving shot:
  * depth-based parallax camera (push / orbit / pull / shake) so it feels 3D
  * talking-mouth effect driven by the voice
  * 'beat' zoom on speech, punch-in / shake reactions, emoji sticker pop, scene-start flash
Frames are streamed straight into ffmpeg."""
import math, os, subprocess
import numpy as np
import cv2
import config as C
from fx import envelope, load_emoji, ease_out_back, FPS, TAU

W, H = 1080, 1920
cv2.setNumThreads(1)

def _load_cover(path):
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if im is None:                                          # fallback reader
        from PIL import Image
        im = cv2.cvtColor(np.asarray(Image.open(path).convert("RGB")), cv2.COLOR_RGB2BGR)
    k = max(W / im.shape[1], H / im.shape[0])
    im = cv2.resize(im, (int(im.shape[1] * k) + 1, int(im.shape[0] * k) + 1), interpolation=cv2.INTER_CUBIC)
    y0, x0 = (im.shape[0] - H) // 2, (im.shape[1] - W) // 2
    return im[y0:y0 + H, x0:x0 + W]

def _vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.70)) ** 2)
    return (1.0 - 0.28 * np.clip(r - 0.35, 0, 1) ** 1.4)[..., None]

def _camera(kind, p, t):
    """Returns zoom, pan_x, pan_y, parallax_x, parallax_y for progress p (0..1) and time t."""
    if kind == "orbit":
        z, px, py, qx, qy = 1.09, 0, 0, 52 * (2 * p - 1), 12 * math.sin(TAU * p)
    elif kind == "pull":
        z, px, py, qx, qy = 1.16 - 0.13 * p, 0, 0, 34 * (1 - 2 * p), 8
    elif kind == "shake":
        z, px, py, qx, qy = 1.07 + 0.015 * math.sin(TAU * 3 * t), 9 * math.sin(TAU * 7.3 * t), 7 * math.sin(TAU * 9.1 * t), 20 * math.sin(TAU * 1.5 * t), 8
    else:  # push
        z, px, py, qx, qy = 1.0 + 0.15 * (p * p * (3 - 2 * p)), 0, 0, 30 * math.sin(TAU * 0.6 * p), 8 * math.sin(TAU * 0.4 * p)
    return z, px + 4 * math.sin(TAU * 0.7 * t), py + 3 * math.sin(TAU * 0.9 * t + 1), qx, qy      # + handheld wobble

def _blend_rgba(frame, rgba, cx, cy, alpha=1.0):
    h, w = rgba.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    fx0, fy0, fx1, fy1 = max(x0, 0), max(y0, 0), min(x0 + w, W), min(y0 + h, H)
    if fx1 <= fx0 or fy1 <= fy0:
        return
    s = rgba[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0]
    a = (s[..., 3:4].astype(np.float32) / 255.0) * alpha
    bgr = s[..., 2::-1].astype(np.float32)
    roi = frame[fy0:fy1, fx0:fx1].astype(np.float32)
    frame[fy0:fy1, fx0:fx1] = (roi * (1 - a) + bgr * a).astype(np.uint8)

def render_scene(spec, out_path, snapshot=None):
    """spec: image, depth(.npy), audio, dur, camera, reaction, sticker, mouth({'x','y','w'} or None), speaker_is_char, idx
    snapshot: (jpg_path, fraction) saves one finished frame (used as the Instagram cover)."""
    dur, idx = float(spec["dur"]), int(spec.get("idx", 0))
    nframes = max(2, int(round(dur * FPS)))
    sm = envelope(spec["audio"], nframes)

    base = (_load_cover(spec["image"]).astype(np.float32) * _vignette()).astype(np.uint8)
    d = np.load(spec["depth"]).astype(np.float32)
    d = cv2.GaussianBlur(cv2.resize(d, (W, H), interpolation=cv2.INTER_LINEAR), (0, 0), 7)
    d0 = float(np.median(d[int(H * 0.35):int(H * 0.65), int(W * 0.3):int(W * 0.7)]))     # subject depth stays still
    dc = d - d0
    xr = (np.arange(W, dtype=np.float32) - W / 2)[None, :].repeat(H, 0)
    yr = (np.arange(H, dtype=np.float32) - H / 2)[:, None].repeat(W, 1)

    mouth = spec.get("mouth") if (C.MOUTH_FX and spec.get("speaker_is_char")) else None
    if mouth:
        mx, my, mrx = mouth["x"] * W, mouth["y"] * H, max(mouth["w"] * W, 40) * 0.95
        mry = mrx * 0.75
        dm = float(dc[int(min(max(my, 0), H - 1)), int(min(max(mx, 0), W - 1))])
    sticker = load_emoji(spec.get("sticker", ""))
    kind, react = spec.get("camera", "push"), spec.get("reaction", "none")
    tr = min(max(dur - 0.9, 0.2), max(0.8, 0.6 * dur))
    flash = np.full((H, W, 3), 255, np.uint8)

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", spec["audio"], "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "22", "-pix_fmt", "yuv420p", "-af", "apad", "-t", f"{dur:.3f}", "-c:a", "aac", "-ar", "44100",
           "-ac", "2", out_path]
    errf = open(out_path + ".err", "wb")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=errf)
    snap_f = int(snapshot[1] * nframes) if snapshot else -1
    rc = -1
    try:
        for f in range(nframes):
            t = f / FPS
            e = float(sm[f]) if spec.get("speaker_is_char") or spec.get("speaker") == "narrator" else 0.0
            z, pan_x, pan_y, qx, qy = _camera(kind, t / dur, t)
            k = math.sin(math.pi * (t - tr) / 0.9) if (react != "none" and tr <= t <= tr + 0.9) else 0.0
            z *= 1 + 0.016 * e                                         # beat zoom while speaking
            pan_y -= 7 * e
            if react == "zoom":  z *= 1 + 0.11 * k
            if react == "shake": pan_x += 18 * math.sin(TAU * 17 * t) * k; z *= 1 + 0.04 * k
            if f < 8: z *= 1 + 0.07 * (1 - f / 8) ** 2                 # tiny punch-in at every cut

            yr_eff = yr
            if mouth and e > 0.05:
                mxd = W / 2 + (mx - W / 2 - pan_x - qx * dm) * z
                myd = H / 2 + (my - H / 2 - pan_y - qy * dm) * z
                x0, x1 = int(max(mxd - 2.4 * mrx * z, 0)), int(min(mxd + 2.4 * mrx * z, W))
                y0, y1 = int(max(myd - 2.4 * mry * z, 0)), int(min(myd + 2.4 * mry * z, H))
                if x1 > x0 and y1 > y0:
                    yr_eff = yr.copy()
                    g = np.exp(-(((xr[y0:y1, x0:x1] + W / 2 - mxd) / (mrx * z)) ** 2 +
                                 ((yr[y0:y1, x0:x1] + H / 2 - myd) / (mry * z)) ** 2))
                    cyr = myd - H / 2
                    yr_eff[y0:y1, x0:x1] = cyr + (yr[y0:y1, x0:x1] - cyr) / (1 + 0.6 * e * g)

            mapx = xr / z + (W / 2 + pan_x) + qx * dc
            mapy = yr_eff / z + (H / 2 + pan_y) + qy * dc
            frame = cv2.remap(base, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

            if mouth and e > 0.18:                                      # dark mouth interior + tongue
                ax, ay = int(mrx * z * 0.40 * (0.6 + 0.4 * e)), int(max(2, mrx * z * 0.34 * e))
                x0, x1 = int(max(mxd - ax * 2, 0)), int(min(mxd + ax * 2, W))
                y0, y1 = int(max(myd - ay * 2, 0)), int(min(myd + ay * 2, H))
                if x1 > x0 + 4 and y1 > y0 + 4:
                    m = np.zeros((y1 - y0, x1 - x0), np.float32)
                    cv2.ellipse(m, (int(mxd - x0), int(myd - y0)), (max(ax, 2), max(ay, 2)), 0, 0, 360, 1.0, -1)
                    tg = np.zeros_like(m)
                    cv2.ellipse(tg, (int(mxd - x0), int(myd - y0 + ay * 0.45)), (max(int(ax * 0.55), 1), max(int(ay * 0.45), 1)), 0, 0, 360, 1.0, -1)
                    m = cv2.GaussianBlur(m, (0, 0), 2.2)[..., None] * 0.9
                    tg = cv2.GaussianBlur(tg, (0, 0), 2.0)[..., None] * m
                    roi = frame[y0:y1, x0:x1].astype(np.float32)
                    roi = roi * (1 - m) + np.array([40, 22, 95], np.float32) * m          # dark red (BGR)
                    roi = roi * (1 - tg) + np.array([125, 110, 235], np.float32) * tg     # pink tongue
                    frame[y0:y1, x0:x1] = roi.astype(np.uint8)

            if sticker is not None and t > 0.4:                         # emoji pops in with a bounce and wobble
                s = 0.15 + 0.85 * ease_out_back((t - 0.4) / 0.45)
                sw = max(8, int(sticker.shape[1] * s)); sh = max(8, int(sticker.shape[0] * s))
                st_im = cv2.resize(sticker, (sw, sh), interpolation=cv2.INTER_AREA)
                rot = cv2.getRotationMatrix2D((sw / 2, sh / 2), 9 * math.sin(TAU * 1.1 * t), 1.0)
                st_im = cv2.warpAffine(st_im, rot, (sw, sh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
                _blend_rgba(frame, st_im, W * 0.80, H * 0.20 + 14 * math.sin(TAU * 0.8 * t))
            if f < 4:                                                   # quick white flash on each cut
                a = 0.55 * (1 - f / 4)
                frame = cv2.addWeighted(frame, 1 - a, flash, a, 0)

            if f == snap_f:
                cv2.imwrite(snapshot[0], frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            proc.stdin.write(frame.tobytes())
        proc.stdin.close()
        rc = proc.wait()
    except BrokenPipeError:
        rc = proc.wait()
    finally:
        errf.close()
    if rc != 0:
        raise RuntimeError("ffmpeg (3D motion) failed: " + open(out_path + ".err", errors="ignore").read()[-1200:])
    os.remove(out_path + ".err")
