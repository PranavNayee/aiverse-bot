# 🎬 Bablu ka Vlog - Automated Hindi Cartoon Reel Bot

**Professional AI-powered cartoon studio that generates viral Hindi comedy reels daily and posts to Instagram automatically!**

🎯 **Instagram:** [@storysfrombittu](https://instagram.com/storysfrombittu)

---

## ✨ What This Bot Does

🤖 **Fully Automated Daily Workflow:**
1. Finds trending topics in India 🇮🇳
2. Generates 7-scene Hindi comedy story (Bablu & Chiku characters)
3. Creates Pixar-style 3D animated images
4. Applies professional camera movements (8 types)
5. Adds talking mouth effects synced to Hindi voice
6. Burns in karaoke subtitles with glow effects
7. Adds branded intro & outro with smooth transitions
8. Sends preview to Telegram for your approval
9. Posts to Instagram automatically when you say `/post`

**⏱️ Your time investment:** 30 seconds/day to review and approve!

---

## 🌟 Professional Features

### 🎥 Advanced Cinematography
- **8 camera movements:** push, orbit, pull, shake, spiral, dolly_zoom, crane, drift
- **3D parallax depth engine** (AI depth model)
- **Dynamic reactions:** zoom, shake on punchlines
- **Smooth transitions:** crossfade between scenes

### 📝 Broadcast-Quality Subtitles
- **Karaoke word-by-word timing** (like music videos)
- **3-layer glow effect** (professional outline + blur)
- **Color-coded speakers** (Bablu=cyan, Chiku=yellow-orange)
- **Large readable font** (78px) with thick outline (7px)
- **Smooth animations** (bounce-in, scale pulse, fade)

### 🎨 Consistent Characters
- **Bablu** - Cheerful monkey vlogger (golden-brown fur, red cap, blue scarf)
- **Chiku** - Sarcastic crow sidekick (black feathers, round glasses, orange bow tie)
- Enhanced AI prompts for uniform appearance across scenes

### 🎬 Professional Production
- **Branded intro** (2 sec) - Auto-generated or custom
- **CTA outro** (2.5 sec) - "रोज़ एक नया एपिसोड — फॉलो करें!"
- **Background music** - Auto-ducked under dialogue, normalized volume
- **Safety filters** - Multi-layer content moderation (family-friendly)

### 💰 Cost
- **$0 per video** (unlimited generations)
- **100% free tools** (Pollinations, Gemini, HuggingFace, edge-tts)
- **No paid APIs** required

---

## 🚀 Quick Start

### Prerequisites
- GitHub account (free)
- Telegram account (free)
- Google/Gemini API key (free)
- Supabase account (free)
- Instagram Business/Creator account (free)
- Facebook Page (free)

### Setup Time
- **First-time setup:** ~1 hour
- **Daily operation:** 30 seconds

### Get Started

1. **Fork/clone this repo**
2. **Follow the quick start guide:** [QUICK_START.md](QUICK_START.md)
3. **Instagram API setup:** [INSTAGRAM_SETUP.md](INSTAGRAM_SETUP.md)

**Or jump to specific guides:**
- 📱 [Instagram Graph API Setup](INSTAGRAM_SETUP.md) - Complete Instagram integration
- 🎨 [Visual Enhancements Guide](cartoon-bot/ENHANCEMENTS.md) - All professional features explained
- 🧪 [Testing Checklist](TESTING_CHECKLIST.md) - 15-point verification guide
- 📚 [Technical Setup](cartoon-bot/SETUP.md) - Detailed technical documentation
- 🎯 [Upgrade Summary](UPGRADE_SUMMARY.md) - What's new in latest version

---

## 📊 What Makes This Viral-Quality

### Algorithm-Optimized Features

| Feature | Instagram Algorithm Factor | Impact |
|---------|---------------------------|--------|
| **Karaoke Subtitles** | Sound-off viewing (85% of Reels) | ⬆️ Watch time |
| **Professional Glow** | Production quality signals | ⬆️ Reach |
| **Dynamic Cameras** | Engaging cinematography | ⬆️ Completion rate |
| **Smooth Transitions** | Polished feel | ⬆️ Saves/Shares |
| **Consistent Characters** | Brand recognition | ⬆️ Follower conversion |
| **CTA Outro** | Clear call-to-action | ⬆️ Follow rate |
| **Daily Posting** | Consistency signal | ⬆️ Algorithm push |

### Quality Comparison

**This Bot vs Paid Tools:**

| Feature | This Bot | Kling AI | Professional Editor |
|---------|----------|----------|---------------------|
| Cost per video | **$0** | $10-20 | $50-200 |
| Monthly cost | **$0** | $300-600 | $1500-6000 |
| Generation time | 10-15 min | 5-10 min | 2-4 hours |
| Camera movements | 8 professional | Limited | Custom |
| Karaoke subtitles | ✅ Included | ❌ Extra work | ✅ Custom |
| Consistent characters | ✅ AI-enhanced | ✅ Better | ✅ Perfect |
| Daily automation | ✅ Built-in | ❌ Manual | ❌ Manual |
| Customization | ✅ Full control | ❌ Limited | ✅ Full |

**Verdict:** Professional quality at $0 cost! 🎉

---

## 🎯 Sample Output

**Video Structure (40-45 seconds):**
```
[00:00-00:02] Intro - "Bablu ka Vlog" branded animation
[00:02-00:37] 7 scenes - Trending topic comedy story
              - Scene 1: Hook (Bablu greets camera, sets up topic)
              - Scenes 2-6: Escalation (jokes, reactions, Chiku roasts)
              - Scene 7: Punchline (zoom/shake reaction)
[00:37-00:40] Outro - "रोज़ एक नया एपिसोड — फॉलो करें!" 🔔
```

**Each Scene Has:**
- 5-7 seconds duration
- Professional camera movement (spiral/crane/drift/etc)
- Talking mouth synced to Hindi audio
- Karaoke subtitles with glow
- Beat-zoom while speaking
- Emoji sticker pop (optional)
- Smooth crossfade transition

**Topics:** Cricket, movies/OTT, gadgets, food, festivals, weather, viral memes, tech, shopping, relatable daily life

**Language:** Hindi (Devanagari script) with optional English hashtags

---

## 🛠️ Technology Stack

### AI & Generation
- **LLM:** Google Gemini 3.8 Flash (story generation, safety review)
- **Backup LLM:** HuggingFace (Qwen2.5-72B, Llama 3.3-70B)
- **Image Gen:** Pollinations.ai (Flux model, free tier)
- **Backup Image:** Cloudflare Workers AI (optional)
- **Depth AI:** depth-anything/Depth-Anything-V2-Small-hf (~1.5GB)
- **Voice:** edge-tts (Microsoft's free TTS, Hindi voices)

### Video Processing
- **3D Engine:** Custom parallax system (motion3d.py)
- **Effects:** OpenCV + NumPy (talking mouth, depth parallax)
- **Assembly:** FFmpeg (subtitles, music, transitions)
- **Format:** 1080x1920 (vertical), 30 FPS, H.264, AAC audio

### Infrastructure
- **Runtime:** GitHub Actions (free tier, 2000 min/month)
- **Storage:** Supabase (free tier, 1GB)
- **Posting:** Instagram Graph API v21.0
- **Notifications:** Telegram Bot API
- **Scheduling:** Cron (8:00 AM IST daily)

### Languages & Libraries
- **Python 3.10+**
- **Libraries:** opencv-python-headless, numpy, transformers, torch (CPU), Pillow, requests, edge-tts

---

## 📁 Project Structure

```
cartoon-bot/
├── .github/workflows/       # GitHub Actions automation
│   ├── daily.yml           # Daily video generation (8 AM IST)
│   ├── post.yml            # Post approved reel to Instagram
│   └── check.yml           # Pre-flight system check
├── cartoon-bot/
│   ├── src/                # Main source code
│   │   ├── main.py         # Main workflow orchestration
│   │   ├── story.py        # AI story generation (Gemini/HF)
│   │   ├── images.py       # Image generation (Pollinations/CF)
│   │   ├── motion3d.py     # 3D parallax animation engine
│   │   ├── depth.py        # AI depth model (Depth-Anything)
│   │   ├── mouth.py        # Talking mouth detection & effect
│   │   ├── video.py        # Final assembly (ffmpeg, subtitles)
│   │   ├── voice.py        # Hindi TTS (edge-tts)
│   │   ├── instagram.py    # Instagram Graph API posting
│   │   ├── notify.py       # Telegram notifications
│   │   ├── storage.py      # Supabase storage
│   │   ├── safety.py       # Content moderation
│   │   ├── trends.py       # Google Trends (India)
│   │   └── config.py       # Configuration & secrets
│   ├── assets/             # Optional media assets
│   │   ├── music/          # Background music (MP3/WAV)
│   │   ├── intro.mp4       # Custom intro (optional)
│   │   └── outro.mp4       # Custom outro (optional)
│   ├── tests/              # Automated tests
│   └── SETUP.md            # Technical setup guide
├── QUICK_START.md          # Quick start guide (you are here!)
├── INSTAGRAM_SETUP.md      # Complete Instagram API setup
├── ENHANCEMENTS.md         # Visual features guide
├── TESTING_CHECKLIST.md    # Testing verification
├── UPGRADE_SUMMARY.md      # Latest changes
└── README.md               # This file
```

---

## 🎛️ Configuration

### GitHub Secrets (Required)
```
GEMINI_API_KEY          # Google AI Studio
TELEGRAM_BOT_TOKEN      # @BotFather
TELEGRAM_CHAT_ID        # Your Telegram user ID
SUPABASE_URL            # Supabase project URL
SUPABASE_SERVICE_KEY    # Supabase service_role key
SUPABASE_BUCKET         # Storage bucket name (public)
IG_USER_ID              # Instagram Business Account ID
IG_ACCESS_TOKEN         # Instagram long-lived token (60 days)
```

### GitHub Variables (Optional)
```
REVIEW_MODE = approve              # approve | auto_unless_skip | auto
REVIEW_HOURS = 2                   # Hours to wait for approval
MOUTH_FX = true                    # Talking mouth effect
ADD_INTRO = true                   # Branded intro clip
ADD_OUTRO = true                   # CTA outro clip
ADD_TRANSITIONS = true             # Crossfade between scenes
KARAOKE_SUBS = true               # Word-by-word karaoke timing
```

### Customization (src/config.py)
- Characters (look, personality)
- Series name & hashtags
- Art style (3D, colors, lighting)
- Voice settings (pitch, rate)
- Number of scenes (5-9 recommended)
- Safety blocklist (topics to avoid)

---

## 🔒 Security & Safety

### Multi-Layer Content Moderation
1. **Blocklist Filter** - Removes unsafe trending topics before AI sees them
2. **Prompt Engineering** - Strict rules for family-friendly content only
3. **Local Re-Check** - Scans generated story for blocked keywords
4. **AI Safety Editor** - Second Gemini pass reviews brand safety
5. **Manual Approval** - You review every video before posting

### Data Privacy
- ✅ All secrets encrypted in GitHub
- ✅ No passwords stored (tokens only)
- ✅ Tokens can be revoked anytime
- ✅ Videos stored in your Supabase (you control it)
- ✅ Open source (audit the code yourself)

### Compliance
- ✅ Instagram API Terms of Service compliant
- ✅ Uses official Graph API (not scrapers/bots)
- ✅ Respects rate limits (1 post = 1 daily video)
- ✅ AI-generated content labeled (caption notes it)
- ✅ Family-friendly content only (brand-safe)

---

## 📈 Growth Strategy

### Week 1-2: Foundation
- Post daily consistently
- Test different topics
- Reply to all comments
- Use all 30 hashtags
- Cross-post to other platforms

### Week 3-4: Optimization
- Analyze Instagram Insights
- Double down on popular topics
- Adjust posting times (test 6 AM, 12 PM, 6 PM)
- Experiment with camera moves
- Try different music styles

### Month 2-3: Scale
- Aim for 1000+ followers
- Apply for Instagram monetization (need 10k followers)
- Collaborate with other creators
- Run engagement challenges
- Create series/storylines

### Month 4+: Monetize
- Instagram bonuses for Reels plays
- Brand partnerships & sponsorships
- Affiliate marketing in captions
- Merchandise (if audience grows large)
- Consulting for other creators

---

## 🏆 Success Metrics

**Target KPIs:**

| Metric | Week 1 | Month 1 | Month 3 |
|--------|--------|---------|---------|
| Followers | 50-100 | 500-1000 | 5000-10k |
| Avg Views | 500-1000 | 2000-5000 | 10k-50k |
| Engagement Rate | 2-5% | 5-8% | 8-12% |
| Completion Rate | 40-60% | 60-75% | 75-85% |
| Daily Posts | 1 | 1 | 1-2 |

**What matters most:**
1. **Consistency** (daily posting without gaps)
2. **Completion rate** (people watch to the end)
3. **Saves** (viewers save for later = strong signal)
4. **Shares** (best virality signal)

---

## 🛠️ Maintenance

### Daily (30 seconds)
- Check Telegram for video preview
- Watch and approve with `/post`
- (Optional) Reply to Instagram comments

### Weekly (5 minutes)
- Review Instagram Insights
- Note which topics performed best
- Check Gemini API quota usage

### Monthly (10 minutes)
- Review overall growth trends
- Adjust strategy based on data
- Update hashtags if needed
- Check GitHub Actions quota (2000 min/month free)

### Every 60 Days (15 minutes)
- Refresh Instagram access token
- Update `IG_ACCESS_TOKEN` secret in GitHub
- (Or token may auto-refresh if bot posts regularly)

---

## 🆘 Troubleshooting

### Common Issues

| Problem | Quick Fix |
|---------|-----------|
| Pre-flight check fails | Verify all secrets, check logs |
| No Telegram message | Message bot first, check Chat ID |
| Gemini 429 error | API quota exceeded, wait 24 hours |
| Instagram posting fails | Token expired (60 days), regenerate |
| Video quality low | Check image generation, try Cloudflare backup |
| Characters inconsistent | AI limitation, but improved with new prompts |
| Subtitles overlapping | Set `KARAOKE_SUBS=false` for simpler style |

**Detailed troubleshooting:** See [INSTAGRAM_SETUP.md](INSTAGRAM_SETUP.md) → Troubleshooting

---

## 📚 Documentation

### For Users
- **[QUICK_START.md](QUICK_START.md)** - Get started in 1 hour
- **[INSTAGRAM_SETUP.md](INSTAGRAM_SETUP.md)** - Instagram API integration
- **[ENHANCEMENTS.md](cartoon-bot/ENHANCEMENTS.md)** - Visual features explained
- **[TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)** - 15-point testing guide

### For Developers
- **[SETUP.md](cartoon-bot/SETUP.md)** - Technical setup & architecture
- **[UPGRADE_SUMMARY.md](UPGRADE_SUMMARY.md)** - Latest changes & improvements
- **Source Code** - Extensively commented Python files

---

## 🎓 Learn More

### Recommended Reading
- [Instagram Content Publishing API](https://developers.facebook.com/docs/instagram-api/guides/content-publishing)
- [Instagram Algorithm Factors 2024](https://later.com/blog/how-instagram-algorithm-works/)
- [Creating Viral Reels](https://blog.hootsuite.com/instagram-reels/)
- [AI Content Best Practices](https://help.instagram.com/179641320727698)

### Community
- Share your success stories!
- Tag your Instagram: @storysfrombittu
- Contribute improvements via Pull Requests
- Report issues on GitHub

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] More camera movement types
- [ ] Better character consistency prompts
- [ ] Sound effects library integration
- [ ] Multi-language support (Tamil, Telugu, etc.)
- [ ] Interactive caption generation
- [ ] Audience engagement features
- [ ] A/B testing framework
- [ ] Analytics dashboard

**How to contribute:**
1. Fork the repo
2. Create feature branch
3. Make your changes
4. Test thoroughly
5. Submit Pull Request

---

## 📄 License

MIT License - Free to use, modify, and distribute!

**Attribution appreciated but not required.**

---

## ⚠️ Disclaimer

- This bot uses AI to generate content. Always review before posting.
- Instagram's Terms of Service and Content Guidelines apply.
- Use Instagram's AI-generated content label transparency feature.
- Family-friendly content only - multi-layer safety filters included.
- Not affiliated with Meta, Instagram, Google, or HuggingFace.
- Provided as-is with no guarantees of virality (but it helps!).

---

## 🎉 Success Stories

**Your story here!** Share your results:
- How many followers gained?
- Best performing video?
- Monetization success?
- Tips for other creators?

---

## 🚀 Ready to Go Viral?

1. **[Start Setup](QUICK_START.md)** - Get started in 1 hour
2. **Generate First Video** - See the magic happen
3. **Post Daily** - Consistency is key
4. **Grow Audience** - Watch followers increase
5. **Monetize** - Turn views into income

**Your automated cartoon studio awaits!** 🎬✨

---

Made with ❤️ for the creator community

**Instagram:** [@storysfrombittu](https://instagram.com/storysfrombittu)

⭐ Star this repo if it helps you go viral!
