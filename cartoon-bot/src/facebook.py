"""Optional: cross-post each reel to your Facebook Page as a Reel (free extra reach from the same video).
Turn on by adding the GitHub variable FB_PAGE_ID (your Page's numeric id). Uses the same Meta token as Instagram,
which then needs the permissions pages_show_list, pages_read_engagement and pages_manage_posts."""
import os, time, requests
from instagram import GRAPH
import config as C
from util import log


def enabled():
    return bool(os.environ.get("FB_PAGE_ID", "").strip())


def _page_token(page_id):
    r = requests.get(f"{GRAPH}/{page_id}", params={"fields": "access_token", "access_token": C.IG_ACCESS_TOKEN()}, timeout=30)
    j = r.json()
    if "access_token" not in j:
        raise RuntimeError(f"no Page token (add pages_manage_posts + pages_show_list to the Meta token): {j.get('error', j)}")
    return j["access_token"]


def post_reel(video_url, caption):
    page = os.environ["FB_PAGE_ID"].strip()
    tok = _page_token(page)
    j = requests.post(f"{GRAPH}/{page}/video_reels", data={"upload_phase": "start", "access_token": tok}, timeout=60).json()
    if "video_id" not in j:
        raise RuntimeError(f"Facebook reel start failed: {j.get('error', j)}")
    vid = j["video_id"]
    up = requests.post(j.get("upload_url") or f"https://rupload.facebook.com/video-upload/v21.0/{vid}",
                       headers={"Authorization": f"OAuth {tok}", "file_url": video_url}, timeout=300)
    if up.status_code >= 300:
        raise RuntimeError(f"Facebook upload failed {up.status_code}: {up.text[:200]}")
    for _ in range(3):
        f = requests.post(f"{GRAPH}/{page}/video_reels", data={"upload_phase": "finish", "video_id": vid,
                          "video_state": "PUBLISHED", "description": caption[:2200], "access_token": tok}, timeout=60).json()
        if f.get("success"):
            log("Facebook Reel published:", vid)
            return vid
        time.sleep(15)
    raise RuntimeError(f"Facebook reel publish failed: {f}")
