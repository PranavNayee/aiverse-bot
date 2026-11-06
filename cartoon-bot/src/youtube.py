"""Cross-post every reel to YouTube Shorts (YouTube shares ad revenue on Shorts - the main money path).
Enabled when the secrets YT_CLIENT_ID, YT_CLIENT_SECRET and YT_REFRESH_TOKEN exist
(get the refresh token once with: python cartoon-bot/tools/youtube_auth.py).
NOTE: Google keeps uploads from an UNVERIFIED API project PRIVATE until the project passes YouTube's free
API compliance audit - see README 'YouTube Shorts'."""
import json, os, re, requests
from util import log, retry

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"


def enabled():
    return all(os.environ.get(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"))


def _access_token():
    r = requests.post(TOKEN_URL, data={"client_id": os.environ["YT_CLIENT_ID"],
                                       "client_secret": os.environ["YT_CLIENT_SECRET"],
                                       "refresh_token": os.environ["YT_REFRESH_TOKEN"],
                                       "grant_type": "refresh_token"}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"YouTube auth failed {r.status_code}: {r.text[:200]} (re-run tools/youtube_auth.py)")
    return r.json()["access_token"]


def _title(headline, topic):
    t = re.sub(r"[<>]", "", (headline or topic or "AI in 60 seconds")).strip()
    t = t[:88].rstrip()
    return f"{t} #Shorts"


@retry(tries=3, delay=10)
def upload(video_url, caption, headline, topic, tags=()):
    """Downloads the reel from storage and uploads it as a public Short. Returns the YouTube video id."""
    data = requests.get(video_url, timeout=300).content
    if len(data) < 50_000:
        raise RuntimeError("could not download the reel for YouTube")
    tok = _access_token()
    desc = re.sub(r"[<>]", "", caption)[:4800]
    meta = {"snippet": {"title": _title(headline, topic), "description": desc,
                        "tags": [t.lstrip("#") for t in tags][:15] + ["AI", "machine learning", "shorts"],
                        "categoryId": "27", "defaultLanguage": "en" if os.environ.get("LANGUAGE_MODE") == "english_only" else "hi"},
            "status": {"privacyStatus": os.environ.get("YT_PRIVACY", "public"), "selfDeclaredMadeForKids": False}}
    r = requests.post(UPLOAD_URL, params={"uploadType": "resumable", "part": "snippet,status"},
                      headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                               "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(len(data))},
                      data=json.dumps(meta), timeout=60)
    if r.status_code != 200 or "Location" not in r.headers:
        raise RuntimeError(f"YouTube upload init failed {r.status_code}: {r.text[:300]}")
    up = requests.put(r.headers["Location"], data=data, headers={"Content-Type": "video/mp4"}, timeout=600)
    if up.status_code not in (200, 201):
        raise RuntimeError(f"YouTube upload failed {up.status_code}: {up.text[:300]}")
    vid = up.json().get("id")
    log("YouTube Short uploaded:", vid)
    return vid
