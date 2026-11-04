import glob, os, random, re, subprocess
import config as C

FPS = 30

def run(cmd, cwd=None):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if p.returncode != 0:
        raise RuntimeError("ffmpeg failed:\n" + p.stderr[-1800:])

def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())

# ---------------- subtitles (ASS): karaoke with glow effects ----------------
def _ts(t):
    cs = int(round(max(t, 0) * 100))
    return f"{cs//360000}:{cs%360000//6000:02d}:{cs%6000//100:02d}.{cs%100:02d}"

def _esc(s):
    return re.sub(r"[{}\\]", "", s).replace("\n", " ")

def make_ass(timing, hook, total, path):
    """Enhanced ASS with karaoke timing, glow effects, and smooth animations."""
    F = "Noto Sans Devanagari"
    # Enhanced styles with glow (3-layer outline + blur effect)
    def style(name, size, col, secondcol, align, mv, outline=7):
        # col = primary (karaoke highlight), secondcol = unsung text
        return (f"Style: {name},{F},{size},{col},{secondcol},&H00000000,&H40000000,"
                f"1,0,0,0,100,100,0,0,1,{outline},3,{align},60,60,{mv},1\n")
    
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n"
            "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
            "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,"
            "MarginL,MarginR,MarginV,Encoding\n"
            # Primary = highlight color (sung), Secondary = unsung color
            + style("Default", 78, "&H00FFFFFF", "&H00CCCCCC", 2, 320, 7)
            + style("bablu", 78, "&H0000FFFF", "&H0099D6FF", 2, 320, 7)    # cyan glow
            + style("chiku", 78, "&H0000D4FF", "&H0099E0AA", 2, 320, 7)    # yellow-orange glow
            + style("Hook", 88, "&H0000E5FF", "&H0088C5FF", 8, 220, 8)
            + style("CTA", 68, "&H0000E5FF", "&H0088C5FF", 8, 220, 7)
            + "\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    
    ev = []
    if hook:
        # Hook with bounce-in effect
        ev.append(f"Dialogue: 1,{_ts(0.15)},{_ts(2.8)},Hook,,0,0,0,,{{\\fad(200,250)\\t(0,300,\\fscx120\\fscy120)\\t(300,400,\\fscx100\\fscy100)}}{_esc(hook)}")
    
    for start, dur, text, speaker in timing:
        sty = speaker if speaker in ("bablu", "chiku") else "Default"
        words = text.split()
        
        # Enhanced karaoke: word-by-word timing with smooth color sweep
        if len(words) > 1:
            usable = max(dur - 0.3, 0.6)
            word_dur = usable / len(words)
            
            # Build karaoke string with word-by-word timing
            k_times = []
            for w in words:
                k_times.append(int(word_dur * 100))  # centiseconds
            
            # Format: {\k<time>}word creates karaoke effect
            k_text = "".join(f"{{\\k{kt}}}{_esc(w)} " for kt, w in zip(k_times, words)).strip()
            
            # Add glow pulse effect and slight scale bounce on each line
            fx = f"{{\\fad(150,200)\\t(0,200,\\blur3\\fscx105\\fscy105)\\t(200,350,\\blur0\\fscx100\\fscy100)}}"
            ev.append(f"Dialogue: 0,{_ts(start + 0.08)},{_ts(start + dur)},{sty},,0,0,0,,{fx}{k_text}")
        else:
            # Single word - just glow pulse
            fx = f"{{\\fad(150,200)\\t(0,250,\\blur4)\\t(250,400,\\blur0)}}"
            ev.append(f"Dialogue: 0,{_ts(start + 0.08)},{_ts(start + dur)},{sty},,0,0,0,,{fx}{_esc(text)}")
    
    if C.CTA_TEXT:
        # CTA with attention-grabbing pulse
        fx = "{{\\fad(300,0)\\t(0,400,\\fscx110\\fscy110\\blur5)\\t(400,600,\\fscx100\\fscy100\\blur0)}}"
        ev.append(f"Dialogue: 1,{_ts(max(total-2.5, 0))},{_ts(total)},CTA,,0,0,0,,{fx}{_esc(C.CTA_TEXT)}")
    
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

