"""Tests the 3D motion + assembly with stand-in pictures and fake audio (no internet, no API keys).
Run:  python tests/offline_test.py"""
import os, shutil, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, depth, motion3d, video

W = "test_work"
shutil.rmtree(W, ignore_errors=True); os.makedirs(W)
sh = lambda *a: subprocess.run(a, check=True, capture_output=True)
cams = [("push", "none"), ("orbit", "zoom"), ("pull", "none"), ("shake", "shake")]
specs, timing, t = [], [], 0.0
for i, (cam, react) in enumerate(cams):
    img, aud, d = f"{W}/i{i}.png", f"{W}/a{i}.wav", f"{W}/d{i}.npy"
    sh("ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=size=768x1344", "-frames:v", "1", img)
    np.save(d, depth.pseudo_depth(768, 1344))
    dur = 2.5 + i * 0.4
    sh("ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=frequency={200+50*i}:duration={dur-0.45},tremolo=f=5:d=0.9", aud)
    out = f"{W}/c{i}.mp4"
    motion3d.render_scene(dict(image=img, depth=d, audio=aud, dur=dur, camera=cam, reaction=react,
                               sticker="😂" if i == 1 else "", mouth={"x": .5, "y": .5, "w": .2} if i else None,
                               speaker="bablu" if i != 2 else "narrator", speaker_is_char=(i != 2), idx=i), out)
    specs.append(out); timing.append((t, dur, f"यह सीन नंबर {i+1} का एक छोटा सा संवाद है", "bablu" if i != 2 else "narrator")); t += dur
    print("scene ok:", cam, react)

os.makedirs(f"{W}/music", exist_ok=True)
sh("ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=5", f"{W}/music/m.wav")
for name, mdir in (("with_music", f"{W}/music"), ("no_music", f"{W}/none")):
    out = f"{W}/final_{name}.mp4"
    length = video.assemble(W, timing, specs, out, hook="आज की बड़ी खबर", music_dir=mdir)
    print(f"{name}: {length:.1f}s, {os.path.getsize(out)/1e6:.2f} MB")
    assert length > 8 and os.path.getsize(out) > 50_000
print("ALL VIDEO TESTS PASSED")
