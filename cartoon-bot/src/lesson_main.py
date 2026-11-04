"""Main lesson generation - coordinates syllabus, script, animations, voice"""
import datetime, os, shutil, sys, time
from util import log
import config as C
import syllabus, lesson_script, animations, voice, storage, notify, instagram
import hashtags, captions

def is_weekend():
    """Check if today is weekend"""
    day = datetime.date.today().weekday()  # Monday=0, Sunday=6
    return day in (5, 6)  # Saturday or Sunday

def build_lesson_caption(script, lesson_num, level):
    """Build optimized caption for lesson"""
    # Get key points
    summary = script.get("caption_summary", "")
    key_terms = script.get("key_terms", [])
    
    # Hook
    hook = script.get("hook", "Aaj kuch naya seekhte hain! 🧠")
    
    # Build caption
    caption_parts = [
        f"📚 Lesson #{lesson_num} - {level.title()}",
        "",
        hook,
        "",
        summary if summary else "AI concepts ko simple Hinglish mein samjho!",
        "",
        "💡 Aaj ke key terms:",
        " • " + "\n • ".join(key_terms[:3]) if key_terms else " • AI, ML, Data",
        "",
        "Comment mein batao: Aapko kya naya seekhne mila? 💬",
        "",
        "Roz naya lesson! Follow karo 🔔",
        "",
        f"🎓 AI Seekho - Hinglish AI Education"
    ]
    
    caption = "\n".join(caption_parts)
    
    # Generate smart hashtags for education
    edu_hashtags = [
        "#aiseekho", "#ailearning", "#hinglish", "#aiexplained",
        "#machinelearning", "#deeplearning", "#datascience",
        "#aiinhindi", "#techeducation", "#learnai", "#coding",
        "#python", "#artificialintelligence", "#techinhindi",
        "#educationreels"
    ]
    
    # Add hashtags
    caption += "\n\n" + " ".join(edu_hashtags)
    
    log(f"Lesson caption: {len(caption)} chars")
    return caption

def build_fun_fact_caption(script):
    """Build caption for weekend fun fact"""
    hook = script.get("hook", "AI fun fact! 🤯")
    summary = script.get("caption_summary", "")
    shareability = script.get("shareability_factor", "")
    
    caption_parts = [
        "🎉 Weekend Special - AI Fun Fact!",
        "",
        hook,
        "",
        summary,
        "",
        f"💡 {shareability}" if shareability else "",
        "",
        "Aur bhi interesting facts ke liye follow karo! 🔔",
        "",
        "🎓 AI Seekho"
    ]
    
    caption = "\n".join([p for p in caption_parts if p])  # Remove empty
    
    # Fun fact hashtags
    fun_hashtags = [
        "#aifacts", "#techfacts", "#didyouknow", "#aiinhindi",
        "#hinglish", "#interesting", "#viral", "#trending",
        "#aiseekho", "#techeducation", "#learnai",
        "#artificialintelligence", "#technology", "#innovation"
    ]
    
    caption += "\n\n" + " ".join(fun_hashtags)
    
    return caption

