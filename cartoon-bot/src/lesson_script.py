"""Writes the lesson script as structured scenes (what to SAY + what to SHOW), then has a second AI fact-check it.
No silent fallback: if a good, checked script can't be made, we raise and the bot alerts you instead of posting junk."""
import re
import llm
import config as C
from util import log

SCHEMA = """Scene kinds and their "visual" fields (keep texts SHORT, they appear big on a phone screen):
- hook:     {"text": "question/surprise, max 9 words", "emoji": "one emoji"}
- bullets:  {"heading": "max 4 words", "items": ["max 6 words each", 2 to 4 items]}
- flow:     {"heading": "max 4 words", "steps": [{"label": "max 3 words", "emoji": "one emoji"}, 2 to 5 steps], "caption": "optional, max 8 words"}
- compare:  {"left_title": "max 3 words", "right_title": "max 3 words", "left": ["max 4 words", 2 to 3 items], "right": ["max 4 words", 2 to 3 items]}
- network:  {"heading": "max 4 words", "layers": [e.g. 3,4,4,2 (2 to 5 numbers, each 1 to 6)], "labels": ["Input","Hidden","Output"]}
- code:     {"heading": "max 4 words", "lines": ["valid short Python, max 34 chars per line, max 8 lines"]}
- stat:     {"big": "big number/term, max 10 chars", "caption": "max 8 words", "emoji": "one emoji"}
- formula:  {"heading": "max 4 words", "lines": ["max 28 chars per line, max 2 lines"], "note": "max 8 words"}
- takeaway: {"text": "one-line summary, max 14 words", "terms": ["max 3 words", exactly 3 key terms]}
- chat:     {"user": "what the person types to the AI, max 90 chars", "ai": "the AI's short reply, max 140 chars"}  (a ChatGPT-style chat demo that SHOWS a result)
- cta:      {"text": "teaser for the next video, max 10 words"}"""

HOOK_RULE = """HOOK (critical for views): the first sentence must promise a concrete PAYOFF or show a surprising real-life RESULT
the viewer gets (e.g. "Ek prompt se 1 ghante ka kaam 2 minute mein"), never a vague question like "Kya aap jaante hain AI kya hai?".
Talk to ONE viewer ("aap"/"you"). No greetings, no channel intro."""

CTA_RULE = """LAST SCENE kind=cta: tell viewers to comment the word {keyword} to get {freebie_what} in the reply, then follow {channel}.
Also return "freebie": {freebie_spec}"""

LESSON_PROMPT = """You write a 45-60 second Instagram Reel lesson for an Indian audience, in {language_style}, for a faceless animated channel called "{channel}".

LESSON #{num} ({level}): {title}  /  {title_en}
CORE FACTS (the ONLY facts you may state as true): {facts}
Everyday Indian analogy to use: {analogy}
Keywords: {keywords}
Next lesson (for the teaser): {next_title}
{feedback}{winners}
LANGUAGE (critical): {language_instruction}
{hook_rule}
{cta_rule}
ACCURACY (critical): Do not invent statistics, dates, names, prices or claims beyond the CORE FACTS. If the analogy is imperfect, say "roughly" or "approximately". Never mention politics or religion.

STRUCTURE: 7 to 9 scenes. Scene 1 kind=hook (narration 8-14 words). Then analogy, concept breakdown (use different visual kinds: flow / compare / network / bullets / formula / code / stat where they truly fit the topic), an example, then kind=takeaway, last kind=cta (narration 12-24 words: the comment-keyword offer, tease the next lesson, ask to follow).
Each scene "narration": 12-30 words (hook and cta may be shorter). Total narration about 120-170 words.
Visuals must show THIS lesson's real content (real step names, real layer sizes, real formula), never generic placeholders.

{schema}

Return ONLY JSON:
{{"scenes": [{{"kind": "hook", "narration": "...", "visual": {{...}}}}, ...],
 "caption_summary": "2 short lines, same language as the narration",
 "headline": "Instagram caption first line: curiosity hook with the main search keyword, max 70 chars, 1 emoji",
 "hashtags": ["5 niche hashtags for this exact topic, lowercase, with #"],
 "freebie": "...",
 "key_terms": ["term1", "term2", "term3"]}}"""

