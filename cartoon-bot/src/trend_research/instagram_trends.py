"""Instagram trend & hashtag discovery.
Uses:
1. Official Meta Instagram Graph API hashtag search (ig_hashtag_search & top_media)
   when IG_ACCESS_TOKEN and IG_USER_ID are configured.
   This is 100% sanctioned, official, and carries ZERO risk of account suspension.
2. Web trend signals for trending Reel topics in India as a graceful zero-auth fallback.
"""
import os
import re
import urllib.parse
import urllib.request
import ssl
import json
import xml.etree.ElementTree as ET
from .normalizer import create_candidate, normalize_text

GRAPH_API = "https://graph.facebook.com/v21.0"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 AIVerseTrendBot/1.0"

# Target hashtags for educational & curiosity reels in India
FACT_HASHTAGS = [
    "factsinhindi",
    "didyouknowfacts",
    "sciencefacts",
    "spacefacts",
    "indianhistory",
    "amazingfacts"
]

def _fetch_graph_hashtag_media(ig_user_id, token, hashtag_name):
    """Fetches top media under a hashtag using the official Instagram Graph API."""
    ctx = ssl._create_unverified_context()
    
    # 1. Search hashtag ID
    search_url = f"{GRAPH_API}/ig_hashtag_search?user_id={ig_user_id}&q={hashtag_name}&access_token={token}"
    req = urllib.request.Request(search_url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
        data = json.loads(resp.read().decode())
    
    tags = data.get("data", [])
    if not tags:
        return []
    tag_id = tags[0]["id"]
    
    # 2. Get top media
    media_url = (f"{GRAPH_API}/{tag_id}/top_media?user_id={ig_user_id}"
                 f"&fields=id,caption,media_type,comments_count,like_count,permalink,timestamp"
                 f"&access_token={token}")
    req2 = urllib.request.Request(media_url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req2, context=ctx, timeout=15) as resp:
        mdata = json.loads(resp.read().decode())
        
    return mdata.get("data", [])

def _clean_caption_topic(caption):
    """Extracts the first hook line or core topic from an Instagram caption."""
    lines = [line.strip() for line in caption.split("\n") if line.strip()]
    if not lines:
        return ""
    # Filter out pure hashtag lines
    for line in lines:
        if line.startswith("#") or len(line.split("#")) > 3:
            continue
        cleaned = re.sub(r"#[A-Za-z0-9_]+", "", line).strip()
        cleaned = re.sub(r"[^\w\s\?\!\,\.\'\"]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if len(cleaned) >= 15:
            return cleaned[:100]
    return lines[0][:80]

def fetch():
    candidates = []
    ig_user_id = os.environ.get("IG_USER_ID", "").strip()
    token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    
    # 1. Try official Instagram Graph API if credentials exist
    if ig_user_id and token:
        try:
            # Query up to 2 hashtags per run to preserve Meta's rolling weekly limit (30/week)
            # Pick by current day of year
            import datetime as dt
            day_idx = dt.datetime.now().timetuple().tm_yday
            active_tags = [FACT_HASHTAGS[day_idx % len(FACT_HASHTAGS)],
                           FACT_HASHTAGS[(day_idx + 1) % len(FACT_HASHTAGS)]]
            
            for tag in active_tags:
                try:
                    media_list = _fetch_graph_hashtag_media(ig_user_id, token, tag)
                    for m in media_list[:5]:
                        caption = m.get("caption", "")
                        topic = _clean_caption_topic(caption)
                        if not topic or len(topic) < 15:
                            continue
                        
                        likes = m.get("like_count", 0)
                        comments = m.get("comments_count", 0)
                        permalink = m.get("permalink", "")
                        timestamp = m.get("timestamp")
                        
                        cand = create_candidate(
                            title=topic,
                            category="facts",
                            source="instagram_hashtag",
                            url=permalink,
                            summary=caption[:300],
                            published_at=timestamp,
                            raw_metrics={
                                "likes": likes,
                                "comments": comments,
                                "hashtag": tag,
                                "source_type": "instagram_graph_api"
                            }
                        )
                        candidates.append(cand)
                except Exception as e:
                    print(f"[trend_research.instagram_trends] Notice: Graph API hashtag #{tag} query: {e}")
                    continue
        except Exception as e:
            print(f"[trend_research.instagram_trends] Notice: Instagram Graph API search skipped: {e}")

    # 2. Add search-indexed viral reel signals for India (Zero-auth public fallback)
    try:
        ctx = ssl._create_unverified_context()
        query = urllib.parse.quote("(trending reels OR viral reel) (facts OR science OR space OR history) India when:3d")
        url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            content = resp.read()
            root = ET.fromstring(content)
            for item in root.findall(".//item")[:5]:
                title_el = item.find("title")
                title = normalize_text(title_el.text if title_el is not None else "")
                link_el = item.find("link")
                link = (link_el.text or "").strip() if link_el is not None else ""
                desc_el = item.find("description")
                summary = normalize_text(desc_el.text if desc_el is not None else "")
                
                if title:
                    cand = create_candidate(
                        title=title,
                        category="facts",
                        source="instagram_reels_search",
                        url=link,
                        summary=summary or title,
                        raw_metrics={"source_type": "web_reel_signals"}
                    )
                    candidates.append(cand)
    except Exception as e:
        pass

    print(f"[trend_research.instagram_trends] Fetched {len(candidates)} Instagram-relevant candidates.")
    return candidates
