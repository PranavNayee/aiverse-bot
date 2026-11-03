import datetime, os, shutil, sys, time, traceback
import config as C, trends, story as S, storage, notify, instagram, insights
from util import log

# Always use the image pipeline — free, fast, reliable
USE_AI_VIDEO = False

def build_caption(st):
    tags = list(dict.fromkeys(st.get("hashtags", []) + C.CHANNEL_HASHTAGS))[:15]
    return f"{st['caption']}\n\n🤖 AI-generated cartoon\n\n{' '.join(tags)}"

def run_ai_video(st):
    """Generate reel using fal.ai AI video (one real video clip per scene)."""
    import video_ai, video
    clips, timing, t = [], [], 0.0

    for i, sc in enumerate(st["scenes"]):
        log(f"Scene {i+1}/{len(st['scenes'])} (AI video)")
        narration = sc["narration"]

        # Estimate duration from narration word count (approx 3 words/sec for Hindi TTS)
        words = len(narration.split())
        est_dur = max(3.5, words / 3.0 + 0.5)
        clip_dur = max(3, min(10, int(round(est_dur))))

        clip_path = f"work/s{i}.mp4"
        video_ai.make_video_clip(
            scene=sc,
            narration=narration,
            duration=clip_dur,
            out_path=clip_path,
            hook=st.get("hook") if i == 0 else None,
            is_first=(i == 0),
            idx=i,
        )

        # Generate Hindi voice audio separately and mux over the AI video
        import voice
        aud = f"work/s{i}.mp3"
        voice.synth(narration, sc["speaker"], aud)
        actual_dur = voice.duration(aud) + 0.4

        # Replace the AI video's audio with our Hindi TTS
        muxed = f"work/s{i}_muxed.mp4"
        video.run(["ffmpeg", "-y", "-i", clip_path, "-i", aud,
                   "-map", "0:v", "-map", "1:a",
                   "-c:v", "copy", "-c:a", "aac", "-ar", "44100",
                   "-shortest", muxed])

        clips.append(muxed)
        timing.append((t, actual_dur, narration))
        t += actual_dur

    return clips, timing, t


def run_image_pipeline(st):
    """Fallback: generate reel from still images (original pipeline)."""
    import images, voice, video
    clips, timing, first_img, t = [], [], None, 0.0

    for i, sc in enumerate(st["scenes"]):
        log(f"Scene {i+1}/{len(st['scenes'])} (image pipeline)")
        img = images.make_image(sc, f"work/s{i}")
        first_img = first_img or img
        aud = f"work/s{i}.mp3"
        voice.synth(sc["narration"], sc["speaker"], aud)
        dur = voice.duration(aud) + 0.45
        clip = f"work/s{i}.mp4"
        video.scene_clip(img, aud, dur, i, clip)
        clips.append(clip)
        timing.append((t, dur, sc["narration"]))
        t += dur

    return clips, timing, t, first_img


def run():
    t0 = time.time()
    shutil.rmtree("work", ignore_errors=True)
    os.makedirs("work")

    history = storage.get_json("history.json", [])
    old = storage.get_json("pending.json", None)

    st = S.make_story(trends.get_trends(), [h["topic"] for h in history[-30:]],
                      insights.performance_hints(history))
    log(f"Topic: {st['topic']} | Title: {st['title']} | Hook: {st['hook']}")
    log(f"Pipeline: {'AI video (fal.ai)' if USE_AI_VIDEO else 'image pipeline'}")

    if USE_AI_VIDEO:
        clips, timing, total_dur = run_ai_video(st)
        first_img = None
    else:
        clips, timing, total_dur, first_img = run_image_pipeline(st)

    # Assemble final reel with subtitles, music, loudnorm
    import video
    final = "work/final.mp4"
    length = video.assemble("work", timing, clips, final, hook=st["hook"])

    if not (C.MIN_SECONDS <= length <= C.MAX_SECONDS):
        raise RuntimeError(f"Video length {length:.1f}s outside {C.MIN_SECONDS}-{C.MAX_SECONDS}s")
    size_mb = os.path.getsize(final) / 1e6
    log(f"Video ready: {length:.1f}s, {size_mb:.1f} MB")

    day = datetime.date.today().isoformat()
    stamp = datetime.datetime.utcnow().strftime("%H%M")
    url = storage.upload_file(final, f"reels/{day}-{stamp}.mp4")

    # Cover image: use first scene thumbnail or first image
    cover = None
    if first_img:
        ext = first_img.rsplit(".", 1)[-1]
        cover = storage.upload_file(first_img, f"reels/{day}-{stamp}-cover.{ext}",
                                    f"image/{'jpeg' if ext=='jpg' else ext}")
    else:
        # Extract thumbnail from first video frame
        thumb = "work/thumb.jpg"
        video.run(["ffmpeg", "-y", "-i", clips[0], "-frames:v", "1", "-q:v", "2", thumb])
        if os.path.exists(thumb):
            cover = storage.upload_file(thumb, f"reels/{day}-{stamp}-cover.jpg", "image/jpeg")

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
        storage.put_json("pending.json", {
            "video_url": url, "cover_url": cover, "caption": caption,
            "date": day, "topic": st["topic"],
            "created_ts": int(time.time()), "attempts": 0
        })
        how = ("Reply /post to publish or /skip to discard." if C.REVIEW_MODE == "approve" else
               f"It will post automatically in {C.REVIEW_HOURS:g}h unless you reply /skip.")
        warn = "\n⚠️ Previous video was never posted and has been replaced." if old else ""
        notify.video(final, f"🎬 Ready ({length:.0f}s) — {st['topic']}\n\n{caption}\n\n👉 {how}{warn}", url)

    try:
        storage.cleanup("reels", keep=30)
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
