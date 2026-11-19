# 📑 AIVerse Bot - Project Index

Quick navigation to all documentation and tools.

---

## 🚀 Start Here

### New to the Project?
1. **[AUTOMATION_SUMMARY.txt](AUTOMATION_SUMMARY.txt)** ⭐
   - Visual overview of what's running
   - Quick commands
   - System status at a glance

2. **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** ⭐
   - Everything that's automated
   - What happens next
   - Your action items

3. **[README.md](README.md)**
   - Project overview
   - Features and tech stack
   - Basic setup instructions

### Want to Manage the Bot?
1. **Interactive Menu** ⭐ `./quick-commands.sh`
   - 20+ commands in easy menu
   - Status checks, triggers, testing

2. **Live Dashboard** ⭐ `./dashboard.sh`
   - Real-time system health
   - Recent workflow runs
   - Health score calculation

3. **[AUTOMATION_STATUS.md](AUTOMATION_STATUS.md)** ⭐
   - Complete automation guide
   - All workflows explained
   - Configuration reference
   - Troubleshooting

---

## 📚 Documentation

### Core Guides
| File | Description | When to Read |
|------|-------------|--------------|
| [README.md](README.md) | Project overview & features | First time setup |
| [SETUP_COMPLETE.md](SETUP_COMPLETE.md) | Setup summary & next steps | After deployment |
| [AUTOMATION_STATUS.md](AUTOMATION_STATUS.md) | Complete automation guide | Managing the bot |
| [AUTOMATION_SUMMARY.txt](AUTOMATION_SUMMARY.txt) | Visual quick reference | Daily reference |
| [DASHBOARD.md](DASHBOARD.md) | System metrics & status | Monitoring |

### Specialized Guides
| File | Description | When to Read |
|------|-------------|--------------|
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Common tasks & commands | Troubleshooting |
| [GET_NEW_TOKEN.md](GET_NEW_TOKEN.md) | Instagram token refresh | Every 60 days |
| [INSTAGRAM_TOKEN_GUIDE.md](INSTAGRAM_TOKEN_GUIDE.md) | Meta/Instagram setup | Initial setup |
| [VIMAX_UPGRADES.md](VIMAX_UPGRADES.md) | Technical architecture | Understanding code |
| [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) | Implementation details | Deep dive |
| [UPGRADE_COMPLETE.md](UPGRADE_COMPLETE.md) | Full documentation | Reference |

### Workflow Documentation
| Workflow | File | Description |
|----------|------|-------------|
| Daily Reel | [.github/workflows/daily.yml](.github/workflows/daily.yml) | Content generation |
| Posting | [.github/workflows/post.yml](.github/workflows/post.yml) | Scheduled posting |
| Engagement | [.github/workflows/engage.yml](.github/workflows/engage.yml) | Comment replies |
| Weekly Video | [.github/workflows/weekly.yml](.github/workflows/weekly.yml) | YouTube compilation |
| Testing | [.github/workflows/check.yml](.github/workflows/check.yml) | Pre-flight checks |

---

## 🛠️ Management Tools

### Interactive Tools
```bash
./quick-commands.sh       # Interactive menu (20+ commands)
./dashboard.sh            # Live system status
./dashboard.sh update     # Update DASHBOARD.md
```

### Scripts
| Script | Description | Usage |
|--------|-------------|-------|
| [quick-commands.sh](quick-commands.sh) | Interactive management menu | `./quick-commands.sh` |
| [dashboard.sh](dashboard.sh) | Live status dashboard | `./dashboard.sh` |
| [refresh_token.sh](refresh_token.sh) | Instagram token refresh | `bash refresh_token.sh` |

### GitHub CLI Commands
```bash
# Status
gh workflow list                    # All workflows
gh run list --limit 10              # Recent runs
gh run view --log                   # View logs

# Trigger
gh workflow run daily.yml           # Generate reel
gh workflow run post.yml            # Post reel
gh workflow run engage.yml          # Run engagement

# Config
gh secret list                      # View secrets
gh variable list                    # View variables
```

---

## 🤖 Source Code

