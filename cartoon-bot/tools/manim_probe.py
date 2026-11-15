"""Feasibility probe: can Manim render a 1080x1920 scene on the GitHub runner (no LaTeX)?"""
import subprocess, sys, time, os
src = '''
from manim import *
config.pixel_width, config.pixel_height, config.frame_rate = 1080, 1920, 30
config.frame_width = 9; config.frame_height = 16
class Probe(Scene):
    def construct(self):
        self.camera.background_color = "#0d0f26"
        layers = [3, 4, 2]
        cols = VGroup(*[VGroup(*[Circle(0.28, color="#2dd4bf", fill_opacity=0.9) for _ in range(n)]).arrange(DOWN, buff=0.45) for n in layers]).arrange(RIGHT, buff=1.8)
        edges = VGroup(*[Line(a.get_right(), b.get_left(), stroke_width=2, color="#818cf8") for i in range(len(layers)-1) for a in cols[i] for b in cols[i+1]])
        t = Text("Neural Network", font_size=56, weight=BOLD).to_edge(UP, buff=2)
        self.play(Write(t), run_time=0.6)
        self.play(LaggedStart(*[GrowFromCenter(c) for c in cols], lag_ratio=0.3), run_time=1.0)
        self.play(Create(edges), run_time=1.0)
        self.play(*[ShowPassingFlash(e.copy().set_color(YELLOW).set_stroke(width=6), time_width=0.5) for e in edges], run_time=1.0)
        ax = Axes(x_range=[-3, 3], y_range=[0, 9], x_length=7, y_length=5).shift(DOWN*4)
        g = ax.plot(lambda x: x*x, color="#fb923c")
        dot = Dot(ax.c2p(-2.5, 6.25), color=YELLOW)
        self.play(Create(ax), Create(g), FadeIn(dot), run_time=0.8)
        self.play(MoveAlongPath(dot, ax.plot(lambda x: x*x, x_range=[-2.5, 0])), run_time=1.0)
'''
open("probe_scene.py", "w").write(src)
t = time.time()
r = subprocess.run([sys.executable, "-m", "manim", "-ql" if os.environ.get("FAST") else "-qh", "--format", "mp4",
                    "-o", "probe.mp4", "probe_scene.py", "Probe", "--disable_caching"], capture_output=True, text=True)
print(r.stdout[-1500:], r.stderr[-1500:])
print(f"render exit={r.returncode} in {time.time()-t:.1f}s")
