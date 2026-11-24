"""Renders a ~25 s demo reel in the current VIDEO_STYLE (default: the smooth light 'motion' look) so you can see
changes without running the whole bot. No API keys, no network.
  python cartoon-bot/tools/preview_reel.py [out.mp4]
Voice: espeak-ng if installed (robotic, English - only a placeholder), otherwise a silent-ish tone. The real reels
use Gemini TTS (Charon) via tts.py."""
import os, shutil, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import edu_render, soundtrack, voice

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "preview_reel.mp4")
W = "preview_work"
shutil.rmtree(W, ignore_errors=True); os.makedirs(W)
SC = [
    ("hook", "Why does AI give you boring answers? It is not the AI. It is your prompt.",
     {"text": "Why does AI give boring answers?", "emoji": "🤔"}),
    ("chat", "Watch this. A vague prompt gets a vague answer. Tell it who to be, and the answer changes completely.",
     {"user": "Act as a food blogger. Write a 3 line review of chai.", "ai": "Chai is not a drink, it is a mood. Ginger, cardamom, and one perfect sip."}),
    ("compare", "Vague prompts give generic answers. Specific prompts give answers you can actually use.",
     {"left_title": "Vague", "right_title": "Specific", "left": ["Write about chai", "Generic answer"], "right": ["Role plus task", "Useful answer"]}),
    ("formula", "Here is the formula. Role, plus task, plus format. Every time.",
     {"heading": "Prompt Formula", "lines": ["Role + Task", "+ Format", "= Great Answer"], "note": "Works in ChatGPT, Gemini, Claude"}),
    ("takeaway", "Remember this. Better prompts mean better answers.",
     {"text": "Better prompt, better answer", "terms": ["role", "task", "format"]}),
    ("cta", "Follow for one new AI trick every day.", {"text": "One AI trick, every day"}),
]
sh = lambda *a: subprocess.run(a, check=True, capture_output=True)
have_tts = shutil.which("espeak-ng") is not None
clips, scenes, words, t = [], [], [], 0.0
for i, (kind, narr, vis) in enumerate(SC):
    a = f"{W}/a{i}.wav"
    if have_tts:
        sh("espeak-ng", "-v", "en-us", "-s", "165", "-p", "35", "-w", a, narr)
    else:
        sh("ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=200:duration=3.5", a)
    d = voice.duration(a) + 0.25
    words += [(t + s, t + e, w) for s, e, w in voice.estimate_words(narr, d)]
    scenes.append({"kind": kind, "visual": vis, "start": t, "dur": d}); clips.append(a); t += d
lv = soundtrack.build(clips, [s["start"] for s in scenes], t, f"{W}/mix.wav", edu_render.FPS, music=True,
                      sfx_at=[s["start"] for s in scenes[1:]])
edu_render.render_video(scenes, f"{W}/mix.wav", lv, OUT, "AI Trick", "trick", words=words,
                        snapshot=(OUT.replace(".mp4", "_cover.jpg"), 1.4))
print(f"preview ok: {t:.1f}s -> {OUT}")
