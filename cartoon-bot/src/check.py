"""Pre-flight check: tests every service the bot uses and tells you exactly what is wrong (also sent to Telegram)."""
import os, shutil, subprocess, sys, tempfile, time
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
    need("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "SUPABASE_URL", "SUPABASE_SERVICE_KEY", "IG_USER_ID", "IG_ACCESS_TOKEN")
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY")):
        raise RuntimeError("set GEMINI_API_KEY and/or GROQ_API_KEY")
    return "all core secrets present"

def c_schedule():
    import slots
    s = slots.upcoming_slot()
    return f"next post slot {slots.fmt(s)} ({C.TIMEZONE}), review mode '{C.REVIEW_MODE}'"

def c_ffmpeg():
    for b in ("ffmpeg", "ffprobe"):
        if not shutil.which(b): raise RuntimeError(f"{b} not installed")
    out = subprocess.run(["ffmpeg", "-filters"], capture_output=True, text=True).stdout
    if "loudnorm" not in out: raise RuntimeError("ffmpeg is missing the loudnorm filter")
    return "ffmpeg OK"

def c_font():
    out = subprocess.run(["fc-list"], capture_output=True, text=True).stdout if shutil.which("fc-list") else ""
    if "NotoSans-Bold" not in out and "Noto Sans" not in out:
        raise RuntimeError("Noto Sans font missing (apt install fonts-noto-core)")
    if "Emoji" not in out:
        raise RuntimeError("emoji font missing (apt install fonts-noto-color-emoji): emojis will be skipped")
    return "Noto + emoji fonts found"

def c_llm():
    import llm
    r = llm.generate_json('Return only this JSON: {"ok": true}', temperature=0)
    if not r.get("ok"): raise RuntimeError(f"unexpected reply {r}")
    return f"AI writer reachable ({llm.LAST})"

def c_telegram():
    import notify
    notify.text("✅ Pre-flight check: Telegram works.")
    return "message sent to your chat (check Telegram)"

def c_storage():
    import storage, requests
    storage.put_json("healthcheck.json", {"ok": True, "ts": time.time()})
    if not storage.get_json("healthcheck.json", None):
        raise RuntimeError("write worked but read failed")
    url = storage.public_url("healthcheck.json")
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"upload works, but the PUBLIC url returns {r.status_code}. Make the bucket PUBLIC in Supabase: {url}")
    p = storage.get_json("pending.json", None)
    q = f"; queued reel for {p.get('slot', p.get('date'))}" if p else "; nothing queued"
    return "Supabase read/write + public URL OK" + q

def c_voice():
    import tts
    os.makedirs("work", exist_ok=True)
    sc = {"narration": "Hello doston, aaj hum AI seekhenge." if C.LANGUAGE_MODE != "english_only" else
          "Hello friends, today we learn AI.", "speech": "नमस्ते दोस्तों, आज हम AI सीखेंगे।"}
    (p, d, words), = tts.speak_scenes([sc])
    return f"voice OK via {tts.LAST} ({d:.1f}s, {len(words)} timed words); provider order {tts.order()}"

def c_render():
    import edu_render, soundtrack
    d = tempfile.mkdtemp()
    a = os.path.join(d, "a.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=220:duration=2", a], check=True)
    scenes = [{"kind": "hook", "visual": {"text": "Test reel", "emoji": "🤖"}, "start": 0.0, "dur": 2.0}]
    lv = soundtrack.build([a], [0.0], 2.0, os.path.join(d, "m.wav"), edu_render.FPS)
    out = os.path.join(d, "t.mp4")
    edu_render.render_video(scenes, os.path.join(d, "m.wav"), lv, out, "Check",
                            words=[(0.1, 0.6, "Test"), (0.6, 1.2, "reel")])
    return f"2D animation engine OK ({os.path.getsize(out)//1024} KB test clip)"

def c_ig():
    import instagram
    user = instagram.check_token()
    days = instagram.token_days_left()
    left = f", token expires in {days:.0f} days" if days is not None else ""
    if days is not None and days < 7:
        raise RuntimeError(f"token for @{user} expires in {days:.1f} days - renew it now (GET_NEW_TOKEN.md)")
    scopes = instagram.token_scopes()
    need = {"instagram_content_publish": "posting", "instagram_manage_insights": "analytics + learning",
            "instagram_manage_comments": "auto-replies"}
    miss = [f"{k} ({v})" for k, v in need.items() if scopes and k not in scopes]
    extra = f"; MISSING permissions: {', '.join(miss)} - regenerate the token with them (GET_NEW_TOKEN.md)" if miss else ""
    return f"Instagram token OK for @{user}{left}{extra}"

if __name__ == "__main__":
    check("Secrets", c_secrets); check("Schedule", c_schedule); check("FFmpeg", c_ffmpeg)
    check("Fonts", c_font, critical=False); check("AI writer", c_llm); check("Telegram", c_telegram)
    check("Supabase storage", c_storage); check("Voice", c_voice); check("2D animation", c_render)
    check("Instagram", c_ig)
    lines = [f"{'✅' if ok else ('⚠️' if ok is None else '❌')} {name}: {info}" for ok, name, info in results]
    report = "\n".join(lines)
    print(report)
    try:
        import notify; notify.text("Pre-flight report\n\n" + report)
    except Exception:
        pass
    sys.exit(0 if all(r[0] is not False for r in results) else 1)
