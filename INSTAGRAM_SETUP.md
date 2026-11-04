# 📱 Instagram Graph API Setup Guide

Complete guide to connect your Instagram account (@storysfrombittu) to the cartoon bot for automated posting.

---

## ⚠️ Important Security Notes

- ✅ We use **Access Tokens** (official Instagram API)
- ✅ Tokens are stored as **encrypted GitHub Secrets**
- ✅ Tokens can be **revoked anytime**
- ✅ **NEVER** store passwords in code
- ✅ This is Instagram's **official automation method**

---

## 📋 Prerequisites Checklist

Before starting, verify:

- [ ] Instagram account: **@storysfrombittu**
- [ ] Account is active and in good standing
- [ ] You have access to the account
- [ ] You have access to a Facebook account

---

## Phase 1: Convert to Business/Creator Account

### Step 1.1: Switch Account Type

1. **Open Instagram app** on your phone
2. Go to **Profile** (bottom right)
3. Tap **☰ Menu** (top right) → **Settings**
4. Tap **Account**
5. Scroll down → **Switch to Professional Account**
6. Choose account type:
   - Select **Creator** (recommended for content creators)
   - Or **Business** (either works)
7. Select category: **Entertainment** or **Video Creator**
8. Tap **Done**

**Verify:** Your profile should now show "Creator" or "Business" under your name.

---

## Phase 2: Create & Link Facebook Page

### Step 2.1: Create Facebook Page

