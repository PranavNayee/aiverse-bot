"""Mandatory Fact-Checking Engine for Trending Topics.
Before any topic is selected for video generation:
1. Identifies the exact factual claims from supporting articles.
2. Checks whether claims are supported by credible sources.
3. Rejects unsupported, contradictory, or sensational rumors.
4. Uses the existing llm.py engine (Groq/Gemini free models).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import llm

FACT_CHECK_PROMPT = """You are a strict, senior scientific fact-checker for an educational animated video series in India.

TOPIC TITLE: {title}
CATEGORY: {category}
EVIDENCE & SOURCE EXCERPTS:
{evidence}

YOUR TASK:
1. Analyze the topic and evidence excerpts.
2. Verify:
   - Is this topic based on real, verifiable facts (science, space, history, biology, genuine discoveries)?
   - Are the claims accurate and not sensational clickbait or rumors?
   - Does it contain 3-4 concrete facts that can be clearly explained in a 30-second animated video?
   - Is it completely free from political, religious, or defamatory controversies?
3. If valid, extract the 3-4 confirmed core facts and a 1-sentence Indian analogy or everyday hook.
4. If invalid, speculative, or unverified, reject it.

Return ONLY JSON:
{{
  "verdict": "pass" or "reject",
  "reason": "1-line explanation of your decision",
  "verified_facts": ["fact 1", "fact 2", "fact 3"],
  "analogy": "Everyday Indian analogy or relatable hook to explain this simply",
  "title_hinglish": "Catchy, non-clickbait Hinglish title (max 8 words)"
}}"""

def verify_topic(candidate):
    """Returns (passed: bool, verified_data: dict)"""
    title = candidate.get("title", "")
    category = candidate.get("category", "general")
    evidence_list = candidate.get("evidence", []) or [candidate.get("summary", "")]
    evidence_text = "\n".join(f"- {ev[:400]}" for ev in evidence_list[:4])

    prompt = FACT_CHECK_PROMPT.format(
        title=title,
        category=category,
        evidence=evidence_text or title
    )

    try:
        res = llm.generate_json(prompt, temperature=0.1)
        verdict = res.get("verdict", "").lower().strip()
        if verdict == "pass" and res.get("verified_facts"):
            return True, {
                "verified_facts": res.get("verified_facts", []),
                "analogy": res.get("analogy", ""),
                "title_hinglish": res.get("title_hinglish", title),
                "reason": res.get("reason", "Passed verification")
            }
        else:
            return False, {"reason": res.get("reason", "Failed fact check criteria")}
    except Exception as e:
        print(f"[trend_research.fact_checker] Warning: Fact checking call failed: {e}")
        # Safe fallback: if LLM fails, we do NOT blindly allow unverified claims
        return False, {"reason": f"Fact verification call error: {e}"}
