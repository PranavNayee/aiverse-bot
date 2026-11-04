"""Pre-flight check: run this first. It tests every service and tells you exactly what is wrong."""
import os, shutil, subprocess, sys, tempfile
import config as C

results = []
def check(name, fn, critical=True):
    try:
        info = fn()
        results.append((True, name, info or ""))
    except Exception as e:
        results.append((False if critical else None, name, str(e)[:300]))

def need(*names):
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise RuntimeError("missing secrets: " + ", ".join(missing))

def c_secrets():
    need("GEMINI_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "SUPABASE_URL", "SUPABASE_SERVICE_KEY")
    return "all core secrets present"

def c_ffmpeg():
    for b in ("ffmpeg", "ffprobe"):
        if not shutil.which(b): raise RuntimeError(f"{b} not installed")
    out = subprocess.run(["ffmpeg", "-filters"], capture_output=True, text=True).stdout
    for f in (" ass ", "zoompan", "sidechaincompress", "loudnorm"):
        if f not in out: raise RuntimeError(f"ffmpeg is missing filter {f.strip()}")
    return "ffmpeg + required filters OK"

def c_font():
    out = subprocess.run(["fc-list"], capture_output=True, text=True).stdout
    if "Devanagari" not in out:
        raise RuntimeError("Noto Sans Devanagari font missing (apt install fonts-noto-core). Hindi subtitles would show boxes.")
    if "Emoji" not in out:
        raise RuntimeError("Hindi font OK, but emoji font missing (apt install fonts-noto-color-emoji): stickers will be skipped")
    return "Hindi + emoji fonts found"

def c_gemini():
    import story
    r = story.gemini('Return only JSON: {"ok": true}', temperature=0)
    if not r.get("ok"): raise RuntimeError(f"unexpected reply {r}")
    return f"Gemini reachable (models: {', '.join(C.GEMINI_MODELS)})"

def c_trends():
    import trends
    t = trends.get_trends()
    if not t: raise RuntimeError("no safe trending topics found (bot will fall back to everyday jokes)")
    return f"{len(t)} safe topics, e.g. {t[0][:60]}"

def c_telegram():
    import notify
    notify.text("✅ Pre-flight check: Telegram works.")
    return "message sent to your chat (check Telegram)"

def c_storage():
    import storage, requests
    storage.put_json("healthcheck.json", {"ok": True})
    if not storage.get_json("healthcheck.json", None):
        raise RuntimeError("write worked but read failed")
    url = storage.public_url("healthcheck.json")
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"upload works, but the PUBLIC url returns {r.status_code}. Make the bucket PUBLIC in Supabase: {url}")
    return "Supabase storage read/write + public URL OK"

_TEST = {}
def c_image():
    import images
    p = images.make_image({"visual": "the monkey vlogger smiling and waving at the camera in a sunny park", "with_sidekick": False},
                          os.path.join(tempfile.mkdtemp(), "t"))
    _TEST["img"] = p
    return f"3D-style image generated ({os.path.getsize(p)//1024} KB): {p}"

def c_depth():
    import depth
    p, real = depth.estimate(_TEST["img"], os.path.join(tempfile.mkdtemp(), "d.npy"))
    _TEST["depth"] = p
    if not real:
        raise RuntimeError("AI depth model unavailable -> videos will use simple depth (still works, less 3D). See log above.")
    return "AI depth model works"

def c_mouth():
    import mouth
    m = mouth.detect(_TEST["img"], "bablu")
    if not m:
        raise RuntimeError("could not locate the mouth in the test image (talking effect will be skipped for such images)")
    return f"mouth found at x={m['x']:.2f}, y={m['y']:.2f}"

def c_render():
    import motion3d, depth
    d = tempfile.mkdtemp()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=200:duration=1.5,tremolo=f=5:d=0.9",
                    f"{d}/a.wav"], check=True)
    dp = _TEST.get("depth") or depth.estimate(_TEST["img"], f"{d}/d.npy")[0]
    motion3d.render_scene(dict(image=_TEST["img"], depth=dp, audio=f"{d}/a.wav", dur=1.5, camera="orbit", reaction="zoom",
                               sticker="😂", mouth={"x": .5, "y": .45, "w": .2}, speaker="bablu", speaker_is_char=True, idx=0),
                          f"{d}/o.mp4")
    return f"3D animation engine renders ({os.path.getsize(d + '/o.mp4')//1024} KB test clip)"

def c_voice():
    import voice
    p = os.path.join(tempfile.mkdtemp(), "t.mp3")
    voice.synth("नमस्ते दोस्तों, यह एक टेस्ट है।", "narrator", p)
    return f"Hindi voice OK ({voice.duration(p):.1f}s)"

def c_ig():
    need("IG_USER_ID", "IG_ACCESS_TOKEN")
    import instagram
    return f"Instagram token OK for @{instagram.check_token()}"

if __name__ == "__main__":
    check("Secrets", c_secrets); check("FFmpeg", c_ffmpeg); check("Hindi font", c_font)
    check("Gemini", c_gemini); check("Trends feed", c_trends, critical=False)
    check("Telegram", c_telegram); check("Supabase storage", c_storage)
    check("Image generation", c_image); check("Depth (3D feel)", c_depth, critical=False)
    check("Mouth detection", c_mouth, critical=False); check("3D animation engine", c_render)
    check("Hindi voice", c_voice)
    check("Instagram token", c_ig, critical=False)
    lines = []
    for ok, name, info in results:
        icon = "✅" if ok else ("⚠️" if ok is None else "❌")
        lines.append(f"{icon} {name}: {info}")
    report = "\n".join(lines)
    print(report)
    try:
        import notify; notify.text("Pre-flight report\n\n" + report)
    except Exception:
        pass
    sys.exit(0 if all(r[0] is not False for r in results) else 1)