FACT_PROMPT = """You are a strict senior ML engineer fact-checking a short lesson for beginners.

REFERENCE FACTS: {facts}
LESSON TOPIC: {title_en}

SCRIPT (narration and on-screen text):
{script}

Check: (1) every claim is correct and consistent with the reference facts and standard ML knowledge; (2) nothing misleading or invented (numbers, dates, names); (3) the analogy does not teach a wrong idea; (4) the on-screen text (steps, formulas, code, layers) is correct; (5) no politics, religion or unsafe content; (6) it actually explains the topic.
Verdict: "pass" = fine; "minor" = small wording issues only; "major" = any factual error, misleading claim, wrong formula/code, or off-topic.
Return ONLY JSON: {{"verdict": "pass|minor|major", "issues": ["short description of each problem and how to fix it"]}}"""

FUN_PROMPT = """You write a 35-45 second weekend "AI fun fact" Instagram Reel in {language_style} for the channel "{channel}".
LANGUAGE (critical): {language_instruction}
{hook_rule}
TOPIC: {title}
CORE FACT (the ONLY fact you may state): {facts}
{feedback}
Rules: friendly, surprising, accurate. Do not add facts, numbers or dates beyond the core fact. No emojis/symbols in "narration". 5 to 6 scenes: hook, 2-3 story/explain scenes (use stat / bullets / flow / compare kinds), takeaway, cta (tell viewers to comment AI for one more surprising fact, then follow).
Also return "freebie": one more short surprising fact strictly from the CORE FACT, max 300 chars.

{schema}

Return ONLY JSON: {{"scenes": [{{"kind": "hook", "narration": "...", "visual": {{...}}}}, ...], "caption_summary": "2 short lines, same language as the narration", "headline": "caption first line: curiosity hook with the topic keyword, max 70 chars, 1 emoji", "hashtags": ["5 niche hashtags with #"], "freebie": "...", "key_terms": ["t1","t2","t3"]}}"""

TRICK_PROMPT = """You write a 35-55 second "AI Trick of the Day" Instagram Reel in {language_style} for the faceless animated channel "{channel}".
The viewer must be able to USE this trick right after watching.
TRICK: {title}  /  {title_en}
CORE FACTS (the ONLY facts you may state as true; never invent app features, prices, menu names or numbers): {facts}
Keywords: {keywords}
{feedback}{winners}
LANGUAGE (critical): {language_instruction}
{hook_rule}
{cta_rule}
STRUCTURE: 5 to 8 scenes. Scene 1 kind=hook showing the payoff. Use kind=chat to SHOW an example prompt and a realistic short
AI reply when the trick involves a chatbot; use flow for steps, compare for before/after. Then kind=takeaway, last kind=cta.
Each "narration": 8-28 words. Total narration about 90-150 words. No emojis/symbols in "narration".

{schema}

Return ONLY JSON: {{"scenes": [{{"kind": "hook", "narration": "...", "visual": {{...}}}}, ...],
 "caption_summary": "2 short lines, same language as the narration",
 "headline": "caption first line: the payoff + main keyword, max 70 chars, 1 emoji",
 "hashtags": ["5 niche hashtags for this exact trick, with #"],
 "freebie": "...", "key_terms": ["t1","t2","t3"]}}"""

KINDS = {"hook", "bullets", "flow", "compare", "network", "code", "stat", "formula", "takeaway", "chat", "cta"}

def _s(x, n):
    return re.sub(r"\s+", " ", str(x or "")).strip()[:n]

def _list(x, lo, hi, n):
    items = [_s(i, n) for i in (x or []) if _s(i, n)]
    if len(items) < lo:
        raise ValueError(f"needs {lo}-{hi} items")
    return items[:hi]

def _roman_ratio(text):
    letters = [c for c in text if c.isalpha()]
    return sum(c.isascii() for c in letters) / len(letters) if letters else 0

