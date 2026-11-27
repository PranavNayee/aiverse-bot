"""Multi-niche Google News RSS and Science RSS aggregator for Indian audience.
Covers: Space, Science, Human Body, Animals, India History, Tech, Psychology.
100% Free, no API keys required.
"""
import email.utils
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from .normalizer import create_candidate, normalize_text

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 AIVerseTrendBot/1.0"

FEEDS = [
    # Space & ISRO
    ("space", "https://news.google.com/rss/search?q=(space+OR+ISRO+OR+NASA+OR+astronomy+OR+galaxy+OR+solar+system)+when:3d&hl=en-IN&gl=IN&ceid=IN:en"),
    # Human Body & Neuroscience
    ("body", "https://news.google.com/rss/search?q=(human+body+OR+brain+discovery+OR+biology+OR+genetics)+when:3d&hl=en-IN&gl=IN&ceid=IN:en"),
    # Animals & Wildlife
    ("animals", "https://news.google.com/rss/search?q=(animal+discovery+OR+wildlife+species+OR+surprising+creature)+when:3d&hl=en-IN&gl=IN&ceid=IN:en"),
    # Science & Breakthroughs
    ("science", "https://news.google.com/rss/search?q=(scientific+discovery+OR+physics+breakthrough+OR+chemistry+discovery)+when:3d&hl=en-IN&gl=IN&ceid=IN:en"),
    # India & History Secrets
    ("india", "https://news.google.com/rss/search?q=(India+history+OR+ancient+temple+discovery+OR+Indian+monument+secret+OR+archaeology+India)+when:7d&hl=en-IN&gl=IN&ceid=IN:en"),
    # Future Tech & Discoveries
    ("tech", "https://news.google.com/rss/search?q=(future+technology+OR+robotics+OR+quantum+computing+OR+AI+breakthrough)+when:3d&hl=en-IN&gl=IN&ceid=IN:en"),
    # Psychology & Mind Facts
    ("psychology", "https://news.google.com/rss/search?q=(psychology+study+OR+human+behavior+experiment+OR+why+people)+when:3d&hl=en-IN&gl=IN&ceid=IN:en"),
    # ScienceDaily Space & Top
    ("space", "https://www.sciencedaily.com/rss/space_time.xml"),
    ("science", "https://www.sciencedaily.com/rss/top/science.xml"),
]

def fetch(max_per_feed=8):
    candidates = []
    ctx = ssl._create_unverified_context()

    for category, url in FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
                content = resp.read()
            root = ET.fromstring(content)
        except Exception as e:
            # Continue gracefully on any network/feed failure
            continue

        feed_count = 0
        for item in root.findall(".//item"):
            if feed_count >= max_per_feed:
                break

            title_el = item.find("title")
            title = normalize_text(title_el.text if title_el is not None else "")
            if not title or len(title) < 12:
                continue

            link_el = item.find("link")
            link = (link_el.text or "").strip() if link_el is not None else ""

            desc_el = item.find("description")
            summary = normalize_text(desc_el.text if desc_el is not None else "")

            pub_el = item.find("pubDate")
            pub_date = None
            if pub_el is not None and pub_el.text:
                try:
                    dt = email.utils.parsedate_to_datetime(pub_el.text)
                    pub_date = dt.isoformat()
                except Exception:
                    pub_date = None

            cand = create_candidate(
                title=title,
                category=category,
                source="rss_news",
                url=link,
                summary=summary or title,
                published_at=pub_date,
                raw_metrics={"source_type": "rss_news", "feed_category": category}
            )
            candidates.append(cand)
            feed_count += 1

    print(f"[trend_research.rss_trends] Fetched {len(candidates)} stories across 8 curiosity niches.")
    return candidates
