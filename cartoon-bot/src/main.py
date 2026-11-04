import datetime, os, shutil, sys, time, traceback
from concurrent.futures import ProcessPoolExecutor
import config as C, trends, story as S, images, depth, mouth, voice, video, storage, notify, instagram, insights, motion3d
import hashtags, captions
from util import log

def build_caption(st, ep):
    """Build optimized caption with smart hashtags"""
    # Generate smart hashtags based on topic
    smart_tags = hashtags.smart_hashtags(st.get("topic", ""), max_tags=15)
    
    # Generate optimized caption
    optimized_caption = captions.generate_optimized_caption(st, st.get("hook", ""), ep)
    
    # Add hashtags
    full_caption = captions.add_hashtags_to_caption(optimized_caption, smart_tags)
    
    log(f"Caption: {len(full_caption)} chars, {len(smart_tags)} hashtags")
    return full_caption

def run():
    t0 = time.time()
    shutil.rmtree("work", ignore_errors=True); os.makedirs("work")
    history = storage.get_json("history.json", [])
    old = storage.get_json("pending.json", None)
    ep = len(history) + 1

    st = S.make_story(trends.get_trends(), [h["topic"] for h in history[-30:]], insights.performance_hints(history), ep)
    log(f"Episode {ep} | Topic: {st['topic']} | Title: {st['title']} | Hook: {st['hook']}")

    specs, timing, t = [], [], 0.0
    for i, sc in enumerate(st["scenes"]):
        log(f"Preparing scene {i+1}/{len(st['scenes'])} ({sc['speaker']})")
        img = images.make_image(sc, f"work/s{i}")
        dpath, real = depth.estimate(img, f"work/s{i}.npy")
        mth = mouth.detect(img, sc["speaker"]) if C.MOUTH_FX else None
        aud = f"work/s{i}.mp3"
        voice.synth(sc["narration"], sc["speaker"], aud)
        dur = voice.duration(aud) + 0.45
        specs.append(dict(image=img, depth=dpath, audio=aud, dur=dur, camera=sc["camera"], reaction=sc["reaction"],
                          sticker=sc["sticker"], mouth=mth, speaker=sc["speaker"],
                          speaker_is_char=sc["speaker"] in C.CHARACTERS, idx=i, out=f"work/s{i}.mp4"))
        timing.append((t, dur, sc["narration"], sc["speaker"])); t += dur
        log(f"  depth={'AI' if real else 'simple'} mouth={'found' if mth else 'none'} dur={dur:.1f}s")

    log("Rendering animated shots...")
    cover_idx = 1 if len(specs) > 1 else 0
    cover_path = "work/cover.jpg"
    workers = max(1, min(os.cpu_count() or 1, 4, len(specs)))
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(motion3d.render_scene, sp, sp["out"], (cover_path, 0.5) if sp["idx"] == cover_idx else None)
                for sp in specs]
        for fu in futs:
            fu.result()

    final = "work/final.mp4"
    length = video.assemble("work", timing, [sp["out"] for sp in specs], final, hook=st["hook"])
    if not (C.MIN_SECONDS <= length <= C.MAX_SECONDS):
        raise RuntimeError(f"Video length {length:.1f}s is outside {C.MIN_SECONDS}-{C.MAX_SECONDS}s")
    log(f"Video ready: {length:.1f}s, {os.path.getsize(final)/1e6:.1f} MB")

    day = datetime.date.today().isoformat()
    stamp = datetime.datetime.utcnow().strftime("%H%M")
    url = storage.upload_file(final, f"reels/{day}-{stamp}.mp4")
    cover = storage.upload_file(cover_path, f"reels/{day}-{stamp}-cover.jpg", "image/jpeg")
    caption = build_caption(st, ep)
    entry = {"date": day, "topic": st["topic"], "title": st["title"], "episode": ep}

    if C.REVIEW_MODE == "auto":
        entry["media_id"] = instagram.post_reel(url, caption, cover)
        history.append(entry); storage.put_json("history.json", history[-100:])
        notify.video(final, f"✅ Posted automatically ({length:.0f}s)\n\n{caption}", url)
    else:
        history.append(entry); storage.put_json("history.json", history[-100:])
        storage.put_json("pending.json", {"video_url": url, "cover_url": cover, "caption": caption, "date": day,
                                          "topic": st["topic"], "created_ts": int(time.time()), "attempts": 0})
        how = ("Reply /post to publish or /skip to discard." if C.REVIEW_MODE == "approve" else
               f"It will post automatically in {C.REVIEW_HOURS:g}h unless you reply /skip.")
        warn = "\n⚠️ The previous video was never posted and has been replaced." if old else ""
        notify.video(final, f"🎬 Part {ep} ready ({length:.0f}s) — {st['topic']}\n\n{caption}\n\n👉 {how}{warn}", url)
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
