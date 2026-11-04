import requests, xml.etree.ElementTree as ET, re
import config as C, safety
from util import log, retry

HT = "{https://trends.google.com/trending/rss}"
UA = {"User-Agent": "Mozilla/5.0"}

@retry(tries=3, delay=4)
def _get(url):
    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    return r.content

def get_reddit_trends(limit=10):
    """Free: Hot topics from Reddit India (no API key needed)"""
    try:
        r = requests.get("https://www.reddit.com/r/india/hot.json?limit=25", headers=UA, timeout=15)
        if r.status_code == 200:
            posts = r.json().get("data", {}).get("children", [])
            titles = [p["data"]["title"] for p in posts if p.get("data", {}).get("title")]
            log(f"Reddit India: {len(titles)} topics found")
            return titles[:limit]
    except Exception as e:
        log("Reddit trends error:", e)
    return []

def get_youtube_trends(limit=10):
    """Free: Trending video topics from YouTube India (no API key)"""
    try:
        r = requests.get("https://www.youtube.com/feed/trending?gl=IN&hl=hi", headers=UA, timeout=15)
        if r.status_code == 200:
            # Extract video titles from JSON data in page
            titles = re.findall(r'"title":{"runs":\[{"text":"([^"]{10,100})"}\]', r.text)
            # Also try simpler pattern
            if not titles:
                titles = re.findall(r'"title":"([^"]{10,100})"', r.text)
            unique = list(dict.fromkeys(titles))[:limit]
            log(f"YouTube trends: {len(unique)} found")
            return unique
    except Exception as e:
        log("YouTube trends error:", e)
    return []

def get_twitter_trends(limit=10):
    """Free: Trending hashtags from Twitter/X (public page scraping)"""
    try:
        # Try Twitter trends via public API alternatives
        r = requests.get("https://getdaytrends.com/india/", headers=UA, timeout=15)
        if r.status_code == 200:
            # Extract trending hashtags
            trends = re.findall(r'<a[^>]*>([#\w\s]+)</a>', r.text)
            # Clean and filter
            clean = [t.strip() for t in trends if len(t.strip()) > 2 and not t.startswith("http")]
            unique = list(dict.fromkeys(clean))[:limit]
            log(f"Twitter trends: {len(unique)} found")
            return unique
    except Exception as e:
        log("Twitter trends error:", e)
    return []

def get_trends(limit=20):
    """Free: Multi-source trending topics for maximum viral potential.
    Sources: Google Trends, Reddit India, YouTube India, Twitter India, Google News.
    Unsafe topics are filtered out."""
    out = []
    
    # Source 1: Google Trends RSS (India)
    try:
        for item in ET.fromstring(_get(f"https://trends.google.com/trending/rss?geo={C.TRENDS_GEO}")).iter("item"):
            title = item.findtext("title")
            news = [n.findtext(f"{HT}news_item_title") for n in item.findall(f"{HT}news_item")][:2]
            if title:
                out.append(f"{title} — {' | '.join(n for n in news if n)}")
    except Exception as e:
        log("Trends RSS failed:", e)
    
    # Source 2: Reddit India hot topics (viral discussions)
    out.extend(get_reddit_trends(10))
    
    # Source 3: YouTube India trending (video trends)
    out.extend(get_youtube_trends(10))
    
    # Source 4: Twitter/X India trends (real-time buzz)
    out.extend(get_twitter_trends(10))
    
    # Source 5: Google News India (fallback if Google Trends failed)
    if len(out) < 5:
        try:
            out += [i.findtext("title") for i in ET.fromstring(
                _get("https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en")).iter("item")]
        except Exception as e:
            log("News RSS failed:", e)
    
    # Remove duplicates while preserving order
    unique = []
    seen = set()
    for item in out:
        if item and item.lower() not in seen:
            unique.append(item)
            seen.add(item.lower())
    
    # Filter unsafe topics
    safe = safety.filter_trends(unique)
    log(f"Multi-source trends: {len(unique)} found, {len(safe)} safe")
    return safe[:limit]
