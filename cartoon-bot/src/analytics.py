"""Analytics and performance tracking using Instagram Graph API (100% free)"""
import requests, time
from util import log
import config as C

GRAPH_API = "https://graph.facebook.com/v21.0"

def get_media_insights(media_id):
    """Fetch insights for a specific Instagram media (reel)
    
    Free metrics available:
    - impressions, reach, saved, video_views
    - likes, comments, shares (from media endpoint)
    
    Returns dict with metrics or None if failed
    """
    try:
        # Get basic metrics from media endpoint
        media_url = f"{GRAPH_API}/{media_id}"
        media_params = {
            "fields": "like_count,comments_count,timestamp,media_type,media_url,permalink",
            "access_token": C.IG_ACCESS_TOKEN()
        }
        
        r = requests.get(media_url, params=media_params, timeout=30)
        if r.status_code != 200:
            log(f"Media insights error: {r.status_code} {r.text[:200]}")
            return None
        
        media_data = r.json()
        
        # Get insights (impressions, reach, etc.)
        insights_url = f"{GRAPH_API}/{media_id}/insights"
        insights_params = {
            "metric": "impressions,reach,saved,video_views,plays,total_interactions",
            "access_token": C.IG_ACCESS_TOKEN()
        }
        
        insights_r = requests.get(insights_url, params=insights_params, timeout=30)
        insights_data = {}
        
        if insights_r.status_code == 200:
            insights_json = insights_r.json()
            for item in insights_json.get("data", []):
                insights_data[item["name"]] = item.get("values", [{}])[0].get("value", 0)
        else:
            log(f"Insights API warning: {insights_r.status_code} (may be too early for insights)")
        
        # Combine data
        metrics = {
            "media_id": media_id,
            "likes": media_data.get("like_count", 0),
            "comments": media_data.get("comments_count", 0),
            "impressions": insights_data.get("impressions", 0),
            "reach": insights_data.get("reach", 0),
            "saved": insights_data.get("saved", 0),
            "video_views": insights_data.get("video_views", 0),
            "plays": insights_data.get("plays", 0),
            "total_interactions": insights_data.get("total_interactions", 0),
            "timestamp": media_data.get("timestamp", ""),
            "permalink": media_data.get("permalink", ""),
        }
        
        # Calculate engagement rate
        if metrics["reach"] > 0:
            engagement = (metrics["likes"] + metrics["comments"] + metrics["saved"]) / metrics["reach"] * 100
            metrics["engagement_rate"] = round(engagement, 2)
        else:
            metrics["engagement_rate"] = 0.0
        
        log(f"Media {media_id}: {metrics['likes']} likes, {metrics['video_views']} views, {metrics['engagement_rate']}% engagement")
        return metrics
        
    except Exception as e:
        log(f"Analytics error for {media_id}: {e}")
        return None

def get_account_insights(days=7):
    """Get account-level insights (follower count, impressions, reach)
    
    Note: Requires additional permissions. Basic implementation.
    """
    try:
        url = f"{GRAPH_API}/{C.IG_USER_ID()}/insights"
        params = {
            "metric": "impressions,reach,profile_views,follower_count",
            "period": "day",
            "access_token": C.IG_ACCESS_TOKEN()
        }
        
        r = requests.get(url, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            log(f"Account insights: {len(data.get('data', []))} metrics retrieved")
            return data.get("data", [])
        else:
            log(f"Account insights error: {r.status_code}")
            return None
    except Exception as e:
        log(f"Account insights error: {e}")
        return None

def analyze_performance(history):
    """Analyze performance trends from history
    
    Identifies:
    - Best performing topics
    - Best posting times
    - Engagement trends
    
    Args:
        history: List of historical posts with media_ids
    
    Returns:
        Dict with performance insights
    """
    
    if not history or len(history) < 3:
        log("Not enough history for analysis (need 3+ posts)")
        return {
            "top_topics": [],
            "avg_engagement": 0.0,
            "best_hour": 8,
            "trending_up": True,
        }
    
    # Fetch metrics for recent posts (last 10)
    recent = history[-10:]
    metrics_list = []
    
    for post in recent:
        media_id = post.get("media_id")
        if media_id:
            # Wait a bit between requests to avoid rate limits
            time.sleep(1)
            metrics = get_media_insights(media_id)
            if metrics:
                metrics["topic"] = post.get("topic", "unknown")
                metrics["date"] = post.get("date", "")
                metrics_list.append(metrics)
    
    if not metrics_list:
        log("No metrics retrieved for analysis")
        return {
            "top_topics": [],
            "avg_engagement": 0.0,
            "best_hour": 8,
            "trending_up": True,
        }
    
    # Calculate average engagement
    avg_engagement = sum(m["engagement_rate"] for m in metrics_list) / len(metrics_list)
    
    # Find top performing topics (by engagement rate)
    topic_performance = {}
    for m in metrics_list:
        topic = m["topic"]
        if topic not in topic_performance:
            topic_performance[topic] = []
        topic_performance[topic].append(m["engagement_rate"])
    
    # Average engagement per topic
    topic_avg = {t: sum(rates)/len(rates) for t, rates in topic_performance.items()}
    top_topics = sorted(topic_avg.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # Detect trend (last 3 vs previous 3)
    if len(metrics_list) >= 6:
        recent_3 = sum(m["engagement_rate"] for m in metrics_list[-3:]) / 3
        previous_3 = sum(m["engagement_rate"] for m in metrics_list[-6:-3]) / 3
        trending_up = recent_3 > previous_3
    else:
        trending_up = True
    
    analysis = {
        "total_posts_analyzed": len(metrics_list),
        "avg_engagement": round(avg_engagement, 2),
        "top_topics": [{"topic": t, "engagement": round(e, 2)} for t, e in top_topics],
        "trending_up": trending_up,
        "best_hour": 8,  # Default (would need more data to determine)
        "recent_metrics": metrics_list[-3:],  # Last 3 posts
    }
    
    log(f"Performance analysis: {avg_engagement:.2f}% avg engagement, trending {'up' if trending_up else 'down'}")
    log(f"Top topics: {', '.join(t for t, _ in top_topics[:3])}")
    
    return analysis

def performance_summary(history):
    """Generate a human-readable performance summary for logging"""
    analysis = analyze_performance(history)
    
    summary = f"""
📊 PERFORMANCE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Posts analyzed: {analysis['total_posts_analyzed']}
Avg engagement: {analysis['avg_engagement']}%
Trend: {'📈 Growing' if analysis['trending_up'] else '📉 Declining'}

🏆 Top Performing Topics:
"""
    for item in analysis['top_topics']:
        summary += f"   • {item['topic']}: {item['engagement']}%\n"
    
    if analysis.get('recent_metrics'):
        summary += "\n📺 Recent Posts:\n"
        for m in analysis['recent_metrics']:
            summary += f"   • {m.get('topic', 'Unknown')[:30]}: {m['likes']} ❤️  {m['video_views']} 👁️  {m['engagement_rate']}% 📊\n"
    
    summary += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    return summary

if __name__ == "__main__":
    # Test with a sample media ID (replace with real one)
    print("Analytics Module - Test Mode")
    print("To test, set a valid media_id and run:")
    print("  metrics = get_media_insights('YOUR_MEDIA_ID')")
    print("  print(metrics)")
