"""Weekly long-form YouTube video: the week's reels stitched into one 16:9 'This Week in AI' video with an intro,
side title panels, chapters and a thumbnail. Long videos earn far more per view than Shorts and count towards the
4,000 watch-hours route into the YouTube Partner Program. Runs every Sunday evening (weekly.yml). Free: ffmpeg + API."""
import os, re, subprocess, sys, time
import numpy as np
from PIL import Image, ImageDraw
import config as C, storage, notify, youtube, slots
import edu_render as E, mascot
from util import log

W, H = 1920, 1080
WORK = "weekly_work"
TEAL, ORANGE = (45, 212, 191), (251, 146, 60)


def _bg():
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    top, bot = np.array((13, 15, 38), np.float32), np.array((40, 24, 86), np.float32)
    img = Image.fromarray(((top + (bot - top) * y)[:, None, :].repeat(W, 1)).astype(np.uint8), "RGB")
    for cx, cy, r, c in ((420, 380, 420, TEAL), (1500, 760, 460, (129, 140, 248))):
        g = E.glow_sprite(r * 2, c, 0.4); img.paste(g, (cx - r, cy - r), g)
    return img


def card(path, title, lines, foot):
    img = _bg(); d = ImageDraw.Draw(img, "RGBA")
    bot = mascot.sprite(TEAL, 2, False, "happy", 21, 1.6)
    img.paste(bot, (150, H // 2 - bot.height // 2), bot)
    d.text((640, 300), title, font=E.font(96), fill=(244, 246, 255), anchor="lm")
    d.rounded_rectangle((640, 370, 960, 382), 6, fill=TEAL)
    for i, ln in enumerate(lines[:7]):
        d.text((650, 450 + i * 62), ln[:58], font=E.font(42, False), fill=(214, 220, 240), anchor="lm")
    d.text((640, 960), foot, font=E.font(44), fill=ORANGE, anchor="lm")
    img.save(path)


def side_panel(path, label, title):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle((60, 380, 600, 700), 36, fill=(10, 12, 30, 200), outline=TEAL + (255,), width=4)
    d.text((100, 440), label, font=E.font(40), fill=TEAL + (255,), anchor="lm")
    f, lines, size = E.fit(d, title, 460, 200, 56, 34)
    for i, ln in enumerate(lines[:3]):
        d.text((100, 520 + i * size * 1.2), ln, font=f, fill=(244, 246, 255, 255), anchor="lm")
    d.rounded_rectangle((1340, 470, 1860, 610), 40, fill=(255, 0, 51, 230))
    d.text((1600, 540), f"SUBSCRIBE @ {C.SERIES_NAME}", font=E.font(34), fill=(255, 255, 255), anchor="mm")
    img.save(path)


ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-r", "30",
       "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2"]


def still(png, secs, out):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", str(secs), "-i", png, "-f", "lavfi", "-t", str(secs),
                    "-i", "anullsrc=r=44100:cl=stereo", "-vf", f"scale={W}:{H}", *ENC, "-shortest", out], check=True)


def segment(clip, panel, out):
    fc = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:2,eq=brightness=-0.28[bg];"
          f"[0:v]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0[v1];[v1][1:v]overlay=0:0[v]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", clip, "-i", panel, "-filter_complex", fc, "-map", "[v]",
                    "-map", "0:a", *ENC, out], check=True)