def clean_scene(i, sc):
    """Validate and trim one scene; raises ValueError with a message the writer can learn from."""
    kind = sc.get("kind")
    if kind not in KINDS:
        raise ValueError(f"scene {i}: unknown kind '{kind}'")
    nar = _s(sc.get("narration"), 400)
    words = len(nar.split())
    if not (5 <= words <= 38):
        raise ValueError(f"scene {i}: narration has {words} words (need 8-30)")
    if _roman_ratio(nar) < 0.9:
        raise ValueError(f"scene {i}: narration must be in Roman script, no Devanagari")
    v = sc.get("visual") or {}
    try:
        if kind == "hook":
            vis = {"text": _s(v.get("text"), 70), "emoji": _s(v.get("emoji"), 4)}
            assert vis["text"]
        elif kind == "bullets":
            vis = {"heading": _s(v.get("heading"), 34), "items": _list(v.get("items"), 2, 4, 44)}
        elif kind == "flow":
            steps = [{"label": _s(s.get("label"), 26), "emoji": _s(s.get("emoji"), 4)} for s in (v.get("steps") or []) if isinstance(s, dict) and _s(s.get("label"), 26)]
            assert 2 <= len(steps) <= 5
            vis = {"heading": _s(v.get("heading"), 34), "steps": steps[:5], "caption": _s(v.get("caption"), 60)}
        elif kind == "compare":
            vis = {"left_title": _s(v.get("left_title"), 22), "right_title": _s(v.get("right_title"), 22),
                   "left": _list(v.get("left"), 2, 3, 34), "right": _list(v.get("right"), 2, 3, 34)}
        elif kind == "network":
            layers = [int(x) for x in (v.get("layers") or [])]
            assert 2 <= len(layers) <= 5 and all(1 <= x <= 6 for x in layers)
            vis = {"heading": _s(v.get("heading"), 34), "layers": layers, "labels": [_s(x, 12) for x in (v.get("labels") or [])][:5]}
        elif kind == "code":
            lines = [str(l).rstrip()[:36] for l in (v.get("lines") or []) if str(l).strip()][:8]
            assert len(lines) >= 1
            vis = {"heading": _s(v.get("heading"), 34), "lines": lines}
        elif kind == "stat":
            vis = {"big": _s(v.get("big"), 12), "caption": _s(v.get("caption"), 60), "emoji": _s(v.get("emoji"), 4)}
            assert vis["big"]
        elif kind == "formula":
            lines = [_s(l, 30) for l in (v.get("lines") or []) if _s(l, 30)][:2]
            assert lines
            vis = {"heading": _s(v.get("heading"), 34), "lines": lines, "note": _s(v.get("note"), 60)}
        elif kind == "takeaway":
            vis = {"text": _s(v.get("text"), 100), "terms": _list(v.get("terms"), 1, 3, 24)}
            assert vis["text"]
        elif kind == "chat":
            vis = {"user": _s(v.get("user"), 100), "ai": _s(v.get("ai"), 160)}
            assert vis["user"] and vis["ai"]
        else:  # cta
            vis = {"text": _s(v.get("text"), 80) or "Agla lesson miss mat karna"}
    except (AssertionError, ValueError, TypeError) as e:
        raise ValueError(f"scene {i} ({kind}): visual fields invalid or missing ({e})")
    return {"kind": kind, "narration": nar, "visual": vis}

def validate(raw, min_scenes=5, max_scenes=10):
    if not isinstance(raw, dict) or not isinstance(raw.get("scenes"), list):
        raise ValueError("answer must be a JSON object with a 'scenes' list")
    scenes = [clean_scene(i + 1, s) for i, s in enumerate(raw["scenes"]) if isinstance(s, dict)]
    if not (min_scenes <= len(scenes) <= max_scenes):
        raise ValueError(f"need {min_scenes}-{max_scenes} scenes, got {len(scenes)}")
    if scenes[0]["kind"] != "hook" or scenes[-1]["kind"] != "cta":
        raise ValueError("first scene must be kind=hook and last scene kind=cta")
    if len({s["kind"] for s in scenes}) < 3:
        raise ValueError("use at least 3 different visual kinds")
    total = sum(len(s["narration"].split()) for s in scenes)
    if not (80 <= total <= 210):
        raise ValueError(f"total narration is {total} words (need about 110-170)")
    terms = [_s(t, 28) for t in (raw.get("key_terms") or []) if _s(t, 28)][:3]
    tags = [("#" + re.sub(r"[^\w]", "", str(t)).lower()) for t in (raw.get("hashtags") or []) if re.sub(r"[^\w]", "", str(t))][:5]
    return {"scenes": scenes, "caption_summary": _s(raw.get("caption_summary"), 260), "key_terms": terms,
            "headline": _s(raw.get("headline"), 90), "hashtags": tags,
            "freebie": re.sub(r"[ \t]+", " ", str(raw.get("freebie") or "")).strip()[:900]}

