import glob, os, random, re, subprocess
import config as C

W, H, FPS = 1080, 1920, 30
BIG_W, BIG_H = 1620, 2880   # 1.5x for smooth zoom/pan

def run(cmd, cwd=None):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if p.returncode != 0:
        raise RuntimeError("ffmpeg failed:\n" + p.stderr[-1800:])

def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())

# ── camera moves (8 types for variety) ──────────────────────────────────────
def _motion(idx, frames):
    kind = idx % 8
    step = 0.18 / frames
    cy = "y='ih/2-(ih/zoom/2)'"
    if kind == 0:   # zoom in
        return f"z='min(1+{step}*on,1.18)':x='iw/2-(iw/zoom/2)':{cy}"
    if kind == 1:   # pan right
        return f"z='1.15':x='(iw-iw/zoom)*on/{frames}':{cy}"
    if kind == 2:   # zoom out
        return f"z='max(1.18-{step}*on,1.0)':x='iw/2-(iw/zoom/2)':{cy}"
    if kind == 3:   # pan left
        return f"z='1.15':x='(iw-iw/zoom)*(1-on/{frames})':{cy}"
    if kind == 4:   # zoom in + pan right
        return f"z='min(1+{step}*on,1.18)':x='(iw-iw/zoom)*on/{frames}/2':{cy}"
    if kind == 5:   # zoom in + pan left
        return f"z='min(1+{step}*on,1.18)':x='(iw-iw/zoom)*(1-on/{frames}/2)':{cy}"
    if kind == 6:   # slow drift up
        return f"z='1.14':x='iw/2-(iw/zoom/2)':y='ih*(0.55-0.05*on/{frames})-(ih/zoom/2)'"
    # slow drift down
    return f"z='1.14':x='iw/2-(iw/zoom/2)':y='ih*(0.45+0.05*on/{frames})-(ih/zoom/2)'"

def scene_clip(img, audio, dur, idx, out):
    """One still image + voice -> animated clip with cinematic motion.
    Non-9:16 images get a blurred background. Smooth transitions built-in."""
    frames = max(2, int(dur * FPS))

    # Blurred background + foreground composite + zoom/pan + vignette
    fc = (
        f"[0:v]split[a][b];"
        f"[a]scale={BIG_W}:{BIG_H}:force_original_aspect_ratio=increase,"
        f"crop={BIG_W}:{BIG_H},boxblur=45:6[bg];"
        f"[b]scale={BIG_W}:{BIG_H}:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,"
        f"zoompan={_motion(idx, frames)}:d={frames}:s={W}x{H}:fps={FPS},"
        # vignette for cinematic look
        f"vignette=PI/4,"
        f"format=yuv420p[v]"
    )
    run(["ffmpeg", "-y", "-i", img, "-i", audio, "-filter_complex", fc,
         "-map", "[v]", "-map", "1:a", "-af", "apad", "-t", f"{dur:.2f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-r", str(FPS),
         "-c:a", "aac", "-ar", "44100", "-ac", "2", out])

# ── subtitles (ASS) ──────────────────────────────────────────────────────────
def _ts(t):
    cs = int(round(max(t, 0) * 100))
    return f"{cs//360000}:{cs%360000//6000:02d}:{cs%6000//100:02d}.{cs%100:02d}"

def _esc(s):
    return re.sub(r"[{}\\]", "", s).replace("\n", " ")

