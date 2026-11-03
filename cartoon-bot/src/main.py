import datetime, os, shutil, sys, time, traceback
import config as C, trends, story as S, images, voice, video, storage, notify, instagram, insights
from util import log

def build_caption(st):
    tags = list(dict.fromkeys(st.get("hashtags", []) + C.CHANNEL_HASHTAGS))[:15]
    return f"{st['caption']}\n\n🤖 AI-generated cartoon\n\n{' '.join(tags)}"

def run():
    t0 = time.time()
    shutil.rmtree("work", ignore_errors=True); os.makedirs("work")
    history = storage.get_json("history.json", [])
    old = storage.get_json("pending.json", None)

    st = S.make_story(trends.get_trends(), [h["topic"] for h in history[-30:]], insights.performance_hints(history))
    log(f"Topic: {st['topic']} | Title: {st['title']} | Hook: {st['hook']}")

    clips, timing, first_img, t = [], [], None, 0.0
    for i, sc in enumerate(st["scenes"]):
        log(f"Scene {i+1}/{len(st['scenes'])}")
        img = images.make_image(sc, f"work/s{i}")
        first_img = first_img or img
        aud = f"work/s{i}.mp3"
        voice.synth(sc["narration"], sc["speaker"], aud)
        dur = voice.duration(aud) + 0.45
        clip = f"work/s{i}.mp4"
        video.scene_clip(img, aud, dur, i, clip)
        clips.append(clip); timing.append((t, dur, sc["narration"])); t += dur

    final = "work/final.mp4"
    length = video.assemble("work", timing, clips, final, hook=st["hook"])
    if not (C.MIN_SECONDS <= length <= C.MAX_SECONDS):
        raise RuntimeError(f"Video length {length:.1f}s is outside {C.MIN_SECONDS}-{C.MAX_SECONDS}s")
    size_mb = os.path.getsize(final) / 1e6
    log(f"Video ready: {length:.1f}s, {size_mb:.1f} MB")

    day = datetime.date.today().isoformat()
    stamp = datetime.datetime.utcnow().strftime("%H%M")
    url = storage.upload_file(final, f"reels/{day}-{stamp}.mp4")
    ext = first_img.rsplit(".", 1)[-1]
    cover = storage.upload_file(first_img, f"reels/{day}-{stamp}-cover.{ext}", f"image/{'jpeg' if ext=='jpg' else ext}")
    caption = build_caption(st)
    entry = {"date": day, "topic": st["topic"], "title": st["title"]}

    if C.REVIEW_MODE == "auto":
        entry["media_id"] = instagram.post_reel(url, caption, cover)
        history.append(entry)
        storage.put_json("history.json", history[-100:])
        notify.video(final, f"✅ Posted automatically ({length:.0f}s)\n\n{caption}", url)
    else:
        history.append(entry)
        storage.put_json("history.json", history[-100:])
        storage.put_json("pending.json", {"video_url": url, "cover_url": cover, "caption": caption, "date": day,
                                          "topic": st["topic"], "created_ts": int(time.time()), "attempts": 0})
        how = ("Reply /post to publish or /skip to discard." if C.REVIEW_MODE == "approve" else
               f"It will post automatically in {C.REVIEW_HOURS:g}h unless you reply /skip.")
        warn = "\n⚠️ The previous video was never posted and has been replaced." if old else ""
        notify.video(final, f"🎬 Ready ({length:.0f}s) — {st['topic']}\n\n{caption}\n\n👉 {how}{warn}", url)
    try:
        storage.cleanup("reels", keep=30)      # stay inside the free 1 GB
    except Exception as e:
        log("Cleanup skipped:", e)
    log(f"Done in {time.time()-t0:.0f}s")

if __name__ == "__main__":
    last_err = ""
    for attempt in (1, 2):
        try:
            run()
            sys.exit(0)
        except Exception:
            last_err = traceback.format_exc()
            log(f"--- attempt {attempt} failed ---\n{last_err}")
            time.sleep(20)
    notify.text("❌ Cartoon bot failed today (nothing posted):\n" + last_err[-1500:])
    sys.exit(1)