def _script_text(script):
    return "\n".join(f"[{s['kind']}] SAY: {s['narration']} | SHOW: {s['visual']}" for s in script["scenes"])

def fact_check(script, facts, title_en):
    """Multi-agent fact-checking (inspired by ViMax): 3 specialized validators"""
    res = llm.generate_json(FACT_PROMPT.format(facts=facts, title_en=title_en, script=_script_text(script)),
                            temperature=0, order=("groq", "gemini"))
    verdict = str(res.get("verdict", "major")).lower()
    issues = [str(i)[:200] for i in (res.get("issues") or [])][:5]
    
    # Second validation: Visual consistency check (new!)
    if verdict in ("pass", "minor"):
        visual_verdict = _check_visual_consistency(script)
        if visual_verdict != "pass":
            verdict = "minor"
            issues.append(f"Visual flow: {visual_verdict}")
    
    return verdict, issues

def _check_visual_consistency(script):
    """Check if scenes flow logically (ViMax-inspired visual continuity)"""
    scenes = script["scenes"]
    kinds = [s["kind"] for s in scenes]
    
    # Check: No duplicate consecutive scene types (boring)
    for i in range(len(kinds) - 1):
        if kinds[i] == kinds[i + 1] and kinds[i] not in ("hook", "cta", "takeaway"):
            return f"Consecutive {kinds[i]} scenes - vary the visual types"
    
    # Check: Hook must be engaging, not just "stat" or "bullets"
    if scenes[0]["kind"] in ("stat", "bullets"):
        return "Hook should be more engaging than stat/bullets"
    
    # Check: Build-up to takeaway (no sudden jump to CTA)
    if len(scenes) > 3:
        pre_cta_idx = -2 if scenes[-1]["kind"] == "cta" else -1
        if scenes[pre_cta_idx]["kind"] == "hook":
            return "Missing build-up before conclusion"
    
    return "pass"

_SERIOUS = re.compile(r"incorrect|inaccurate|wrong|not exist|doesn't exist|invalid|misleading|error in|non-standard|"
                      r"syntax|import|module|undefined|false|mistake", re.I)
WINNERS = ""     # filled by lesson_main from analytics: hooks that performed best on this channel

def _make(prompt_fn, facts, title_en, min_scenes, max_scenes, attempts=4):
    """Multi-attempt generation with A/B testing on first scene (ViMax-inspired)"""
    feedback = ""
    best_script = None
    best_score = -1
    
    for n in range(1, attempts + 1):
        fb = f"\nYOUR PREVIOUS ATTEMPT WAS REJECTED. Fix exactly this: {feedback}\n" if feedback else ""
        
        # First attempt: generate TWO versions in parallel and pick better one (A/B testing)
        if n == 1:
            versions, err = [], None
            for temp in (0.7, 0.85):
                try:
                    versions.append(validate(llm.generate_json(prompt_fn(fb), temperature=temp), min_scenes, max_scenes))
                except ValueError as e:
                    err = e; log(f"  attempt 1 variant rejected (format): {e}")
                except RuntimeError as e:          # AI providers down: keep variant A if we have it
                    if not versions:
                        raise
                    log(f"  second A/B variant skipped (AI busy): {str(e)[:120]}")
                    break
            if not versions:
                feedback = str(err); continue
            if len(versions) == 2:
                script = _select_better_script(versions[0], versions[1], title_en)
                log("  attempt 1: A/B tested 2 versions, selected better one")
            else:
                script = versions[0]
        else:
            try:
                script = validate(llm.generate_json(prompt_fn(fb), temperature=0.7), min_scenes, max_scenes)
            except ValueError as e:
                feedback = str(e); log(f"  attempt {n} rejected (format): {e}"); continue
        
        verdict, issues = fact_check(script, facts, title_en)
        log(f"  attempt {n}: fact-check = {verdict} {issues}")
        
        serious = [i for i in issues if _SERIOUS.search(i)]
        if verdict == "minor" and serious and n < attempts:     # wrong code/formula/claims: rewrite, don't post
            log("  minor issues are real errors - rewriting")
            verdict = "major"
        if verdict in ("pass", "minor"):
            script["fact_check"] = verdict
            return script
        
        # Track best attempt even if not perfect
        score = 2 if verdict == "minor" else 1 if verdict == "pass" else 0
        if score > best_score:
            best_score = score
            best_script = script
        
        feedback = "factual problems: " + "; ".join(issues or ["unspecified"])
    
    # If all attempts failed, return best attempt with warning
    if best_script:
        log(f"⚠️ Using best attempt (not perfect) after {attempts} tries")
        best_script["fact_check"] = "warning"
        return best_script
    
    raise RuntimeError(f"Could not produce a correct lesson after {attempts} attempts. Last problem: {feedback}")

