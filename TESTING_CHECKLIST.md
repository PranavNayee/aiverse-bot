# 🧪 Testing Checklist for Enhanced Features

Use this checklist to verify all new enhancements are working correctly.

---

## Pre-Testing Setup

- [ ] All code pushed to GitHub
- [ ] GitHub Actions enabled
- [ ] All secrets configured (GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, etc.)
- [ ] Supabase bucket is public

---

## 1. ✅ Pre-Flight Check

**Run:** Actions → Pre-flight check → Run workflow

**Verify:**
- [ ] ✅ Gemini API works
- [ ] ✅ Telegram connection works
- [ ] ✅ Supabase storage works
- [ ] ✅ Image generation works (Pollinations or Cloudflare)
- [ ] ✅ Depth model loads (may take 5-10 min first time)
- [ ] ✅ Mouth detection works (⚠️ is OK, just means fallback)
- [ ] ✅ 3D animation engine works
- [ ] ✅ Voice synthesis works (edge-tts)
- [ ] ⚠️ Instagram (optional, can skip for now)

**If anything fails:** Check the workflow logs and fix before continuing.

---

## 2. 🎬 Test Video Generation

**Run:** Actions → Daily cartoon reel → Run workflow

**Wait:** 10-20 minutes for first run (downloads depth model ~1.5GB)

**Check Telegram:**
- [ ] Video arrives on Telegram
- [ ] Video plays correctly
- [ ] Duration is 35-45 seconds (7 scenes × ~5-6 sec)

---

## 3. 🎥 Verify Camera Movements

**Watch the video and identify camera moves:**

- [ ] Different camera movements in different scenes
- [ ] Movements are smooth (not jerky)
- [ ] At least 2-3 different camera types used
- [ ] Dramatic scenes use more dynamic cameras (spiral/crane/dolly_zoom)
- [ ] Calm scenes use gentler cameras (push/drift)

**Possible cameras you might see:**
- push (slow zoom in)
- orbit (circular movement)
- pull (zoom out)
- shake (handheld)
- spiral (zoom + orbit)
- dolly_zoom (vertigo effect)
- crane (vertical rise)
- drift (floating lateral)

---

## 4. 🌟 Verify Karaoke Subtitles

**Watch with sound ON:**

- [ ] Subtitles appear at bottom of screen
- [ ] Words highlight as they're spoken (karaoke effect)
- [ ] Glow effect visible around text
- [ ] Font is large and readable
- [ ] Different speakers have different colors:
  - Bablu = Cyan glow
  - Chiku = Yellow-orange glow
  - Narrator = White
- [ ] Hook line appears at start (larger, top of screen)
- [ ] CTA appears at end "रोज़ एक नया एपिसोड — फॉलो करें!"
- [ ] Subtitles have smooth fade in/out
- [ ] Slight bounce/scale animation on each line

**Test readability:**
- [ ] Watch on phone (small screen) - still readable?
- [ ] Watch with sound OFF - can you follow the story?

---

## 5. 🎬 Verify Intro/Outro

**Check video structure:**

- [ ] **Intro** appears (2 seconds)
  - Shows series name "Bablu ka Vlog"
  - Fade in animation
  - Dark background

- [ ] **Main scenes** (7 scenes, ~35-40 seconds)

- [ ] **Outro** appears (2.5 seconds)
  - Shows CTA with bell emoji 🔔
  - "रोज़ एक नया एपिसोड — फॉलो करें!"
  - Fade in animation

**Total video length:** Should be ~39-44 seconds (2 + 35-40 + 2.5)

---

## 6. 🔄 Verify Scene Transitions

**Watch scene changes carefully:**

- [ ] Scenes blend smoothly (crossfade)
- [ ] No hard cuts between scenes (except maybe first/last)
- [ ] Transition duration is ~0.4 seconds
- [ ] Audio also crossfades (voices blend between scenes)
- [ ] Transitions look professional (not abrupt)

**Note:** If clips are very short, transition might be skipped (this is normal).

---

## 7. 🎨 Verify Image Consistency

**Compare characters across scenes:**

- [ ] **Bablu** looks similar in all scenes:
  - Same fur color (golden-brown)
  - Same red cap
  - Same blue scarf
  - Same facial features
  - Same body proportions

- [ ] **Chiku** looks similar in all scenes (if appears):
  - Same black feathers
  - Same round glasses
  - Same orange bow tie
  - Same size/proportions

**Note:** Won't be 100% identical (it's AI), but should be recognizably the same characters!

---

## 8. 🎵 Test Music Integration

**Add background music:**