def make_ass(timing, hook, total, path):
    head = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n"
        "[V4+ Styles]\n"
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
        "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
        "Alignment,MarginL,MarginR,MarginV,Encoding\n"
        # Main subtitle — white bold with yellow outline, bottom center
        "Style: Default,Noto Sans Devanagari,72,&H00FFFFFF,&H000000FF,&H0000BFFF,&HA0000000,"
        "1,0,0,0,100,100,1,0,1,4,2,2,60,60,80,1\n"
        # Hook — large cyan text, upper center, eye-catching
        "Style: Hook,Noto Sans Devanagari,88,&H00FFFF00,&H000000FF,&H00000000,&H90000000,"
        "1,0,0,0,100,100,0,0,1,6,3,8,60,60,200,1\n"
        # CTA — bottom, bright
        "Style: CTA,Noto Sans Devanagari,62,&H0000FFFF,&H000000FF,&H00000000,&H80000000,"
        "1,0,0,0,100,100,0,0,1,5,2,2,60,60,120,1\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
    )
    ev = []

    # Hook with bounce-in animation
    if hook:
        ev.append(
            f"Dialogue: 2,{_ts(0.1)},{_ts(3.2)},Hook,,0,0,0,,"
            f"{{\\fad(120,300)\\t(0,300,\\fscx110\\fscy110)\\t(300,600,\\fscx100\\fscy100)}}"
            f"{_esc(hook)}"
        )

    # Subtitles with word-by-word pop
    for start, dur, text in timing:
        words = text.split()
        # Group into chunks of 3 words max for readability
        chunks = [" ".join(words[i:i+3]) for i in range(0, len(words), 3)] or [text]
        usable = max(dur - 0.3, 0.4)
        weights = [max(len(c), 1) for c in chunks]
        t = start + 0.08
        for c, w in zip(chunks, weights):
            seg = usable * w / sum(weights)
            ev.append(
                f"Dialogue: 0,{_ts(t)},{_ts(t+seg)},Default,,0,0,0,,"
                f"{{\\fad(80,80)}}{_esc(c)}"
            )
            t += seg

    # CTA with slide-up animation at the end
    if C.CTA_TEXT:
        ev.append(
            f"Dialogue: 1,{_ts(max(total-2.5,0))},{_ts(total)},CTA,,0,0,0,,"
            f"{{\\fad(300,100)\\move(540,1820,540,1750,0,400)}}{_esc(C.CTA_TEXT)}"
        )

    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

# ── transition between clips ─────────────────────────────────────────────────
def _add_transitions(clips, work):
    """Add flash/fade transitions between clips for a more dynamic feel."""
    if len(clips) <= 1:
        return clips

    out_clips = []
    for i, clip in enumerate(clips):
        if i == 0:
            out_clips.append(clip)
            continue
        trans = os.path.join(work, f"trans_{i}.mp4")
        # Quick white flash transition (0.15s)
        dur = probe_duration(clip)
        fc = (
            f"[0:v]fade=t=in:st=0:d=0.15:color=white[v];"
            f"[0:a]afade=t=in:st=0:d=0.1[a]"
        )
        try:
            run(["ffmpeg", "-y", "-i", clip, "-filter_complex", fc,
                 "-map", "[v]", "-map", "[a]",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                 "-c:a", "aac", "-ar", "44100", trans])
            out_clips.append(trans)
        except Exception:
            out_clips.append(clip)  # fallback: use original
    return out_clips

# ── final assembly ───────────────────────────────────────────────────────────
def assemble(work, timing, clips, final_path, hook="", music_dir="assets/music"):
    # Add transitions
    clips = _add_transitions(clips, work)

    listf = os.path.join(work, "list.txt")
    open(listf, "w").write("".join(f"file '{os.path.abspath(c)}'\n" for c in clips))
    joined = os.path.join(work, "joined.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf, "-c", "copy", joined])
    total = probe_duration(joined)
    make_ass(timing, hook, total, os.path.join(work, "subs.ass"))

    tracks = glob.glob(os.path.join(music_dir, "*.mp3")) + glob.glob(os.path.join(music_dir, "*.wav"))
    enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.2f}"]
    final_abs = os.path.abspath(final_path)

    if tracks:
        fc = (
            "[0:v]ass=subs.ass[v];"
            "[0:a]asplit=2[voice][sc];"
            "[1:a]volume=0.45[m];"
            "[m][sc]sidechaincompress=threshold=0.035:ratio=12:attack=12:release=350[duck];"
            "[voice][duck]amix=inputs=2:duration=first:dropout_transition=0,volume=2.2,"
            "loudnorm=I=-14:TP=-1.5:LRA=11[a]"
        )
        run(["ffmpeg", "-y", "-i", "joined.mp4",
             "-stream_loop", "-1", "-i", os.path.abspath(random.choice(tracks)),
             "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
             *enc, final_abs], cwd=work)
    else:
        run(["ffmpeg", "-y", "-i", "joined.mp4",
             "-vf", "ass=subs.ass",
             "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
             *enc, final_abs], cwd=work)

    return probe_duration(final_abs)
