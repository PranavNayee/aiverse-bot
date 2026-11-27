"""Google Trends RSS Fetcher for India (trends.google.com/trending/rss?geo=IN).
100% Free, no API key required.
"""
import email.utils
import html
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from .normalizer import create_candidate, normalize_text

URL = "https://trends.google.com/trending/rss?geo=IN"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 AIVerseTrendBot/1.0"

def _parse_traffic(traffic_str):
    if not traffic_str:
        return 0
    t = str(traffic_str).upper().replace(",", "").replace("+", "").strip()
    try:
        if "M" in t:
            return int(float(t.replace("M", "")) * 1_000_000)
        if "K" in t:
            return int(float(t.replace("K", "")) * 1_000)
        return int(t)
    except Exception:
        return 0

def fetch():
    candidates = []
    try:
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            content = resp.read()
    except Exception as e:
        print(f"[trend_research.google_trends] Warning: Google Trends RSS request failed: {e}")
        return candidates

    try:
        root = ET.fromstring(content)
    except Exception as e:
        print(f"[trend_research.google_trends] Warning: XML parsing failed: {e}")
        return candidates

    for item in root.findall(".//item"):
        title_el = item.find("title")
        title = normalize_text(title_el.text if title_el is not None else "")
        if not title:
            continue

        link_el = item.find("link")
        link = (link_el.text or "").strip() if link_el is not None else ""

        pub_el = item.find("pubDate")
        pub_date = None
        if pub_el is not None and pub_el.text:
            try:
                dt = email.utils.parsedate_to_datetime(pub_el.text)
                pub_date = dt.isoformat()
            except Exception:
                pub_date = None

        # Approx traffic
        traffic = 0
        for child in item:
            if child.tag.endswith("approx_traffic"):
                traffic = _parse_traffic(child.text)
                break

        # News item snippets attached to the trend
        evidence_parts = []
        for child in item:
            if child.tag.endswith("news_item"):
                ni_title = child.find("{*}news_item_title")
                ni_snip = child.find("{*}news_item_snippet")
                ni_url = child.find("{*}news_item_url")
                part = ""
                if ni_title is not None and ni_title.text:
                    part += normalize_text(ni_title.text) + ". "
                if ni_snip is not None and ni_snip.text:
                    part += normalize_text(ni_snip.text)
                if part:
                    evidence_parts.append(part)
                if not link and ni_url is not None and ni_url.text:
                    link = ni_url.text.strip()

        summary = " ".join(evidence_parts[:2]) if evidence_parts else title

        cand = create_candidate(
            title=title,
            category="general",
            source="google_trends",
            url=link,
            summary=summary,
            published_at=pub_date,
            raw_metrics={"traffic": traffic, "source_type": "search_trends"}
        )
        if evidence_parts:
            cand["evidence"] = evidence_parts
        candidates.append(cand)

    print(f"[trend_research.google_trends] Fetched {len(candidates)} Indian trending searches.")
    return candidates
