"""Generate Hinglish lesson scripts using AI"""
import json, re
from util import log
import config as C

# Prompt for generating educational lesson scripts in Hinglish
LESSON_PROMPT = """You write educational AI/ML lessons for Instagram Reels in HINGLISH (Hindi + English mix).
The channel teaches AI concepts to Indian audience - beginners to advanced.

LESSON DETAILS:
Title: {title}
Title (English): {title_en}
Concept: {concept}
Hook: {hook}
Analogy: {analogy}
Difficulty: {difficulty}
Keywords: {keywords}

TARGET AUDIENCE: Indian students, developers, tech enthusiasts who speak Hindi + English naturally

LANGUAGE RULES (CRITICAL):
1. Use HINGLISH - natural mix of Hindi and English
2. Technical terms in ENGLISH: AI, Machine Learning, Neural Network, Algorithm, Data, Model
3. Explanations in HINDI: kaise, kya, kyun, hota hai, kaam karta hai, seekhta hai
4. Examples: "Machine Learning ek technique hai jahan computer khud se seekhta hai data se"
5. Keep it conversational and simple - jaise dost ko samjha rahe ho

STRUCTURE (45-60 seconds total):
1. HOOK (3-5s): Question that grabs attention (from provided hook)
2. SETUP (8-12s): Introduce concept with everyday Indian analogy
3. EXPLANATION (20-30s): Break down the concept simply with 2-3 key points
4. EXAMPLE (8-12s): Real-world example they can relate to
5. TAKEAWAY (5-8s): One-line summary they'll remember
6. CTA (5s): "Next lesson mein..." + follow call

VISUAL INSTRUCTIONS:
- "visual_type": {visual_type}
- Describe what animation/diagram to show
- No faces, no characters - only diagrams, text, animations
- Clean, minimal, educational style

HINGLISH EXAMPLES:
✅ GOOD: "Neural Network ek aisa system hai jo human brain ki tarah kaam karta hai"
✅ GOOD: "Data collect karke pattern dhundho, phir prediction karo"
✅ GOOD: "Jaise aap roz chai peete ho aur dukaan wala yaad kar leta hai"
❌ BAD: "तंत्रिका नेटवर्क एक प्रणाली है" (too formal Hindi)
❌ BAD: "Neural network is a system" (too much English)

Return ONLY JSON:
{{
  "hook": "Hinglish hook question with emoji",
  "segments": [
    {{"type": "setup", "narration_hi": "Hinglish text", "duration": 10, "visual": "what to show"}},
    {{"type": "explanation", "narration_hi": "Hinglish explanation", "duration": 25, "visual": "diagram description"}},
    {{"type": "example", "narration_hi": "Hinglish example", "duration": 10, "visual": "example visual"}},
    {{"type": "takeaway", "narration_hi": "Hinglish one-liner", "duration": 6, "visual": "highlight box"}},
    {{"type": "cta", "narration_hi": "Hinglish CTA", "duration": 5, "visual": "next lesson teaser"}}
  ],
  "caption_summary": "2-3 line Hinglish summary",
  "key_terms": ["term1", "term2", "term3"]
}}"""

FUN_FACT_PROMPT = """You write entertaining AI fun facts for Instagram Reels in HINGLISH (Hindi + English mix).
These are weekend special episodes - light, fun, interesting AI trivia.

TOPIC: {topic}

STYLE: Casual, fun, surprising - make AI interesting!

LANGUAGE: Hinglish (Hindi + English naturally mixed)
- Keep it light and conversational
- Use emojis for energy
- Make it shareable

STRUCTURE (40-50 seconds):
1. HOOK (3s): Surprising fact or question
2. STORY (20-25s): Tell the interesting story/fact
3. DETAILS (10-15s): Add context or additional facts
4. CLOSING (5s): Funny or thought-provoking ending + CTA

EXAMPLES OF FUN FACTS:
- "Pehla AI program 1951 mein chess khelne ke liye bana tha!"
- "ChatGPT ko train karne mein $100 million se zyada lage!"
- "AI ab painting bhi bana sakta hai jo auction mein lakhs mein bikti hai!"

Return ONLY JSON:
{{
  "hook": "Surprising Hinglish hook",
  "segments": [
    {{"type": "story", "narration_hi": "Hinglish story", "duration": 22, "visual": "fun animation"}},
    {{"type": "details", "narration_hi": "Hinglish details", "duration": 12, "visual": "supporting visual"}},
    {{"type": "closing", "narration_hi": "Hinglish closing", "duration": 5, "visual": "end screen"}}
  ],
  "caption_summary": "Fun Hinglish summary",
  "shareability_factor": "Why this is interesting to share"
}}"""

