# Bablu ka Vlog — Hindi 3D-style trending cartoon Reels (free tools only)

## What it makes
Every day (8:00 AM IST): trending topic (India) → unsafe topics filtered → Gemini writes a Hindi vlog-comedy episode
→ safety-editor review → Pixar-style 3D images of Bablu (monkey) and Chiku (crow) → free AI depth model makes each
picture move in 3D (parallax camera) → talking-mouth effect synced to the Hindi voice → beat-zoom, reactions, emoji
stickers, coloured subtitles, hook line, end card, ducked music → Telegram preview.
Reply **/post** to publish or **/skip** to discard.

## Updating an existing repo (you already created `cartoon-bot` on GitHub)
1. Unzip the new zip. In your repo: delete the old `src`, `tests`, `assets` folders and old files (open each → trash icon → commit),
   then **upload everything from the new unzipped folder** (drag in `src`, `tests`, `assets`, `extras`, `requirements.txt`, `SETUP.md`, `workflows_copy`).
2. Workflows: the hidden `.github` folder is easy to miss. Easiest way: in the repo open `workflows_copy/daily.yml` → pencil (edit) icon →
   change the file name box from `workflows_copy/daily.yml` to `.github/workflows/daily.yml` → Commit. Repeat for `post.yml` and `check.yml`
   (if they already exist in `.github/workflows`, open them and paste the new content instead).
3. Add the new optional variable if you want (Settings → Secrets and variables → Actions → Variables): `MOUTH_FX` = `false` turns the talking-mouth effect off.

## Secrets (Settings → Secrets and variables → Actions → New repository secret)
| Secret | Where |
|---|---|
| `GEMINI_API_KEY` | aistudio.google.com |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | @BotFather, then `getUpdates` |
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_BUCKET` | supabase.com (public bucket `cartoon-reels`) |
| `CF_API_TOKEN` + `CF_ACCOUNT_ID` *(optional)* | Cloudflare Workers AI backup image generator |
| `IG_USER_ID`, `IG_ACCESS_TOKEN` | Instagram setup (last) |

## Run order
1. **Actions → Pre-flight check → Run workflow.** First run is slow (installs torch, downloads the depth model ~10 min). It reports ✅/❌ for
   Gemini, Telegram, Supabase, image generation, **depth model**, **mouth detection**, the **3D animation engine**, voice, and Instagram.
   Fix every ❌ (lines marked ⚠️ are optional features that fall back gracefully).
2. **Actions → Daily cartoon reel → Run workflow.** Expect 10–20 minutes. Video arrives on Telegram.
3. Look at the first 5–10 videos carefully before trusting it. Then Instagram setup, then `/post`.

## Controls (Variables)
`REVIEW_MODE` = `approve` (default) | `auto_unless_skip` | `auto`  ·  `REVIEW_HOURS`  ·  `MOUTH_FX` = `true`/`false`

## Customize (src/config.py)
Characters (`CHARACTERS`: look + personality), series name, art style (`STYLE_3D`), voices/pitch, number of scenes, hashtags,
topic blocklist. Put royalty-free `.mp3` files in `assets/music/`. (Copyrighted film songs will be muted/claimed; Instagram's API cannot add licensed music.)
The older 2D puppet engine is kept in `extras/puppet_2d/` (not used).

## Honest limits
- This is a **2.5D** look: still AI pictures that move with depth parallax, zooms, reactions and a talking-mouth effect. It is **not** true AI video
  (like Kling/Veo): limbs and bodies don't move. The talking-mouth effect depends on Gemini locating the mouth; if it looks bad, set `MOUTH_FX=false`.
- Free image generation isn't perfectly consistent: Bablu will look similar, not identical, between scenes and days.
- Free tiers change. The bot has fallbacks, but check occasionally. Kling/other paid video can be added later as a plug-in step.
- Safety layers: blocklist → prompt rules → local re-check → second Gemini safety editor → your approval. Keep `approve` mode for the first weeks.
- Captions say "AI-generated cartoon"; also use Instagram's AI label toggle.

## Troubleshooting
| Symptom | Fix |
|---|---|
| Pre-flight: depth ⚠️ "unavailable" | Videos still work with simple depth. Check the log for the model download error and re-run |
| Pre-flight: mouth ⚠️ | Normal for some images; set `MOUTH_FX=false` if results look odd |
| Pre-flight: Supabase "public url returns 400/404" | Make the bucket **Public** |
| Image generation ❌ | Add the optional Cloudflare backup (`CF_API_TOKEN`, `CF_ACCOUNT_ID`) or retry later |
| Nothing on Telegram | Message your bot first; check `TELEGRAM_CHAT_ID` |
| Instagram permission error | Token needs `instagram_content_publish`; IG must be Creator/Business linked to a Facebook Page |
| Posting stops after 3 tries | Fix the cause, then run *Post approved reel* with **force_post** |
