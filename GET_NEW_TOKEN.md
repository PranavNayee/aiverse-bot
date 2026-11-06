# 🔑 How to Get New Instagram Access Token

## The Problem
Your Instagram access token expired on **Nov 4, 2026**. Instagram tokens last 60 days and need to be refreshed.

## ✅ Quick Solution (5 minutes)

### Step 1: Generate Short-Lived Token
1. **Open:** https://developers.facebook.com/tools/explorer
2. **Select your app:** Find "cartoon" or app ID `1445425344359379` in dropdown
3. **Click:** "Get User Access Token" (or "Generate Access Token")
4. **Select permissions:**
   - ✅ `instagram_basic`
   - ✅ `instagram_content_publish`
   - ✅ `pages_read_engagement`
   - ✅ `pages_show_list`
5. **Click:** "Generate Access Token"
6. **Login:** with your Instagram Business account if asked
7. **Copy the token** (looks like: `EAAUim1AzK9MB...`)

### Step 2: Convert to Long-Lived Token (60 days)

**Option A: Using Browser**
1. Replace `YOUR_SHORT_TOKEN` in this URL:
```
https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=1445425344359379&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_TOKEN
```

2. Paste in browser, press Enter
3. You'll get JSON response like:
```json
{
  "access_token": "EAAUim1AzK9MB...[LONG_TOKEN]",
  "token_type": "bearer",
  "expires_in": 5183944
}
```
4. Copy the `access_token` value

**Option B: Using Terminal**
```bash
SHORT_TOKEN="PASTE_YOUR_SHORT_TOKEN_HERE"

curl "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=1445425344359379&client_secret=YOUR_APP_SECRET&fb_exchange_token=$SHORT_TOKEN"
```

### Step 3: Update GitHub Secret
```bash
cd /Users/pranavdipakbhainayee/Downloads/cartoon-bot

# Paste your long-lived token here
gh secret set IG_ACCESS_TOKEN --body "PASTE_YOUR_LONG_TOKEN_HERE"
```

### Step 4: Test
```bash
gh workflow run daily.yml
```

---

## 🔄 Automatic Reminder (Optional)

To get reminded before token expires, add this to your calendar:
- **Reminder:** "Refresh Instagram Token"
- **Repeat:** Every 55 days (5 days before expiration)
- **Next due:** January 4, 2027

---

## 📱 Verify Token Works

After updating, verify with:
```bash
NEW_TOKEN="your_token_here"
curl "https://graph.instagram.com/me?fields=id,username&access_token=$NEW_TOKEN"
```

Should return:
```json
{
  "id": "17841479592722450",
  "username": "storysfrombittu"
}
```

---

## 🚨 If Token Still Fails

1. **Check Instagram Account:**
   - Must be a Business or Creator account
   - Must be connected to a Facebook Page
   
2. **Check App Settings:**
   - Go to: https://developers.facebook.com/apps/1445425344359379
   - Check if app is still active
   - Verify Instagram Basic Display is enabled

3. **Regenerate Token:**
   - Sometimes tokens get invalidated (password change, app changes, etc.)
   - Just generate a fresh one following steps above

---

## ✅ Once Token is Updated

Your bot will automatically:
- ✅ Post lessons daily at 8 AM IST
- ✅ Use the deep male voice (Andrew)
- ✅ Generate professional animations
- ✅ Fact-check all content

**The video is already generated and uploaded to Supabase!**
Just need the new token to post it to Instagram.

---

## 🎯 Current Status

- ✅ Video generation: **WORKING** (54.9s video created)
- ✅ Deep voice: **WORKING** (Andrew voice sounds great!)
- ✅ Professional animations: **WORKING** (all 7 scenes rendered)
- ✅ Fact-checking: **WORKING** (script validated)
- ✅ Supabase upload: **WORKING**
- ❌ Instagram posting: **NEEDS NEW TOKEN**

**System is 99% ready - just needs fresh Instagram token!**
