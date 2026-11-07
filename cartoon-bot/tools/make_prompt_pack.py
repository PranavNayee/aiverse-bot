"""Builds the free 'AIVerse AI Prompt Pack' PDF (lead magnet) into docs/ so GitHub Pages hosts it for free.
Run: PYTHONPATH=cartoon-bot/src python cartoon-bot/tools/make_prompt_pack.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from PIL import Image, ImageDraw
import edu_render as E, mascot, syllabus

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "aiverse-prompt-pack.pdf")
PW, PH = 1240, 1754                                   # A4 @150 dpi
TEAL, ORANGE, INK, MUTED = (13, 148, 136), (234, 88, 12), (24, 26, 48), (90, 96, 120)

PROMPTS = [
 ("Expert in one line", "Act as an experienced [ROLE]. My goal is [GOAL]. Context: [DETAILS ABOUT ME/SITUATION]. Answer as [FORMAT, e.g. 5 bullet points / a table]."),
 ("Explain like I'm 10", "Explain [TOPIC] like I'm 10 years old, using one everyday Indian example. Then give a 1-line summary."),
 ("Flashcards from notes", "Turn these notes into 10 question-and-answer flashcards for revision. Keep answers under 20 words.\n[PASTE NOTES]"),
 ("Quiz me", "Quiz me on [CHAPTER/TOPIC]. Ask one question at a time, wait for my answer, then tell me if I'm right and explain mistakes."),
 ("Study timetable", "My exam is on [DATE]. Subjects: [LIST]. I can study [X] hours a day. Make a day-by-day timetable with revision days."),
 ("Socratic tutor", "Don't give me the answer. Guide me to solve this with questions, one step at a time: [PROBLEM]"),
 ("Mock interview", "Act as an interviewer for a [JOB ROLE] role. Ask me one question at a time and give feedback on each answer."),
 ("Tell me about yourself", "Write a 30-second 'tell me about yourself' answer for a [JOB] interview. Education: [..]. Skills: [..]. Keep it natural."),
 ("Honest resume bullets", "Rewrite these resume points to be clear and action-focused. Do NOT add skills or experience I don't have:\n[PASTE]"),
 ("Professional email", "Write a short, polite email to [WHO] about [PURPOSE]. Key points: [..]. Tone: [formal/friendly]. Max 120 words."),
 ("Fix my English", "Correct the grammar in this text and list each mistake with a one-line explanation:\n[PASTE]"),
 ("Change the tone", "Rewrite this to sound more [confident/formal/friendly] without changing the meaning:\n[PASTE]"),
 ("Summarise a video", "Summarise this transcript into 5 key points and 3 quiz questions:\n[PASTE TRANSCRIPT]"),
 ("Excel formula", "Give me a Google Sheets/Excel formula that [WHAT YOU WANT]. My data is in columns [..]. Explain it in one line."),
 ("Explain my error", "I got this error. Explain what it means in simple words and how to fix it:\nError: [..]\nCode: [..]"),
 ("Explain code", "Explain what each line of this code does, in simple language:\n[PASTE CODE]"),
 ("Learning roadmap", "Make a 6-week roadmap to learn [SKILL] from zero, with weekly goals and free resources to search for."),
 ("Three options", "Give me 3 very different options for [TITLE / PLAN / IDEA], with one pro and one con each, in a table."),
 ("Ask me first", "Before answering, ask me any questions you need to give a personalised answer about [TOPIC]."),
 ("Step by step maths", "Solve this step by step and show each step clearly, then check the final answer: [PROBLEM]"),
 ("Both sides", "Give the 3 strongest points FOR and AGAINST: [TOPIC]. Keep it balanced."),
 ("Weekly plan", "These are my tasks and deadlines: [LIST]. Arrange them into a realistic weekly plan with breaks."),
 ("Image prompt formula", "Create an image of [SUBJECT] in [SETTING], [STYLE e.g. 3D cartoon / photo], [LIGHTING], [CAMERA ANGLE], high detail."),
 ("Check the answer", "Which parts of your previous answer are you least sure about? What should I double-check, and where?"),
 ("Mind map", "Break [TOPIC] into a mind map: 4-6 main branches, each with 3 short sub-points."),
]


def page():
    im = Image.new("RGB", (PW, PH), (255, 255, 255)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, PW, 120), fill=(16, 18, 44))
    d.text((70, 60), "AIVerse  ·  AI Prompt Pack", font=E.font(40), fill=(255, 255, 255), anchor="lm")
    d.text((PW - 70, 60), "Free · Hinglish AI", font=E.font(30, False), fill=(45, 212, 191), anchor="rm")
    return im, d


def build():
    pages = []
    cover = Image.new("RGB", (PW, PH), (16, 18, 44)); d = ImageDraw.Draw(cover)
    bot = mascot.sprite((45, 212, 191), 2, False, "happy", 21, 2.4)
    cover.paste(bot, (PW // 2 - bot.width // 2, 300), bot)
    d.text((PW // 2, 1150), "25 Copy-Paste AI Prompts", font=E.font(76), fill=(255, 255, 255), anchor="mm")
    d.text((PW // 2, 1250), f"+ {len(syllabus.TRICKS)} AI tricks for students", font=E.font(48, False), fill=(45, 212, 191), anchor="mm")
    d.text((PW // 2, 1480), "by AIVerse  ·  Roz naya AI video on Instagram & YouTube", font=E.font(36, False), fill=(200, 205, 230), anchor="mm")
    d.text((PW // 2, 1560), "Tip: replace the [BRACKETS] with your own details.", font=E.font(32, False), fill=(251, 146, 60), anchor="mm")
    pages.append(cover)
    im, d = page(); y = 170
    for n, (title, prompt) in enumerate(PROMPTS, 1):
        f = E.font(30, False, True)
        lines = []
        for para in prompt.split("\n"):
            lines += E.wrap(d, para, f, PW - 200) or [""]
        h = 70 + len(lines) * 42 + 40
        if y + h > PH - 80:
            pages.append(im); im, d = page(); y = 170
        d.text((70, y + 20), f"{n}. {title}", font=E.font(38), fill=TEAL, anchor="lm")
        d.rounded_rectangle((70, y + 50, PW - 70, y + 50 + len(lines) * 42 + 30), 18, fill=(243, 245, 250), outline=(210, 215, 230))
        for i, ln in enumerate(lines):
            d.text((100, y + 80 + i * 42), ln, font=f, fill=INK, anchor="lm")
        y += h + 20
    pages.append(im)
    im, d = page(); y = 180
    d.text((70, y), f"{len(syllabus.TRICKS)} AI Tricks (quick list)", font=E.font(44), fill=ORANGE, anchor="lm"); y += 70
    for n, t in enumerate(syllabus.TRICKS, 1):
        if y > PH - 90:
            pages.append(im); im, d = page(); y = 180
        d.text((70, y), f"{n:>2}. {t[1]}", font=E.font(28, False), fill=INK, anchor="lm"); y += 42
    pages.append(im)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pages[0].save(OUT, save_all=True, append_images=pages[1:], resolution=150)
    print(f"Wrote {OUT} ({len(pages)} pages)")


if __name__ == "__main__":
    build()
