"""Read-only status report: what was posted, and how every reel is doing on Instagram + YouTube.
Run from 'Pre-flight check' -> status_report = true. Prints a table to the log and sends a summary to Telegram."""
import datetime as dt, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import storage, slots, growth, youtube, notify, requests
import config as C
from instagram import GRAPH

days = int(os.environ.get("REPORT_DAYS", "14"))
cut = time.time() - days * 86400
hist = [h for h in storage.get_json("history.json", []) if (h.get("posted_ts") or 0) >= cut]
print(f"== {len(hist)} posts in the last {days} days ==")

yt_stats = {}
if youtube.enabled():
    try:
        tok = youtube._access_token()
        ids = [h["youtube_id"] for h in hist if h.get("youtube_id")]
        for i in range(0, len(ids), 50):
            j = youtube._api("GET", "videos", tok, params={"part": "statistics,contentDetails,status", "id": ",".join(ids[i:i+50])})
            for v in j.get("items", []):
                yt_stats[v["id"]] = {**v["statistics"], "privacy": v["status"]["privacyStatus"]}
        ch = youtube._api("GET", "channels", tok, params={"part": "statistics", "mine": "true"})["items"][0]["statistics"]
        print(f"YouTube channel: {ch.get('subscriberCount')} subs, {ch.get('viewCount')} total views, {ch.get('videoCount')} videos")
    except Exception as e:
        print("YouTube stats failed:", e)

try:
    me = growth._get(C.IG_USER_ID(), fields="followers_count,media_count,username")
    print(f"Instagram @{me.get('username')}: {me.get('followers_count')} followers, {me.get('media_count')} posts")
except Exception as e:
    print("Instagram profile failed:", e)

rows = []
print(f"{'posted (IST)':<17}{'type':<9}{'IG views':>9}{'reach':>7}{'likes':>6}{'cmts':>5}{'shares':>7}{'saves':>6}{'avgwatch':>9}{'YT views':>9}{'YT likes':>9}  topic")
for h in sorted(hist, key=lambda x: x.get("posted_ts", 0)):
    ig = {}
    if str(h.get("media_id", "")).isdigit():
        try:
            ig = growth.media_insights(h["media_id"])
        except Exception as e:
            ig = {"err": str(e)[:60]}
    yt = yt_stats.get(h.get("youtube_id"), {})
    when = dt.datetime.fromtimestamp(h["posted_ts"], slots.TZ).strftime("%a %d %b %H:%M")
    aw = ig.get("ig_reels_avg_watch_time")
    aw = f"{aw/1000:.1f}s" if isinstance(aw, (int, float)) else "-"
    print(f"{when:<17}{h.get('type','?'):<9}{ig.get('views', ig.get('plays', '-')):>9}{ig.get('reach','-'):>7}{ig.get('likes','-'):>6}"
          f"{ig.get('comments','-'):>5}{ig.get('shares','-'):>7}{ig.get('saved','-'):>6}{aw:>9}{yt.get('viewCount','-'):>9}"
          f"{yt.get('likeCount','-'):>9}  {str(h.get('topic',''))[:45]} {('[YT ' + yt.get('privacy','') + ']') if yt.get('privacy') not in (None, 'public') else ''}"
          f"{(' ERR ' + ig['err']) if 'err' in ig else ''}")
    rows.append((h, ig, yt))

missing_yt = [h for h in hist if not h.get("youtube_id")]
print(f"\nPosts without a YouTube copy: {len(missing_yt)}")
w = storage.get_json("weekly.json", {})
print("Weekly long video:", w or "none yet")
pend = storage.get_json("pending.json", None)
print("Pending:", {k: pend.get(k) for k in ("slot", "type", "topic", "attempts", "status")} if pend else "nothing queued")
