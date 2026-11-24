# 🤖 AIVerse Bot - Automation Status & Guide

**Status**: ✅ **FULLY OPERATIONAL** 
**Repository**: https://github.com/PranavNayee/aiverse-bot
**Last Updated**: November 19, 2026

---

## 📊 Current Status

### ✅ Active Workflows
- **Daily AIVerse Reel** - 141 total runs, currently running
- **Post Approved Reel** - Active, posting schedule
- **Grow Channel** - Active, engagement automation
- **Weekly Long Video** - Active, Sunday compilations
- **Pre-flight Check** - Active, testing

### ✅ Configured Secrets (14 total)
All required secrets are configured:
- ✅ `GEMINI_API_KEY` - AI content generation
- ✅ `GROQ_API_KEY` - AI processing
- ✅ `IG_USER_ID` - Instagram posting
- ✅ `IG_ACCESS_TOKEN` - Instagram auth
- ✅ `SUPABASE_URL` - Storage backend
- ✅ `SUPABASE_SERVICE_KEY` - Storage auth
- ✅ `SUPABASE_BUCKET` - Media storage
- ✅ `TELEGRAM_BOT_TOKEN` - Notifications
- ✅ `TELEGRAM_CHAT_ID` - Notification target
- ✅ `YT_CLIENT_ID` - YouTube posting
- ✅ `YT_CLIENT_SECRET` - YouTube auth
- ✅ `YT_REFRESH_TOKEN` - YouTube refresh
- ✅ `HF_TOKEN` - Hugging Face (optional)
- ✅ `FAL_API_KEY` - AI services (optional)

### ✅ Configured Variables
- `REVIEW_MODE`: `auto` (posts automatically)

---

## 🔄 Automated Workflows

### 1️⃣ Daily Content Generation
**Workflow**: `daily.yml` - "Daily AIVerse Reel"

**Schedule**:
- **20:17 IST** (Main) - Makes tomorrow's reel
- **22:53 IST** (Backup)
- **02:41 IST** (Backup, waits for 08:00)
- **05:23 IST** (Last backup)
- **08:17 IST** - Makes 19:00 reel
- **Multiple backups** throughout day

**What it does**:
1. Picks next lesson from 100-lesson curriculum
2. Generates AI script with fact-checking
3. Creates voice narration with Indian accent
4. Renders 2D animated video with mascot
5. Queues for posting at scheduled time
6. Sends Telegram preview

**Manual Trigger Options**:
```bash
# Run workflow with options
gh workflow run daily.yml \
  --field post_now=true \          # Post immediately
  --field force_new=true \         # Re-make if already queued
  --field content=lesson \         # Type: lesson|trick|news|alert|photo|fun_fact
  --field dry_run=true \           # Test mode (Telegram only)
  --field youtube_preview=true     # Upload to YouTube as private
```

### 2️⃣ Automated Posting
**Workflow**: `post.yml` - "Post approved reel"

**Schedule**: Every 20 minutes (handles GitHub scheduling delays)
- Runs at `:04`, `:24`, `:44` of every hour
- Sleeps and posts exactly at scheduled time (08:00 IST by default)
- Never posts twice (storage lock + account check)

**Safety Features**:
- Duplicate post prevention
- Slot-based timing
- Retry limits
- Approval system

**Manual Posting**:
```bash
# Force post queued reel immediately
gh workflow run post.yml --field force_post=true
```

### 3️⃣ Channel Growth
**Workflow**: `engage.yml` - "Grow channel"

**Schedule**: Every hour (`:37` past the hour)

**What it does**:
1. Refreshes reel statistics (views, likes, comments, shares)
2. Replies to genuine comments automatically
3. Sends weekly report (Sundays)
4. Updates analytics for learning loop

**Features**:
- AI-powered comment responses
- Spam/link filtering
- Multi-language support
- Comment keyword triggers (NOTES, PROMPT, NEWS, AI)

**Manual Trigger**:
```bash
# Force weekly report
gh workflow run engage.yml --field force_report=true
```

### 4️⃣ Weekly Compilation
**Workflow**: `weekly.yml` - "Weekly long video"

**Schedule**: Sunday 20:53 IST

**What it does**:
1. Collects week's reels from storage
2. Stitches into 16:9 YouTube video
3. Adds chapters and timestamps
4. Uploads "This Week in AI" video
5. Heartbeat commit (keeps workflows active)

**Manual Trigger**:
```bash
# Make weekly video now
gh workflow run weekly.yml --field force=true
```

### 5️⃣ Pre-flight Testing
**Workflow**: `check.yml` - "Pre-flight check"

