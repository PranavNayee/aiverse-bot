# 🚀 Quick Start Guide

Get your cartoon bot posting to Instagram in under 1 hour!

---

## 📋 Overview

Your bot will:
1. ✅ Generate daily Hindi cartoon videos (Bablu & Chiku)
2. ✅ Use trending topics from India
3. ✅ Send preview to your Telegram
4. ✅ Wait for your approval (`/post` command)
5. ✅ Auto-post to Instagram @storysfrombittu
6. ✅ All with professional quality (karaoke subs, camera moves, transitions)

**Total time:** 30 seconds per day (just to review and approve!)

---

## ⚡ Super Quick Setup (If You Already Have Everything)

**Already have all the accounts?** Skip to:

1. ✅ **Secrets configured?** → Skip to [Phase 6: Test](#phase-6-test-everything)
2. ✅ **Instagram API setup?** → See [INSTAGRAM_SETUP.md](INSTAGRAM_SETUP.md)
3. ✅ **Starting from scratch?** → Continue below

---

## 🎯 Phase 1: Get Your API Keys (15 minutes)

### 1.1 Gemini API Key (Free)

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click **Get API Key**
3. Click **Create API Key**
4. Copy the key (starts with `AIza...`)
5. **Save it** for later

**Quota:** 15 requests/min free tier (enough for 1-2 videos/day)

### 1.2 Telegram Bot (Free)

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose name: **Bablu ka Vlog Bot** (or any name)
4. Choose username: **bablu_vlog_bot** (must end in _bot)
5. Copy the **token** (looks like `1234567890:ABCdef...`)
6. **Save it** as `TELEGRAM_BOT_TOKEN`

**Get your Chat ID:**
1. Send a message to your new bot (any message like "hi")
2. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   (Replace `<YOUR_TOKEN>` with your bot token)
3. Look for `"chat":{"id":123456789}`
4. Copy the **number** (your Chat ID)
5. **Save it** as `TELEGRAM_CHAT_ID`

### 1.3 Supabase Storage (Free)

1. Go to [supabase.com](https://supabase.com)
2. Click **Start your project**
3. Create new project:
   - Name: **cartoon-bot**
   - Database Password: (generate one)
   - Region: **Southeast Asia (Mumbai)** (closest to India)
4. Wait 2 minutes for project to initialize

**Get credentials:**
1. Click **Settings** (left sidebar) → **API**
2. Copy **Project URL** (like `https://xxxx.supabase.co`)
3. Copy **service_role key** (the secret one, not anon)
4. **Save these**

**Create storage bucket:**
1. Click **Storage** (left sidebar)
2. Click **Create bucket**
3. Name: **cartoon-reels**
4. **Make it Public** (toggle ON)
5. Click **Create bucket**

**Important:** Bucket must be PUBLIC for Instagram to access videos!

---

## 🎯 Phase 2: Add Secrets to GitHub (5 minutes)

1. Go to your repo: [github.com/PranavNayee/cartoon-bot](https://github.com/PranavNayee/cartoon-bot)
2. Click **Settings** (top tab)
3. Left sidebar → **Secrets and variables** → **Actions**
4. Click **New repository secret** for each:

| Secret Name | Value | From |
|-------------|-------|------|
| `GEMINI_API_KEY` | `AIza...` | Step 1.1 |
| `TELEGRAM_BOT_TOKEN` | `1234567890:ABC...` | Step 1.2 |
| `TELEGRAM_CHAT_ID` | `123456789` | Step 1.2 |
| `SUPABASE_URL` | `https://xxxx.supabase.co` | Step 1.3 |
| `SUPABASE_SERVICE_KEY` | `eyJ...` | Step 1.3 |
| `SUPABASE_BUCKET` | `cartoon-reels` | Step 1.3 |

**Instagram (optional for now, add later):**
| `IG_USER_ID` | Get from Instagram setup |
| `IG_ACCESS_TOKEN` | Get from Instagram setup |

---

## 🎯 Phase 3: Instagram Setup (30 minutes)

**This is the longest part, but only needs to be done once!**

Follow the complete guide here: **[INSTAGRAM_SETUP.md](INSTAGRAM_SETUP.md)**

**Summary:**
1. Convert Instagram to Business account
2. Create Facebook Page
3. Link Instagram to Facebook Page
4. Create Meta Developer App
5. Generate Access Token
6. Get Instagram Business Account ID
7. Add `IG_USER_ID` and `IG_ACCESS_TOKEN` to GitHub Secrets

**Don't skip steps!** Each one is necessary for Instagram API to work.

---

## 🎯 Phase 4: Optional Enhancements (5 minutes)

### 4.1 Add Background Music

1. Download royalty-free music:
   - [YouTube Audio Library](https://www.youtube.com/audiolibrary)
   - [Incompetech](https://incompetech.com/music/royalty-free/)
2. Place MP3 files in `cartoon-bot/assets/music/` folder
3. Commit and push to GitHub

**Recommended:** Upbeat Indian music or comedy background tracks

### 4.2 Create Custom Intro/Outro (Optional)

1. Create 2-second `intro.mp4` (1080x1920):
   - Add your logo/branding
   - Series name animation
2. Create 2-second `outro.mp4` (1080x1920):
   - "Follow for more!" CTA
   - Channel name/logo
3. Place in `cartoon-bot/assets/` folder
4. Commit and push

**Or skip:** Bot will auto-generate text-based intro/outro!

---

## 🎯 Phase 5: Configure Variables (Optional)

GitHub → Settings → Secrets and variables → Actions → **Variables** tab

**Optional configuration:**
| Variable | Default | Options |
|----------|---------|---------|
| `REVIEW_MODE` | `approve` | `approve` / `auto_unless_skip` / `auto` |
| `MOUTH_FX` | `true` | `true` / `false` (talking mouth effect) |
| `ADD_INTRO` | `true` | `true` / `false` |
| `ADD_OUTRO` | `true` | `true` / `false` |
| `ADD_TRANSITIONS` | `true` | `true` / `false` |
| `KARAOKE_SUBS` | `true` | `true` / `false` |

**Recommended:** Keep all defaults for best quality!

---

## 🎯 Phase 6: Test Everything (10 minutes)

### 6.1 Pre-Flight Check

1. GitHub → **Actions** tab
2. Left sidebar → **Pre-flight check**
3. Click **Run workflow** → **Run workflow**
4. Wait 3-5 minutes (first run downloads ~1.5GB depth model)

**Expected results:**
- ✅ Gemini API works
- ✅ Telegram connection works
- ✅ Supabase storage works
- ✅ Image generation works
- ✅ Depth model loaded
- ⚠️ Mouth detection (warning is OK)
- ✅ 3D animation works
- ✅ Voice synthesis works
- ✅ Instagram API works (if configured)

**If anything fails:** Check the logs and fix the corresponding secret/configuration.

### 6.2 Generate First Video

1. GitHub → **Actions** → **Daily cartoon reel**
2. Click **Run workflow** → **Run workflow**
3. Wait 10-15 minutes
4. Check your Telegram for the video!

**What to check in the video:**
- [ ] Video plays correctly
- [ ] Characters (Bablu & Chiku) appear
- [ ] Hindi audio works
- [ ] Karaoke subtitles with glow
- [ ] Intro at start (2 sec)
- [ ] Outro at end (2.5 sec)
- [ ] Smooth transitions between scenes
- [ ] Different camera movements
- [ ] Duration ~40-45 seconds

### 6.3 Test Instagram Posting

1. In Telegram, send `/post` to your bot
2. Wait 2-3 minutes
3. Check Instagram @storysfrombittu
4. Your video should appear in Reels! 🎉

**Or manual post:**
- Download video from Telegram
- Post manually from Instagram app

---

## 🎯 Phase 7: Enable Daily Automation (2 minutes)

Your bot can run automatically every day at 8:00 AM IST.

**Already enabled!** The schedule is in `.github/workflows/daily.yml`:
```yaml
schedule:
  - cron: '30 2 * * *'  # 8:00 AM IST = 2:30 AM UTC
```

**Workflow:**
1. Bot generates video at 8 AM
2. Sends to your Telegram
3. You watch and send `/post` (or `/skip`)
4. Bot posts to Instagram
5. **Done for the day!**

**To disable automation:**
- Comment out the `schedule:` section in `daily.yml`
- Run workflows manually instead

---

## 📱 Daily Workflow (30 seconds)

Once everything is set up:

### Morning (8:00 AM IST):
1. ✅ Bot generates video automatically
2. ✅ Telegram notification arrives

### Your Action (30 seconds):
3. 📱 Open Telegram
4. 📺 Watch the video
5. ✅ Send `/post` (or `/skip` if not good)
6. 🎉 Bot posts to Instagram

**That's it!** Your daily content is handled.

---

## 🎛️ Bot Commands

Send these to your Telegram bot:

- `/post` - Approve and post the video to Instagram
- `/skip` - Reject this video (won't post)
- `/status` - Check bot status
- `/help` - Show available commands

---

## 📊 Monitoring & Analytics

### Check Video Performance

**Instagram Insights:**
1. Open Instagram app
2. Go to your Reel
3. View Insights
4. Track: Views, Likes, Comments, Shares, Reach

**What to track:**
- Which topics get most views
- Best posting times
- Engagement rate (likes + comments / views)
- Follower growth rate

### Optimize Based on Data

- 📈 Topics with 5000+ views → More of that style
- 📉 Topics with <1000 views → Avoid similar
- 🕐 Post at times with highest engagement
- 🎥 Check which camera moves work best

---

## 🛠️ Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| Pre-flight fails | Check GitHub Actions logs, verify all secrets |
| No Telegram message | Message your bot first, verify Chat ID |
| Video generation fails | Check Gemini API quota, try again later |
| Instagram posting fails | Verify token hasn't expired (60 days) |
| Subtitles look weird | Set `KARAOKE_SUBS=false` |
| Characters inconsistent | AI limitation, but improved with new prompts |
| Token expired | Regenerate long-lived token (see Instagram guide) |

**For detailed troubleshooting:** See `INSTAGRAM_SETUP.md` → Troubleshooting section

---

## 📚 Full Documentation

- **[SETUP.md](cartoon-bot/SETUP.md)** - Complete technical setup guide
- **[INSTAGRAM_SETUP.md](INSTAGRAM_SETUP.md)** - Instagram API setup (detailed)
- **[ENHANCEMENTS.md](cartoon-bot/ENHANCEMENTS.md)** - Visual enhancement guide
- **[TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)** - 15-point testing guide
- **[UPGRADE_SUMMARY.md](UPGRADE_SUMMARY.md)** - What's new in latest version

---

## ✅ Setup Complete Checklist

- [ ] Gemini API key added
- [ ] Telegram bot created and secrets added
- [ ] Supabase project created with public bucket
- [ ] All GitHub secrets configured
- [ ] Instagram Business account created
- [ ] Facebook Page linked to Instagram
- [ ] Meta Developer App created
- [ ] Instagram access token generated
- [ ] `IG_USER_ID` and `IG_ACCESS_TOKEN` added
- [ ] Pre-flight check passes ✅
- [ ] First video generated successfully
- [ ] Test post to Instagram works 🎉
- [ ] Daily automation enabled

**When all checked: You're ready to go viral!** 🚀

---

## 🎉 What You've Built

A **professional AI-powered cartoon studio** that:

✅ Generates 40-second Hindi comedy videos daily  
✅ Uses trending topics automatically  
✅ Creates consistent characters (Bablu & Chiku)  
✅ Applies 8 professional camera movements  
✅ Adds karaoke subtitles with glow effects  
✅ Includes branded intro/outro  
✅ Uses smooth scene transitions  
✅ Posts to Instagram automatically  
✅ Costs $0 per video (unlimited generations)  

**Value:** Equivalent to hiring a $50-200/video animator — but free!

---

## 🚀 Next Steps

### Week 1: Learn & Optimize
- Generate 5-10 videos
- Test different topics
- Find what resonates with your audience
- Adjust settings if needed

### Week 2: Build Audience
- Post consistently daily
- Reply to comments
- Use all 30 hashtags
- Cross-post to other platforms

### Week 3: Scale & Monetize
- Analyze what's working
- Double down on popular topics
- Apply for Instagram monetization
- Consider brand partnerships

### Month 2+: Go Viral
- Consistent daily posting builds momentum
- Instagram algorithm will push your content
- Aim for 10k+ followers for monetization
- Keep improving based on analytics

---

## 💡 Pro Tips

1. **Post at peak times:** 6-9 AM, 12-2 PM, 6-9 PM IST
2. **Reply to comments quickly:** Boosts engagement signals
3. **Use trending sounds:** Add to `assets/music/`
4. **Stay consistent:** Daily posting is key to growth
5. **Enable AI label:** Instagram Settings → Account → Labels
6. **Test different cameras:** Track which ones get most views
7. **Monitor Gemini quota:** Don't generate too many test videos in one day
8. **Refresh Instagram token:** Every 60 days (set calendar reminder)

---

## 🆘 Need Help?

**Common issues:**
- Check relevant `.md` file for your problem
- Review GitHub Actions logs for errors
- Verify all secrets are correct (no extra spaces!)
- Try running Pre-flight check again

**Still stuck?**
- Check Instagram API documentation
- Test tokens in Graph API Explorer
- Verify Facebook Page linkage
- Ensure account is Business/Creator type

---

## 🎊 Congratulations!

You now have a **fully automated, professional-quality cartoon production system** posting daily to Instagram!

**Time investment:**
- Setup: ~1 hour (one-time)
- Daily: 30 seconds (review + approve)
- Maintenance: 5 minutes every 60 days (refresh token)

**Return:**
- Daily viral-quality content
- Growing Instagram following
- Potential monetization
- Professional brand presence

**All for $0 in ongoing costs!** 🎉

---

**Ready to go viral? Run your first workflow now!** 🚀📱

GitHub → Actions → Daily cartoon reel → Run workflow