def duration(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def ts(sec):
    sec = int(sec)
    return f"{sec // 60}:{sec % 60:02d}"


LABEL = {"lesson": "AI COURSE", "trick": "AI TRICK", "news": "AI NEWS", "fun_fact": "FUN FACT"}


def main():
    if not youtube.enabled():
        log("YouTube not connected - skipping weekly video"); return
    week = slots.now().strftime("%G-W%V")
    state = storage.get_json("weekly.json", {})
    if state.get("last_week") == week and os.environ.get("FORCE_WEEKLY") != "true":
        log("This week's long video is already up."); return
    history = storage.get_json("history.json", [])
    cutoff = time.time() - 7 * 86400
    posted = [h for h in history if (h.get("posted_ts") or 0) >= cutoff and h.get("slot")
              and str(h.get("media_id", "")).isdigit()]
    names = storage.list_names("lessons")
    picks = []
    for h in posted:
        f = [n for n in names if n.startswith(h["slot"])]
        if f:
            picks.append((h, storage.public_url(f"lessons/{f[-1]}")))
    if len(picks) < 4:
        log(f"Only {len(picks)} reels this week - need 4+ for a long video."); return
    os.makedirs(WORK, exist_ok=True)
    import requests
    parts, chapters, t = [], [], 0.0
    titles = [h.get("topic", "") for h, _ in picks]
    card(f"{WORK}/intro.png", "This Week in AI", [f"• {x}" for x in titles], f"{len(picks)} videos · Hinglish · {C.SERIES_NAME}")
    still(f"{WORK}/intro.png", 5, f"{WORK}/p_intro.mp4"); parts.append(f"{WORK}/p_intro.mp4")
    chapters.append(f"0:00 Is hafte kya seekha"); t += 5
    for i, (h, url) in enumerate(picks):
        clip = f"{WORK}/c{i}.mp4"
        with open(clip, "wb") as fh:
            fh.write(requests.get(url, timeout=300).content)
        label = LABEL.get(h.get("type"), "AI") + (f" #{h['lesson_num']}" if h.get("lesson_num") else "")
        side_panel(f"{WORK}/s{i}.png", label, h.get("topic", ""))
        seg = f"{WORK}/p{i}.mp4"
        segment(clip, f"{WORK}/s{i}.png", seg)
        nice = {"AI COURSE": "AI Course", "AI TRICK": "AI Trick", "AI NEWS": "AI News", "FUN FACT": "Fun Fact"}
        pretty = label.replace(label.split(" #")[0], nice.get(label.split(" #")[0], label.split(" #")[0]))
        parts.append(seg); chapters.append(f"{ts(t)} {pretty}: {h.get('topic', '')}"[:90]); t += duration(seg)
    card(f"{WORK}/outro.png", "Roz naya AI video!", ["Subscribe karo aur bell icon dabao 🔔", "",
         "Lessons · AI Tricks · AI News · Fun Facts", "Har din subah 8 baje aur shaam 7 baje"], f"@{C.SERIES_NAME}")
    still(f"{WORK}/outro.png", 5, f"{WORK}/p_outro.mp4"); parts.append(f"{WORK}/p_outro.mp4")
    chapters.append(f"{ts(t)} Subscribe")
    with open(f"{WORK}/list.txt", "w") as fh:
        fh.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    out = f"{WORK}/weekly.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{WORK}/list.txt", "-c", "copy",
                    "-movflags", "+faststart", out], check=True)
    total = duration(out)
    # thumbnail
    th = _bg().resize((1280, 720)); d = ImageDraw.Draw(th, "RGBA")
    bot = mascot.sprite(TEAL, 2, False, "surprised", 21, 1.2); th.paste(bot, (60, 720 // 2 - bot.height // 2), bot)
    d.text((440, 250), f"{len(picks)} AI cheezein", font=E.font(96), fill=(255, 255, 255), anchor="lm")
    d.text((440, 370), "is hafte!", font=E.font(96), fill=ORANGE, anchor="lm")
    d.text((440, 480), "Hinglish mein, simple", font=E.font(52, False), fill=(214, 220, 240), anchor="lm")
    th.convert("RGB").save(f"{WORK}/thumb.jpg", quality=92)
    title = f"This Week in AI (Hinglish) | {len(picks)} AI Lessons & Tricks in {max(1, round(total / 60))} Minutes | {C.SERIES_NAME}"
    desc = (f"Is hafte {C.SERIES_NAME} pe kya seekha - sab ek video mein! 🤖\n\n" + "\n".join(chapters) +
            "\n\nRoz subah 8 baje aur shaam 7 baje naya AI video. Subscribe karo! 🔔\n\n"
            "#AIinHindi #ChatGPT #MachineLearning #ArtificialIntelligence #AIVerse")
    vid = youtube.upload(out, desc, title, "This Week in AI", ["AI in Hindi", "ChatGPT tips", "machine learning"],
                         title=title, shorts=False)
    youtube.set_thumbnail(vid, f"{WORK}/thumb.jpg")
    youtube.add_to_playlist(vid, "weekly")
    storage.put_json("weekly.json", {"last_week": week, "video_id": vid, "ts": int(time.time())})
    notify.text(f"🎬 Weekly long video is up ({ts(total)}): https://youtube.com/watch?v={vid}")
    log(f"Weekly video: https://youtube.com/watch?v={vid} ({ts(total)})")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback; traceback.print_exc(); sys.exit(1)