**Triggers**:
- Every push to `main` (auto-test)
- Manual with options

**Manual Options**:
```bash
gh workflow run check.yml \
  --field image_test=true \        # Test AI image generation
  --field status_report=true \     # Print stats
  --field ig_admin="post-lesson 1" # Instagram admin
  --field yt_admin="delete ID" \   # YouTube admin
  --field youtube_test=true \      # Test YouTube upload
  --field voice_samples=true       # Render voice samples
```

---

## 🎯 Content Schedule

### Two Posts Per Day (08:00 & 19:00 IST)

| Day | Morning (08:00) | Evening (19:00) |
|-----|----------------|-----------------|
| **Mon/Wed/Fri** | Course Lesson | AI Trick |
| **Tue/Thu/Sat** | AI Trick | AI News |
| **Sunday** | AI Fun Fact | AI Trick + Weekly Video |

### Content Types
- **Lessons** (1-100): Structured AI/ML curriculum
- **Tricks**: Quick practical tips
- **News**: Latest AI developments (RSS feeds)
- **Fun Facts**: Engaging AI trivia
- **Alerts**: Special announcements

---

## 🎬 Production Pipeline

### Full Automation Flow
```
Evening (Night Before)
├─ Pick content (next lesson/trick/news)
├─ Generate AI script (Groq/Gemini)
├─ Fact-check (3-stage validation)
├─ A/B test hooks
├─ Generate voice (Indian accent, word timings)
├─ Create soundtrack (voice + music)
├─ Render 2D animation
│  ├─ Animated mascot (lip-sync, blinks, gestures)
│  ├─ Karaoke captions (word-by-word)
│  ├─ 10 scene types (hook, bullets, flow, etc.)
│  └─ Transitions & cover frame
├─ Upload to Supabase storage
├─ Send Telegram preview
└─ Queue for morning posting

Morning (08:00 IST)
├─ Verify not already posted
├─ Acquire posting lock
├─ Post to Instagram
├─ Cross-post to YouTube Shorts
├─ Write history
├─ Send confirmation
└─ Release lock

Throughout Day
├─ Monitor statistics
├─ Reply to comments
├─ Update analytics
└─ Learn from performance
```

---

## 🛠️ Management Commands

### Using GitHub CLI

#### Check Status
```bash
# View recent runs
gh run list --limit 10

# Check specific workflow
gh workflow view "Daily AIVerse reel"

# Watch live run
gh run watch
```

#### Manual Triggers
```bash
# Make and post reel immediately
gh workflow run daily.yml --field post_now=true

# Test with dry run
gh workflow run daily.yml --field dry_run=true --field content=lesson

# Force post queued reel
gh workflow run post.yml --field force_post=true

# Weekly report
gh workflow run engage.yml --field force_report=true
```

#### View Logs
```bash
# Latest run
gh run view

# Specific run
gh run view 44508629429 --log

# Failed runs only
gh run list --status failure
```

#### Secrets Management
```bash
# List secrets
gh secret list

# Update secret
gh secret set GEMINI_API_KEY < key.txt
# or
echo "your-key-here" | gh secret set GEMINI_API_KEY

# Delete secret
gh secret delete SECRET_NAME
```

#### Variables Management
```bash
# List variables
gh variable list

# Set variable
gh variable set REVIEW_MODE --body "auto"
gh variable set POST_TIME --body "08:00"
gh variable set TIMEZONE --body "Asia/Kolkata"
gh variable set LANGUAGE_MODE --body "hinglish"

# Delete variable
gh variable delete VARIABLE_NAME
```

---

## 📱 Telegram Control

### Interactive Commands
Send these in your Telegram bot chat:

- `/post` - Approve queued reel for scheduled posting
- `/postnow` - Post immediately (ignores schedule)
- `/skip` - Discard queued reel
- `/status` - Get current status

### User Commands (Comment Keywords)
Users can comment on reels:
- `NOTES` - Bot replies with lesson notes
- `PROMPT` - Get exact AI prompt used
- `NEWS` - Get 3-line news summary
- `AI` - Extra related fact

---

## 🔧 Configuration Options

### Core Settings (Variables)