1. Go to [facebook.com/pages/create](https://facebook.com/pages/create)
2. Click **Get Started**
3. Fill in:
   - **Page Name:** Storys From Bittu
   - **Category:** Entertainment Website or Video Creator
   - **Bio:** Daily Hindi cartoon comedy reels featuring Bablu & Chiku
4. Click **Create Page**
5. Skip adding profile picture for now (can add later)

**Note:** Keep this Facebook tab open, you'll need the Page ID later.

### Step 2.2: Get Facebook Page ID

1. On your new Facebook Page, click **About**
2. Scroll down to find **Page ID**
3. Copy the number (example: `123456789012345`)
4. **Save this ID** - you'll need it!

### Step 2.3: Link Instagram to Facebook Page

**Option A: Via Instagram App (Recommended)**
1. Instagram app → Profile → ☰ Menu → **Settings**
2. Tap **Account**
3. Tap **Linked Accounts**
4. Tap **Facebook**
5. Log in to Facebook
6. Select your page: **Storys From Bittu**
7. Tap **Allow**

**Option B: Via Facebook**
1. Go to your Facebook Page
2. Click **Settings** (left sidebar)
3. Click **Instagram** (left menu)
4. Click **Connect Account**
5. Log in to Instagram
6. Authorize the connection

**Verify:** 
- Instagram Profile → Edit Profile → Should show "Page: Storys From Bittu"
- OR Instagram Settings → Account → Linked Accounts → Facebook should show ✓

---

## Phase 3: Create Meta (Facebook) Developer App

### Step 3.1: Register as Developer

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Click **Get Started** (top right)
3. Log in with your Facebook account
4. Click **Continue** to register as developer
5. Accept terms and conditions

### Step 3.2: Create New App

1. Click **My Apps** (top right)
2. Click **Create App**
3. Select use case: **Other**
4. Click **Next**
5. Select app type: **Business**
6. Click **Next**
7. Fill in details:
   - **App Name:** Cartoon Bot (or any name you like)
   - **App Contact Email:** Your email
   - **Business Account:** (leave as is or create new)
8. Click **Create App**
9. Complete security check if prompted

**Save:** Your **App ID** (shown at top of page)

### Step 3.3: Add Instagram Product

1. In your new app dashboard, scroll to **Add Products**
2. Find **Instagram** → Click **Set Up**
3. Also add **Instagram Graph API** if separate option
4. Click through any setup wizards

---

## Phase 4: Get Access Token & Permissions

### Step 4.1: Configure App Settings

1. In app dashboard, left sidebar → **Settings** → **Basic**
2. Scroll down to **App Domains**
3. Add: `github.com` (for GitHub Actions)
4. Scroll to bottom → Click **Save Changes**

### Step 4.2: Add Facebook Page to App

1. Left sidebar → **App Roles** or **Roles**
2. Find section for **Test Users** or **Testers**
3. Add your Facebook account as admin/tester

### Step 4.3: Generate Access Token

1. Go to [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer)
2. Top right dropdown → Select your app: **Cartoon Bot**
3. Click **Generate Access Token**
4. In permissions popup, add these permissions:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`
5. Click **Generate Access Token**
6. **IMPORTANT:** Copy this token and save it temporarily (you'll upgrade it next)

**This is a short-lived token (1 hour). We'll convert it to long-lived next.**

### Step 4.4: Get Instagram Business Account ID

1. In Graph API Explorer (same page)
2. Replace the query with:
   ```
   /{YOUR_FACEBOOK_PAGE_ID}?fields=instagram_business_account
   ```
   (Replace `{YOUR_FACEBOOK_PAGE_ID}` with the number you saved earlier)
3. Click **Submit**
4. Response will show:
   ```json
   {
     "instagram_business_account": {
       "id": "17841XXXXXXXXXX"
     },
     "id": "123456789012345"
   }
   ```
5. **Copy the instagram_business_account ID** (the 17841... number)
6. **Save this** - this is your `IG_USER_ID`!

### Step 4.5: Convert to Long-Lived Token (60 days)

1. In Graph API Explorer, make this request:
   ```
   /oauth/access_token?grant_type=fb_exchange_token&client_id={YOUR_APP_ID}&client_secret={YOUR_APP_SECRET}&fb_exchange_token={YOUR_SHORT_LIVED_TOKEN}
   ```
   
2. **Get YOUR_APP_SECRET:**
   - Go back to your app dashboard
   - Left sidebar → **Settings** → **Basic**
   - Find **App Secret** → Click **Show**
   - Copy it

3. **Fill in the request:**
   - Replace `{YOUR_APP_ID}` with your App ID
   - Replace `{YOUR_APP_SECRET}` with your App Secret
   - Replace `{YOUR_SHORT_LIVED_TOKEN}` with the token from Step 4.3

4. Click **Submit**

5. Response will be:
   ```json
   {
     "access_token": "EAAxxxxxxxxxxxxxxxxxxxxxxx",
     "token_type": "bearer",
     "expires_in": 5184000
   }
   ```

6. **Copy this new access_token** - this is your `IG_ACCESS_TOKEN`!
7. This token lasts **60 days**

**Important:** You'll need to refresh this token every 60 days. Instagram API requires periodic renewal.

---

## Phase 5: Add Secrets to GitHub

### Step 5.1: Add Instagram Secrets

1. Go to your GitHub repo: [github.com/PranavNayee/cartoon-bot](https://github.com/PranavNayee/cartoon-bot)
2. Click **Settings** (top tab)
3. Left sidebar → **Secrets and variables** → **Actions**
4. Click **New repository secret**

**Add Secret #1:**
- Name: `IG_USER_ID`
- Value: (paste the Instagram Business Account ID from Step 4.4)
- Click **Add secret**

**Add Secret #2:**
- Name: `IG_ACCESS_TOKEN`
- Value: (paste the long-lived access token from Step 4.5)
- Click **Add secret**

### Step 5.2: Verify Secrets

You should now have these secrets:
- ✅ `GEMINI_API_KEY`
- ✅ `TELEGRAM_BOT_TOKEN`
- ✅ `TELEGRAM_CHAT_ID`
- ✅ `SUPABASE_URL`
- ✅ `SUPABASE_SERVICE_KEY`
- ✅ `SUPABASE_BUCKET`
- ✅ `IG_USER_ID` ← NEW
- ✅ `IG_ACCESS_TOKEN` ← NEW

---

## Phase 6: Test Instagram Integration

### Step 6.1: Run Pre-Flight Check

1. GitHub repo → **Actions** tab
2. Left sidebar → **Pre-flight check**
3. Click **Run workflow** → **Run workflow**
4. Wait 2-3 minutes
5. Check results - Instagram section should show:
   - ✅ **Instagram credentials present**
   - ✅ **Instagram API connection works**

**If ❌ error:**
- Check that tokens were copied correctly (no extra spaces)
- Verify Facebook Page is linked to Instagram
- Confirm Instagram account is Business/Creator type

### Step 6.2: Test Posting (Optional)

To test without generating a full video:

1. Download a test video to your computer
2. Go to GitHub Actions → **Post approved reel**
3. (This requires a video to be in Supabase first)

**Better approach:** Generate a full video first, then approve it via Telegram, then test posting.

---

## Phase 7: Generate & Post Your First Video

### Step 7.1: Generate Video

1. GitHub → **Actions** → **Daily cartoon reel**
2. Click **Run workflow** → **Run workflow**
3. Wait 10-15 minutes
4. Video will arrive on Telegram

### Step 7.2: Review & Approve

1. Check your Telegram
2. Watch the video
3. Send `/post` to approve
4. Bot will automatically post to Instagram!

### Step 7.3: Verify on Instagram

1. Open Instagram app
2. Go to your profile: **@storysfrombittu**
3. Check your Reels tab
4. Your video should be there! 🎉

---

## 🔄 Token Maintenance

### Long-Lived Token Expires After 60 Days

**30 days before expiration, refresh the token:**

1. Go to Graph API Explorer
2. Use current token to request new one:
   ```
   /oauth/access_token?grant_type=fb_exchange_token&client_id={APP_ID}&client_secret={APP_SECRET}&fb_exchange_token={CURRENT_TOKEN}
   ```
3. Update GitHub secret with new token

**Or use automatic refresh (advanced):**
- Instagram API can auto-refresh tokens if used frequently
- Your daily posts will keep the token alive
- Still check every 60 days to be safe

---

## 📊 Posting Workflow After Setup

Once configured, here's your daily workflow:

### Automatic Mode:
1. **8:00 AM IST** - Bot generates video automatically
2. Video posts to Telegram for review
3. You send `/post` (or `/skip`)
4. Bot posts to Instagram automatically
5. **Done!** Takes 30 seconds of your time

### Configuration Options:

**`REVIEW_MODE` variable** (GitHub → Settings → Variables):
- `approve` (default) - You review every video before posting
- `auto_unless_skip` - Posts automatically unless you say `/skip` within review hours
- `auto` - Full automation, posts without approval (use carefully!)

---

## 🛠️ Troubleshooting

### Error: "Invalid User ID"
**Fix:** 
- Verify you used Instagram Business Account ID (17841...), not Page ID
- Re-check Step 4.4

### Error: "Insufficient Permissions"
**Fix:**
- Regenerate token with all required permissions
- Ensure permissions include: `instagram_basic`, `instagram_content_publish`

### Error: "Invalid Access Token"
**Fix:**
- Token may have expired (60 day limit)
- Regenerate long-lived token (Step 4.5)
- Update GitHub secret

### Error: "Account Not Linked"
**Fix:**
- Verify Instagram is linked to Facebook Page
- Check Settings → Linked Accounts in Instagram app

### Error: "Publishing Failed"
**Fix:**
- Instagram has rate limits (don't post too frequently)
- Wait 10 minutes between posts
- Check video meets Instagram requirements (max 60 sec, vertical format)

### Token Expires Warning
**Fix:**
- Tokens last 60 days
- Set calendar reminder to refresh every 2 months
- Or switch to `approve` mode and manually post if token expires

---

## ✅ Success Checklist

Setup is complete when:

- [ ] Instagram account is Business/Creator type
- [ ] Facebook Page created and linked to Instagram
- [ ] Meta Developer App created
- [ ] Long-lived access token generated (60 days)
- [ ] `IG_USER_ID` added to GitHub Secrets
- [ ] `IG_ACCESS_TOKEN` added to GitHub Secrets
- [ ] Pre-flight check passes Instagram tests ✅
- [ ] First video generated successfully
- [ ] Test post to Instagram works 🎉

---

## 📱 Instagram Best Practices

### Posting Guidelines:
- ✅ Post 1-3 times per day maximum
- ✅ Best times: 6-9 AM, 12-2 PM, 6-9 PM IST
- ✅ Use all 30 hashtags (bot does this automatically)
- ✅ Include caption with emojis (bot generates this)
- ✅ Enable Instagram's AI label (Settings → Account → Labels)

### Content Guidelines:
- ✅ Keep videos under 60 seconds (bot makes ~40 sec videos)
- ✅ Vertical format 9:16 (bot uses 1080x1920) ✅
- ✅ Include hook in first 3 seconds (bot does this) ✅
- ✅ Add CTA at end (bot adds "Follow for more") ✅
- ✅ Use trending audio/music (add to `assets/music/`)

### Growth Tips:
- 📈 Post consistently (daily schedule works best)
- 📈 Reply to comments quickly
- 📈 Use Instagram's AI label transparency
- 📈 Cross-post to other platforms
- 📈 Analyze Insights to see what works

---

## 🎉 You're All Set!

Your cartoon bot can now:
- ✅ Generate videos automatically
- ✅ Post to Instagram via official API
- ✅ Handle captions and hashtags
- ✅ Send preview to Telegram first
- ✅ Wait for your `/post` approval
- ✅ Track posted videos in Supabase

**Daily workflow:** Check Telegram → Watch video → Send `/post` → Done! 🚀

---

## 📚 Additional Resources

- [Instagram Content Publishing API Docs](https://developers.facebook.com/docs/instagram-api/guides/content-publishing)
- [Instagram API Rate Limits](https://developers.facebook.com/docs/instagram-api/overview#rate-limiting)
- [Graph API Explorer](https://developers.facebook.com/tools/explorer)
- [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken)

---

## 🆘 Need Help?

If you get stuck:
1. Check the Troubleshooting section above
2. Verify all steps were completed in order
3. Check GitHub Actions logs for specific errors
4. Review Instagram API documentation
5. Test token in Graph API Explorer

---

**Happy posting!** 📱✨
