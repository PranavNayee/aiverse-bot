"""Main lesson generation - uses edu_render professional animation system"""
import datetime, json, os, shutil, subprocess, sys, time
from util import log, retry
import config as C
import syllabus, lesson_script, edu_render, voice, storage, notify, instagram

def is_weekend():
    """Check if today is weekend"""
    day = datetime.date.today().weekday()  # Monday=0, Sunday=6
    return day in (5, 6)  # Saturday or Sunday

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
    """Generate voice narration for one scene"""
    narration = scene["narration"]
    audio_path = f"work/audio_{scene_idx}.mp3"
    
    # Use hinglish voice
    voice.synth(narration, "hinglish", audio_path)
    
    # Get actual duration
    duration = voice.duration(audio_path)
    
    log(f"  Scene {scene_idx}: voice {duration:.1f}s - {narration[:50]}...")
    return audio_path, duration

def generate_lesson_video(lesson, lesson_num, script):
    """Generate complete lesson video using edu_render professional system
    
    Args:
        lesson: Lesson dict from syllabus
        lesson_num: Lesson number
        script: Generated script dict with scenes
    
    Returns:
        Path to final video, duration
    """
    
    log(f"🎬 Rendering Lesson #{lesson_num}: {lesson['title']}")
    
    # Create work directory
    shutil.rmtree("work", ignore_errors=True)
    os.makedirs("work")
    
    # Prepare scenes with audio and timing
    scenes = []
    total_time = 0.0
    
    for i, scene_spec in enumerate(script["scenes"]):
        # Generate voice
        audio_path, audio_dur = generate_voice_for_scene(scene_spec, i)
        
        # Build scene spec for edu_render
        scene = {
            "kind": scene_spec["kind"],
            "visual": scene_spec["visual"],
            "audio": audio_path,
            "dur": audio_dur,
            "level": lesson.get("level", "basics"),
            "label": f"Lesson #{lesson_num}",
            "t0": total_time,  # Scene start time in whole video
            "total": 0.0  # Will be set after we know total duration
        }
        
        scenes.append(scene)
        total_time += audio_dur
    
    # Update total duration in all scenes
    for scene in scenes:
        scene["total"] = total_time
    
    # Render each scene to separate video
    scene_videos = []
    for i, scene in enumerate(scenes):
        scene_video = f"work/scene_{i}.mp4"
        log(f"  Rendering scene {i+1}/{len(scenes)}: {scene['kind']} ({scene['dur']:.1f}s)")
        edu_render.render_scene(scene, scene_video)
        scene_videos.append(scene_video)
    
    # Concatenate all scenes
    log("Concatenating scenes...")
    concat_list = "work/concat_list.txt"
    with open(concat_list, "w") as f:
        for vid in scene_videos:
            f.write(f"file '{os.path.abspath(vid)}'\n")
    
    final_video = "work/final.mp4"
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c", "copy", final_video
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"FFmpeg concat error: {result.stderr}")
        raise RuntimeError(f"Video concatenation failed: {result.stderr[-500:]}")
    
    file_size = os.path.getsize(final_video) / (1024 * 1024)  # MB
    log(f"✅ Lesson video complete: {total_time:.1f}s, {file_size:.1f} MB")
    
    return final_video, total_time

def run_lesson_generation():
    """Main entry point - generate and post lesson"""
    t0 = time.time()
    history = storage.get_json("history.json", [])
    
    # Check if weekend for fun fact
    if is_weekend():
        log("🎉 Weekend detected - generating fun fact")
        fact = syllabus.get_fun_fact()
        script = lesson_script.generate_fun_fact_script(fact)
        caption = build_fun_fact_caption(script, fact["title"])
        content_type = "fun_fact"
        lesson_num = None
        level = "weekend"
        topic = fact["title"]
        
        # Adapt fact for video generation (treat as lesson-like)
        lesson = {
            "title": fact["title"],
            "title_en": fact["title"],
            "level": "weekend"
        }
    else:
        log("📚 Weekday - generating lesson")
        lesson, lesson_num, next_lesson = syllabus.get_next_lesson(history)
        
        if not lesson:
            log("⚠️ No more lessons in syllabus!")
            return
        
        # Generate script with fact-checking
        script = lesson_script.generate_lesson_script(lesson, lesson_num, next_lesson)
        
        # Build caption
        caption = build_lesson_caption(script, lesson_num, lesson["level"], lesson["title"])
        content_type = "lesson"
        level = lesson["level"]
        topic = lesson["title"]
    
    # Generate video with professional animations
    log("🎬 Starting video generation with edu_render...")
    final_video, duration = generate_lesson_video(lesson, lesson_num, script)
    
    # Upload to Supabase
    day = datetime.date.today().isoformat()
    stamp = datetime.datetime.utcnow().strftime("%H%M")
    log("☁️ Uploading to Supabase...")
    url = storage.upload_file(final_video, f"lessons/{day}-{stamp}.mp4")
    
    # Record in history
    entry = {
        "date": day,
        "type": content_type,
        "lesson_num": lesson_num,
        "level": level,
        "topic": topic,
        "duration": round(duration, 1),
        "fact_check": script.get("fact_check", "pass")
    }
    
    # Post to Instagram or queue for approval
    if C.REVIEW_MODE == "auto":
        log("📱 Posting to Instagram automatically...")
        entry["media_id"] = instagram.post_reel(url, caption, None)
        history.append(entry)
        storage.put_json("history.json", history[-100:])
        notify.text(f"✅ Lesson #{lesson_num if lesson_num else 'Weekend'} posted automatically!\n\n{caption[:500]}")
    else:
        log("⏸️ Queuing for manual approval...")
        history.append(entry)
        storage.put_json("history.json", history[-100:])
        storage.put_json("pending.json", {
            "video_url": url,
            "caption": caption,
            "date": day,
            "created_ts": int(time.time()),
            "attempts": 0
        })
        notify.text(f"🎓 New lesson ready! Reply /post to publish.\n\n{caption[:500]}")
    
    elapsed = time.time() - t0
    log(f"✅ Done in {elapsed:.0f}s ({elapsed/60:.1f}min)")

if __name__ == "__main__":
    try:
        run_lesson_generation()
    except Exception as e:
        log(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        notify.text(f"❌ Lesson generation failed:\n{str(e)[:800]}")
        sys.exit(1)
