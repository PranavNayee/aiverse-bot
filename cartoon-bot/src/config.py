import os

def env(name, default=None, required=False):
    v = os.environ.get(name, default)
    if required and not v:
        raise RuntimeError(f"Missing secret/env var: {name}")
    return v

def flag(name, default="true"):
    return str(env(name, default) or default).strip().lower() in ("1", "true", "yes", "on")

# ---------------- Secrets (GitHub: Settings > Secrets and variables > Actions) ----------------
GEMINI_API_KEY   = lambda: env("GEMINI_API_KEY", required=True)
TELEGRAM_TOKEN   = lambda: env("TELEGRAM_BOT_TOKEN", required=True)
TELEGRAM_CHAT_ID = lambda: str(env("TELEGRAM_CHAT_ID", required=True))
SUPABASE_URL     = lambda: env("SUPABASE_URL", required=True).rstrip("/")      # https://xxxx.supabase.co
SUPABASE_KEY     = lambda: env("SUPABASE_SERVICE_KEY", required=True)         # secret / service_role key
SUPABASE_BUCKET  = lambda: env("SUPABASE_BUCKET", "cartoon-reels")            # must be a PUBLIC bucket
IG_USER_ID       = lambda: env("IG_USER_ID", required=True)
IG_ACCESS_TOKEN  = lambda: env("IG_ACCESS_TOKEN", required=True)

# ---------------- Behaviour (GitHub: Settings > Secrets and variables > Actions > Variables) ----------------
# REVIEW_MODE: auto             -> posts by itself at the slot time
#              auto_unless_skip -> posts at the slot unless you send /skip in Telegram
#              approve          -> posts at/after the slot only once you send /post in Telegram
REVIEW_MODE  = (env("REVIEW_MODE", "approve") or "approve").strip().lower()
REVIEW_HOURS = float(env("REVIEW_HOURS", "2"))   # auto_unless_skip: minimum time you get to /skip after the preview

# ---------------- Schedule ----------------
POST_TIME          = env("POST_TIME", "08:00") or "08:00"           # daily posting time (24h, in TIMEZONE)
TIMEZONE           = env("TIMEZONE", "Asia/Kolkata") or "Asia/Kolkata"
LATE_GRACE_MINUTES = int(env("LATE_GRACE_MINUTES", "600") or 600)   # a reel made <=10 h after the slot still posts that day
MAX_WAIT_MINUTES   = int(env("MAX_WAIT_MINUTES", "330") or 330)     # a job may sleep this long to hit the slot exactly

# ---------------- 2D animation ----------------
MASCOT = flag("MASCOT")      # animated 'Seekho Bot' teacher: blinks, gestures, lip-syncs to the voice
MUSIC  = flag("MUSIC")       # soft background music bed (generated, or a file from assets/music), ducked under voice
MUSIC_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "music")

# ---------------- The series & channel (edit freely) ----------------
SERIES_NAME = env("SERIES_NAME", "AI Seekho")

# Content language: "hinglish" (default), "english_only", "hindi_only"
LANGUAGE_MODE = env("LANGUAGE_MODE", "hinglish")

# Indian voices for proper Hinglish pronunciation (US/UK voices butcher Hindi words)
VOICES = {
    "hinglish":       {"voice": "en-IN-PrabhatNeural", "rate": "+3%", "pitch": "+0Hz"},   # main teacher voice
    "english":        {"voice": "en-US-AndrewNeural",  "rate": "+5%", "pitch": "+0Hz"},
    "hinglish_hindi": {"voice": "hi-IN-MadhurNeural",  "rate": "+3%", "pitch": "+0Hz"},
    "narrator":       {"voice": "en-IN-PrabhatNeural", "rate": "+0%", "pitch": "+0Hz"},
    "hindi":          {"voice": "hi-IN-MadhurNeural",  "rate": "+3%", "pitch": "+0Hz"},
    "hindi_female":   {"voice": "en-IN-NeerjaNeural",  "rate": "+3%", "pitch": "+0Hz"},
}

def get_lesson_voice():
    if LANGUAGE_MODE == "english_only":
        return "english"
    if LANGUAGE_MODE == "hindi_only":
        return "hindi"
    return "hinglish"

DEFAULT_LESSON_VOICE = get_lesson_voice()
