import requests, xml.etree.ElementTree as ET
import config as C, safety
from util import log, retry

HT = "{https://trends.google.com/trending/rss}"
UA = {"User-Agent": "Mozilla/5.0"}

@retry(tries=3, delay=4)
def _get(url):
    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    return r.content

def get_trends(limit=20):
    """Free: Google Trends RSS (India), falls back to Google News India. Unsafe topics are removed."""
    out = []
    try:
        for item in ET.fromstring(_get(f"https://trends.google.com/trending/rss?geo={C.TRENDS_GEO}")).iter("item"):
            title = item.findtext("title")
            news = [n.findtext(f"{HT}news_item_title") for n in item.findall(f"{HT}news_item")][:2]
            if title:
                out.append(f"{title} — {' | '.join(n for n in news if n)}")
    except Exception as e:
        log("Trends RSS failed:", e)
    if len(out) < 5:
        try:
            out += [i.findtext("title") for i in ET.fromstring(
                _get("https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en")).iter("item")]
        except Exception as e:
            log("News RSS failed:", e)
    safe = safety.filter_trends([o for o in out if o])
    log(f"Trends: {len(out)} found, {len(safe)} safe")
    return safe[:limit]
