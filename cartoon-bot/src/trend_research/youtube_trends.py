"""Optional YouTube Trending Feed for India.
Uses YouTube Data API v3 when YOUTUBE_API_KEY is configured.
Quota efficient: uses 1 quota unit out of 10,000 daily free units.
Gracefully skips if YOUTUBE_API_KEY is not set.
"""
import json
import os
import ssl
import urllib.request
from .normalizer import create_candidate, normalize_text

URL = "https://www.googleapis.com/youtube/v3/videos"

def fetch():
    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        # Graceful skip as specified in master prompt
        return []

    candidates = []
    try:
        ctx = ssl._create_unverified_context()
        # Category 28 = Science & Technology; regionCode = IN
        query_url = (f"{URL}?part=snippet,statistics&chart=mostPopular"
                     f"&regionCode=IN&videoCategoryId=28&maxResults=10&key={api_key}")
        req = urllib.request.Request(query_url, headers={"User-Agent": "AIVerseBot/1.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            data = json.loads(resp.read().decode())

        for item in data.get("items", []):
            snip = item.get("snippet", {})
            stats = item.get("statistics", {})
            title = normalize_text(snip.get("title", ""))
            if not title:
                continue

            vid_id = item.get("id", "")
            video_url = f"https://www.youtube.com/watch?v={vid_id}" if vid_id else ""
            desc = normalize_text(snip.get("description", ""))[:300]
            published_at = snip.get("publishedAt")
            view_count = int(stats.get("viewCount", 0))

            cand = create_candidate(
                title=title,
                category="tech",
                source="youtube_popular",
                url=video_url,
                summary=desc or title,
                published_at=published_at,
                raw_metrics={"views": view_count, "source_type": "youtube_data_api"}
            )
            candidates.append(cand)
        print(f"[trend_research.youtube_trends] Fetched {len(candidates)} YouTube India trending items.")
    except Exception as e:
        print(f"[trend_research.youtube_trends] Warning: YouTube API fetch error: {e}")

    return candidates