# ---------------- scene transitions ----------------
def apply_transitions(clips, work_dir, transition_dur=0.4):
    """Apply crossfade transitions between clips. Returns list of transitioned clip paths."""
    if len(clips) <= 1:
        return clips
    
    trans_clips = []
    for i in range(len(clips)):
        if i == 0:
            trans_clips.append(clips[i])
        else:
            # Crossfade transition between previous and current
            trans_out = os.path.join(work_dir, f"trans_{i}.mp4")
            prev_clip = clips[i-1]
            curr_clip = clips[i]
            
            # Get durations
            prev_dur = probe_duration(prev_clip)
            curr_dur = probe_duration(curr_clip)
            
            # Only apply transition if clips are long enough
            if prev_dur > transition_dur and curr_dur > transition_dur:
                # Use xfade filter for smooth crossfade
                xfade_time = prev_dur - transition_dur
                total_dur = prev_dur + curr_dur - transition_dur
                
                cmd = ["ffmpeg", "-y", "-i", prev_clip, "-i", curr_clip,
                       "-filter_complex",
                       f"[0:v][1:v]xfade=transition=fadeblack:duration={transition_dur}:offset={xfade_time}[vout];"
                       f"[0:a][1:a]acrossfade=d={transition_dur}[aout]",
                       "-map", "[vout]", "-map", "[aout]",
                       "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                       "-t", f"{total_dur:.2f}", trans_out]
                try:
                    run(cmd)
                    # Replace both clips with transitioned version
                    if i == 1:
                        trans_clips[-1] = trans_out
                    else:
                        trans_clips.append(trans_out)
                except:
                    # Fallback: no transition
                    if i > 1:
                        trans_clips.append(curr_clip)
            else:
                if i > 1:
                    trans_clips.append(curr_clip)
    
    return trans_clips

# ---------------- intro/outro templates ----------------
def create_intro(work_dir, duration=2.0):
    """Create a branded intro clip with series name and character reveal."""
    intro_path = os.path.join(work_dir, "intro.mp4")
    
    # Check if custom intro exists in assets
    custom_intro = "assets/intro.mp4"
    if os.path.exists(custom_intro):
        return custom_intro
    
    # Generate simple text intro with animation
    intro_text = C.SERIES_NAME.replace("'", "\\\\'")
    
    cmd = ["ffmpeg", "-y", "-f", "lavfi",
           "-i", f"color=c=#1a1a2e:s=1080x1920:d={duration}:r={FPS}",
           "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={duration}",
           "-vf", (f"drawtext=text='{intro_text}':"
                   f"fontfile=/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf:"
                   f"fontsize=90:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:"
                   f"enable='between(t,0.3,{duration})':"
                   f"alpha='if(lt(t,0.6),(t-0.3)/0.3,if(lt(t,{duration-0.4}),1,({duration}-t)/0.4))'"),
           "-t", f"{duration}", "-pix_fmt", "yuv420p", "-c:a", "aac", intro_path]
    try:
        run(cmd)
        return intro_path
    except:
        return None  # Skip intro if generation fails

def create_outro(work_dir, duration=2.5):
    """Create a branded outro clip with CTA and channel info."""
    outro_path = os.path.join(work_dir, "outro.mp4")
    
    # Check if custom outro exists in assets
    custom_outro = "assets/outro.mp4"
    if os.path.exists(custom_outro):
        return custom_outro
    
    # Generate simple text outro
    cta_text = C.CTA_TEXT.replace("'", "\\\\'")
    
    cmd = ["ffmpeg", "-y", "-f", "lavfi",
           "-i", f"color=c=#1a1a2e:s=1080x1920:d={duration}:r={FPS}",
           "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={duration}",
           "-vf", (f"drawtext=text='🔔 {cta_text}':"
                   f"fontfile=/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf:"
                   f"fontsize=70:fontcolor=#FFE500:x=(w-text_w)/2:y=(h-text_h)/2:"
                   f"enable='between(t,0.2,{duration})':"
                   f"alpha='if(lt(t,0.5),(t-0.2)/0.3,if(lt(t,{duration-0.5}),1,({duration}-t)/0.5))'"),
           "-t", f"{duration}", "-pix_fmt", "yuv420p", "-c:a", "aac", outro_path]
    try:
        run(cmd)
        return outro_path
    except:
        return None  # Skip outro if generation fails

# ---------------- final assembly ----------------
def assemble(work, timing, clips, final_path, hook="", music_dir="assets/music", 
             add_intro=True, add_outro=True, transitions=True):
    """Enhanced assembly with intro/outro and transitions."""
    
    # Create intro/outro if requested
    final_clips = []
    if add_intro and C.env("ADD_INTRO", "true").lower() == "true":
        intro = create_intro(work)
        if intro:
            final_clips.append(intro)
    
    # Apply transitions between main clips
    if transitions and C.env("ADD_TRANSITIONS", "true").lower() == "true":
        trans_clips = apply_transitions(clips, work)
        final_clips.extend(trans_clips)
    else:
        final_clips.extend(clips)
    
    if add_outro and C.env("ADD_OUTRO", "true").lower() == "true":
        outro = create_outro(work)
        if outro:
            final_clips.append(outro)
    
    # Continue with original assembly logic
    listf = os.path.join(work, "list.txt")
    open(listf, "w").write("".join(f"file '{os.path.abspath(c)}'\n" for c in final_clips))
    joined = os.path.join(work, "joined.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf, "-c", "copy", joined])
    total = probe_duration(joined)
    make_ass(timing, hook, total, os.path.join(work, "subs.ass"))

    tracks = glob.glob(os.path.join(music_dir, "*.mp3")) + glob.glob(os.path.join(music_dir, "*.wav"))
    enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-t", f"{total:.2f}"]
    final_abs = os.path.abspath(final_path)
    if tracks:   # music ducks under the voice, then loudness is normalised
        fc = ("[0:v]ass=subs.ass[v];[0:a]asplit=2[voice][sc];[1:a]volume=0.5[m];"
              "[m][sc]sidechaincompress=threshold=0.04:ratio=10:attack=15:release=400[duck];"
              "[voice][duck]amix=inputs=2:duration=first:dropout_transition=0,volume=2,"
              "loudnorm=I=-16:TP=-1.5:LRA=11[a]")
        run(["ffmpeg", "-y", "-i", "joined.mp4", "-stream_loop", "-1", "-i", os.path.abspath(random.choice(tracks)),
             "-filter_complex", fc, "-map", "[v]", "-map", "[a]", *enc, final_abs], cwd=work)
    else:
        run(["ffmpeg", "-y", "-i", "joined.mp4", "-vf", "ass=subs.ass", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
             *enc, final_abs], cwd=work)
    return probe_duration(final_abs)