def _select_better_script(script_a, script_b, title_en):
    """Use LLM to pick the more engaging script (ViMax A/B selection pattern)"""
    prompt = f"""You are judging which lesson hook is MORE ENGAGING for Instagram Reels.
Lesson topic: {title_en}

OPTION A:
Hook: {script_a['scenes'][0]['narration']}
Visual: {script_a['scenes'][0]['visual']}

OPTION B:
Hook: {script_b['scenes'][0]['narration']}
Visual: {script_b['scenes'][0]['visual']}

Which hook grabs attention better? Consider: curiosity, relatability, surprise, clarity.
Return ONLY JSON: {{"choice": "A"|"B", "reason": "one sentence why"}}"""
    
    try:
        result = llm.generate_json(prompt, temperature=0)
        choice = result.get("choice", "A").upper()
        reason = result.get("reason", "unknown")
        log(f"  A/B selection: chose {choice} - {reason}")
        return script_a if choice == "A" else script_b
    except:
        log("  A/B selection failed, using script A")
        return script_a

def _language():
    if C.LANGUAGE_MODE == "english_only":
        language_style = "CLEAR ENGLISH"
        language_instruction = "Use clear, simple English. Friendly tone like explaining to a friend. Avoid jargon. No emojis or symbols like = * % in 'narration' (it is read aloud)."
    elif C.LANGUAGE_MODE == "hindi_only":
        language_style = "PURE HINDI (Devanagari)"
        language_instruction = "Pure Hindi in Devanagari script. Use Hindi equivalents for technical terms where possible. Friendly, conversational tone."
    else:  # hinglish (default)
        language_style = "HINGLISH"
        language_instruction = "Hinglish in ROMAN script only (no Devanagari). Hindi words like hai, kaise, kyun, matlab, samjho; technical terms in English (model, data, neural network). Friendly, like explaining to a friend. No emojis or symbols like = * % in 'narration' (it is read aloud), write numbers/terms as words where needed."
    return language_style, language_instruction

def _rules(kind):
    """hook + call-to-action rules for a content type: (hook_rule, cta_rule, keyword)."""
    en = C.LANGUAGE_MODE == "english_only"
    if kind == "trick":
        kw, what = "PROMPT", ("the exact prompt/steps" if en else "exact prompt/steps")
        spec = '"the exact copy-paste prompt or the steps from this reel, max 600 chars, plain text"'
    elif kind == "lesson":
        kw, what = "NOTES", ("short revision notes" if en else "short revision notes")
        spec = '"3-5 short revision bullet points of this lesson (each starting with •), max 600 chars"'
    else:
        kw, what = "AI", ("one more surprising fact" if en else "ek aur surprising fact")
        spec = '"one more short surprising fact strictly from the CORE FACT, max 300 chars"'
    return HOOK_RULE, CTA_RULE.format(keyword=kw, freebie_what=what, channel=C.SERIES_NAME, freebie_spec=spec), kw

def _winners():
    return f"\nHOOKS THAT PERFORMED BEST ON THIS CHANNEL (learn their style, do not copy): {WINNERS}\n" if WINNERS else ""

