import requests
import config as C
from util import log

def _clean_token():
    t = str(C.TELEGRAM_TOKEN() or "").strip().strip("\"'").strip()
    if t.lower().startswith("bot") and len(t) > 3 and t[3].isdigit():
        t = t[3:]
    return t

def _api(method):
    return f"https://api.telegram.org/bot{_clean_token()}/{method}"

def text(msg):
    try:
        tok = _clean_token()
        if not tok or tok == "test":
            return
        r = requests.post(_api("sendMessage"), data={"chat_id": C.TELEGRAM_CHAT_ID(), "text": msg[:4000]}, timeout=60)
        if r.status_code != 200:
            log(f"Telegram text failed ({r.status_code}):", r.text[:200])
    except Exception as e:
        log("Telegram text failed:", e)

def video(path, caption, fallback_url=""):
    try:
        tok = _clean_token()
        if not tok or tok == "test":
            return
        with open(path, "rb") as f:
            r = requests.post(_api("sendVideo"), data={"chat_id": C.TELEGRAM_CHAT_ID(), "caption": caption[:1000],
                              "supports_streaming": "true"}, files={"video": f}, timeout=300)
        if r.status_code == 200:
            return
        log(f"Telegram video failed ({r.status_code}):", r.text[:200])
    except Exception as e:
        log("Telegram video failed:", e)
    text(f"{caption[:600]}\n\n(Video upload to Telegram failed. Watch it here: {fallback_url})")

def latest_command(since_ts):
    """Reads recent Telegram messages from YOUR chat only (latest command wins). Returns:
    'post' (/post: publish at the slot time), 'post_now' (/postnow: publish immediately), 'skip' (/skip) or None."""
    tok = _clean_token()
    if not tok or tok == "test":
        return None
    try:
        r = requests.get(_api("getUpdates"), params={"limit": 100, "timeout": 0}, timeout=60)
        if r.status_code != 200:
            log(f"getUpdates failed ({r.status_code}):", r.text[:200])
            return None
        cmd = None
        for u in r.json().get("result", []):
            m = u.get("message") or u.get("channel_post") or {}
            if str(m.get("chat", {}).get("id")) != str(C.TELEGRAM_CHAT_ID()) or m.get("date", 0) < since_ts:
                continue
            t = (m.get("text") or "").strip().lower().split("@")[0]
            if t in ("/post", "/approve", "/yes"):
                cmd = "post"
            elif t in ("/postnow", "/now"):
                cmd = "post_now"
            elif t in ("/skip", "/reject", "/no"):
                cmd = "skip"
        return cmd
    except Exception as e:
        log("Telegram command check failed (ignored):", e)
        return None
