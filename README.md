# 🎓 AI Seekho - Automated Hinglish AI Education Bot

Fully automated Instagram bot that posts daily AI/ML educational lessons in Hinglish with professional animations and fact-checked content.

---

## 🚀 **Features**

- ✅ **100-Lesson Curriculum** - Complete AI/ML course (Basics → Advanced)
- ✅ **2D Animated Teacher** - "Seekho Bot" mascot that lip-syncs, blinks, waves and points
- ✅ **Karaoke Captions** - word-by-word highlighted speech bubble, synced to the voice
- ✅ **Professional Animations** - 10 scene types (hook, bullets, flow, compare, network, code, stat, formula, takeaway, cta)
- ✅ **Fact-Checked Content** - Multi-agent AI verification (3-stage validation)
- ✅ **A/B Tested Hooks** - Generates 2 versions, picks more engaging one
- ✅ **Parallel Processing** - 5-7× faster voice generation (3-4 min total)
- ✅ **Smart Pacing** - Complex scenes get +0.3s pause for better learning
- ✅ **Language Modes** - Hinglish (default), English-only, or Pure Hindi
- ✅ **Indian Voice** - en-IN-PrabhatNeural (perfect Hinglish pronunciation)
- ✅ **Reliable Scheduling** - Made the night before, posted at exactly 8 AM IST, never twice
- ✅ **100% Free** - No paid APIs (Groq + Gemini)

**New (Nov 2026):** Upgraded with ViMax-inspired architecture (see `VIMAX_UPGRADES.md`)

---

## 📂 **Project Structure**

```
cartoon-bot/
├── .github/workflows/
│   ├── daily.yml          # Makes the reel the night before + backups, posts at 08:00 IST
│   ├── post.yml           # Light poster: publishes the queued reel exactly at the slot
│   └── check.yml          # Offline render test on every push + manual service check
│
├── cartoon-bot/src/
│   ├── lesson_main.py     # Generator entry point (slot-aware, runs once per day)
│   ├── publisher.py       # The ONLY Instagram posting path (slot timing, lock, dedupe)
│   ├── post_pending.py    # Poster entry point
│   ├── slots.py           # Posting-slot maths (POST_TIME / TIMEZONE)
│   ├── syllabus.py        # 100-lesson curriculum + weekend fun facts
│   ├── lesson_script.py   # AI script writer + fact-checker
│   ├── llm.py             # Gemini / Groq with fail-fast fallback
│   ├── edu_render.py      # 2D animation engine (scenes, captions, transitions)
│   ├── mascot.py          # "Seekho Bot" 2D cartoon teacher (lip-sync, blinks, gestures)
│   ├── soundtrack.py      # One continuous audio track + ducked music bed + lip-sync levels
│   ├── voice.py           # Edge TTS with word timings
│   ├── instagram.py / storage.py / notify.py / config.py / util.py
│   └── check.py           # Pre-flight check of every service
├── cartoon-bot/tests/offline_test.py   # No-keys render + schedule tests
└── refresh_token.sh       # Token refresh (reads secrets from env, never hard-code them)
```

---

## ⚙️ **Setup**

### **1. GitHub Secrets** (Required)

Set these in: Settings → Secrets and variables → Actions → New secret

```bash
GROQ_API_KEY=your_groq_key          # AI writer (at least one of Groq / Gemini)
GEMINI_API_KEY=your_gemini_key
IG_USER_ID=your_instagram_user_id
IG_ACCESS_TOKEN=your_instagram_token
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
SUPABASE_BUCKET=cartoon-reels       # must be a PUBLIC bucket
TELEGRAM_BOT_TOKEN=your_bot_token   # previews + /post /postnow /skip commands
TELEGRAM_CHAT_ID=your_chat_id
```

### **2. GitHub Variables** (Optional)

Settings → Secrets and variables → Actions → Variables

```bash
REVIEW_MODE=auto          # auto | auto_unless_skip | approve
POST_TIME=08:00           # daily posting time (24h)
TIMEZONE=Asia/Kolkata
REVIEW_HOURS=2            # auto_unless_skip: minimum time to /skip after the preview
MASCOT=true               # animated 2D teacher character
MUSIC=true                # soft background music (drop your own .mp3 in cartoon-bot/assets/music)
LANGUAGE_MODE=hinglish    # hinglish | english_only | hindi_only
```

---

## 🎯 **How It Works**

### **Scheduling (why it now really posts at 8 AM)**

GitHub's cron is best-effort: the old single `08:00` trigger was routinely **hours late** (e.g. it started at
15:03 IST) and most 30-minute post triggers were skipped. So the bot no longer renders *at* 8 AM:

1. **20:17 IST (night before)** – `daily.yml` makes tomorrow's reel and queues it for **08:00** (backups at
   22:53, 02:41 and 05:23 IST; each later run sees the reel is already queued and exits in seconds).
2. You get a **Telegram preview** of the video the evening before.
3. **From ~02:30 IST** – any `post.yml` (every 20 min) or backup run that starts within 5.5 h of the slot
   **stays alive and publishes at exactly 08:00**.
4. If everything is late, the reel still posts as soon as a run happens (up to 10 h after the slot).
5. **Never twice:** one reel per slot (keyed by date), a storage lock, and a check of the account's latest
   posts before publishing. History is written only after a successful post.

Telegram commands: `/post` (approve for the slot), `/postnow` (publish immediately), `/skip` (discard).
Manual runs: **Daily AIVerse reel → post_now** makes and posts one right away; **Post approved reel →
force_post** publishes the queued reel now.

### **Content pipeline**

1. **Pick topic** – weekday of the *posting* day = next lesson, weekend = AI fun fact
2. **Write + fact-check** – A/B-tested hook, second AI verifies accuracy
3. **Voice** – Indian voice with **word-level timings**
4. **Soundtrack** – one continuous track + generated music bed ducked under the voice (−14 LUFS)
5. **2D animation** – single-pass render: animated scenes, **Seekho Bot** mascot lip-syncing the narration,
   karaoke speech-bubble captions, crossfade transitions, cover frame
6. **Queue → post at the slot → Telegram confirmation**

---

## 🎙️ **Voice Configuration**

The narration uses the most human-sounding provider available, with automatic fallback (one voice per reel):

| Provider | Sound | Cost | Turn on |
|---|---|---|---|
| **ElevenLabs** | most human | paid (commercial use needs a paid plan) | secret `ELEVENLABS_API_KEY` (+ optional variable `ELEVENLABS_VOICE_ID`) |
| **Gemini TTS** (default) | natural, expressive, directed like an actor | free with `GEMINI_API_KEY` | on by default |
| Edge (`hi-IN-MadhurNeural`) | clearly synthetic | free | automatic safety net |

```bash
GEMINI_VOICE=Charon              # Orus, Fenrir, Iapetus, Alnilam, Sadaltager ... (listen: Pre-flight check -> voice_samples)
GEMINI_SPEAK_DEVANAGARI=false    # Hinglish: voice reads Roman text (false) or a Devanagari copy (true)
TTS_PROVIDER=auto                # or force: elevenlabs | gemini | edge
```

Captions always show the script's own words, time-aligned to the voice.

### **Language Modes** (NEW)

Switch between languages with one environment variable:

```bash
# GitHub: Settings → Variables → LANGUAGE_MODE
LANGUAGE_MODE=hinglish       # Default (Indian voice)
LANGUAGE_MODE=english_only   # Clear English (US voice)
LANGUAGE_MODE=hindi_only     # Pure Hindi (Hindi voice)
```

`english_only` switches everything: script, on-screen labels, captions, hashtags and the voice's accent direction.


⚠️ **Never use US/UK voices for Hinglish** - they butcher Hindi words!

---

## 📅 **Weekly Content Plan**