### Main Application
```
cartoon-bot/src/
├── lesson_main.py      # Main entry point (content generation)
├── post_pending.py     # Posting entry point
├── publisher.py        # Instagram/YouTube posting
├── slots.py            # Scheduling logic
├── syllabus.py         # 100-lesson curriculum
├── lesson_script.py    # AI script generation
├── edu_render.py       # 2D animation engine
├── mascot.py           # Animated teacher character
├── soundtrack.py       # Audio mixing
├── voice.py            # TTS generation
├── llm.py              # AI API integration
├── instagram.py        # Instagram API
├── youtube.py          # YouTube API
├── storage.py          # Supabase storage
├── notify.py           # Telegram notifications
└── config.py           # Configuration
```

### Tools
```
cartoon-bot/tools/
├── youtube_auth.py         # YouTube OAuth setup
├── ig_admin.py            # Instagram admin commands
├── yt_admin.py            # YouTube admin commands
├── status_report.py       # Generate reports
├── voice_samples.py       # Test voices
├── yt_upload_check.py     # Test YouTube upload
└── make_prompt_pack.py    # Build prompt PDF
```

### Tests
```
cartoon-bot/tests/
└── offline_test.py        # No-API render test
```

---

## 📋 Workflows Reference

### Daily Content Generation
**File**: [.github/workflows/daily.yml](.github/workflows/daily.yml)

