import os

def env(name, default=None, required=False):
    v = os.environ.get(name, default)
    if required and not v:
        raise RuntimeError(f"Missing secret/env var: {name}")
    return v

# ---------------- Secrets (GitHub: Settings > Secrets and variables > Actions) ----------------
GEMINI_API_KEY   = lambda: env("GEMINI_API_KEY", required=True)
TELEGRAM_TOKEN   = lambda: env("TELEGRAM_BOT_TOKEN", required=True)
TELEGRAM_CHAT_ID = lambda: str(env("TELEGRAM_CHAT_ID", required=True))
SUPABASE_URL     = lambda: env("SUPABASE_URL", required=True).rstrip("/")      # https://xxxx.supabase.co
SUPABASE_KEY     = lambda: env("SUPABASE_SERVICE_KEY", required=True)         # secret / service_role key
SUPABASE_BUCKET  = lambda: env("SUPABASE_BUCKET", "cartoon-reels")            # must be a PUBLIC bucket
IG_USER_ID       = lambda: env("IG_USER_ID", required=True)
IG_ACCESS_TOKEN  = lambda: env("IG_ACCESS_TOKEN", required=True)
CF_API_TOKEN     = lambda: env("CF_API_TOKEN")        # optional: backup image generator (Cloudflare Workers AI)
CF_ACCOUNT_ID    = lambda: env("CF_ACCOUNT_ID")       # optional: needed only with CF_API_TOKEN

# ---------------- Behaviour (GitHub: Settings > Secrets and variables > Actions > Variables) ----------------
# REVIEW_MODE: approve (default: posts after you send /post) | auto_unless_skip | auto
REVIEW_MODE  = env("REVIEW_MODE", "approve")
REVIEW_HOURS = float(env("REVIEW_HOURS", "2"))
MOUTH_FX     = env("MOUTH_FX", "true").lower() == "true"     # talking-mouth effect (set false if it looks bad)

# Visual enhancements (set to "false" to disable)
ADD_INTRO       = env("ADD_INTRO", "true").lower() == "true"        # Branded intro clip
ADD_OUTRO       = env("ADD_OUTRO", "true").lower() == "true"        # CTA outro clip
ADD_TRANSITIONS = env("ADD_TRANSITIONS", "true").lower() == "true"  # Crossfade between scenes
KARAOKE_SUBS    = env("KARAOKE_SUBS", "true").lower() == "true"     # Word-by-word karaoke timing

# Leave GEMINI_MODELS empty: the bot asks Google which Flash models exist today (names get retired often).
# To force specific ones, set the variable GEMINI_MODELS="model-a,model-b".
GEMINI_MODELS = [m.strip() for m in env("GEMINI_MODELS", "").split(",") if m.strip()]
GEMINI_FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3-flash-preview"]
DEPTH_MODELS = ["depth-anything/Depth-Anything-V2-Small-hf", "LiheYoung/depth-anything-small-hf",
                "Intel/dpt-hybrid-midas"]
TRENDS_GEO   = env("TRENDS_GEO", "IN")
NUM_SCENES   = int(env("NUM_SCENES", "7"))           # ~35-45 seconds
IMG_SEED     = int(env("IMG_SEED", "4242"))
MIN_SECONDS, MAX_SECONDS = 15, 80

# ---------------- The series & channel (edit freely) ----------------
SERIES_NAME = env("SERIES_NAME", "AI Seekho")
CHANNEL_HASHTAGS = ["#aiseekho", "#hinglish", "#aiexplained", "#machinelearning", "#hindi", "#techeducation"]
CTA_TEXT = "Roz naya lesson - Follow karo! 🔔"

# Hinglish voice for education (Indian English for tech + Hindi mix)
VOICES = {
    "narrator": {"voice": "en-IN-PrabhatNeural", "rate": "+8%", "pitch": "-2Hz"},  # Indian English Male
    "hinglish": {"voice": "en-IN-PrabhatNeural", "rate": "+10%", "pitch": "+5Hz"},  # Main teaching voice
    "hindi": {"voice": "hi-IN-MadhurNeural", "rate": "+5%", "pitch": "-2Hz"},  # Pure Hindi segments
}

# Content type for determining what to generate
CONTENT_MODE = env("CONTENT_MODE", "educational")  # "educational" or "entertainment"

# Topics containing these words are removed BEFORE the AI sees them, and stories containing them are rejected.
BLOCK_EN = """election elections vote voting poll polls bjp congress aap tmc modi rahul kejriwal yogi mamata shah
 parliament minister cm government govt protest riot riots war army military attack attacks terror terrorist blast
 bomb murder murdered killed kill dead death dies died suicide rape assault arrest arrested jail court verdict
 accident crash collapse flood earthquake cyclone covid cancer disease hospital hindu muslim christian sikh islam
 religion religious temple mosque church caste dalit reservation pakistan china israel gaza ukraine russia
 sex sexual porn drugs""".split()
BLOCK_HI = ["चुनाव", "भाजपा", "कांग्रेस", "आतंक", "दंगा", "हत्या", "मौत", "बलात्कार", "आत्महत्या",
            "धर्म", "मस्जिद", "मंदिर", "हिंदू", "मुस्लिम", "जाति", "युद्ध", "हमला", "सरकार"]
