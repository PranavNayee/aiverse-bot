"""Renders a complete multi-scene 2D lesson reel with fake audio (no internet, no API keys) and checks
the scheduling logic. Run:  python cartoon-bot/tests/offline_test.py   (needs ffmpeg, numpy, pillow)"""
import datetime as dt, os, shutil, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import edu_render, soundtrack, voice, slots, syllabus, lesson_script

W = "test_work"
shutil.rmtree(W, ignore_errors=True); os.makedirs(W)

# ---------------------------------------------------------------- scheduling
IST = slots.TZ
at = lambda y, mo, d, h, mi: dt.datetime(y, mo, d, h, mi, tzinfo=IST)
up = lambda *a, done=(): slots.key(slots.upcoming_slot(at(*a), done=set(done)))
assert up(2026, 11, 6, 20, 17, done=["2026-11-06-1900"]) == "2026-11-07"      # evening run -> tomorrow 08:00
assert up(2026, 11, 7, 5, 23) == "2026-11-07"                                    # early backup -> today 08:00
assert up(2026, 11, 7, 9, 30) == "2026-11-07"                                    # a bit late -> still the 08:00 slot
assert up(2026, 11, 7, 12, 43, done=["2026-11-07"]) == "2026-11-07-1900"        # midday run -> 19:00 slot
assert up(2026, 11, 7, 15, 3) == "2026-11-07-1900"                               # 08:00 grace over -> 19:00
assert slots.is_weekend(slots.upcoming_slot(at(2026, 11, 6, 21, 0), done={"2026-11-06-1900"}))
print("schedule ok")

# ---------------------------------------------------------------- syllabus counters survive history trimming
hist = [{"type": "lesson", "lesson_num": 57}] + [{"type": "fun_fact", "fact_idx": 3}]
assert syllabus.get_next_lesson(hist)[1] == 58
assert syllabus.get_fun_fact(hist)["idx"] == 4
assert syllabus.get_fun_fact([])["idx"] == 0
assert syllabus.get_next_trick([{"type": "trick", "trick_idx": 2}])["idx"] == 3
import lesson_main
kinds = [lesson_main.content_kind(at(2026, 11, d, 8, 0)) for d in range(9, 16)]     # Mon 9 Nov .. Sun 15 Nov
assert kinds == ["lesson", "trick", "lesson", "trick", "lesson", "trick", "fun_fact"], kinds
pm = [lesson_main.content_kind(at(2026, 11, d, 19, 0)) for d in range(9, 16)]
assert pm == ["trick", "news", "trick", "news", "trick", "news", "trick"], pm
print("syllabus + weekly plan ok")

# ---------------------------------------------------------------- render
raw = {"scenes": [
    {"kind": "hook", "narration": "Kya aapka AI model real world me fail ho jata hai?", "visual": {"text": "Model fail kyun hota hai?", "emoji": "🤔"}},
    {"kind": "compare", "narration": "Isko cricket ki tarah samjho, nets me practice aur match me asli test.", "visual": {"left_title": "Training", "right_title": "Testing", "left": ["Model seekhta hai", "Answers dikhte hain"], "right": ["Naya data", "Asli score"]}},
    {"kind": "flow", "narration": "Pehle data ko do hisson me split karo, phir training set par model ko train karo, aur aakhir me test set par uska asli score check karo.", "visual": {"heading": "Steps", "steps": [{"label": "Split data", "emoji": "✂️"}, {"label": "Train", "emoji": "🏋️"}, {"label": "Test", "emoji": "✅"}]}},
    {"kind": "network", "narration": "Neural network layers me data aage badhta hai aur pattern seekhta hai.", "visual": {"heading": "Neural Net", "layers": [3, 4, 2], "labels": ["Input", "Hidden", "Output"]}},
    {"kind": "code", "narration": "Python me train test split ek line me ho jata hai, bilkul simple.", "visual": {"heading": "Python", "lines": ["from sklearn.model_selection \\", "  import train_test_split", "X_tr, X_te = train_test_split(X)"]}},
    {"kind": "chat", "narration": "ChatGPT ko bolo, act as a teacher aur mujhe train test split samjhao, simple example ke saath.", "visual": {"user": "Act as a teacher. Explain train/test split with a cricket example.", "ai": "Sure! Nets practice = training data. The real match = test data the model has never seen."}},
    {"kind": "takeaway", "narration": "Yaad rakho, model ko hamesha unseen data par test karo, warna score jhoota hoga aur real world me model fail ho sakta hai.", "visual": {"text": "Unseen data par test karo", "terms": ["train", "test", "split"]}},
    {"kind": "cta", "narration": "Agle lesson me supervised learning. Follow karo AI Seekho!", "visual": {"text": "Next: Supervised Learning"}},
], "caption_summary": "x", "key_terms": ["a", "b", "c"]}
script = lesson_script.validate(raw, 5, 10)
assert any(sc["kind"] == "chat" for sc in script["scenes"])

sh = lambda *a: subprocess.run(a, check=True, capture_output=True)
clips, scenes, words, t = [], [], [], 0.0
for i, sc in enumerate(script["scenes"]):
    dur = 2.2 + 0.2 * (i % 3)
    a = f"{W}/a{i}.wav"
    sh("ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency={180+30*i}:duration={dur-0.3},tremolo=f=6:d=0.9", a)
    words += [(t + s, t + e, w) for s, e, w in voice.estimate_words(sc["narration"], dur)]
    scenes.append({"kind": sc["kind"], "visual": sc["visual"], "start": t, "dur": dur}); clips.append(a); t += dur

lv = soundtrack.build(clips, [s["start"] for s in scenes], t, f"{W}/mix.wav", edu_render.FPS, music=True)
assert len(lv) == int(round(t * edu_render.FPS)) and lv.max() > 0.5
out = f"{W}/reel.mp4"
total = edu_render.render_video(scenes, f"{W}/mix.wav", lv, out, "Lesson #7", "basics", words=words,
                                snapshot=(f"{W}/cover.jpg", 1.2))
probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height",
                        "-of", "default=nw=1", out], capture_output=True, text=True).stdout
assert "width=1080" in probe and "height=1920" in probe and "aac" in probe, probe
for i in range(len(scenes)):                                   # one frame per scene for eyeballing
    sh("ffmpeg", "-y", "-ss", f"{scenes[i]['start'] + 1.2:.2f}", "-i", out, "-frames:v", "1", f"{W}/frame_{i}.jpg")
print(f"render ok: {total:.1f}s, {os.path.getsize(out)/1e6:.2f} MB -> {out}")
print("ALL OFFLINE TESTS PASSED")
