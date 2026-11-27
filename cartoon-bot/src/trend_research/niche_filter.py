"""Niche and Quality Filter.
Rejects:
- Political controversies, elections, ministers, parties.
- Religious controversies, communal disputes, caste.
- Celebrity gossip, dating, personal lives.
- Sensational rumors, unverified clickbait.
- Dangerous challenges, scams, malware, illegal acts.
- Medical claims, miracle cures without peer-reviewed evidence.
- Violence, crimes, deaths, accidents.

Prioritizes:
- Science, Space, Human Body, Animals, India History, Future Tech, Psychology, Everyday Facts.
- Clear educational and curiosity value suitable for 20-35s animated short-form video.
"""
import re

# Strict regex pattern for toxic / banned topics
BANNED_REGEX = re.compile(
    r"\b(election|vote|voting|ballot|bjp|congress|aap|modi|rahul gandhi|minister|parliament|lok sabha|rajya sabha|"
    r"hindu|muslim|christian|sikh|caste|dalit|mandir|masjid|waqf|communal|riot|sharia|"
    r"bollywood scandal|divorce|dating|affair|celebrity arrest|bigg boss|"
    r"murder|kill|killing|dead|death|suicide|rape|assault|molest|beaten|stolen|robbery|loot|terror|terrorist|bomb|blast|"
    r"court|lawsuit|sued|fir|jail|bail|police arrest|scam|fraud|cryptocurrency|ponzi|"
    r"cancer cure|miracle diet|weight loss pill|covid conspiracy|vaccine secret|"
    r"pakistan|israel|gaza|ukraine|russia war|military clash|army attack)\b",
    re.IGNORECASE
)

ALLOWED_CATEGORIES = {
    "space": ["space", "isro", "nasa", "planet", "galaxy", "black hole", "moon", "mars", "star", "telescope", "solar system", "asteroid"],
    "body": ["brain", "heart", "dna", "cell", "organ", "eye", "blood", "sleep", "dream", "muscle", "nerve", "human body", "biology"],
    "animals": ["animal", "bird", "fish", "whale", "insect", "ant", "dog", "cat", "species", "wildlife", "octopus", "dolphin"],
    "science": ["physics", "chemistry", "quantum", "gravity", "energy", "element", "atom", "discovery", "scientist", "experiment"],
    "india": ["india", "ancient india", "temple", "monument", "vedic", "chola", "mughal", "harappa", "fort", "history", "indian heritage"],
    "tech": ["ai", "robot", "supercomputer", "chip", "battery", "quantum computing", "future tech", "gadget", "technology"],
    "psychology": ["psychology", "mind", "memory", "behavior", "habit", "decision", "human mind", "illusion", "placebo"],
    "facts": ["did you know", "surprising", "fact", "secret", "mystery", "why does", "how does"]
}

def is_safe_and_relevant(candidate):
    """Returns (is_allowed: bool, reason: str, detected_category: str)"""
    text = (candidate.get("title", "") + " " + candidate.get("summary", "")).lower()

    # 1. Banned topic check
    match = BANNED_REGEX.search(text)
    if match:
        return False, f"Banned keyword match: '{match.group(0)}'", "rejected"

    # 2. Length check
    if len(candidate.get("title", "").strip()) < 10:
        return False, "Title too short", "rejected"

    # 3. Detect or validate category
    curr_cat = candidate.get("category", "general")
    if curr_cat in ALLOWED_CATEGORIES:
        return True, "Passed niche filter", curr_cat

    # Classify by keyword match
    for cat, kws in ALLOWED_CATEGORIES.items():
        for kw in kws:
            if kw in text:
                return True, f"Categorized as {cat}", cat

    # Default general curiosity if non-toxic
    return True, "General curiosity topic", "facts"