**Schedule**: Multiple times daily
- 20:17 IST (main - makes tomorrow's reel)
- 22:53 IST (backup)
- 02:41 IST (backup, waits for 08:00)
- 05:23 IST (last backup)
- 08:17 IST (makes 19:00 reel)
- More backups throughout day

**What it does**:
1. Picks next lesson/trick/news
2. Generates AI script with fact-checking
3. Creates voice narration
4. Renders 2D animated video
5. Queues for posting
6. Sends Telegram preview

**Manual Trigger**:
```bash
# Standard run
gh workflow run daily.yml

# Post immediately
gh workflow run daily.yml --field post_now=true

# Test mode (no posting)
gh workflow run daily.yml --field dry_run=true

# Specific content type
gh workflow run daily.yml --field content=lesson

# Re-make even if queued
gh workflow run daily.yml --field force_new=true

# Fresh start (reset to Lesson 1)
gh workflow run daily.yml --field fresh_start=true
```

### Automated Posting
**File**: [.github/workflows/post.yml](.github/workflows/post.yml)

**Schedule**: Every 20 minutes (`:04`, `:24`, `:44`)

**What it does**:
1. Checks for queued reel
2. Waits until exact slot time
3. Posts to Instagram
4. Cross-posts to YouTube
5. Sends confirmation

**Manual Trigger**:
```bash
# Force post queued reel NOW
gh workflow run post.yml --field force_post=true
```

### Channel Growth
**File**: [.github/workflows/engage.yml](.github/workflows/engage.yml)

**Schedule**: Every hour (`:37`)

**What it does**:
1. Refreshes reel statistics
2. Replies to comments (AI-powered)
3. Sends weekly report (Sundays)
4. Updates analytics

**Manual Trigger**:
```bash
# Force weekly report now
gh workflow run engage.yml --field force_report=true
```

### Weekly Compilation
**File**: [.github/workflows/weekly.yml](.github/workflows/weekly.yml)

**Schedule**: Sunday 20:53 IST

**What it does**:
1. Collects week's reels
2. Stitches into 16:9 video
3. Adds chapters
4. Uploads to YouTube
5. Heartbeat commit

**Manual Trigger**:
```bash
# Make weekly video now
gh workflow run weekly.yml --field force=true
```

### Pre-flight Testing
**File**: [.github/workflows/check.yml](.github/workflows/check.yml)

**Triggers**:
- Every push to main (auto)
- Manual with options

**Manual Options**:
```bash
# Test AI image generation
gh workflow run check.yml --field image_test=true

# Status report
gh workflow run check.yml --field status_report=true

# Instagram admin
gh workflow run check.yml --field ig_admin="post-lesson 1"

# YouTube admin
gh workflow run check.yml --field yt_admin="delete ID"

# Test YouTube upload
gh workflow run check.yml --field youtube_test=true

# Voice samples
gh workflow run check.yml --field voice_samples=true
```

---

## ⚙️ Configuration Reference

### Required Secrets
```bash
GEMINI_API_KEY          # Gemini AI (content generation)
GROQ_API_KEY            # Groq AI (alternative)
IG_USER_ID              # Instagram user ID
IG_ACCESS_TOKEN         # Instagram long-lived token (60 days)
SUPABASE_URL            # Supabase project URL
SUPABASE_SERVICE_KEY    # Supabase service role key
SUPABASE_BUCKET         # Storage bucket name (must be PUBLIC)
TELEGRAM_BOT_TOKEN      # Telegram bot token
TELEGRAM_CHAT_ID        # Your Telegram chat ID
YT_CLIENT_ID            # YouTube OAuth client ID
YT_CLIENT_SECRET        # YouTube OAuth client secret
YT_REFRESH_TOKEN        # YouTube refresh token
```

### Optional Secrets
```bash
ELEVENLABS_API_KEY      # ElevenLabs TTS (premium voice)
HF_TOKEN                # Hugging Face (AI models)
FAL_API_KEY             # Fal.ai (AI services)
APIFY_TOKEN             # Apify (web scraping for news)
```

### Variables
```bash
# Posting
REVIEW_MODE             # auto | auto_unless_skip | approve
POST_TIME               # Default: 08:00
POST_TIMES              # Default: 08:00,19:00
TIMEZONE                # Default: Asia/Kolkata
REVIEW_HOURS            # Default: 2

# Content
SERIES_NAME             # Default: AIVerse
LANGUAGE_MODE           # hinglish | english_only | hindi_only
MASCOT                  # true | false (2D animated teacher)
MUSIC                   # true | false (background music)
CONTENT_PLAN            # Morning content type
CONTENT_PLAN_PM         # Evening content type

# Voice
TTS_PROVIDER            # auto | elevenlabs | gemini | edge
GEMINI_VOICE            # Charon | Orus | Fenrir | Iapetus | etc.
GEMINI_SPEAK_DEVANAGARI # false | true
VOICE_NAME              # Edge TTS voice name
VOICE_PITCH             # Default: -6Hz
VOICE_RATE              # Default: -3%
VOICE_FX                # true | false

# YouTube
YT_PRIVACY              # public | unlisted | private
FB_PAGE_ID              # Facebook page for cross-posting

# Growth
AUTO_REPLY              # true | false (auto comment replies)

# Night Shift (advanced)
NS_NICHE                # Night Shift content niche
NS_HANDLE               # Instagram handle for Night Shift
```

---

## 🔍 Quick Lookup

### Common Tasks

#### Check Status
```bash
./dashboard.sh                          # Full dashboard
gh run list --limit 10                  # Recent runs
gh workflow list                        # All workflows
gh run view --log                       # Latest logs
```

#### Make Content
```bash
# Make and post immediately
gh workflow run daily.yml --field post_now=true

# Test without posting
gh workflow run daily.yml --field dry_run=true

# Specific content type
gh workflow run daily.yml --field content=lesson
```

#### Posting
```bash
# Force post queued reel
gh workflow run post.yml --field force_post=true

# Via Telegram
/post       # Approve for scheduled time
/postnow    # Post immediately
/skip       # Discard reel
```

#### Testing
```bash
# Pre-flight check
gh workflow run check.yml

# Voice samples
gh workflow run check.yml --field voice_samples=true

# AI image test
gh workflow run check.yml --field image_test=true

# Offline test (local, no APIs)
python cartoon-bot/tests/offline_test.py
```

#### Configuration
```bash
# View
gh secret list
gh variable list

# Update secret
echo "new-key" | gh secret set SECRET_NAME

# Update variable
gh variable set VAR_NAME --body "value"
```

#### Monitoring
```bash
# Live run
gh run watch

# Failed runs
gh run list --status failure

# Specific workflow
gh run list --workflow daily.yml --limit 5
```

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  GitHub Actions                      │
│  ┌──────────────────────────────────────────────┐  │
│  │  Daily Workflow (20:17 IST)                  │  │
│  │  ┌────────────────────────────────────────┐  │  │
│  │  │ 1. Pick Content (Lesson/Trick/News)   │  │  │
│  │  │ 2. Generate Script (Gemini/Groq)      │  │  │
│  │  │ 3. Fact-Check (3-stage validation)    │  │  │
│  │  │ 4. Create Voice (Gemini TTS)          │  │  │
│  │  │ 5. Render Video (2D Animation)        │  │  │
│  │  │ 6. Upload to Supabase                 │  │  │
│  │  │ 7. Queue for Posting                  │  │  │
│  │  └────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  Post Workflow (Every 20 min)                │  │
│  │  ┌────────────────────────────────────────┐  │  │
│  │  │ 1. Check for Queued Reel              │  │  │
│  │  │ 2. Wait Until Slot Time (08:00/19:00) │  │  │
│  │  │ 3. Post to Instagram                  │  │  │
│  │  │ 4. Cross-post to YouTube Shorts       │  │  │
│  │  │ 5. Send Confirmation                  │  │  │
│  │  └────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  Engage Workflow (Hourly)                    │  │
│  │  ┌────────────────────────────────────────┐  │  │
│  │  │ 1. Refresh Statistics                 │  │  │
│  │  │ 2. Reply to Comments (AI)             │  │  │
│  │  │ 3. Track Analytics                    │  │  │
│  │  │ 4. Weekly Report (Sundays)            │  │  │
│  │  └────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │Instagram │     │ YouTube  │     │ Telegram │
  │  Reels   │     │ Shorts   │     │   Bot    │
  └──────────┘     └──────────┘     └──────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │   Supabase   │
                  │   Storage    │
                  └──────────────┘
```

---

## 🎓 Learning Resources

### Understanding the Bot
1. [README.md](README.md) - Feature overview
2. [VIMAX_UPGRADES.md](VIMAX_UPGRADES.md) - Architecture
3. [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) - Implementation details

### Managing Workflows
1. [AUTOMATION_STATUS.md](AUTOMATION_STATUS.md) - Complete guide
2. [.github/workflows/](./github/workflows/) - Workflow files
3. `./dashboard.sh` - Live monitoring

### Troubleshooting
1. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common issues
2. `gh run view --log` - Error logs
3. Telegram bot - Real-time alerts

---

## 📞 Support & Contact

### Built-in Help
- **Dashboard**: `./dashboard.sh`
- **Interactive Menu**: `./quick-commands.sh`
- **Documentation**: All files in this index

### Real-time Monitoring
- **Telegram Bot**: Instant notifications
- **GitHub Actions**: https://github.com/PranavNayee/aiverse-bot/actions
- **Workflow Logs**: `gh run view --log`

### Emergency
```bash
# Stop posting
gh workflow disable post.yml

# Resume posting
gh workflow enable post.yml

# Force post
gh workflow run post.yml --field force_post=true
```

---

## 🎯 Quick Navigation

**Getting Started**:
- [AUTOMATION_SUMMARY.txt](AUTOMATION_SUMMARY.txt) - Visual overview
- [SETUP_COMPLETE.md](SETUP_COMPLETE.md) - What's running now
- [README.md](README.md) - Project overview

**Daily Use**:
- `./dashboard.sh` - Check status
- `./quick-commands.sh` - Run commands
- [AUTOMATION_STATUS.md](AUTOMATION_STATUS.md) - Reference guide

**Maintenance**:
- [GET_NEW_TOKEN.md](GET_NEW_TOKEN.md) - Token refresh
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Troubleshooting
- `gh run view --log` - Debug issues

---

**📚 Full Documentation Map**

```
📑 INDEX.md (you are here)
├── 🚀 Quick Start
│   ├── AUTOMATION_SUMMARY.txt
│   ├── SETUP_COMPLETE.md
│   └── README.md
├── 🛠️ Management
│   ├── quick-commands.sh
│   ├── dashboard.sh
│   └── AUTOMATION_STATUS.md
├── 📖 Guides
│   ├── QUICK_REFERENCE.md
│   ├── GET_NEW_TOKEN.md
│   ├── INSTAGRAM_TOKEN_GUIDE.md
│   └── VIMAX_UPGRADES.md
├── 🔧 Workflows
│   ├── daily.yml
│   ├── post.yml
│   ├── engage.yml
│   ├── weekly.yml
│   └── check.yml
└── 💻 Source Code
    ├── cartoon-bot/src/
    ├── cartoon-bot/tools/
    └── cartoon-bot/tests/
```

---

**Last Updated**: November 19, 2026  
**Repository**: https://github.com/PranavNayee/aiverse-bot  
**Status**: 🟢 Fully Operational
