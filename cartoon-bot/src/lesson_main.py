"""Main lesson generation - uses edu_render professional animation system"""
import datetime, os, shutil, sys, time
from util import log, retry
import config as C
import syllabus, lesson_script, edu_render, voice, storage, notify, instagram, soundtrack, slots, publisher

def _optimize_scene_pacing(scenes):
    """ViMax-inspired pacing: add micro-pauses for complex scenes, speed up simple ones"""
    for scene in scenes:
        kind = scene["kind"]
        
        # Complex scenes need slightly more time to absorb
        if kind in ("network", "formula", "code"):
            # Add 0.3s pause at end for complex visual content
            scene["dur"] += 0.3
            scene["pause_end"] = True
        
        # Fast scenes can be tighter
        elif kind in ("hook", "stat"):
            # These are punchy, no extra pause needed
            scene["pause_end"] = False
        
        else:
            # Normal scenes
            scene["pause_end"] = False
    
    return scenes

def build_lesson_caption(script, lesson_num, level, lesson_title):
    """Build optimized caption for lesson"""
    summary = script.get("caption_summary", "")
    key_terms = script.get("key_terms", [])
    
    # Build caption
    caption_parts = [
        f"📚 Lesson #{lesson_num} - {level.title()}",
        "",
        f"✨ {lesson_title}",
        "",
        summary if summary else "AI concepts ko simple Hinglish mein samjho!",
        "",
        "💡 Key terms:",
        " • " + "\n • ".join(key_terms[:3]) if key_terms else " • AI, ML, Data",
        "",
        "Comment mein batao: Kya naya seekha? 💬",
        "",
        "Roz naya lesson! Follow karo 🔔",
        "",
        f"🎓 AI Seekho - Hinglish AI Education"
    ]
    
    caption = "\n".join(caption_parts)
    
    # Add hashtags
    edu_hashtags = [
        "#aiseekho", "#ailearning", "#hinglish", "#aiexplained",
        "#machinelearning", "#deeplearning", "#datascience",
        "#aiinhindi", "#techeducation", "#learnai", "#coding",
        "#python", "#artificialintelligence", "#techinhindi",
        "#educationreels"
    ]
    
    caption += "\n\n" + " ".join(edu_hashtags)
    
    log(f"Lesson caption: {len(caption)} chars")
    return caption

def build_fun_fact_caption(script, topic):
    """Build caption for weekend fun fact"""
    summary = script.get("caption_summary", "")
    
    caption_parts = [
        "🎉 Weekend Special - AI Fun Fact!",
        "",
        f"✨ {topic}",
        "",
        summary,
        "",
        "Aur bhi interesting facts ke liye follow karo! 🔔",
        "",
        "🎓 AI Seekho"
    ]
    
    caption = "\n".join([p for p in caption_parts if p])
    
    # Fun fact hashtags
    fun_hashtags = [
        "#aifacts", "#techfacts", "#didyouknow", "#aiinhindi",
        "#hinglish", "#interesting", "#viral", "#trending",
        "#aiseekho", "#techeducation", "#learnai",
        "#artificialintelligence", "#technology", "#innovation"
    ]
    
    caption += "\n\n" + " ".join(fun_hashtags)
    
    return caption

@retry(tries=3, delay=5)
def generate_voice_for_scene(scene, scene_idx):
    """Narration for one scene -> (mp3 path, seconds, word timings)."""
    audio_path = f"work/audio_{scene_idx}.mp3"
    speech = scene.get("speech")
    if speech:                                   # native Hindi voice reads the Devanagari copy
        spoken = voice.synth(speech, C.DEFAULT_LESSON_VOICE, audio_path)
    else:                                        # Roman text: use the Indian-English voice (reads Roman best)
        spk = "hinglish_roman" if C.SPEAK_DEVANAGARI else C.DEFAULT_LESSON_VOICE
        spoken = voice.synth(scene["narration"], spk, audio_path)
    duration = voice.duration(audio_path)
    words = voice.align(scene["narration"], spoken, duration)   # captions show the Roman words
    log(f"  Scene {scene_idx}: voice {duration:.1f}s - {(speech or scene['narration'])[:50]}...")
    return audio_path, duration, words


