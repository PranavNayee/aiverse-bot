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

# ---------------- Voice ----------------
# Hinglish is SPOKEN by the native Hindi voice from a Devanagari copy of the script (English tech terms stay
# in English), so Hindi words are pronounced properly. Captions on screen stay in Roman Hinglish.
VOICE_NAME  = env("VOICE_NAME", "hi-IN-MadhurNeural") or "hi-IN-MadhurNeural"
VOICE_RATE  = env("VOICE_RATE", "-3%") or "-3%"          # slower = more weight and clarity
VOICE_PITCH = env("VOICE_PITCH", "-6Hz") or "-6Hz"       # lower = deeper (try -10Hz for even deeper)
VOICE_FX    = flag("VOICE_FX")                          # broadcast polish: bass, clarity, compression

VOICES = {
    "hinglish":       {"voice": VOICE_NAME,            "rate": VOICE_RATE, "pitch": VOICE_PITCH},  # main teacher voice
    "hinglish_roman": {"voice": "en-IN-PrabhatNeural", "rate": "+0%",      "pitch": "-4Hz"},       # fallback for Roman text
    "english":        {"voice": "en-US-AndrewNeural",  "rate": "+0%",      "pitch": "-4Hz"},
    "narrator":       {"voice": VOICE_NAME,            "rate": VOICE_RATE, "pitch": VOICE_PITCH},
    "hindi":          {"voice": VOICE_NAME,            "rate": VOICE_RATE, "pitch": VOICE_PITCH},
}

# deep, powerful "radio" voice chain (ffmpeg filters)
VOICE_FILTER = ("highpass=f=70,equalizer=f=110:t=q:w=1:g=5,equalizer=f=320:t=q:w=1.2:g=-2,"
                "equalizer=f=3200:t=q:w=1.5:g=2.5,acompressor=threshold=-20dB:ratio=3:attack=5:release=90:makeup=3,"
                "alimiter=limit=0.95")

def get_lesson_voice():
    if LANGUAGE_MODE == "english_only":
        return "english"
    if LANGUAGE_MODE == "hindi_only":
        return "hindi"
    return "hinglish"

DEFAULT_LESSON_VOICE = get_lesson_voice()
SPEAK_DEVANAGARI = LANGUAGE_MODE == "hinglish" and VOICE_NAME.startswith("hi-")   # edge fallback only

# ---------------- Human-like voice providers (see tts.py) ----------------
# auto = ElevenLabs if ELEVENLABS_API_KEY is set, else Gemini TTS (free with GEMINI_API_KEY), else Edge.
TTS_PROVIDER     = (env("TTS_PROVIDER", "auto") or "auto").strip().lower()
GEMINI_VOICE     = env("GEMINI_VOICE", "Charon") or "Charon"          # Charon / Orus / Fenrir / Iapetus / Puck...
GEMINI_SPEAK_DEVANAGARI = flag("GEMINI_SPEAK_DEVANAGARI", "false")   # Hinglish: read Roman text (false) or Devanagari copy
ELEVENLABS_MODEL = env("ELEVENLABS_MODEL", "eleven_multilingual_v2") or "eleven_multilingual_v2"
# human voices need only light polish; the heavy chain is for the Edge voice
VOICE_FILTER_LIGHT = "highpass=f=60,acompressor=threshold=-18dB:ratio=2:attack=8:release=120:makeup=2,alimiter=limit=0.95"