| Day | Content | Comment keyword -> auto-reply sends |
|---|---|---|
| Mon / Wed / Fri | Course lesson (#1, #2, ...) | `NOTES` -> revision notes |
| Tue / Thu / Sat | **AI Trick of the Day** (practical, most shareable; animated chat demo) | `PROMPT` -> the exact prompt/steps |
| Sun | AI fun fact | `AI` -> one more fact |

Change it with the variable `CONTENT_PLAN` (e.g. `mon:lesson,tue:trick,...`). Every script opens with a
result-first hook. Manual runs: **Daily AIVerse reel** -> `content` (lesson/trick/fun_fact), `dry_run`
(Telegram preview only), `post_now`, `fresh_start` (restart at Lesson #1, history backed up).

## 💰 **Monetization & Growth**

- **YouTube Shorts cross-post** (YouTube shares Shorts ad revenue - the main money path in India):
  1. Google Cloud console -> new project -> enable **YouTube Data API v3** -> OAuth consent screen (External,
     publish it) -> Credentials -> **OAuth client ID (Desktop app)**.
  2. On your computer: `python cartoon-bot/tools/youtube_auth.py CLIENT_ID CLIENT_SECRET` (saves the secrets).
  3. ⚠️ Google keeps API uploads from an **unverified** project **private** until it passes the free
     [YouTube API compliance audit](https://support.google.com/youtube/contact/yt_api_form). Apply once; until then
     set variable `YT_PRIVACY=private` and publish manually, or keep it and wait for approval.
- **Analytics + learning loop** (`engage.yml`, every 4 h): views/reach/likes/comments/shares/saves per reel; the
  script writer learns from your best hooks. Needs token permission **`instagram_manage_insights`**.
- **Auto-replies** to genuine comments in the viewer's language (spam/links/politics skipped, max 12 per run,
  never twice). Needs **`instagram_manage_comments`**. Turn off with variable `AUTO_REPLY=false`.
- **Weekly report** on Telegram every Sunday evening (or run *Grow channel -> force_report*).
- **SEO captions**: searchable hook headline, save/share/comment prompts, 5 topic hashtags + brand tags.

Instagram's own payouts (gifts, subscriptions, bonuses) need eligibility (followers, age, region); brand deals
follow audience size, so consistency + shares/saves matter most.

## 🎨 **Animation Types**

The bot uses 10 professional scene types:

1. **hook** - Opening question with emoji + pulsing rings
2. **bullets** - Animated bullet point lists
3. **flow** - Step-by-step process flows with arrows
4. **compare** - Side-by-side comparisons (left vs right)
5. **network** - Neural network visualizations with nodes
6. **code** - Syntax-highlighted Python code
7. **stat** - Big number/statistic displays
8. **formula** - Mathematical formulas
9. **takeaway** - Key points summary
10. **cta** - Call-to-action with follow button

---

## 🔧 **Maintenance**

### **Refresh Instagram Token (Every 60 Days)**

```bash
# Step 1: Generate new token
# Go to: https://developers.facebook.com/tools/explorer
# Select your app → Get User Access Token
# Permissions: instagram_basic, instagram_content_publish

# Step 2: Convert to long-lived token
bash refresh_token.sh

# Step 3: Update GitHub secret
gh secret set IG_ACCESS_TOKEN --body "YOUR_NEW_TOKEN"
```

See `GET_NEW_TOKEN.md` for detailed instructions.

### **Manual Trigger**

```bash
# Trigger workflow manually
gh workflow run daily.yml

# Check status
gh run list --limit 5

# View logs
gh run view <run_id> --log
```

---

## 📊 **Monitoring**

- **GitHub Actions**: https://github.com/YOUR_USERNAME/cartoon-bot/actions
- **Instagram**: @aiverse.daily16
- **Telegram**: Notifications for success/failure

---

## 🐛 **Troubleshooting**

### **Token Expired**
```bash
# Error: "Session has expired"
# Solution: Refresh Instagram token (see above)
```

### **Gemini Quota Exhausted**
```bash
# Error: 429 quota exceeded
# Solution: Wait 24 hours or add more API keys
```

### **Voice Generation Fails**
```bash
# Has automatic retry (4 attempts)
# Usually resolves itself
```

### **Graphics Glitches**
```bash
# All safety checks added in edu_render.py
# Should not occur anymore
```

---

## 📝 **Content Quality**

### **Fact-Checking Process**

1. AI writes script based on verified curriculum facts
2. Second AI reviews for accuracy
3. Checks formulas, code, analogies
4. Rejects if any errors found
5. Up to 4 attempts to get it right
6. **Bot will NOT post misinformation**

### **Curriculum**

- **Lessons 1-30**: Basics (AI fundamentals, ML, neural networks)
- **Lessons 31-70**: Intermediate (Python, models, CNNs, NLP)
- **Lessons 71-100**: Advanced (Transformers, LLMs, agents)
- **Weekends**: Fun AI facts

---

## 🎯 **Tech Stack**

- **Languages**: Python 3.11
- **Animation**: PIL/Pillow, NumPy
- **Voice**: Edge-TTS (Microsoft voices)
- **Video**: FFmpeg
- **AI**: Groq (primary), Gemini (backup)
- **Storage**: Supabase
- **Posting**: Instagram Graph API
- **Automation**: GitHub Actions
- **Notifications**: Telegram

---

## 📄 **Documentation**

- **Quick Reference**: `QUICK_REFERENCE.md` - Common tasks & troubleshooting
- **ViMax Upgrades**: `VIMAX_UPGRADES.md` - Technical details on improvements
- **Instagram Setup**: `INSTAGRAM_TOKEN_GUIDE.md` - Token management
- **Complete Guide**: `UPGRADE_COMPLETE.md` - Full documentation

---

## 📄 **License**

This project is for educational purposes.

---

## 🙏 **Credits**

- Animation system: Professional edu_render engine
- Curriculum: 100 verified AI/ML lessons
- Voice: Microsoft Edge TTS
- Architecture: Inspired by ViMax (HKUDS) - https://arxiv.org/abs/2606.07649

---

**Bot is fully operational - posts automatically every day at 8 AM IST!** 🚀

**Performance:** 3-4 min generation time | 90% script quality | 100% free APIs

For detailed documentation, see `QUICK_REFERENCE.md` or `UPGRADE_COMPLETE.md`
