"""Tests the VIDEO part with fake images and fake audio (no internet, no API keys needed).
Run:  python tests/offline_test.py      (needs ffmpeg installed)"""
import os, shutil, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import video

W = "test_work"
shutil.rmtree(W, ignore_errors=True); os.makedirs(W)
sh = lambda *a: subprocess.run(a, check=True, capture_output=True)

scenes = [("tall 9:16 image", "768x1344"), ("square image", "1024x1024"), ("wide image", "1280x720"), ("tall again", "768x1344")]
clips, timing, t = [], [], 0.0
for i, (label, size) in enumerate(scenes):
    img, aud, clip = f"{W}/i{i}.png", f"{W}/a{i}.wav", f"{W}/c{i}.mp4"
    sh("ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc2=size={size}", "-frames:v", "1", img)
    dur = 3.0 + i * 0.5
    sh("ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency={300+100*i}:duration={dur-0.45}", aud)
    video.scene_clip(img, aud, dur, i, clip)
    clips.append(clip); timing.append((t, dur, f"यह सीन नंबर {i+1} का एक छोटा सा संवाद है")); t += dur
    print("scene ok:", label)

os.makedirs(f"{W}/music", exist_ok=True)
sh("ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=5", f"{W}/music/m.wav")
for name, mdir in (("with_music", f"{W}/music"), ("no_music", f"{W}/none")):
    out = f"{W}/final_{name}.mp4"
    length = video.assemble(W, timing, clips, out, hook="आज की बड़ी खबर", music_dir=mdir)
    print(f"{name}: {length:.1f}s, {os.path.getsize(out)/1e6:.2f} MB")
    assert length > 10 and os.path.getsize(out) > 50_000
print("ALL VIDEO TESTS PASSED")