```bash
# Posting Configuration
POST_TIMES="08:00,19:00"           # Comma-separated posting times
TIMEZONE="Asia/Kolkata"             # Timezone for scheduling

# Review & Approval
REVIEW_MODE="auto"                  # auto | auto_unless_skip | approve
REVIEW_HOURS="2"                    # Minimum hours for /skip (auto_unless_skip)

# Content Settings
LANGUAGE_MODE="hinglish"            # hinglish | english_only | hindi_only
SERIES_NAME="AIVerse"               # Brand name
MASCOT="true"                       # Enable 2D animated teacher
MUSIC="true"                        # Background music

# Voice Configuration (see Voice section below)
TTS_PROVIDER="auto"                 # auto | elevenlabs | gemini | edge
GEMINI_VOICE="Charon"               # Voice name for Gemini TTS
VOICE_NAME="hi-IN-MadhurNeural"     # Edge TTS voice
VOICE_PITCH="-6Hz"                  # Voice pitch adjustment
VOICE_RATE="-3%"                    # Voice speed adjustment

# YouTube Settings
YT_PRIVACY="public"                 # public | unlisted | private
FB_PAGE_ID=""                       # For Facebook cross-posting

# Growth Settings
AUTO_REPLY="true"                   # Auto-reply to comments
CONTENT_PLAN="lesson"               # Morning content type
CONTENT_PLAN_PM="trick"             # Evening content type
```

### Voice Providers

#### 1. Gemini TTS (Default - Free)
**Sound**: Natural, expressive, actor-like
**Cost**: Free with `GEMINI_API_KEY`

```bash
GEMINI_VOICE="Charon"              # Recommended voices:
                                    # Charon, Orus, Fenrir, Iapetus
GEMINI_SPEAK_DEVANAGARI="false"    # false = Roman, true = Devanagari
```

#### 2. ElevenLabs (Premium)
**Sound**: Most human-like
**Cost**: Paid (commercial use requires paid plan)

```bash
ELEVENLABS_API_KEY="your-key"
ELEVENLABS_VOICE_ID="voice-id"
```

#### 3. Edge TTS (Fallback)
**Sound**: Clearly synthetic
**Cost**: Free
**Automatic fallback** if others fail

```bash
VOICE_NAME="hi-IN-MadhurNeural"    # For Hinglish
VOICE_PITCH="-6Hz"
VOICE_RATE="-3%"
```

### Test Voice Samples
```bash
gh workflow run check.yml --field voice_samples=true
# Downloads artifact with all voice samples
```

---

## 📈 Monitoring & Analytics

### Automatic Tracking
- ✅ Views per reel
- ✅ Reach & impressions
- ✅ Likes, comments, shares, saves
- ✅ Engagement rate
- ✅ Best performing hooks
- ✅ Optimal posting times
- ✅ Audience growth

### Weekly Reports (Sundays)
Telegram receives:
- Total views/engagement this week
- Best performing reel
- Growth statistics
- Comment highlights
- Recommendations

### Learning Loop
The AI learns from your best content:
- Analyzes top-performing hooks
- Adapts writing style
- Optimizes scene timing
- Improves fact accuracy

---

## 🚨 Maintenance Schedule

### Daily (Automatic)
- ✅ Content generation
- ✅ Posting at scheduled times
- ✅ Comment monitoring & replies
- ✅ Statistics refresh

### Weekly (Automatic)
- ✅ Sunday report
- ✅ Weekly video compilation
- ✅ Performance analysis

### Monthly (Manual - You)
1. Check Instagram token expiry (warns via Telegram)
2. Review analytics and adjust content strategy
3. Check Supabase storage (auto-cleans old reels)
4. Review comment interactions

### Every 60 Days (Manual - You)
**Instagram Token Refresh** - Telegram will warn you

```bash
# Step 1: Get new token from Meta
# https://developers.facebook.com/tools/explorer
# Permissions: instagram_basic, instagram_content_publish,
#              instagram_manage_comments, instagram_manage_insights

# Step 2: Convert to long-lived (60 days)
bash refresh_token.sh

# Step 3: Update GitHub secret
gh secret set IG_ACCESS_TOKEN
```

See `GET_NEW_TOKEN.md` for detailed instructions.

---

## 🎓 Owner Checklist

### Initial Setup ✅
- [x] GitHub repository created
- [x] All secrets configured
- [x] Variables set
- [x] Workflows enabled
- [x] Instagram connected
- [x] YouTube connected
- [x] Telegram bot setup
- [x] Supabase storage configured

### Content Setup ✅
- [x] 100-lesson curriculum loaded
- [x] Voice configuration
- [x] Animation settings
- [x] Posting schedule

### Platform Setup
- [ ] Instagram bio link: Add `https://pranavnayee.github.io/aiverse-bot/links.html`
- [ ] Instagram bio name: `AIVerse | AI Hindi Mein`
- [ ] Pin Lesson #1 reel
- [ ] YouTube Studio: Verify phone (for custom thumbnails)
- [ ] YouTube API compliance audit (for public uploads)

