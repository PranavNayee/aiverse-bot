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

# ---------------- subtitles (ASS): each speaker gets their own colour ----------------
def _ts(t):
    cs = int(round(max(t, 0) * 100))
    return f"{cs//360000}:{cs%360000//6000:02d}:{cs%6000//100:02d}.{cs%100:02d}"

def _esc(s):
    return re.sub(r"[{}\\]", "", s).replace("\n", " ")

def make_ass(timing, hook, total, path):
    F = "Noto Sans Devanagari"
    def style(name, size, col, align, mv):
        return f"Style: {name},{F},{size},{col},&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,6,2,{align},60,60,{mv},1\n"
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n"
            "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
            "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,"
            "MarginL,MarginR,MarginV,Encoding\n"
            + style("Default", 76, "&H00FFFFFF", 2, 330) + style("bablu", 76, "&H0033D6FF", 2, 330)
            + style("chiku", 76, "&H00FFE078", 2, 330) + style("Hook", 86, "&H0000E5FF", 8, 230)
            + style("CTA", 66, "&H0000E5FF", 8, 230)
            + "\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    ev = []
    if hook:
        ev.append(f"Dialogue: 1,{_ts(0.15)},{_ts(2.8)},Hook,,0,0,0,,{{\\fad(200,250)}}{_esc(hook)}")
    for start, dur, text, speaker in timing:
        sty = speaker if speaker in ("bablu", "chiku") else "Default"
        words = text.split()
        chunks = [" ".join(words[i:i+4]) for i in range(0, len(words), 4)] or [text]
        usable = max(dur - 0.35, 0.5)
        weights = [max(len(c), 1) for c in chunks]
        t = start + 0.1
        for c, w in zip(chunks, weights):
            seg = usable * w / sum(weights)
            ev.append(f"Dialogue: 0,{_ts(t)},{_ts(t+seg)},{sty},,0,0,0,,{_esc(c)}")
            t += seg
    if C.CTA_TEXT:
        ev.append(f"Dialogue: 1,{_ts(max(total-2.2, 0))},{_ts(total)},CTA,,0,0,0,,{{\\fad(250,0)}}{_esc(C.CTA_TEXT)}")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")

# ---------------- final assembly ----------------
def assemble(work, timing, clips, final_path, hook="", music_dir="assets/music"):
    listf = os.path.join(work, "list.txt")
    open(listf, "w").write("".join(f"file '{os.path.abspath(c)}'\n" for c in clips))
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
