"""Data normalization and standard structure for Trend candidates."""
import hashlib
import re
import datetime as dt

def normalize_text(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(text))
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def topic_key(title):
    t = normalize_text(title).lower()
    t = re.sub(r"[^\w\s]", "", t)
    words = sorted(set(w for w in t.split() if len(w) > 3))
    return "-".join(words[:5]) if words else t[:32]

def generate_topic_id(title):
    k = topic_key(title)
    return hashlib.sha256(k.encode("utf-8")).hexdigest()[:16]

def create_candidate(title, category="general", source="unknown", url="",
                     summary="", published_at=None, raw_metrics=None):
    clean_title = normalize_text(title)
    clean_summary = normalize_text(summary)
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    
    return {
        "topic_id": generate_topic_id(clean_title),
        "title": clean_title,
        "normalized_title": topic_key(clean_title),
        "category": category.lower(),
        "sources": [source] if source else [],
        "source_urls": [url] if url else [],
        "summary": clean_summary,
        "evidence": [clean_summary] if clean_summary else [],
        "published_at": published_at or now_iso,
        "fetched_at": now_iso,
        "raw_metrics": raw_metrics or {},
        "score": 0.0,
        "score_breakdown": {},
        "status": "candidate"
    }

def merge_candidates(existing, new_item):
    """Combines evidence and sources if same topic is discovered across multiple providers."""
    for s in new_item.get("sources", []):
        if s not in existing["sources"]:
            existing["sources"].append(s)
            
    for u in new_item.get("source_urls", []):
        if u and u not in existing["source_urls"]:
            existing["source_urls"].append(u)
            
    for ev in new_item.get("evidence", []):
        if ev and ev not in existing["evidence"]:
            existing["evidence"].append(ev)
            
    # Merge metrics
    if new_item.get("raw_metrics"):
        existing["raw_metrics"].update(new_item["raw_metrics"])
        
    return existing
