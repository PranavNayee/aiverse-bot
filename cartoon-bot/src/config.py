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

# ---------------- The series & characters (edit freely) ----------------
SERIES_NAME = env("SERIES_NAME", "Bablu ka Vlog")
CHANNEL_HASHTAGS = ["#hindicomedy", "#cartoon", "#animation", "#funny", "#reels", "#aicartoon"]
CTA_TEXT = "रोज़ एक नया एपिसोड — फॉलो करें!"

STYLE_3D = ("3D animated movie still, Pixar-style, cute stylized characters, big expressive eyes, "
            "soft cinematic lighting, rich vibrant colors, highly detailed, shallow depth of field, vertical 9:16 composition")

CHARACTERS = {
    "bablu": {"look": "Bablu, a cute chubby cartoon monkey with golden-brown fur, big expressive brown eyes, "
                      "a red cap, a blue scarf and a small yellow backpack",
              "persona": "cheerful overconfident vlogger who talks to the camera and always lands in funny trouble"},
    "chiku": {"look": "Chiku, a small sarcastic cartoon crow with glossy black feathers, round glasses and an orange bow tie",
              "persona": "Bablu's dry-witted sidekick who roasts him"},
}

# edge-tts Hindi voices: hi-IN-MadhurNeural (male), hi-IN-SwaraNeural (female). Pitch/rate make them cartoony.
VOICES = {
    "narrator": {"voice": "hi-IN-MadhurNeural", "rate": "+5%",  "pitch": "-4Hz"},
    "bablu":    {"voice": "hi-IN-MadhurNeural", "rate": "+10%", "pitch": "+32Hz"},
    "chiku":    {"voice": "hi-IN-SwaraNeural",  "rate": "+4%",  "pitch": "+10Hz"},
}

# Topics containing these words are removed BEFORE the AI sees them, and stories containing them are rejected.
BLOCK_EN = """election elections vote voting poll polls bjp congress aap tmc modi rahul kejriwal yogi mamata shah
 parliament minister cm government govt protest riot riots war army military attack attacks terror terrorist blast
 bomb murder murdered killed kill dead death dies died suicide rape assault arrest arrested jail court verdict
 accident crash collapse flood earthquake cyclone covid cancer disease hospital hindu muslim christian sikh islam
 religion religious temple mosque church caste dalit reservation pakistan china israel gaza ukraine russia
 sex sexual porn drugs""".split()
BLOCK_HI = ["चुनाव", "भाजपा", "कांग्रेस", "आतंक", "दंगा", "हत्या", "मौत", "बलात्कार", "आत्महत्या",
            "धर्म", "मस्जिद", "मंदिर", "हिंदू", "मुस्लिम", "जाति", "युद्ध", "हमला", "सरकार"]
