"""Trending AI news for the 'AI News' reels (free RSS feeds, no API key).
Picks ONE fresh, consumer-relevant story; its headline + summary become the ONLY facts the script may use."""
import datetime as dt, email.utils, html, re, xml.etree.ElementTree as ET
import requests
import llm
from util import log

FEEDS = [
    "https://news.google.com/rss/search?q=%22AI%22+(launch+OR+launches+OR+new+feature+OR+rolls+out)+when:2d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=ChatGPT+OR+Gemini+OR+%22AI+tool%22+when:2d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
]
BLOCK = re.compile(r"\b(election|vote|bjp|congress|minister|government|war|army|military|attack|terror|bomb|murder|kill|"
                   r"dead|death|suicide|rape|assault|arrest|court|lawsuit|sued|jail|crash|religio|hindu|muslim|caste|"
                   r"pakistan|israel|gaza|ukraine|russia|porn|sex|stock|shares|ipo|crypto|layoff)\w*", re.I)
UA = {"User-Agent": "Mozilla/5.0 (AIVerse news reader)"}


def _text(x):
    x = html.unescape(re.sub(r"<[^>]+>", " ", x or ""))
    return re.sub(r"\s+", " ", x).strip()


def fetch(max_age_hours=60):
    items, seen = [], set()
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=max_age_hours)
    for url in FEEDS:
        try:
            r = requests.get(url, headers=UA, timeout=20)
            root = ET.fromstring(r.content)
        except Exception as e:
            log("News feed failed:", url[:60], e); continue
        for it in root.iter():
            tag = it.tag.split("}")[-1]
            if tag not in ("item", "entry"):
                continue
            def get(*names):                     # NB: childless XML elements are falsy, so never use `a or b`
                for name in names:
                    for c in it:
                        if c.tag.split("}")[-1] == name:
                            return c
                return None
            title = _text((get("title").text if get("title") is not None else ""))
            link_el = get("link")
            link = (link_el.get("href") if link_el is not None and link_el.get("href") else
                    (link_el.text if link_el is not None else "")) or ""
            summ_el = get("description", "summary", "content")
            summary = _text(summ_el.text if summ_el is not None else "")[:600]
            date_el = get("pubDate", "published", "updated")
            try:
                d = email.utils.parsedate_to_datetime(date_el.text) if date_el is not None else None
            except (TypeError, ValueError):
                try:
                    d = dt.datetime.fromisoformat(date_el.text.replace("Z", "+00:00"))
                except Exception:
                    d = None
            if not title or (d and d < cutoff) or BLOCK.search(title + " " + summary):
                continue
            k = re.sub(r"\W+", "", title.lower())[:60]
            if k in seen:
                continue
            seen.add(k)
            items.append({"title": title, "summary": summary, "link": link.strip(),
                          "date": d.strftime("%d %b %Y") if d else ""})
    log(f"News: {len(items)} candidate stories")
    return items


PICK_PROMPT = """You choose ONE AI news story for a short Instagram/YouTube reel for Indian students and young professionals.
Pick the story that is most useful, surprising and easy to understand for a normal phone user (new feature they can try,
a big launch, a useful tool). Avoid business/finance, lawsuits, politics, safety scares and anything vague.
Only choose a story whose SUMMARY contains enough concrete facts for a 25-second reel. If none qualifies, choose -1.

STORIES:
{stories}

Return ONLY JSON: {{"index": <number or -1>, "title_hinglish": "short catchy Hinglish title, max 8 words",
"facts": "the 2-4 key facts, copied faithfully from that story's headline/summary only", "why": "one line"}}"""


def pick(used_links=(), used_titles=()):
    items = [i for i in fetch() if i["link"] not in used_links and i["title"] not in used_titles]
    rich = lambda i: len(set(re.findall(r"\w+", i["summary"].lower())) - set(re.findall(r"\w+", i["title"].lower())))
    items = sorted(items, key=rich, reverse=True)[:18]          # stories whose summary adds real facts first
    if not items:
        return None
    listing = "\n".join(f"{n}. [{i['date']}] {i['title']} -- {i['summary'][:300]}" for n, i in enumerate(items))
    try:
        res = llm.generate_json(PICK_PROMPT.format(stories=listing), temperature=0.2)
        n = int(res.get("index", -1))
    except Exception as e:
        log("News pick failed:", e); return None
    if not 0 <= n < len(items) or not str(res.get("facts", "")).strip():
        log("No suitable news story today")
        return None
    it = items[n]
    facts = f"{it['title']} ({it['date']}). {res['facts']}"
    log(f"📰 News pick: {it['title']}  ({res.get('why', '')})")
    return {"title": str(res.get("title_hinglish") or it["title"])[:80], "title_en": it["title"][:120],
            "facts": facts[:900], "link": it["link"], "keywords": ["AI news", "new feature"]}
