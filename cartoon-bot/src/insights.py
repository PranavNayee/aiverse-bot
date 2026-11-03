import requests
import config as C
from util import log
from instagram import GRAPH

def performance_hints(history):
    """Looks at likes/comments of recent posts and tells the story writer what worked. Never raises."""
    try:
        scored = []
        for h in history[-20:]:
            mid = h.get("media_id")
            if not mid:
                continue
            r = requests.get(f"{GRAPH}/{mid}", params={"fields": "like_count,comments_count",
                             "access_token": C.IG_ACCESS_TOKEN()}, timeout=30)
            if r.status_code == 200:
                j = r.json()
                scored.append((j.get("like_count", 0) + 3 * j.get("comments_count", 0), h["topic"]))
        if len(scored) < 4:
            return ""
        scored.sort(reverse=True)
        best = "; ".join(t for _, t in scored[:3])
        worst = "; ".join(t for _, t in scored[-3:])
        return f"Past topics that got the most engagement: {best}. Least engagement: {worst}. Lean towards what worked."
    except Exception as e:
        log("Insights skipped:", e)
        return ""