def generate_all_voices_parallel(scenes):
    """All scene voices at once (5-7x faster than one by one)."""
    import concurrent.futures
    log(f"🎙️ Generating {len(scenes)} voice tracks in parallel...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(generate_voice_for_scene, sc, i) for i, sc in enumerate(scenes)]
        errors = [f"scene {i}: {f.exception()}" for i, f in enumerate(futs) if f.exception()]
        if errors:
            raise RuntimeError("Voice generation failed: " + "; ".join(errors))
        return [f.result() for f in futs]


def generate_lesson_video(lesson, lesson_num, script):
    """Voice -> one soundtrack -> one single-pass 2D animated render. Returns (video, seconds, cover jpg)."""
    label = f"Lesson #{lesson_num}" if lesson_num else "Fun Fact"
    log(f"🎬 Rendering {label}: {lesson['title']}")
    shutil.rmtree("work", ignore_errors=True)
    os.makedirs("work")

    if C.SPEAK_DEVANAGARI:
        log("🗣️ Preparing Devanagari speech for proper Hindi pronunciation...")
        for sc, sp in zip(script["scenes"], lesson_script.to_speech([s["narration"] for s in script["scenes"]])):
            sc["speech"] = sp
    voices = generate_all_voices_parallel(script["scenes"])
    scenes = _optimize_scene_pacing([{"kind": s["kind"], "visual": s["visual"], "dur": d}
                                     for s, (_, d, _) in zip(script["scenes"], voices)])
    t, words = 0.0, []
    for sc, (_, _, ws) in zip(scenes, voices):
        sc["start"] = t
        words += [(t + a, t + b, w) for a, b, w in ws]
        t += sc["dur"]
    total = t

    log("🎵 Building soundtrack (voice + music bed + lip-sync levels)...")
    levels = soundtrack.build([v[0] for v in voices], [s["start"] for s in scenes], total, "work/mix.wav",
                              edu_render.FPS, music=C.MUSIC, music_dir=C.MUSIC_DIR,
                              voice_af=C.VOICE_FILTER if C.VOICE_FX else None)

    log(f"🖌️ Animating {len(scenes)} scenes, {total:.1f}s (mascot={C.MASCOT})...")
    final_video, cover = "work/final.mp4", "work/cover.jpg"
    edu_render.render_video(scenes, "work/mix.wav", levels, final_video, label, lesson.get("level", "basics"),
                            words=words, mascot_on=C.MASCOT, snapshot=(cover, min(1.4, total / 2)))
    log(f"✅ Video complete: {total:.1f}s, {os.path.getsize(final_video) / 1e6:.1f} MB")
    return final_video, total, cover


def build_content(history, slot):
    """Picks today's content: a lesson on weekdays, an AI fun fact on weekends (of the POSTING day)."""
    if slots.is_weekend(slot):
        log("🎉 Weekend slot - generating fun fact")
        fact = syllabus.get_fun_fact(history)
        script = lesson_script.generate_fun_fact_script(fact)
        lesson = {"title": fact["title"], "title_en": fact["title"], "level": "weekend"}
        return dict(script=script, lesson=lesson, lesson_num=None, fact_idx=fact["idx"], type="fun_fact",
                    level="weekend", topic=fact["title"], caption=build_fun_fact_caption(script, fact["title"]))
    log("📚 Weekday slot - generating lesson")
    lesson, num, nxt = syllabus.get_next_lesson(history)
    script = lesson_script.generate_lesson_script(lesson, num, nxt)
    return dict(script=script, lesson=lesson, lesson_num=num, fact_idx=None, type="lesson", level=lesson["level"],
                topic=lesson["title"], caption=build_lesson_caption(script, num, lesson["level"], lesson["title"]))


def _token_warning():
    try:
        days = instagram.token_days_left()
        if days is not None and days < 10:
            notify.text(f"⚠️ Your Instagram access token expires in {days:.0f} days. "
                        "Renew it (see GET_NEW_TOKEN.md) or posting will stop.")
    except Exception as e:
        log("Token check skipped:", e)


def run_lesson_generation():
    t0 = time.time()
    force_new = os.environ.get("FORCE_NEW", "false").lower() == "true"
    post_now = os.environ.get("POST_NOW", "false").lower() == "true"

    if post_now:                                    # manual "make one and post it right now"
        slot = slots.now()
        key = slot.strftime("%Y-%m-%d-now%H%M")
    else:
        slot = slots.upcoming_slot()
        key = slots.key(slot)
    log(f"🗓️ Target slot: {slots.fmt(slot)} (key {key}, review mode: {C.REVIEW_MODE})")

    history = storage.get_json("history.json", [])
    pending = storage.get_json("pending.json", None)
    if not force_new and not post_now:
        if any(h.get("slot") == key for h in history):
            log(f"✅ The {key} reel is already posted - nothing to do.")
            return
        if pending and pending.get("slot") == key:
            log(f"✅ The {key} reel is already made and queued - handing over to the poster.")
            publisher.run(wait=True)
            return
    if pending and pending.get("slot") != key:
        log(f"Replacing an old unposted reel for slot {pending.get('slot')}.")
        notify.text(f"ℹ️ The reel for {pending.get('slot')} was never posted; replacing it with the {key} reel.")

    c = build_content(history, slot)
    final_video, duration, cover = generate_lesson_video(c["lesson"], c["lesson_num"], c["script"])

    log("☁️ Uploading to Supabase...")
    stamp = slots.now().strftime("%H%M%S")
    url = storage.upload_file(final_video, f"lessons/{key}-{stamp}.mp4")
    cover_url = None
    try:
        cover_url = storage.upload_file(cover, f"covers/{key}-{stamp}.jpg", "image/jpeg")
    except Exception as e:
        log("Cover upload failed (posting without cover):", e)

    post_at = time.time() if post_now else slot.timestamp()
    storage.put_json("pending.json", {
        "slot": key, "post_at": int(post_at), "video_url": url, "cover_url": cover_url, "caption": c["caption"],
        "topic": c["topic"], "type": c["type"], "lesson_num": c["lesson_num"], "fact_idx": c["fact_idx"],
        "level": c["level"], "duration": round(duration, 1), "fact_check": c["script"].get("fact_check", "pass"),
        "created_ts": int(time.time()), "attempts": 0, "status": "queued",
    })
    for prefix, keep in (("lessons", 30), ("covers", 30)):
        try:
            storage.cleanup(prefix, keep=keep)
        except Exception as e:
            log("Cleanup skipped:", e)

    when = "right now" if post_now or post_at <= time.time() else slots.fmt(post_at)
    how = {"auto": f"It will post automatically {when}.",
           "auto_unless_skip": f"It will post {when} unless you reply /skip.",
           "approve": f"Reply /post to publish it at {when} (or /postnow to publish immediately, /skip to discard)."}
    warn = "\n⚠️ Fact-check flagged issues - please watch before it posts." if c["script"].get("fact_check") == "warning" else ""
    notify.video(final_video, f"🎬 {c['topic']} ({duration:.0f}s)\n{how.get(C.REVIEW_MODE, how['approve'])}{warn}", url)
    _token_warning()
    log(f"✅ Reel ready in {time.time() - t0:.0f}s. Queued for {when}.")

    publisher.run(force=post_now, wait=True)       # posts now if due, or sleeps until the slot if it is close
    log(f"✅ Done in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    try:
        run_lesson_generation()
    except Exception as e:
        log(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        notify.text(f"❌ Reel generation failed (a backup run will retry):\n{str(e)[:800]}")
        sys.exit(1)