1. [ ] Download a royalty-free MP3 from:
   - [YouTube Audio Library](https://www.youtube.com/audiolibrary)
   - [Incompetech](https://incompetech.com/music/royalty-free/)

2. [ ] Place in `cartoon-bot/assets/music/` folder

3. [ ] Commit and push to GitHub

4. [ ] Run Daily Reel workflow again

**Verify in new video:**
- [ ] Background music plays throughout
- [ ] Music volume lowers when dialogue plays (ducking)
- [ ] Music volume returns when no dialogue
- [ ] Music doesn't overpower voices
- [ ] Overall volume is normalized

---

## 9. 🎛️ Test Feature Toggles

### Test Disabling Intro

1. [ ] GitHub → Settings → Secrets and variables → Actions → Variables
2. [ ] New variable: `ADD_INTRO` = `false`
3. [ ] Run Daily Reel workflow
4. [ ] Verify video starts directly with first scene (no intro)

### Test Disabling Outro

1. [ ] New variable: `ADD_OUTRO` = `false`
2. [ ] Run Daily Reel workflow
3. [ ] Verify video ends on last scene (no outro)

### Test Disabling Transitions

1. [ ] New variable: `ADD_TRANSITIONS` = `false`
2. [ ] Run Daily Reel workflow
3. [ ] Verify scenes have hard cuts (no crossfades)

### Test Disabling Karaoke

1. [ ] New variable: `KARAOKE_SUBS` = `false`
2. [ ] Run Daily Reel workflow
3. [ ] Verify subtitles are simpler (no word-by-word highlighting)

**After testing, set all back to `true` or delete variables!**

---

## 10. 🎨 Test Custom Intro/Outro (Optional)

### Create Custom Intro

1. [ ] Create a 2-second video (1080x1920):
   - Use Canva, After Effects, or any video editor
   - Add your logo/branding
   - Export as `intro.mp4`

2. [ ] Place in `cartoon-bot/assets/` folder (NOT in `music/` subfolder!)

3. [ ] Commit and push

4. [ ] Run Daily Reel workflow

5. [ ] Verify your custom intro plays instead of auto-generated one

### Create Custom Outro

1. [ ] Create a 2-3 second video (1080x1920):
   - Add CTA "Follow for more!"
   - Add channel name/logo
   - Export as `outro.mp4`

2. [ ] Place in `cartoon-bot/assets/` folder

3. [ ] Commit and push

4. [ ] Run Daily Reel workflow

5. [ ] Verify your custom outro plays

---

## 11. 📱 Real-World Testing

### Phone Screen Test

- [ ] Transfer video to phone
- [ ] Watch on small screen
- [ ] Subtitles still readable?
- [ ] Characters recognizable?
- [ ] Video feels professional?

### Sound-Off Test

- [ ] Watch video with sound OFF
- [ ] Can you follow the story from subtitles alone?
- [ ] Karaoke highlighting helps understanding?

### Full-Screen Test

- [ ] Watch in Instagram Reels format
- [ ] Intro/outro feel appropriate?
- [ ] Video length feels right (not too long/short)?
- [ ] Would you watch to the end?

---

## 12. 🚀 Performance Test

### Generation Speed

- [ ] First run: ~15-25 minutes (depth model download)
- [ ] Second run: ~8-12 minutes (model cached)
- [ ] Third run: Similar speed to second

**If slower:** Check GitHub Actions logs for bottlenecks.

### File Sizes

- [ ] Final video: ~5-15 MB (reasonable for Instagram)
- [ ] Not too large (>50 MB = slow upload)
- [ ] Not too small (<2 MB = low quality)

---

## 13. ✅ Quality Checklist

**Rate each aspect 1-5 (5 = perfect):**

- [ ] **Camera work:** Dynamic and engaging? ___/5
- [ ] **Subtitles:** Readable and professional? ___/5
- [ ] **Consistency:** Characters look similar? ___/5
- [ ] **Branding:** Intro/outro appropriate? ___/5
- [ ] **Transitions:** Smooth and polished? ___/5
- [ ] **Overall:** Would go viral? ___/5

**Average score:** ___/5

**Goal:** All ratings 4+ (professional quality)

---

## 14. 🐛 Troubleshooting

### Common Issues

**Issue:** Subtitles look weird/overlapping
- **Fix:** Set `KARAOKE_SUBS=false` for simpler subtitles

**Issue:** Intro/outro don't appear
- **Fix:** Check variables aren't set to `false`

**Issue:** Transitions cause artifacts
- **Fix:** Set `ADD_TRANSITIONS=false` or adjust duration in `video.py`

**Issue:** Characters look very different each scene
- **Fix:** This is an AI limitation, but should be better than before

**Issue:** Camera moves too fast/slow
- **Fix:** Edit `motion3d.py` camera parameters (zoom/pan values)

**Issue:** Music too loud/quiet
- **Fix:** Adjust volume in `video.py` line ~56: `[m]volume=0.5` (change 0.5)

---

## 15. 📊 Comparison Test

**Generate 2 videos to compare:**

### Video A (All Features ON)
- All enhancements enabled
- Intro + outro
- Transitions + karaoke

### Video B (All Features OFF)
- `ADD_INTRO=false`
- `ADD_OUTRO=false`
- `ADD_TRANSITIONS=false`
- `KARAOKE_SUBS=false`

**Compare:**
- [ ] Video A looks more professional?
- [ ] Video A more engaging?
- [ ] Video A more viral-worthy?

**Expected result:** Video A should feel significantly more polished!

---

## ✅ Final Approval

Once all checks pass:

- [ ] All enhancements working correctly
- [ ] Video quality is professional
- [ ] Ready for daily automation
- [ ] Ready to post to Instagram

**Set up automation:**
1. [ ] Enable daily workflow schedule in `.github/workflows/daily.yml`
2. [ ] Set review mode to `approve` (for manual review before posting)
3. [ ] Monitor first week of videos before trusting fully

---

## 🎉 Success Criteria

Your bot is ready when:

✅ Pre-flight check passes all tests  
✅ Videos generate in 8-12 minutes  
✅ Camera movements are dynamic  
✅ Subtitles are readable with karaoke effect  
✅ Intro/outro branding looks good  
✅ Scene transitions are smooth  
✅ Characters are recognizably consistent  
✅ Overall quality looks professional  
✅ You'd be proud to post to Instagram  

**When all ✅: You're ready to go viral!** 🚀

---

## 📝 Notes Section

Use this space to record your test results:

**Test Date:** ___________

**Issues Found:**
- 
- 
- 

**What Works Great:**
- 
- 
- 

**Customizations Made:**
- 
- 
- 

**Overall Rating:** ___/10

**Ready for Production?** YES / NO

---

Happy testing! 🎬✨
