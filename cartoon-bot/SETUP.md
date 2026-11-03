# Hindi Trending Cartoon Reels — Setup Guide (100% free tools)

## How it works
Every day at 8:00 AM IST: trending topics (India) → unsafe ones filtered → Gemini writes a Hindi comic story →
a second Gemini "safety editor" reviews it → images → Hindi voices → video with subtitles, hook line, music ducking and
end card → sent to your Telegram. You reply **/post** to publish or **/skip** to discard.

## Step 1 — GitHub repo
Create a **public** repo (free unlimited Actions minutes) and upload everything in this folder
(including the hidden `.github` folder). Your keys are stored in GitHub Secrets, never in the code.

## Step 2 — Get the free keys
Add each under *Settings → Secrets and variables → Actions → New repository secret*.

| Secret | How to get it |
|---|---|
| `GEMINI_API_KEY` | aistudio.google.com → Get API key |
| `TELEGRAM_BOT_TOKEN` | Telegram → @BotFather → /newbot |
| `TELEGRAM_CHAT_ID` | Send any message to your bot, open `https://api.telegram.org/bot<TOKEN>/getUpdates`, copy `chat` → `id` |
| `SUPABASE_URL` | supabase.com → your project → Project Settings → API → Project URL (`https://xxxx.supabase.co`) |
| `SUPABASE_SERVICE_KEY` | Same page → API Keys → `service_role` (legacy tab) or the `secret` key. **Powerful: keep private** |
| `SUPABASE_BUCKET` | `cartoon-reels` (a **Public** bucket you create under Storage) |
| `CF_API_TOKEN` + `CF_ACCOUNT_ID` *(optional)* | Cloudflare → My Profile → API Tokens → template "Workers AI", and your Cloudflare Account ID. **Backup image generator** if Pollinations is down |
| `IG_USER_ID`, `IG_ACCESS_TOKEN` | Step 4 (do this last) |

## Step 3 — Run the pre-flight check (do this BEFORE Instagram)
GitHub → **Actions → Pre-flight check → Run workflow**.
It tests ffmpeg, the Hindi font, Gemini, Telegram, Supabase storage (including the public URL), image generation and Hindi voice,
and sends a ✅/❌ report to your Telegram. Fix any ❌ (each line says what is wrong) and re-run until all are ✅.
Then run **Actions → Daily cartoon reel → Run workflow** and watch the video arrive on Telegram.
Review the first 5–10 videos carefully before trusting it.

## Step 4 — Instagram API (longest step)
1. Instagram → switch to a **Professional (Creator/Business)** account.
2. Create a Facebook Page and link it to the Instagram account.
3. developers.facebook.com → Create App (type **Business**) → add the **Instagram Graph API** product.
4. Graph API Explorer → select your app → generate a **User token** with permissions:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management`.
5. Convert it to a long-lived user token (Graph API: `GET /oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_TOKEN`).
6. Call `GET /me/accounts?access_token=LONG_USER_TOKEN`. The **Page access token** it returns (derived from a long-lived user token)
   does not expire normally. **Use that Page token as `IG_ACCESS_TOKEN`.** Note the Page `id` too.
7. Call `GET /{page-id}?fields=instagram_business_account&access_token=...` → the `id` inside is `IG_USER_ID`.
8. Re-run the **Pre-flight check**; the Instagram line should show your username.
You do not need app review while you only post to your own account (you're the app admin).

## Step 5 — Daily use
- Each morning you get the video on Telegram. Reply **/post** (or /skip).
- A background workflow checks Telegram every 30 minutes (08:30–21:00 IST) and posts when it sees /post. Approve within 24 hours.
- Want it fully automatic? *Settings → Secrets and variables → Actions → Variables*:
  - `REVIEW_MODE` = `approve` (default, safest) | `auto_unless_skip` (posts after `REVIEW_HOURS`, default 2, unless you /skip) | `auto` (no review)
- Post immediately: Actions → **Post approved reel** → Run workflow → tick *force_post*.

## Step 6 — Customize (src/config.py)
Characters and art style, voices, number of scenes, hashtags, end-card text, and the topic blocklist (`BLOCK_EN`, `BLOCK_HI`).
Put royalty-free `.mp3` files in `assets/music/` for background music (it automatically lowers when someone speaks).

## Safety layers (so a bad joke doesn't go out)
1. Blocklist removes political/religious/violent/tragic topics before the AI sees them.
2. The story prompt forbids sensitive subjects and real-person jokes.
3. Local blocklist re-check on the finished script.
4. A second Gemini call acts as a strict safety editor (fails closed).
5. You approve every video (default mode). No automated filter is perfect — keep `approve` mode for the first weeks.

## Troubleshooting
| Symptom | Fix |
|---|---|
| Pre-flight says Hindi font missing | Workflows install `fonts-noto-core`; if running elsewhere: `sudo apt install fonts-noto-core` |
| "public url returns 400/404" | The Supabase bucket must be switched to **Public** (Storage → bucket → edit → Public bucket) |
| Images fail on all providers | Add the optional `CF_API_TOKEN` backup; or retry later |
| Instagram error "(#10) / permission" | Token lacks `instagram_content_publish`, or the IG account is not Professional/linked to the Page |
| Instagram "media not ready / unsupported format" | Video must be a public MP4 URL (check the Supabase public URL) — pre-flight tests this |
| Nothing arrives on Telegram | You must send your bot a message first; check `TELEGRAM_CHAT_ID` |
| Posting retries 3 times then stops | Fix the cause, then run *Post approved reel* with **force_post** |
| Scheduled runs stopped | GitHub pauses idle repos after 60 days; the daily job makes a monthly keep-alive commit to prevent this |

## Honest limits
- Free image generators vary: characters can look slightly different day to day.
- Supabase free tier: 1 GB storage, 50 MB per file; the bot auto-deletes old videos (keeps the newest 30 files). Free projects pause after ~7 days with no activity; the daily job keeps it active.
- Free tiers change; if one stops working the backups/fallbacks help, but check occasionally.
- Instagram requires AI-content labeling: captions say "AI-generated cartoon"; also use Instagram's AI label toggle.
