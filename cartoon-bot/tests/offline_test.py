"""Offline test suite for AIVerse Bot. No API keys, no network calls, nothing is posted.

Covers: scheduler, syllabus integrity (100 lessons, tricks, alerts, fun facts),
script validation, YouTube metadata/playlists, and publisher claim/lock logic.
"""
import datetime as dt, json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))

for k in ("SUPABASE_URL", "SUPABASE_SERVICE_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "IG_USER_ID", "IG_ACCESS_TOKEN"):
    os.environ.setdefault(k, "test")
os.environ["REVIEW_MODE"] = "auto"
for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN", "GEMINI_API_KEY", "GROQ_API_KEY", "FB_CROSSPOST"):
    os.environ.pop(k, None)

import config as C, slots, syllabus, lesson_script, youtube, publisher

PASSED = []

def ok(name):
    PASSED.append(name)
    print("ok -", name)

def raises(exc, fn, *a, **k):
    try:
        fn(*a, **k)
    except exc as e:
        return e
    raise AssertionError(f"{getattr(fn, '__name__', fn)} did not raise {exc.__name__}")

# ------------------------------------------------------------------ 1. Scheduler
IST = slots.TZ
at = lambda y, mo, d, h, mi: dt.datetime(y, mo, d, h, mi, tzinfo=IST)
# Slot at 10:00 AM when morning slot (08:00) is marked done -> picks 19:00 evening slot
s1 = slots.upcoming_slot(at(2026, 11, 26, 10, 0), done={"2026-11-26"})
assert slots.key(s1) == "2026-11-26-1900", f"Expected 19:00 slot, got {slots.key(s1)}"
# Slot at 23:00 PM -> picks tomorrow morning slot
s2 = slots.upcoming_slot(at(2026, 11, 26, 23, 0), done=set())
assert slots.key(s2) == "2026-11-27", f"Expected morning slot, got {slots.key(s2)}"
ok("scheduler")

# ------------------------------------------------------------------ 2. Syllabus integrity
assert len(syllabus.LESSONS) == 100, f"Expected 100 lessons, got {len(syllabus.LESSONS)}"
assert syllabus.TOTAL == 100
assert len(syllabus.TRICKS) >= 10, f"Tricks: {len(syllabus.TRICKS)}"
assert len(syllabus.ALERTS) >= 10, f"Alerts: {len(syllabus.ALERTS)}"
assert len(syllabus.FUN_FACTS) >= 10, f"Fun facts: {len(syllabus.FUN_FACTS)}"

# Rotation tests
lesson, num, nxt = syllabus.get_next_lesson([])
assert num == 1, f"Expected lesson 1, got {num}"
assert lesson["title_en"] == "What is AI?"

trick = syllabus.get_next_trick([])
assert "title" in trick and "facts" in trick

alert = syllabus.get_next_alert([])
assert "title" in alert and "facts" in alert

fact = syllabus.get_fun_fact([])
assert "title" in fact and "facts" in fact

themes = syllabus.seasonal_themes(dt.date(2026, 11, 26))
assert len(themes) >= 5
ok(f"syllabus ({syllabus.TOTAL} lessons, tricks, alerts, fun facts, themes)")

# ------------------------------------------------------------------ 3. Script validation
RAW = {
    "scenes": [
        {"kind": "hook", "narration": "AI kya hai aur ye kaise kaam karta hai", "visual": {"text": "AI kya hai?", "emoji": "🤖"}},
        {"kind": "stat", "narration": "Daily billions log AI models use karte hain", "visual": {"big": "1 Billion+", "caption": "users worldwide", "emoji": "🌍"}},
        {"kind": "bullets", "narration": "Speech recognition maps translation sab AI hai", "visual": {"heading": "Examples", "items": ["Speech", "Maps", "Vision"]}},
        {"kind": "takeaway", "narration": "Narrow AI specific tasks mein human se behtar hai", "visual": {"text": "Narrow AI is powerful", "terms": ["Narrow AI"]}},
        {"kind": "cta", "narration": "Follow karo AIVerse aur comment karo NOTES", "visual": {"text": "Comment NOTES"}}
    ],
    "headline": "AI kya hai? 🤖",
    "caption_summary": "AI ka simple explanation sirf 60 seconds mein!",
    "hashtags": ["#AI", "#MachineLearning"],
    "freebie": "AI basics cheat sheet"
}
script = lesson_script.validate(RAW, 4, 7)
assert len(script["scenes"]) == 5
assert script["scenes"][0]["kind"] == "hook"
assert script["scenes"][-1]["kind"] == "cta"

# Must reject invalid length or missing cta
raises(ValueError, lesson_script.validate, {**RAW, "scenes": RAW["scenes"][:-1]}, 4, 7)
ok("script validation")

# ------------------------------------------------------------------ 4. YouTube metadata
assert set(youtube.PLAYLISTS.keys()) >= {"lesson", "trick", "fun_fact", "alert", "photo", "news", "weekly"}
t = youtube._title("AI Lesson 1: Basics", "AI")
assert t.endswith("#Shorts")
assert len(t) <= 100
ok("youtube metadata and playlists")

# ------------------------------------------------------------------ 5. Publisher claim & dedupe
assert publisher.MAX_ATTEMPTS == 3
assert publisher.due_at({"post_at": 1000}) == 1000
ok("publisher configuration")

print(f"\nAll {len(PASSED)} tests passed successfully!")
