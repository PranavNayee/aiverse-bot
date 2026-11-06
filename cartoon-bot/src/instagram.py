import time, requests
import config as C
from util import log

GRAPH = "https://graph.facebook.com/v21.0"

def _check(r):
    try:
        j = r.json()
    except Exception:
        raise RuntimeError(f"Instagram API non-JSON response {r.status_code}: {r.text[:200]}")
    if r.status_code != 200 or "error" in j:
        raise RuntimeError(f"Instagram API error: {j.get('error', j)}")
    return j

def check_token():
    """Returns the account username if the token and user id work."""
    j = _check(requests.get(f"{GRAPH}/{C.IG_USER_ID()}", params={"fields": "username",
               "access_token": C.IG_ACCESS_TOKEN()}, timeout=60))
    return j.get("username", "?")

def post_reel(video_url, caption, cover_url=None):
    """Publishes a Reel. Returns the media id."""
    uid, tok = C.IG_USER_ID(), C.IG_ACCESS_TOKEN()
    data = {"media_type": "REELS", "video_url": video_url, "caption": caption[:2200],
            "share_to_feed": "true", "access_token": tok}
    if cover_url:
        data["cover_url"] = cover_url
    cid = _check(requests.post(f"{GRAPH}/{uid}/media", data=data, timeout=60))["id"]
    log("Instagram container created:", cid)
    for _ in range(48):                       # up to ~12 minutes
        time.sleep(15)
        s = _check(requests.get(f"{GRAPH}/{cid}", params={"fields": "status_code,status",
                   "access_token": tok}, timeout=60))
        code = s.get("status_code")
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram processing failed: {s}")
    else:
        raise RuntimeError("Instagram processing timed out")
    media_id = _check(requests.post(f"{GRAPH}/{uid}/media_publish",
                      data={"creation_id": cid, "access_token": tok}, timeout=60))["id"]
    log("Published media id:", media_id)
    return media_id

def recent_media(limit=6):
    """[(caption, unix_ts)] of the account's newest posts. Used to avoid ever posting the same reel twice."""
    import datetime as dt
    j = _check(requests.get(f"{GRAPH}/{C.IG_USER_ID()}/media", params={"fields": "caption,timestamp",
               "limit": limit, "access_token": C.IG_ACCESS_TOKEN()}, timeout=60))
    out = []
    for m in j.get("data", []):
        try:
            ts = dt.datetime.strptime(m.get("timestamp", ""), "%Y-%m-%dT%H:%M:%S%z").timestamp()
        except ValueError:
            ts = 0
        out.append((m.get("caption") or "", ts))
    return out


def already_posted(caption, within_hours=30):
    """True if a post with the same headline went out recently (dedupe across overlapping/retried jobs)."""
    head = "\n".join(caption.strip().splitlines()[:3]).strip()
    if not head:
        return False
    cutoff = time.time() - within_hours * 3600
    try:
        return any(c.strip().startswith(head) and ts >= cutoff for c, ts in recent_media())
    except Exception as e:
        log("Could not read recent posts (continuing):", e)
        return False


def token_days_left():
    """Days until the access token expires (None = never/unknown)."""
    tok = C.IG_ACCESS_TOKEN()
    try:
        j = requests.get(f"{GRAPH}/debug_token", params={"input_token": tok, "access_token": tok}, timeout=30).json()
        exp = (j.get("data") or {}).get("expires_at") or (j.get("data") or {}).get("data_access_expires_at")
        if exp:
            return (exp - time.time()) / 86400
    except Exception as e:
        log("Token expiry check failed:", e)
    return None
