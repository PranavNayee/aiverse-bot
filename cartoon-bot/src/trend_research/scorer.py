"""Trend Scoring Engine.
Calculates a 0-100 score based on 6 weighted signals:
1. Search popularity and momentum (Weight: 25)
2. Recency and momentum (Weight: 20)
3. Cross-source popularity (Weight: 20)
4. Niche relevance (Weight: 20)
5. Curiosity & short-video potential (Weight: 10)
6. Competition opportunity (Weight: 5)
"""
import datetime as dt
import re

CURIOSITY_HOOK_WORDS = [
    "why", "how", "secret", "never", "surprising", "mystery", "reason", "first time",
    "hidden", "dangerous", "real", "truth", "discover", "bizarre", "weird", "shocking"
]

def _score_search_popularity(candidate):
    """Signal 1: Search popularity and momentum (0-25)"""
    metrics = candidate.get("raw_metrics", {})
    traffic = metrics.get("traffic", 0)
    views = metrics.get("views", 0)
    likes = metrics.get("likes", 0)

    if traffic >= 500_000 or views >= 500_000:
        return 25.0
    if traffic >= 200_000 or views >= 200_000:
        return 22.0
    if traffic >= 100_000 or views >= 100_000 or likes >= 50_000:
        return 19.0
    if traffic >= 50_000 or views >= 50_000 or likes >= 10_000:
        return 16.0
    if traffic >= 20_000 or views >= 10_000 or likes >= 2_000:
        return 13.0
    if "google_trends" in candidate.get("sources", []):
        return 12.0
    return 10.0  # Neutral baseline

def _score_recency(candidate):
    """Signal 2: Recency and freshness (0-20)"""
    pub_at = candidate.get("published_at")
    if not pub_at:
        return 14.0  # Neutral

    try:
        if isinstance(pub_at, str):
            # Parse ISO or standard formats
            clean_str = pub_at.replace("Z", "+00:00")
            pub_dt = dt.datetime.fromisoformat(clean_str)
        else:
            pub_dt = pub_at
        now = dt.datetime.now(dt.timezone.utc)
        if pub_dt.tzinfo is None:
            pub_dt = pub_dt.replace(tzinfo=dt.timezone.utc)
        age_hours = (now - pub_dt).total_seconds() / 3600.0

        if age_hours <= 6:
            return 20.0
        if age_hours <= 18:
            return 18.0
        if age_hours <= 36:
            return 15.0
        if age_hours <= 72:
            return 11.0
        return 7.0
    except Exception:
        return 12.0

def _score_cross_source(candidate):
    """Signal 3: Cross-source appearance (0-20)"""
    sources = set(candidate.get("sources", []))
    n = len(sources)
    if n >= 3:
        return 20.0
    if n == 2:
        return 16.0
    # Boost if evidence contains multiple distinct URLs
    urls = set(candidate.get("source_urls", []))
    if len(urls) >= 2:
        return 14.0
    return 10.0

def _score_niche_relevance(candidate):
    """Signal 4: High-curiosity niche fit (0-20)"""
    cat = candidate.get("category", "").lower()
    # High-retention visual categories for 2D animation
    high_retention = {"space": 20.0, "body": 20.0, "animals": 19.0, "india": 19.0, "science": 18.0, "tech": 17.0}
    return high_retention.get(cat, 15.0)

def _score_curiosity(candidate):
    """Signal 5: Curiosity and short-video potential (0-10)"""
    text = (candidate.get("title", "") + " " + candidate.get("summary", "")).lower()
    score = 4.0  # baseline
    for w in CURIOSITY_HOOK_WORDS:
        if re.search(r"\b" + re.escape(w) + r"\b", text):
            score += 1.5
    if "?" in candidate.get("title", ""):
        score += 1.5
    return min(10.0, score)

def _score_competition_opportunity(candidate):
    """Signal 6: Under-explored, highly educational opportunity (0-5)"""
    title_len = len(candidate.get("title", ""))
    # Concise, punchy titles perform better than bloated text
    if 25 <= title_len <= 85:
        return 5.0
    return 3.0

def score_candidate(candidate):
    s_pop = _score_search_popularity(candidate)
    s_rec = _score_recency(candidate)
    s_src = _score_cross_source(candidate)
    s_niche = _score_niche_relevance(candidate)
    s_cur = _score_curiosity(candidate)
    s_comp = _score_competition_opportunity(candidate)

    total = round(s_pop + s_rec + s_src + s_niche + s_cur + s_comp, 1)
    total = max(0.0, min(100.0, total))

    breakdown = {
        "search_popularity": s_pop,
        "recency": s_rec,
        "cross_source": s_src,
        "niche_relevance": s_niche,
        "curiosity_potential": s_cur,
        "competition_opportunity": s_comp,
        "total": total
    }

    candidate["score"] = total
    candidate["score_breakdown"] = breakdown
    return candidate
