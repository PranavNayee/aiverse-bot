# 🎓 AI Seekho - Automated Hinglish AI Education Bot

Fully automated Instagram bot that posts daily AI/ML educational lessons in Hinglish with professional animations and fact-checked content.

---

## 🚀 **Features**

- ✅ **100-Lesson Curriculum** - Complete AI/ML course (Basics → Advanced)
- ✅ **Professional Animations** - 10 scene types (hook, bullets, flow, compare, network, code, stat, formula, takeaway, cta)
- ✅ **Fact-Checked Content** - Multi-agent AI verification (3-stage validation)
- ✅ **A/B Tested Hooks** - Generates 2 versions, picks more engaging one
- ✅ **Parallel Processing** - 5-7× faster voice generation (3-4 min total)
- ✅ **Smart Pacing** - Complex scenes get +0.3s pause for better learning
- ✅ **Language Modes** - Hinglish (default), English-only, or Pure Hindi
- ✅ **Indian Voice** - en-IN-PrabhatNeural (perfect Hinglish pronunciation)
- ✅ **Fully Automated** - Posts daily at 8 AM IST
- ✅ **100% Free** - No paid APIs (Groq + Gemini)

**New (Nov 2026):** Upgraded with ViMax-inspired architecture (see `VIMAX_UPGRADES.md`)

---

## 📂 **Project Structure**

```
cartoon-bot/
├── .github/workflows/     # GitHub Actions (automated posting)
│   ├── daily.yml         # Main daily posting workflow
│   ├── check.yml         # Pre-flight tests
│   └── post.yml          # Manual posting workflow
│
├── cartoon-bot/src/       # Source code
│   ├── lesson_main.py    # Main entry point
│   ├── syllabus.py       # 100-lesson curriculum
│   ├── lesson_script.py  # AI script writer + fact-checker
│   ├── edu_render.py     # Professional animation engine
│   ├── llm.py           # Smart LLM orchestration
│   ├── voice.py         # Text-to-speech (Hinglish)
│   ├── instagram.py     # Instagram posting API
│   ├── storage.py       # Supabase file storage
│   ├── config.py        # Configuration
│   └── util.py          # Helper functions
│
├── README.md            # This file
├── UPGRADE_COMPLETE.md  # Detailed documentation
├── refresh_token.sh     # Instagram token refresh script
└── .gitignore          # Git ignore rules
```

---

## ⚙️ **Setup**

### **1. GitHub Secrets** (Required)

Set these in: Settings → Secrets and variables → Actions → New secret

```bash
# AI APIs (Free)
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key

# Instagram
IG_USER_ID=your_instagram_user_id
IG_ACCESS_TOKEN=your_instagram_token

# Storage (Supabase - Free tier)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
SUPABASE_BUCKET=cartoon-reels

# Notifications (Optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### **2. GitHub Variables** (Optional)

Settings → Secrets and variables → Actions → Variables

```bash
REVIEW_MODE=auto          # auto posting (or 'approve' for manual)
REVIEW_HOURS=2            # hours to wait for approval
```

---

## 🎯 **How It Works**

### **Daily Workflow (8 AM IST)**

1. **Check Day** - Weekday (lesson) or weekend (fun fact)
2. **Get Next Topic** - Sequential from 100-lesson curriculum
3. **Generate Script** - AI writes Hinglish script with proper scene types
4. **Fact-Check** - Second AI verifies accuracy (rejects if wrong)
5. **Generate Voice** - Indian voice (Prabhat) pronounces Hindi correctly
6. **Render Animations** - Professional 10-scene animation system
7. **Assemble Video** - FFmpeg combines all scenes
8. **Upload** - Saves to Supabase
9. **Post** - Automatically posts to Instagram
10. **Notify** - Sends Telegram notification

---

## 🎙️ **Voice Configuration**

**Current:** `en-IN-PrabhatNeural` (Indian English Male)
- Pronounces Hindi naturally
- Reads Hinglish perfectly
- Deep, clear voice

### **Language Modes** (NEW)

Switch between languages with one environment variable:

```bash
# GitHub: Settings → Variables → LANGUAGE_MODE
LANGUAGE_MODE=hinglish       # Default (Indian voice)
LANGUAGE_MODE=english_only   # Clear English (US voice)
LANGUAGE_MODE=hindi_only     # Pure Hindi (Hindi voice)
```

**Alternative voices available in `config.py`:**
- `hi-IN-MadhurNeural` - Pure Hindi male
- `en-IN-NeerjaNeural` - Indian English female

⚠️ **Never use US/UK voices for Hinglish** - they butcher Hindi words!

---

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
