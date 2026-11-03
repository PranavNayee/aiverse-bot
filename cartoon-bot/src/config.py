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
SUPABASE_KEY     = lambda: env("SUPABASE_SERVICE_KEY", required=True)         # service_role / secret key
SUPABASE_BUCKET  = lambda: env("SUPABASE_BUCKET", "cartoon-reels")            # must be a PUBLIC bucket
IG_USER_ID       = lambda: env("IG_USER_ID", required=True)
IG_ACCESS_TOKEN  = lambda: env("IG_ACCESS_TOKEN", required=True)
CF_API_TOKEN     = lambda: env("CF_API_TOKEN")        # optional: backup image generator (Cloudflare Workers AI)
CF_ACCOUNT_ID    = lambda: env("CF_ACCOUNT_ID")       # optional: needed only with CF_API_TOKEN

# ---------------- Behaviour (GitHub: Settings > Secrets and variables > Actions > Variables) ----------------
# REVIEW_MODE:
#   approve           -> video goes to Telegram; it posts only after you send /post   (safest, default)
#   auto_unless_skip  -> posts automatically after REVIEW_HOURS unless you send /skip
#   auto              -> posts immediately, no review
REVIEW_MODE  = env("REVIEW_MODE", "approve")
REVIEW_HOURS = float(env("REVIEW_HOURS", "2"))

GEMINI_MODELS = [m.strip() for m in env("GEMINI_MODELS",
                 "gemini-3.8-flash,gemini-3.6-flash,gemini-3.5-flash-lite").split(",")]
TRENDS_GEO   = env("TRENDS_GEO", "IN")
NUM_SCENES   = int(env("NUM_SCENES", "7"))          # 7 scenes ~ 35-45 sec
IMG_SEED     = int(env("IMG_SEED", "4242"))
MIN_SECONDS, MAX_SECONDS = 15, 80

CHANNEL_HASHTAGS = ["#hindicomedy", "#cartoon", "#trending", "#funny", "#reels", "#aicartoon"]
CTA_TEXT = "रोज़ एक नया कार्टून — फॉलो करें!"        # shown at the end of every video

STYLE = ("vibrant 2D cartoon illustration, bold clean outlines, flat bright colors, "
         "expressive faces, Indian setting, comedic, vertical composition, full scene")

CHARACTERS = {
    "chintu": "Chintu: short chubby Indian man, big black moustache, yellow kurta, round face, always excited",
    "mintu":  "Mintu: tall thin Indian man, round glasses, blue shirt, calm sarcastic expression",
}

# edge-tts Hindi voices: hi-IN-MadhurNeural (male), hi-IN-SwaraNeural (female)
VOICES = {
    "narrator": {"voice": "hi-IN-MadhurNeural", "rate": "+5%",  "pitch": "+0Hz"},
    "chintu":   {"voice": "hi-IN-MadhurNeural", "rate": "+12%", "pitch": "+25Hz"},
    "mintu":    {"voice": "hi-IN-SwaraNeural",  "rate": "+0%",  "pitch": "-8Hz"},
}

# Topics containing these words are removed BEFORE the AI sees them, and stories containing them are rejected.
# English words are matched as whole words, Hindi words as substrings. Edit freely.
BLOCK_EN = """election elections vote voting poll polls bjp congress aap tmc modi rahul kejriwal yogi mamata shah
 parliament minister cm government govt protest riot riots war army military attack attacks terror terrorist blast
 bomb murder murdered killed kill dead death dies died died suicide rape assault arrest arrested jail court verdict
 accident crash collapse flood earthquake cyclone covid cancer disease hospital hindu muslim christian sikh islam
 religion religious temple mosque church caste dalit reservation pakistan china israel gaza ukraine russia
 sex sexual porn drugs""".split()
BLOCK_HI = ["चुनाव", "भाजपा", "कांग्रेस", "आतंक", "दंगा", "हत्या", "मौत", "बलात्कार", "आत्महत्या",
            "धर्म", "मस्जिद", "मंदिर", "हिंदू", "मुस्लिम", "जाति", "युद्ध", "हमला", "सरकार"]
