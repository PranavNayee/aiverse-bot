# 🔑 Complete Instagram Token Setup Guide

## Current Issue
The tokens you provided aren't working for Instagram Graph API. This usually means we need to generate a token with the correct permissions and from the right place.

---

## ✅ **CORRECT Way to Get Instagram Token**

### Step 1: Open Graph API Explorer
Go to: **https://developers.facebook.com/tools/explorer**

### Step 2: Select Your App
1. In the top-left dropdown, select: **"cartoon"** or App ID **1445425344359379**
2. Make sure you see your app name in the dropdown

### Step 3: Get User Access Token
1. Click **"Get User Access Token"** button
2. A permissions dialog will appear

### Step 4: Select Instagram Permissions
**CRITICAL:** Check these exact permissions:
- ✅ `instagram_basic`
- ✅ `instagram_content_publish`
- ✅ `pages_read_engagement`
- ✅ `pages_show_list`
- ✅ `pages_manage_metadata`

### Step 5: Generate Token
1. Click **"Generate Access Token"**
2. You may need to:
   - Login with your Facebook account
   - Select the Facebook Page connected to Instagram
   - Confirm permissions

### Step 6: Copy the Short-Lived Token
1. After generation, you'll see a long token in the "Access Token" field
2. **Copy the ENTIRE token** (should start with `EAAUim1...`)
3. This is a SHORT-LIVED token (1 hour)

### Step 7: Convert to Long-Lived Token (60 days)
Run this in terminal (replace `YOUR_SHORT_TOKEN`):

```bash
cd /Users/pranavdipakbhainayee/Downloads/cartoon-bot

SHORT_TOKEN="PASTE_YOUR_SHORT_TOKEN_HERE"

curl "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=1445425344359379&client_secret=cac042373d9d2c94c86c0a2d6229621f&fb_exchange_token=$SHORT_TOKEN"
```

This will return:
```json
{
  "access_token": "EAAUim1AzK9MB...[LONG_TOKEN]",
  "token_type": "bearer",
  "expires_in": 5184000
}
```

### Step 8: Test the Long-Lived Token
```bash
LONG_TOKEN="PASTE_LONG_TOKEN_FROM_ABOVE"

# Test it works
curl "https://graph.instagram.com/me?fields=id,username&access_token=$LONG_TOKEN"
```

Should return:
```json
{
  "id": "17841479592722450",
  "username": "storysfrombittu"
}
```

### Step 9: Update GitHub Secret
```bash
cd /Users/pranavdipakbhainayee/Downloads/cartoon-bot

gh secret set IG_ACCESS_TOKEN --body "PASTE_LONG_TOKEN_HERE"
```

### Step 10: Test the Bot
```bash
gh workflow run daily.yml
```

---

## 🔍 **Troubleshooting**

### Problem: "Invalid OAuth access token"
**Solution:** The token might be for Facebook, not Instagram. Make sure:
1. Your Instagram account is a **Business** or **Creator** account
2. It's connected to a **Facebook Page**
3. You selected the Instagram permissions (not just Facebook ones)

### Problem: "No Instagram account found"
**Solution:** 
1. Go to Instagram app → Settings → Account → Switch to Professional Account
2. Choose Business or Creator
3. Connect to your Facebook Page

### Problem: Token works but can't post
**Solution:** Check these permissions are granted:
- `instagram_content_publish` (required for posting)
- `pages_read_engagement` (required for insights)

### Problem: Token expires quickly
**Solution:** Make sure you converted to long-lived token (Step 7). Long-lived tokens last 60 days.

---

## 📱 **Verify Your Instagram Setup**

### Check 1: Is it a Business Account?
1. Open Instagram app
2. Go to Profile → ≡ Menu → Settings
3. Should say "Switch to Personal Account" (meaning you're currently Business/Creator)

### Check 2: Is it Connected to Facebook?
1. Instagram app → Profile → ≡ Menu → Settings
2. Account → Linked accounts → Facebook
3. Should show your Facebook Page name

### Check 3: Can You Access Instagram Professional Dashboard?
Go to: https://business.facebook.com/instagram
Should see your Instagram account @storysfrombittu

---

## 🎯 **Alternative: Use Meta Business Suite**

If Graph API Explorer is confusing:

1. Go to: **https://business.facebook.com**
2. Select your Facebook Page
3. Settings → Instagram → Generate Token
4. Follow the prompts

---

## ✅ **Once Token is Working**

Your bot will:
- ✅ Post automatically at 8 AM IST daily
- ✅ Use deep male voice (Andrew)
- ✅ Generate professional animations
- ✅ Fact-check all content
- ✅ Post to @storysfrombittu

**The video for Lesson #2 is already created and waiting!**
Just need the working token to post it.

---

## 📞 **Still Having Issues?**

If you're still stuck after trying the above:

1. **Check your Instagram account type:**
   ```
   Is it Business or Creator? (Not Personal)
   ```

2. **Check Facebook Page connection:**
   ```
   Is your Instagram linked to a Facebook Page?
   ```

3. **Check app permissions:**
   - Go to: https://developers.facebook.com/apps/1445425344359379/instagram-basic-display/basic-display/
   - Make sure Instagram Basic Display is configured

4. **Try regenerating everything:**
   - Sometimes the cleanest solution is to disconnect and reconnect Instagram to Facebook Page
   - Then generate a fresh token

---

## 🔔 **Reminder**

Tokens expire every 60 days. Set a calendar reminder for **January 3, 2027** to refresh the token before it expires.

---

**Your bot is 99% ready - just needs a valid Instagram token!** 🚀
