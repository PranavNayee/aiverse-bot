"""Renders the same lines with every voice option so you can pick by ear. Output: test_work/voices/*.mp3
Run in GitHub Actions: 'Pre-flight check' workflow -> voice_samples = true (uses your GEMINI_API_KEY)."""
import os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import config as C, tts, voice, soundtrack

OUT = "test_work/voices"
os.makedirs(OUT, exist_ok=True); os.makedirs("work", exist_ok=True)
HI = "Kya aapka AI model real world mein fail ho jata hai? Isko cricket ki tarah samjho. Nets mein practice karna training hai, aur asli match testing hai."
HI_DEV = "क्या आपका AI model real world में fail हो जाता है? इसको cricket की तरह समझो। Nets में practice करना training है, और असली match testing है।"
EN = "Does your AI model fail in the real world? Think of it like cricket. Practice in the nets is training, and the real match is testing."


def mp3(wav, name):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-af", C.VOICE_FILTER_LIGHT, "-q:a", "2",
                    f"{OUT}/{name}.mp3"], check=True)
    print("ok", name)


voices = [v.strip() for v in os.environ.get("SAMPLE_VOICES", "Charon,Orus,Fenrir,Iapetus,Alnilam,Sadaltager").split(",")]
for v in voices:
    C.GEMINI_VOICE = v
    for lang, text, tag in (("hinglish", HI, "hinglish"), ("hinglish", HI_DEV, "hinglish_devanagari"),
                            ("english_only", EN, "english")):
        C.LANGUAGE_MODE = lang
        try:
            model, x, sr = tts._gemini_one(text, "x")
            soundtrack.write_wav("work/s.wav", x, sr)
            mp3("work/s.wav", f"gemini_{v}_{tag}")
        except Exception as e:
            print("FAILED", v, tag, str(e)[:300])

for name, text, spk in (("edge_madhur_hinglish", HI_DEV, "hinglish"), ("edge_andrew_english", EN, "english")):
    try:
        voice.synth(text, spk, "work/e.mp3"); mp3("work/e.mp3", name)
    except Exception as e:
        print("FAILED", name, e)
print("models used:", tts.gemini_tts_models())
