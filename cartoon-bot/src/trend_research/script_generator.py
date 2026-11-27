"""Hinglish Viral Script Generator for Trending Curiosity Reels.
Produces 20-30 second structured scene JSON strictly compatible with edu_render & motion_render.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import llm
import lesson_script

TREND_SCRIPT_PROMPT = """You write a viral 25-30 second animated "Did You Know?" Instagram Reel / YouTube Short in Hinglish for Indian youth, for the channel "@aiverse.agent".

TOPIC: {title}
CATEGORY: {category}
CONFIRMED CORE FACTS (The ONLY facts you may state as true):
{facts}

EVERYDAY ANALOGY / HOOK ANGLE:
{analogy}

AUDIENCE & TONE:
- Indian youth & students.
- Conversational Roman Hinglish (e.g., "Kkya aapko pata hai?", "Darasal baat ye hai...", "Hum sab sochte hain ki...").
- Fast-paced, punchy, curiosity-driven.
- Absolutely NO lectures, NO generic corporate greetings ("Namaste doston", "Hello friends"). Open straight with the curiosity hook!

CRITICAL FORMAT REQUIREMENTS:
1. Scene 1 MUST be kind="hook". Narration max 12 words. Relatable, shocking, or curiosity gap opening.
2. Intermediate scenes (4-6 scenes) MUST use a mix of visual kinds:
   - "stat": big number / short stat label
   - "compare": side by side comparison
   - "bullets": 2-3 quick takeaway points
   - "flow": 2-3 sequential steps or cause-and-effect
3. Scene 7 MUST be kind="takeaway": 1-line punchline summary + exactly 3 key terms.
4. Scene 8 MUST be kind="cta": Narration telling viewers to comment "FACT" for a secret bonus fact, follow @aiverse.agent, and loop seamlessly back to the opening line!

JSON SCHEMA:
{schema}

Return ONLY a valid JSON object:
{{
  "scenes": [
    {{"kind": "hook", "narration": "...", "visual": {{"text": "max 6 punchy words", "emoji": "🧠"}}}},
    ...
    {{"kind": "cta", "narration": "Aise hi mind-blowing facts ke liye comment karo FACT aur follow karo @aiverse.agent!", "visual": {{"text": "Follow for more!"}}}}
  ],
  "caption_summary": "2 short engaging Hinglish lines for the caption",
  "headline": "Curiosity hook headline with emoji, max 60 chars",
  "hashtags": ["5 niche hashtags with #"],
  "freebie": "One bonus secret fact from the confirmed facts (max 150 chars)",
  "key_terms": ["term1", "term2", "term3"]
}}"""

def generate_trend_script(topic_candidate):
    """
    Takes a verified topic candidate and generates a complete script validated by lesson_script.
    """
    facts_str = "\n".join(f"- {f}" for f in topic_candidate.get("verified_facts", []))
    prompt = TREND_SCRIPT_PROMPT.format(
        title=topic_candidate.get("title_hinglish") or topic_candidate.get("title"),
        category=topic_candidate.get("category", "curiosity"),
        facts=facts_str or topic_candidate.get("summary", ""),
        analogy=topic_candidate.get("analogy", "Think of this like an everyday Indian occurrence"),
        schema=lesson_script.SCHEMA
    )

    # Generate with LLM (Groq / Gemini)
    raw = llm.generate_json(prompt, temperature=0.3)

    # Validate scenes through existing validator to guarantee zero render crashes
    validated = lesson_script.validate(raw, min_scenes=5, max_scenes=9)
    return validated
