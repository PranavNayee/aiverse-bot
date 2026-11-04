import requests
import config as C
from util import log

def _api(method):
    return f"https://api.telegram.org/bot{C.TELEGRAM_TOKEN()}/{method}"

def text(msg):
    try:
        requests.post(_api("sendMessage"), data={"chat_id": C.TELEGRAM_CHAT_ID(), "text": msg[:4000]}, timeout=60)
    except Exception as e:
        log("Telegram text failed:", e)

def video(path, caption, fallback_url=""):
    try:
        with open(path, "rb") as f:
            r = requests.post(_api("sendVideo"), data={"chat_id": C.TELEGRAM_CHAT_ID(), "caption": caption[:1000],
                              "supports_streaming": "true"}, files={"video": f}, timeout=300)
        if r.status_code == 200:
            return
        log("Telegram video failed:", r.text[:200])
    except Exception as e:
        log("Telegram video failed:", e)
    text(f"{caption[:600]}\n\n(Video upload to Telegram failed. Watch it here: {fallback_url})")

def latest_command(since_ts):
    """Reads recent Telegram messages from YOUR chat only. Returns 'post', 'skip' or None (latest command wins)."""
    r = requests.get(_api("getUpdates"), params={"limit": 100, "timeout": 0}, timeout=60)
    if r.status_code != 200:
        log("getUpdates failed:", r.text[:200]); return None
    cmd = None
    for u in r.json().get("result", []):
        m = u.get("message") or {}
        if str(m.get("chat", {}).get("id")) != C.TELEGRAM_CHAT_ID() or m.get("date", 0) < since_ts:
            continue
        t = (m.get("text") or "").strip().lower().split("@")[0]
        if t in ("/post", "/approve", "/yes"):
            cmd = "post"
        elif t in ("/skip", "/reject", "/no"):
            cmd = "skip"
    return cmd
