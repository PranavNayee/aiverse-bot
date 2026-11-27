"""Trend Intelligence Engine for AIVerse Bot.
Discovers Indian trending topics across Science, Space, Body, Animals, India History, Tech, Psychology,
verifies facts, and generates viral Hinglish animated scripts.
"""
from .selector import select_best_trend
from .script_generator import generate_trend_script

def discover_and_select_trend(history=None):
    """
    Main entrypoint:
    1. Selects top verified trend topic + backups.
    2. Generates animated script adhering to edu_render schema.
    Returns: dict with {candidate, backups, script} or None.
    """
    winner, backups = select_best_trend(history=history)
    if not winner:
        print("[trend_research] No verified trend passed fact-checking today.")
        return None

    try:
        script = generate_trend_script(winner)
        return {
            "candidate": winner,
            "backups": backups,
            "script": script
        }
    except Exception as e:
        print(f"[trend_research] Script generation failed for {winner['title']}: {e}")
        # Try next backup if script generation fails
        for b in backups:
            try:
                print(f"[trend_research] Retrying script generation with backup: {b['title']}")
                script = generate_trend_script(b)
                return {
                    "candidate": b,
                    "backups": [x for x in backups if x != b],
                    "script": script
                }
            except Exception as be:
                print(f"[trend_research] Backup script generation failed: {be}")

        return None
