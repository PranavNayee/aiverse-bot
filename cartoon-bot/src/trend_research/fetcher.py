"""Multi-source trend fetcher orchestrator.
Queries:
1. Google Trends RSS (India)
2. Multi-niche Google News RSS (Space, Body, Animals, Science, India, Tech, Psychology)
3. Instagram trend signals (Official Meta Graph API + Web signals)
4. YouTube India Trending (when key is available)
Deduplicates and merges candidates.
"""
from . import google_trends
from . import rss_trends
from . import instagram_trends
from . import youtube_trends
from .normalizer import merge_candidates

def fetch_all():
    raw_list = []

    # 1. Google Trends (India)
    try:
        gt_items = google_trends.fetch()
        raw_list.extend(gt_items)
    except Exception as e:
        print(f"[trend_research.fetcher] Google Trends error: {e}")

    # 2. Multi-niche RSS
    try:
        rss_items = rss_trends.fetch()
        raw_list.extend(rss_items)
    except Exception as e:
        print(f"[trend_research.fetcher] RSS trends error: {e}")

    # 3. Instagram Signals (Official Graph API + Web)
    try:
        ig_items = instagram_trends.fetch()
        raw_list.extend(ig_items)
    except Exception as e:
        print(f"[trend_research.fetcher] Instagram trends error: {e}")

    # 4. YouTube Trending (Optional)
    try:
        yt_items = youtube_trends.fetch()
        raw_list.extend(yt_items)
    except Exception as e:
        print(f"[trend_research.fetcher] YouTube trends error: {e}")

    # Deduplicate and merge candidates
    merged = {}
    for item in raw_list:
        tid = item["topic_id"]
        if tid in merged:
            merged[tid] = merge_candidates(merged[tid], item)
        else:
            merged[tid] = item

    all_candidates = list(merged.values())
    print(f"[trend_research.fetcher] Total normalized candidates: {len(all_candidates)}")
    return all_candidates
