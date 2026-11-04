"""Optimized caption generation for engagement and SEO (100% free)"""
import random
from util import log

# Emoji sets for different moods
EMOJI_COMEDY = ["😂", "🤣", "😆", "😁", "🤪", "😜"]
EMOJI_SHOCK = ["😱", "🤯", "😲", "🙀", "😳"]
EMOJI_FIRE = ["🔥", "💯", "⚡", "✨", "💥"]
EMOJI_HEART = ["❤️", "😍", "🥰", "💕", "💖"]
EMOJI_THINK = ["🤔", "🧐", "💭", "🤨"]

# Call-to-action templates (Hindi)
CTA_TEMPLATES = [
    "आपका क्या ख्याल है? Comment में बताएं! 👇",
    "क्या यह सही है? अपनी राय दें! 💬",
    "आपके साथ भी हुआ है? Comment करें! 👇",
    "सहमत हैं? Like करें! ❤️",
    "क्या आपको पसंद आया? बताएं! 👇",
    "आपके विचार? नीचे बताएं! 💭",
]

# Follow CTAs
FOLLOW_CTA = [
    "रोज़ नया एपिसोड - Follow करें! 🔔",
    "Daily नई कहानी - Follow करना मत भूलें! ⭐",
    "हर दिन धमाल - Follow करो! 🎬",
    "रोज़ मज़ा - अभी Follow करें! 🚀",
    "नए एपिसोड के लिए Follow करें! ❤️",
]

# Hook enhancement emojis
HOOK_EMOJIS = {
    "curiosity": ["🤔", "💭", "🧐"],
    "shock": ["🤯", "😱", "💥"],
    "question": ["❓", "🤷", "🧐"],
    "comedy": ["😂", "🤣", "😆"],
    "relatable": ["💯", "✅", "👍"],
}

def detect_mood(story_text):
    """Detect story mood from text (simple keyword matching)"""
    text_lower = story_text.lower()
    
    if any(word in text_lower for word in ["हंसी", "मज़ाक", "funny", "comedy", "हा हा"]):
        return "comedy"
    elif any(word in text_lower for word in ["चौंक", "shock", "surprise", "अचानक"]):
        return "shock"
    elif any(word in text_lower for word in ["सवाल", "क्यों", "कैसे", "question"]):
        return "question"
    elif any(word in text_lower for word in ["सच", "real", "relatable", "होता है"]):
        return "relatable"
    else:
        return "curiosity"

def enhance_hook(hook, mood="comedy"):
    """Add mood-appropriate emoji to hook"""
    if not hook or not isinstance(hook, str):
        return "देखो क्या होता है! 🔥"
    
    # Get appropriate emoji for mood
    emoji = random.choice(HOOK_EMOJIS.get(mood, ["🔥"]))
    
    # Add emoji if not already present
    if not any(e in hook for e in ["😂", "🤣", "🔥", "💯", "😱", "🤯", "❓", "💭", "🤔"]):
        hook = f"{hook.strip()} {emoji}"
    
    return hook

def generate_optimized_caption(story, hook="", episode=1):
    """Generate SEO and engagement-optimized caption
    
    Format:
    1. Hook (with emoji) - grabs attention
    2. Mini summary (2-3 lines) - context
    3. Engagement CTA - drives comments
    4. Follow CTA - drives follows
    5. Episode info
    
    Args:
        story: Story dict with 'topic', 'caption', 'title'
        hook: Story hook text
        episode: Episode number
    
    Returns:
        Optimized caption string
    """
    
    # Get story details
    topic = story.get("topic", "मज़ेदार कहानी")
    ai_caption = story.get("caption", "")
    title = story.get("title", "")
    
    # Detect mood from story
    full_text = f"{topic} {title} {ai_caption}"
    mood = detect_mood(full_text)
    
    # 1. Enhanced hook
    enhanced_hook = enhance_hook(hook, mood)
    
    # 2. Use AI caption or create mini summary
    if ai_caption and len(ai_caption.strip()) > 10:
        summary = ai_caption.strip()
    else:
        summary = f"{topic} पर Bablu का मज़ेदार अनुभव!"
    
    # Add mood emoji to summary if not present
    mood_emoji = random.choice(EMOJI_COMEDY if mood == "comedy" else 
                               EMOJI_SHOCK if mood == "shock" else EMOJI_FIRE)
    if not any(e in summary for e in ["😂", "🤣", "🔥", "💯", "😱", "🤯"]):
        summary = f"{summary} {mood_emoji}"
    
    # 3. Engagement CTA (random for variety)
    engagement_cta = random.choice(CTA_TEMPLATES)
    
    # 4. Follow CTA (random for variety)
    follow_cta = random.choice(FOLLOW_CTA)
    
    # 5. Episode badge
    episode_badge = f"📺 Episode {episode}"
    
    # Assemble caption
    caption_parts = [
        enhanced_hook,
        "",  # Blank line
        summary,
        "",  # Blank line
        engagement_cta,
        "",  # Blank line
        follow_cta,
        "",  # Blank line
        episode_badge,
    ]
    
    caption = "\n".join(caption_parts)
    
    log(f"Generated optimized caption ({len(caption)} chars)")
    return caption

def add_hashtags_to_caption(caption, hashtags):
    """Add hashtags at the end of caption (after double newline for separation)"""
    if not hashtags:
        return caption
    
    # Join hashtags
    hashtag_line = " ".join(hashtags)
    
    # Add to caption with spacing
    full_caption = f"{caption}\n\n{hashtag_line}"
    
    return full_caption

if __name__ == "__main__":
    # Test
    test_story = {
        "topic": "Cricket match में Bablu की shaadi",
        "caption": "Bablu ने cricket match में apni girlfriend को surprise दिया!",
        "title": "Cricket Stadium Romance"
    }
    
    caption = generate_optimized_caption(test_story, "यह तो चौंकाने वाला है!", episode=42)
    print("Generated Caption:")
    print("-" * 50)
    print(caption)
    print("-" * 50)
    
    # Add hashtags
    test_tags = ["#hindicomedy", "#viral", "#cricket", "#funny"]
    full = add_hashtags_to_caption(caption, test_tags)
    print("\nWith Hashtags:")
    print("-" * 50)
    print(full)
