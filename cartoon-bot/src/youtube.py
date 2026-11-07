"""Cross-post every reel to YouTube Shorts (YouTube shares ad revenue on Shorts - the main money path).
Enabled when the secrets YT_CLIENT_ID, YT_CLIENT_SECRET and YT_REFRESH_TOKEN exist
(get the refresh token once with: python cartoon-bot/tools/youtube_auth.py).
NOTE: Google keeps uploads from an UNVERIFIED API project PRIVATE until the project passes YouTube's free
API compliance audit - see README 'YouTube Shorts'."""
import json, os, re, requests
from util import log, retry

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"


API = "https://www.googleapis.com/youtube/v3"
PLAYLISTS = {"lesson": ("AI Course in Hindi - Lesson by Lesson", "AI aur Machine Learning basics se advanced tak, Hinglish mein. Lesson #1 se shuru karo!"),
             "trick": ("AI Tricks & ChatGPT Tips", "Roz ek AI trick jo aapka time bachaye - ChatGPT prompts, Google Lens, AI tools."),
             "fun_fact": ("AI Fun Facts", "AI ki interesting duniya - har Sunday ek naya fact.")}


def _lang():
    return "en" if os.environ.get("LANGUAGE_MODE") == "english_only" else "hi"


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


def _api(method, path, tok, **kw):
    import requests as rq
    r = rq.request(method, f"{API}/{path}", headers={"Authorization": f"Bearer {tok}"}, timeout=60, **kw)
    if r.status_code >= 300:
        raise RuntimeError(f"YouTube {path} {r.status_code}: {r.text[:200]}")
    return r.json() if r.text else {}


def add_to_playlist(video_id, kind, tok=None):
    """Put the Short in its series playlist (creates the playlist the first time). Never raises."""
    if kind not in PLAYLISTS:
        return
    try:
        tok = tok or _access_token()
        title, desc = PLAYLISTS[kind]
        mine = _api("GET", "playlists", tok, params={"part": "snippet", "mine": "true", "maxResults": 50}).get("items", [])
        pid = next((p["id"] for p in mine if p["snippet"]["title"] == title), None)
        if not pid:
            pid = _api("POST", "playlists", tok, params={"part": "snippet,status"},
                       json={"snippet": {"title": title, "description": desc, "defaultLanguage": _lang()},
                             "status": {"privacyStatus": "public"}})["id"]
            log("Created YouTube playlist:", title)
        _api("POST", "playlistItems", tok, params={"part": "snippet"},
             json={"snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": video_id}}})
    except Exception as e:
        log("Playlist step skipped:", e)


def recent_comment_threads(tok, max_results=50):
    """Top-level comments on the channel's videos, newest first."""
    me = _api("GET", "channels", tok, params={"part": "id", "mine": "true"}).get("items", [{}])[0].get("id")
    if not me:
        return me, []
    j = _api("GET", "commentThreads", tok, params={"part": "snippet,replies", "allThreadsRelatedToChannelId": me,
                                                    "maxResults": max_results, "order": "time", "textFormat": "plainText"})
    return me, j.get("items", [])


def reply(tok, parent_id, text):
    _api("POST", "comments", tok, params={"part": "snippet"},
         json={"snippet": {"parentId": parent_id, "textOriginal": text[:2000]}})


@retry(tries=3, delay=10)
def upload(video_url, caption, headline, topic, tags=()):
    """Downloads the reel from storage and uploads it as a public Short. Returns the YouTube video id."""
    if os.path.exists(video_url):                      # local file (tests) or storage URL (normal posts)
        with open(video_url, "rb") as f:
            data = f.read()
    else:
        data = requests.get(video_url, timeout=300).content
    if len(data) < 50_000:
        raise RuntimeError("could not download the reel for YouTube")
    tok = _access_token()
    desc = re.sub(r"[<>]", "", caption)[:4800]
    meta = {"snippet": {"title": _title(headline, topic), "description": desc,
                        "tags": [t.lstrip("#") for t in tags][:15] + ["AI", "machine learning", "shorts"],
                        "categoryId": "27", "defaultLanguage": _lang(), "defaultAudioLanguage": _lang()},
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