def generate_lesson_video(lesson, lesson_num, level, script):
    """Generate complete lesson video with animations and voice
    
    Args:
        lesson: Lesson dict from syllabus
        lesson_num: Lesson number
        level: Level name (basics/intermediate/advanced)
        script: Generated script dict
    
    Returns:
        Path to final video, duration
    """
    
    log(f"Generating video for Lesson #{lesson_num}: {lesson['title']}")
    
    # Create work directory
    shutil.rmtree("work", ignore_errors=True)
    os.makedirs("work")
    
    video_segments = []
    audio_segments = []
    timings = []
    current_time = 0.0
    
    # 1. Title card (3 seconds)
    title_card = animations.create_title_card(
        lesson["title"],
        f"Lesson #{lesson_num}",
        duration=3.0
    )
    video_segments.append(title_card)
    
    # Generate silent audio for title card
    silence_3s = "work/silence_3s.mp3"
    voice.generate_silence(silence_3s, 3.0)
    audio_segments.append(silence_3s)
    timings.append((current_time, 3.0, f"Lesson #{lesson_num}", "title"))
    current_time += 3.0
    
    # 2. Process each segment
    for i, segment in enumerate(script["segments"]):
        seg_type = segment["type"]
        narration = segment["narration_hi"]
        duration = segment.get("duration", 5.0)
        visual_desc = segment.get("visual", "")
        
        log(f"  Segment {i+1}/{len(script['segments'])}: {seg_type} ({duration}s)")
        
        # Generate voice
        audio_path = f"work/seg_{i}.mp3"
        voice.synth(narration, "hinglish", audio_path)
        actual_duration = voice.duration(audio_path) + 0.5  # Add padding
        audio_segments.append(audio_path)
        
        # Generate appropriate animation based on visual type
        if seg_type == "setup" or "flow" in visual_desc.lower():
            # Process flow animation
            video_path = animations.create_process_flow(
                ["Data", "Pattern", "Prediction"],
                duration=actual_duration
            )
        elif seg_type == "explanation" and "network" in visual_desc.lower():
            # Neural network visualization
            video_path = animations.create_neural_network_viz(duration=actual_duration)
        elif "comparison" in visual_desc.lower() or "vs" in narration.lower():
            # Comparison visualization
            video_path = animations.create_comparison(
                "Before", "After",
                duration=actual_duration
            )
        else:
            # Default: animated text
            # Split narration into lines
            words = narration.split()
            lines = []
            current_line = ""
            for word in words:
                if len(current_line) + len(word) < 30:  # Max chars per line
                    current_line += word + " "
                else:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + " "
            if current_line:
                lines.append(current_line.strip())
            
            video_path = animations.create_text_animation(
                lines[:4],  # Max 4 lines
                duration=actual_duration,
                animation_type="fade"
            )
        
        video_segments.append(video_path)
        timings.append((current_time, actual_duration, narration, seg_type))
        current_time += actual_duration
    
    # 3. Combine videos and audio
    log("Combining video segments...")
    
    # Concatenate videos
    list_file = "work/video_list.txt"
    with open(list_file, "w") as f:
        for vid in video_segments:
            f.write(f"file '{os.path.abspath(vid)}'\n")
    
    video_concat = "work/video_concat.mp4"
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
           "-c", "copy", video_concat]
    subprocess.run(cmd, capture_output=True, check=True)
    
    # Concatenate audio
    audio_list_file = "work/audio_list.txt"
    with open(audio_list_file, "w") as f:
        for aud in audio_segments:
            f.write(f"file '{os.path.abspath(aud)}'\n")
    
    audio_concat = "work/audio_concat.mp3"
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", audio_list_file,
           "-c", "copy", audio_concat]
    subprocess.run(cmd, capture_output=True, check=True)
    
    # 4. Merge video and audio
    final_video = "work/final.mp4"
    cmd = ["ffmpeg", "-y", "-i", video_concat, "-i", audio_concat,
           "-c:v", "copy", "-c:a", "aac", "-shortest", final_video]
    subprocess.run(cmd, capture_output=True, check=True)
    
    total_duration = current_time
    log(f"Lesson video complete: {total_duration:.1f}s, {os.path.getsize(final_video)/1e6:.1f} MB")
    
    return final_video, total_duration

def run_lesson_generation():
    """Main entry point - generate and post lesson"""
    import subprocess
    
    t0 = time.time()
    history = storage.get_json("history.json", [])
    
    # Check if weekend for fun fact
    if is_weekend():
        log("🎉 Weekend detected - generating fun fact")
        topic = syllabus.get_fun_fact_topic()
        script = lesson_script.generate_fun_fact_script(topic)
        caption = build_fun_fact_caption(script)
        content_type = "fun_fact"
        lesson_num = None
        level = "weekend"
    else:
        log("📚 Weekday - generating lesson")
        lesson, lesson_num, level = syllabus.get_next_lesson(history)
        
        if not lesson:
            log("No more lessons in syllabus! (or error)")
            return
        
        # Generate script
        script = lesson_script.generate_lesson_script(lesson, lesson_num)
        lesson_script.validate_script(script)
        
        # Build caption
        caption = build_lesson_caption(script, lesson_num, level)
        content_type = "lesson"
    
    # Generate video (placeholder for now)
    # In production, this would call generate_lesson_video()
    log("TODO: Generate actual video with animations")
    
    # For now, create a simple placeholder
    final_video = "work/final.mp4"
    # (Would generate actual video here)
    
    # Upload to Supabase
    day = datetime.date.today().isoformat()
    stamp = datetime.datetime.utcnow().strftime("%H%M")
    url = storage.upload_file(final_video, f"lessons/{day}-{stamp}.mp4")
    
    # Record in history
    entry = {
        "date": day,
        "type": content_type,
        "lesson_num": lesson_num,
        "level": level,
        "topic": topic if is_weekend() else lesson.get("title"),
    }
    
    # Post to Instagram
    if C.REVIEW_MODE == "auto":
        entry["media_id"] = instagram.post_reel(url, caption, None)
        history.append(entry)
        storage.put_json("history.json", history[-100:])
        notify.text(f"✅ Lesson posted automatically!\n\n{caption[:500]}")
    else:
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
    
    log(f"Done in {time.time()-t0:.0f}s")

if __name__ == "__main__":
    run_lesson_generation()