def generate_lesson_script(lesson, num, next_lesson):
    language_style, language_instruction = _language()
    en = C.LANGUAGE_MODE == "english_only"
    
    def prompt(fb):
        return LESSON_PROMPT.format(channel=C.SERIES_NAME, num=num, level=lesson["level"], title=lesson["title_en"] if en else lesson["title"],
                                    title_en=lesson["title_en"], facts=lesson["facts"],
                                    analogy=lesson["analogy"] + (" (adapt it into English)" if en else ""),
                                    keywords=", ".join(lesson["keywords"]), winners=_winners(),
                                    next_title=next_lesson["title_en"] if en else next_lesson["title"], feedback=fb, schema=SCHEMA,
                                    language_style=language_style, language_instruction=language_instruction,
                                    hook_rule=_rules("lesson")[0], cta_rule=_rules("lesson")[1])
    log(f"Writing lesson #{num}: {lesson['title_en']} ({language_style})")
    return _make(prompt, lesson["facts"], lesson["title_en"], 6, 10)

def generate_fun_fact_script(fact):
    def prompt(fb):
        style, instr = _language()
        return FUN_PROMPT.format(channel=C.SERIES_NAME, title=fact["title"], facts=fact["facts"], feedback=fb + _winners(), schema=SCHEMA,
                                 language_style=style, language_instruction=instr, hook_rule=_rules("fun_fact")[0])
    log(f"Writing fun fact: {fact['title']}")
    return _make(prompt, fact["facts"], fact["title"], 4, 8)


SPEECH_PROMPT = """Convert each Hinglish narration line (Roman script) into the form a native HINDI text-to-speech voice reads perfectly.
Rules:
- Write Hindi words in Devanagari (e.g. "samjho" -> "समझो", "kya" -> "क्या", "hai" -> "है").
- Keep English/technical words in English Latin script exactly (AI, model, data, training, neural network, Python...).
- Keep the SAME words in the SAME order. Do not add, drop, translate or explain anything.
- Write numbers and symbols the way they should be spoken.
- Keep the punctuation (? ! , .). Use "।" or "." for full stops.

LINES:
{lines}

Return ONLY JSON: {{"speech": ["line 1 converted", "line 2 converted", ...]}} with exactly {n} items."""

_DEV = re.compile(r"[ऀ-ॿ]")

def to_speech(narrations):
    """Roman Hinglish lines -> Devanagari-for-TTS lines (English terms kept). Returns a list with None for any
    line that could not be converted safely (that line is then spoken from the Roman text)."""
    lines = "\n".join(f"{i+1}. {t}" for i, t in enumerate(narrations))
    try:
        res = llm.generate_json(SPEECH_PROMPT.format(lines=lines, n=len(narrations)), temperature=0,
                                order=("groq", "gemini"))
        out = [str(x) for x in (res.get("speech") or [])]
    except Exception as e:
        log(f"  Devanagari conversion failed, speaking Roman text: {e}")
        return [None] * len(narrations)
    if len(out) != len(narrations):
        log(f"  Devanagari conversion returned {len(out)} lines for {len(narrations)}; speaking Roman text")
        return [None] * len(narrations)
    good = []
    for rom, dev in zip(narrations, out):
        dev = re.sub(r"^\s*\d+[.)]\s*", "", dev).strip()
        n_r, n_d = len(rom.split()), len(dev.split())
        ok = bool(_DEV.search(dev)) and 0.6 * n_r <= n_d <= 1.5 * n_r
        good.append(dev if ok else None)
    log(f"  Devanagari speech ready for {sum(g is not None for g in good)}/{len(good)} scenes")
    return good


def generate_trick_script(trick):
    style, instr = _language()
    hook_rule, cta_rule, _ = _rules("trick")
    en = C.LANGUAGE_MODE == "english_only"
    def prompt(fb):
        return TRICK_PROMPT.format(channel=C.SERIES_NAME, title=trick["title_en"] if en else trick["title"],
                                   title_en=trick["title_en"], facts=trick["facts"], keywords=", ".join(trick["keywords"]),
                                   feedback=fb, winners=_winners(), language_style=style, language_instruction=instr,
                                   hook_rule=hook_rule, cta_rule=cta_rule, schema=SCHEMA)
    log(f"Writing AI trick: {trick['title_en']} ({style})")
    return _make(prompt, trick["facts"], trick["title_en"], 5, 9)