def _clean_json(text):
    """Extract and parse JSON from AI response"""
    text = re.sub(r"^```(?:json)?", "", text.strip()).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)

def generate_lesson_script(lesson, lesson_num, use_groq=True):
    """Generate Hinglish lesson script using AI
    
    Args:
        lesson: Lesson dict from syllabus
        lesson_num: Lesson number
        use_groq: Use Groq API (faster)
    
    Returns:
        Parsed lesson script dict
    """
    
    prompt = LESSON_PROMPT.format(
        title=lesson["title"],
        title_en=lesson["title_en"],
        concept=lesson["concept"],
        hook=lesson["hook"],
        analogy=lesson["analogy"],
        difficulty=lesson["difficulty"],
        keywords=", ".join(lesson["keywords"]),
        visual_type=lesson["visual_type"]
    )
    
    log(f"Generating script for Lesson #{lesson_num}: {lesson['title']}")
    
    # Use existing AI generation (Groq → HF → Gemini fallback)
    from story import generate_story
    
    try:
        result = generate_story(prompt, temperature=0.8)
        log(f"Lesson script generated: {len(str(result))} chars")
        return result
    except Exception as e:
        log(f"Script generation error: {e}")
        # Fallback to simple template
        return {
            "hook": lesson["hook"],
            "segments": [
                {
                    "type": "setup",
                    "narration_hi": f"{lesson['title']} ke baare mein seekhte hain aaj.",
                    "duration": 8,
                    "visual": "title card"
                },
                {
                    "type": "explanation",
                    "narration_hi": f"{lesson['title_en']} ek important concept hai AI mein.",
                    "duration": 25,
                    "visual": "concept diagram"
                },
                {
                    "type": "takeaway",
                    "narration_hi": "Yaad rakho: practice se better hoga!",
                    "duration": 6,
                    "visual": "key point"
                },
                {
                    "type": "cta",
                    "narration_hi": "Next lesson mein aur seekhenge! Follow karo 🔔",
                    "duration": 5,
                    "visual": "follow button"
                }
            ],
            "caption_summary": lesson["title"],
            "key_terms": lesson["keywords"][:3]
        }

def generate_fun_fact_script(topic):
    """Generate weekend fun fact script in Hinglish"""
    
    prompt = FUN_FACT_PROMPT.format(topic=topic)
    
    log(f"Generating fun fact script: {topic}")
    
    from story import generate_story
    
    try:
        result = generate_story(prompt, temperature=1.0)
        log(f"Fun fact script generated")
        return result
    except Exception as e:
        log(f"Fun fact generation error: {e}")
        return {
            "hook": "AI ke baare mein interesting fact! 🤯",
            "segments": [
                {
                    "type": "story",
                    "narration_hi": f"{topic} ke baare mein ek interesting story hai.",
                    "duration": 22,
                    "visual": "animated story"
                },
                {
                    "type": "closing",
                    "narration_hi": "Aur bhi facts dekhne ke liye follow karo! 🔔",
                    "duration": 5,
                    "visual": "subscribe"
                }
            ],
            "caption_summary": f"AI Fun Fact: {topic}",
            "shareability_factor": "Interesting AI trivia"
        }

def validate_script(script):
    """Validate generated script has required fields"""
    required = ["hook", "segments", "caption_summary"]
    for field in required:
        if field not in script:
            raise ValueError(f"Missing required field: {field}")
    
    if not script["segments"] or len(script["segments"]) < 2:
        raise ValueError("Need at least 2 segments")
    
    # Check total duration
    total_duration = sum(seg.get("duration", 0) for seg in script["segments"])
    if not (35 <= total_duration <= 75):
        log(f"Warning: Total duration {total_duration}s outside 35-75s range")
    
    log(f"Script validated: {len(script['segments'])} segments, {total_duration}s total")
    return True

if __name__ == "__main__":
    # Test lesson script generation
    from syllabus import get_lesson_by_number
    
    lesson, level = get_lesson_by_number(2)
    if lesson:
        print(f"Testing: Lesson #{lesson['id']} - {lesson['title']}")
        print(f"Level: {level}")
        print(f"Concept: {lesson['concept']}")
        print("\nGenerating script...")
        
        # This would call AI in production
        print("(In production, AI would generate Hinglish script here)")
