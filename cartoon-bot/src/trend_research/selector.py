"""Automatic Trend Topic Selector.
Pipeline:
1. Fetch from all sources (Google Trends, RSS, Instagram, YouTube).
2. Filter through safety and niche filter.
3. Calculate 0-100 scores.
4. Filter out recently posted topics from history.json.
5. Fact-check top candidates.
6. Select winner + 3 verified backups.
"""
import re
from .fetcher import fetch_all
from .niche_filter import is_safe_and_relevant
from .scorer import score_candidate
from .fact_checker import verify_topic

def _clean_word_set(title):
    words = re.findall(r"\w+", (title or "").lower())
    return set(w for w in words if len(w) > 3)

def select_best_trend(history=None, top_k_to_verify=5):
    """
    Returns (winner_candidate: dict or None, backups: list)
    """
    history = history or []
    used_topics = set()
    used_words = set()
    for h in history:
        t = h.get("topic") or h.get("lesson", {}).get("title") or ""
        if t:
            used_topics.add(t.lower())
            used_words.update(_clean_word_set(t))

    print("[trend_research.selector] 1. Fetching candidates from all providers...")
    candidates = fetch_all()
    if not candidates:
        print("[trend_research.selector] No candidates found from feeds.")
        return None, []

    print("[trend_research.selector] 2. Applying safety and niche filters...")
    filtered = []
    for c in candidates:
        safe, reason, cat = is_safe_and_relevant(c)
        if safe:
            c["category"] = cat
            filtered.append(c)

    print(f"[trend_research.selector] {len(filtered)} / {len(candidates)} candidates passed niche filters.")
    if not filtered:
        return None, []

    print("[trend_research.selector] 3. Scoring candidates (0-100)...")
    scored = [score_candidate(c) for c in filtered]

    # Filter out recent topics from history
    fresh = []
    for c in scored:
        title_lower = c["title"].lower()
        if title_lower in used_topics:
            continue
        c_words = _clean_word_set(title_lower)
        # Avoid heavy word overlap with recent reels
        if c_words and len(c_words.intersection(used_words)) >= 3:
            continue
        fresh.append(c)

    fresh.sort(key=lambda x: x["score"], reverse=True)
    print(f"[trend_research.selector] 4. Sorted {len(fresh)} fresh candidates by score. Top score: {fresh[0]['score'] if fresh else 0}")

    # Fact-check candidates in order of score
    print("[trend_research.selector] 5. Running mandatory fact verification...")
    winner = None
    backups = []

    for c in fresh[:top_k_to_verify]:
        passed, vdata = verify_topic(c)
        if passed:
            c["status"] = "verified"
            c["verified_facts"] = vdata["verified_facts"]
            c["analogy"] = vdata.get("analogy", "")
            c["title_hinglish"] = vdata.get("title_hinglish", c["title"])
            if not winner:
                winner = c
                c["status"] = "selected"
                print(f"[trend_research.selector] ✅ WINNER SELECTED: {c['title']} (Score: {c['score']})")
                print(f"   Reason: {vdata.get('reason')}")
            else:
                backups.append(c)
                if len(backups) >= 3:
                    break
        else:
            c["status"] = "rejected_fact_check"
            print(f"[trend_research.selector] ❌ Rejected: {c['title']} ({vdata.get('reason')})")

    return winner, backups
