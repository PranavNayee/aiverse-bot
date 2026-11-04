"""Intelligent hashtag generation for maximum discoverability (100% free)"""
import re, requests
from util import log

UA = {"User-Agent": "Mozilla/5.0 (compatible; CartoonBot/1.0)"}

# Base hashtags for the channel (always included)
BASE_TAGS = ["#hindicomedy", "#cartoon", "#animation", "#funny", "#reels", "#aicartoon"]

# Hindi content tags
HINDI_TAGS = ["#hindireels", "#hindijokes", "#hindifunny", "#hindicartoon", "#hindivideo"]

# Viral/trending tags (general)
VIRAL_TAGS = ["#viral", "#trending", "#viralreels", "#explorepage", "#foryou", "#fyp"]

# Family-friendly tags
FAMILY_TAGS = ["#familyfriendly", "#kidscomedy", "#cleancomedy", "#wholesome"]

def get_trending_hashtags():
    """Scrape trending Instagram hashtags (free, no API key)"""
    trending = []
    try:
        # Try scraping popular hashtag aggregators
        r = requests.get("https://top-hashtags.com/instagram/", headers=UA, timeout=10)
        if r.status_code == 200:
            # Extract hashtags from HTML
            tags = re.findall(r'#(\w+)', r.text)
            # Filter relevant ones
            relevant = [f"#{t}" for t in tags if len(t) > 3 and t.lower() not in ['instagram', 'follow', 'like']]
            trending.extend(relevant[:10])
            log(f"Trending hashtags: {len(trending)} found")
    except Exception as e:
        log(f"Trending hashtags error: {e}")
    
    return trending

def generate_topic_tags(topic):
    """Generate topic-specific hashtags based on story topic"""
    topic_lower = topic.lower()
    tags = []
    
    # Topic-specific mapping
    topic_map = {
        "cricket": ["#cricket", "#ipl", "#cricketlovers", "#cricketfans"],
        "food": ["#foodie", "#foodlover", "#indianfood", "#foodcomedy"],
        "tech": ["#technology", "#techie", "#gadgets", "#smartphone"],
        "movie": ["#bollywood", "#movies", "#film", "#entertainment"],
        "weather": ["#weather", "#monsoon", "#rain", "#summer"],
        "festival": ["#festival", "#celebration", "#indianfestival", "#diwali"],
        "school": ["#school", "#student", "#education", "#studentlife"],
        "office": ["#office", "#work", "#job", "#corporate"],
        "shopping": ["#shopping", "#online", "#ecommerce", "#flipkart"],
        "travel": ["#travel", "#vacation", "#trip", "#traveller"],
    }
    
    # Check which keywords appear in topic
    for keyword, hashtags in topic_map.items():
        if keyword in topic_lower:
            tags.extend(hashtags[:3])
            break
    
    return tags

def balance_by_size(all_tags):
    """Balance hashtags by size: 3 mega (1M+), 5 mid (100k-1M), 7 small (10k-100k)
    This is a heuristic - we don't have actual counts, so we use popularity estimation"""
    
    # Categorize by assumed popularity
    mega = []  # Very popular
    mid = []   # Medium popularity
    small = [] # Niche
    
    mega_keywords = ["viral", "trending", "funny", "comedy", "reels", "foryou", "explorepage"]
    mid_keywords = ["hindi", "cartoon", "animation", "bollywood", "india"]
    
    for tag in all_tags:
        tag_lower = tag.lower()
        if any(kw in tag_lower for kw in mega_keywords):
            mega.append(tag)
        elif any(kw in tag_lower for kw in mid_keywords):
            mid.append(tag)
        else:
            small.append(tag)
    
    # Balance: 3 mega, 5 mid, 7 small (or whatever we have)
    balanced = mega[:3] + mid[:5] + small[:7]
    return balanced

def smart_hashtags(topic, max_tags=15):
    """Generate intelligent, balanced hashtags for maximum discoverability
    
    Strategy:
    - Base channel tags (always included)
    - Trending tags (viral potential)
    - Topic-specific tags (targeted audience)
    - Hindi tags (language targeting)
    - Balanced by size (mega/mid/small for algorithm)
    """
    
    all_tags = []
    
    # 1. Base channel tags (identity)
    all_tags.extend(BASE_TAGS)
    
    # 2. Trending hashtags (discoverability)
    trending = get_trending_hashtags()
    all_tags.extend(trending[:5])
    
    # 3. Topic-specific tags (relevance)
    topic_tags = generate_topic_tags(topic)
    all_tags.extend(topic_tags)
    
    # 4. Hindi content tags (language targeting)
    all_tags.extend(HINDI_TAGS[:3])
    
    # 5. Viral tags (reach)
    all_tags.extend(VIRAL_TAGS[:3])
    
    # Remove duplicates (case-insensitive)
    seen = set()
    unique = []
    for tag in all_tags:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            unique.append(tag)
            seen.add(tag_lower)
    
    # Balance by size
    balanced = balance_by_size(unique)
    
    # Return max_tags hashtags
    final = balanced[:max_tags]
    log(f"Generated {len(final)} smart hashtags for topic: {topic[:30]}")
    
    return final

if __name__ == "__main__":
    # Test
    test_topic = "Cricket match comedy with Bablu"
    tags = smart_hashtags(test_topic)
    print(f"Smart hashtags for '{test_topic}':")
    print(" ".join(tags))