### Growth Setup
- [ ] Enable all Instagram token permissions
- [ ] Test comment auto-reply
- [ ] Review first week's analytics
- [ ] Engage with 20-30 niche creators weekly
- [ ] Reply to comments manually (complements automation)

---

## 🎯 Growth Strategy

### Automated
✅ Daily consistent posting (2x per day)
✅ Comment auto-replies
✅ Keyword-based interactions
✅ Cross-posting to YouTube Shorts
✅ Weekly compilation videos
✅ SEO-optimized captions

### Manual (Weekly - 30 mins)
1. **Review** Sunday Telegram report
2. **Engage** with 20-30 creators in your niche
3. **Reply** to a few comments personally (builds community)
4. **Share** best reels to Stories
5. **Collaborate** with similar channels

### Monetization Paths
1. **YouTube Shorts** - Ad revenue (main money in India)
2. **Instagram Gifts** - Need eligibility first
3. **Brand Deals** - Follows audience size
4. **Affiliate Links** - AI tools/courses
5. **Premium Content** - Advanced lessons

---

## 🔍 Troubleshooting

### Common Issues

#### Workflow Not Running
```bash
# Check if workflow is enabled
gh workflow list

# Enable workflow
gh workflow enable daily.yml

# View recent runs
gh run list --workflow daily.yml --limit 5
```

#### Reel Not Posting
1. Check workflow logs: `gh run view --log`
2. Verify Instagram token: Token expires every 60 days
3. Check `REVIEW_MODE`: Set to `auto` for automatic posting
4. Manual force post: `gh workflow run post.yml --field force_post=true`

#### Voice Generation Fails
- Automatic retry (4 attempts)
- Falls back to Edge TTS
- Check API keys: `gh secret list`
- Force specific provider: Set `TTS_PROVIDER=edge`

#### Storage Issues
- Supabase auto-cleans old reels (keeps newest 30)
- Check bucket is PUBLIC
- Verify credentials: `gh secret list`

#### Comment Replies Not Working
- Needs `instagram_manage_comments` permission
- Check token permissions in Meta dashboard
- Set `AUTO_REPLY=false` to disable

---

## 📚 Additional Resources

### Documentation Files
- `README.md` - Main documentation
- `QUICK_REFERENCE.md` - Common tasks
- `GET_NEW_TOKEN.md` - Token refresh guide
- `INSTAGRAM_TOKEN_GUIDE.md` - Meta setup
- `VIMAX_UPGRADES.md` - Technical details
- `UPGRADE_COMPLETE.md` - Full documentation

### Tools Directory
- `youtube_auth.py` - YouTube OAuth setup
- `ig_admin.py` - Instagram admin commands
- `yt_admin.py` - YouTube admin commands
- `status_report.py` - Generate status report
- `voice_samples.py` - Test all voices
- `make_prompt_pack.py` - Build prompt PDF

### Testing
```bash
# Offline test (no API keys needed)
python cartoon-bot/tests/offline_test.py

# Pre-flight check (all services)
gh workflow run check.yml

# Dry run (Telegram preview only)
gh workflow run daily.yml --field dry_run=true
```

---

## 🎉 Success Metrics

### Current Status
- ✅ 141 successful workflow runs
- ✅ Automation running smoothly
- ✅ All systems operational

### Goals
- 📈 100 followers in first month
- 📈 1,000 followers in 3 months
- 📈 10,000 followers in 6 months
- 💰 YouTube monetization eligible (1,000 subs + 4,000 watch hours)
- 💰 Instagram monetization eligible (varies by region)

---

## 🆘 Support

### Quick Help
```bash
# View this guide
cat AUTOMATION_STATUS.md

# Check workflow status
gh run list

# View logs of latest run
gh run view --log

# Manual trigger test
gh workflow run check.yml
```

### Emergency Commands
```bash
# Stop all workflows
gh workflow disable daily.yml
gh workflow disable post.yml

# Force post now (if stuck)
gh workflow run post.yml --field force_post=true

# Skip queued reel (via Telegram)
/skip
```

---

**🚀 Your AIVerse Bot is LIVE and AUTOMATED!**

The system is running 24/7, creating content, posting, engaging, and growing your channel automatically. Just monitor the weekly Telegram reports and refresh the Instagram token every 60 days.

**Next Steps**:
1. ✅ Setup complete - automation running
2. Check Telegram for daily previews
3. Review weekly reports every Sunday
4. Refresh Instagram token when Telegram warns
5. Optional: Customize content with variables

**Happy Automating! 🎬🤖**
