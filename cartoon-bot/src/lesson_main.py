"""Main lesson generation - uses edu_render professional animation system"""
import datetime, os, shutil, sys, time
from util import log, retry
import config as C
import syllabus, lesson_script, edu_render, storage, notify, instagram, soundtrack, slots, publisher, tts

def _optimize_scene_pacing(scenes):
    """ViMax-inspired pacing: add micro-pauses for complex scenes, speed up simple ones"""
    for scene in scenes:
        kind = scene["kind"]
        
        # Complex scenes need slightly more time to absorb
        if kind in ("network", "formula", "code"):
            # Add 0.3s pause at end for complex visual content
            scene["dur"] += 0.3
            scene["pause_end"] = True
        
        # Fast scenes can be tighter
        elif kind in ("hook", "stat"):
            # These are punchy, no extra pause needed
            scene["pause_end"] = False
        
        else:
            # Normal scenes
            scene["pause_end"] = False
    
    return scenes

EN = C.LANGUAGE_MODE == "english_only"
TXT = {
    "pack": "🎁 Free AI Prompt Pack (25 prompts) - link in bio!" if EN else "🎁 Free AI Prompt Pack (25 prompts) - link bio mein!",
    "save": "Save this for later and share it with a friend who is learning AI 🔖" if EN else
            "Save karo baad ke liye aur us dost ko bhejo jo AI seekh raha hai 🔖",
    "ask": "💬 Comment \"{kw}\" and I'll reply with {what}!" if EN else
           "💬 Comment karo \"{kw}\" - reply mein {what} milega!",
    "follow": "Follow @{h} for a new AI lesson every day 🔔" if EN else "Roz naya AI lesson - follow karo 🔔",
    "default": "AI explained simply, in 60 seconds." if EN else "AI concepts ko simple Hinglish mein samjho!",
    "terms": "Key terms" if EN else "Key terms",
}
BASE_TAGS = [C.BRAND_TAG, "#learnai", "#artificialintelligence"] + (["#aiexplained"] if EN else ["#aiinhindi"])


FREEBIE = {"NEWS": "a 3-line summary" if EN else "3-line summary", "PROMPT": "the exact prompt" if EN else "exact prompt", "NOTES": "quick revision notes" if EN else "revision notes",
           "AI": "one more surprising fact" if EN else "ek aur surprising fact"}


def _caption(headline, title_line, summary, terms, tags, kw="NOTES"):
    tags = list(dict.fromkeys([t for t in tags if t] + BASE_TAGS))[:8]   # Instagram favours few, relevant tags
    parts = [headline, "", title_line, "", summary or TXT["default"]]
    if terms:
        parts += ["", f"💡 {TXT['terms']}: " + " · ".join(terms[:3])]
    parts += ["", TXT["ask"].format(kw=kw, what=FREEBIE.get(kw, "")), TXT["pack"], TXT["save"], TXT["follow"].format(h=C.SERIES_NAME.replace(' ', '').lower()), "",
              " ".join(tags)]
    cap = "\n".join(parts)
    log(f"Caption: {len(cap)} chars")
    return cap[:2150]


def build_lesson_caption(script, lesson_num, level, lesson_title):
    headline = script.get("headline") or f"🤖 {lesson_title}"
    return _caption(headline, f"📚 Lesson #{lesson_num} · {level.title()} · {lesson_title}",
                    script.get("caption_summary", ""), script.get("key_terms", []), script.get("hashtags", []))


def build_fun_fact_caption(script, topic):
    headline = script.get("headline") or f"🤯 {topic}"
    label = "Weekend AI Fun Fact" if EN else "Weekend Special - AI Fun Fact"
    return _caption(headline, f"🎉 {label}", script.get("caption_summary", ""), script.get("key_terms", []),
                    script.get("hashtags", []) + ["#aifacts", "#didyouknow"], kw="AI")


def build_news_caption(script, title):
    headline = script.get("headline") or f"📰 {title}"
    return _caption(headline, f"📰 AI News · {title}", script.get("caption_summary", ""), script.get("key_terms", []),
                    script.get("hashtags", []) + ["#ainews", "#technews"], kw="NEWS")


def build_trick_caption(script, title):
    headline = script.get("headline") or f"🛠️ {title}"
    label = "AI Trick of the Day" if EN else "AI Trick of the Day"
    return _caption(headline, f"🛠️ {label} · {title}", script.get("caption_summary", ""), script.get("key_terms", []),
                    script.get("hashtags", []) + ["#aitools", "#chatgpttips"], kw="PROMPT")


def generate_lesson_video(lesson, lesson_num, script):
    """Voice -> one soundtrack -> one single-pass 2D animated render. Returns (video, seconds, cover jpg)."""
    lvl = lesson.get("level")
    label = (f"Lesson {lesson_num}/{syllabus.TOTAL}" if lesson_num else "AI Trick" if lvl == "trick" else
             "AI News" if lvl == "news" else "Fun Fact")
    log(f"🎬 Rendering {label}: {lesson['title']}")
    shutil.rmtree("work", ignore_errors=True)
    os.makedirs("work")

    if C.LANGUAGE_MODE == "hinglish" and tts.needs_devanagari():
        log("🗣️ Preparing Devanagari speech for proper Hindi pronunciation...")
        for sc, sp in zip(script["scenes"], lesson_script.to_speech([s["narration"] for s in script["scenes"]])):
            sc["speech"] = sp
    voices = tts.speak_scenes(script["scenes"])
    scenes = _optimize_scene_pacing([{"kind": s["kind"], "visual": s["visual"], "dur": d}
                                     for s, (_, d, _) in zip(script["scenes"], voices)])
    t, words = 0.0, []
    for sc, (_, _, ws) in zip(scenes, voices):
        sc["start"] = t
        words += [(t + a, t + b, w) for a, b, w in ws]
        t += sc["dur"]
    total = t

    log("🎵 Building soundtrack (voice + music bed + lip-sync levels)...")
    levels = soundtrack.build([v[0] for v in voices], [s["start"] for s in scenes], total, "work/mix.wav",
                              edu_render.FPS, music=C.MUSIC, music_dir=C.MUSIC_DIR,
                              voice_af=(C.VOICE_FILTER if tts.LAST == "edge" else C.VOICE_FILTER_LIGHT) if C.VOICE_FX else None,
                              sfx_at=[s["start"] for s in scenes[1:]])

    log(f"🖌️ Animating {len(scenes)} scenes, {total:.1f}s (mascot={C.MASCOT})...")
    final_video, cover = "work/final.mp4", "work/cover.jpg"
    edu_render.render_video(scenes, "work/mix.wav", levels, final_video, label, lesson.get("level", "basics"),
                            words=words, mascot_on=C.MASCOT, snapshot=(cover, min(1.4, total / 2)))
    log(f"✅ Video complete: {total:.1f}s, {os.path.getsize(final_video) / 1e6:.1f} MB")
    return final_video, total, cover


DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def content_kind(slot):
    want = os.environ.get("CONTENT_TYPE", "auto").strip().lower()      # auto | lesson | trick | news | fun_fact
    if want in ("lesson", "trick", "news", "fun_fact"):
        return want
    plan = C.CONTENT_PLAN if slots.index(slot) == 0 else C.CONTENT_PLAN_PM
    return plan.get(DAYS[slot.weekday()], "lesson").strip()


def build_content(history, slot):
    """Picks the slot's content from the weekly plan (C.CONTENT_PLAN) for the POSTING day."""
    kind = content_kind(slot)
    base = dict(lesson_num=None, fact_idx=None, trick_idx=None, news_url=None)
    if kind == "news":
        import news
        story = None
        try:
            story = news.pick(used_links={h.get("news_url") for h in history if h.get("news_url")},
                              used_titles={h.get("topic") for h in history if h.get("type") == "news"})
        except Exception as e:
            log("News skipped:", e)
        if story:
            log("📰 AI News reel")
            script = lesson_script.generate_news_script(story)
            title = story["title_en"] if EN else story["title"]
            lesson = {"title": title, "title_en": story["title_en"], "level": "news"}
            return dict(base, script=script, lesson=lesson, news_url=story["link"], type="news", level="news",
                        keyword="NEWS", topic=title, caption=build_news_caption(script, title))
        log("No good news story - making an AI trick instead")
        kind = "trick"
    if kind == "fun_fact":
        log("🎉 Fun fact day")
        fact = syllabus.get_fun_fact(history)
        script = lesson_script.generate_fun_fact_script(fact)
        lesson = {"title": fact["title"], "title_en": fact["title"], "level": "weekend"}
        return dict(base, script=script, lesson=lesson, fact_idx=fact["idx"], type="fun_fact", level="weekend",
                    keyword="AI", topic=fact["title"], caption=build_fun_fact_caption(script, fact["title"]))
    if kind == "trick":
        log("🛠️ AI Trick of the Day")
        tr = syllabus.get_next_trick(history)
        script = lesson_script.generate_trick_script(tr)
        title = tr["title_en"] if EN else tr["title"]
        lesson = {"title": title, "title_en": tr["title_en"], "level": "trick"}
        return dict(base, script=script, lesson=lesson, trick_idx=tr["idx"], type="trick", level="trick",
                    keyword="PROMPT", topic=title, caption=build_trick_caption(script, title))
    log("📚 Lesson day")
    lesson, num, nxt = syllabus.get_next_lesson(history)
    script = lesson_script.generate_lesson_script(lesson, num, nxt)
    return dict(base, script=script, lesson=lesson, lesson_num=num, type="lesson", level=lesson["level"], keyword="NOTES",
                topic=lesson["title_en"] if EN else lesson["title"],
                caption=build_lesson_caption(script, num, lesson["level"], lesson["title_en"] if EN else lesson["title"]))


def _token_warning():
    try:
        days = instagram.token_days_left()
        if days is not None and days < 10:
            notify.text(f"⚠️ Your Instagram access token expires in {days:.0f} days. "
                        "Renew it (see GET_NEW_TOKEN.md) or posting will stop.")
    except Exception as e:
        log("Token check skipped:", e)


def fresh_start():
    """Restart the series at Lesson #1: back up and clear history + stats (old reels stay on Instagram)."""
    stamp = slots.now().strftime("%Y%m%d-%H%M%S")
    for key, empty in (("history.json", []), ("stats.json", {})):
        old = storage.get_json(key, None)
        if old:
            storage.put_json(f"backups/{stamp}-{key}", old)
        storage.put_json(key, empty)
    storage.delete("pending.json")
    log(f"🆕 Fresh start: history and stats reset (backup: backups/{stamp}-*). Next lesson is #1.")
    notify.text(f"🆕 Fresh start! The series restarts at Lesson #1 (old history backed up as backups/{stamp}-*).")


def run_lesson_generation():
    t0 = time.time()
    force_new = os.environ.get("FORCE_NEW", "false").lower() == "true"
    post_now = os.environ.get("POST_NOW", "false").lower() == "true"

    if post_now:                                    # manual "make one and post it right now"
        slot = slots.now()
        key = slot.strftime("%Y-%m-%d-now%H%M")
    if os.environ.get("FRESH_START", "false").lower() == "true":
        fresh_start()
    history = storage.get_json("history.json", [])
    pending = storage.get_json("pending.json", None)
    if not post_now:
        slot = slots.upcoming_slot(done={h.get("slot") for h in history})
        key = slots.key(slot)
    log(f"🗓️ Target slot: {slots.fmt(slot)} (key {key}, review mode: {C.REVIEW_MODE})")
    if (pending and not post_now and not force_new and pending.get("slot") != key
            and time.time() < float(pending.get("post_at", 0)) + 3 * 3600):
        log(f"✅ An earlier reel ({pending.get('slot')}) is still queued - handing over to the poster first.")
        publisher.run(wait=True)
        return
    if not force_new and not post_now:
        if any(h.get("slot") == key for h in history):
            log(f"✅ The {key} reel is already posted - nothing to do.")
            return
        if pending and pending.get("slot") == key:
            log(f"✅ The {key} reel is already made and queued - handing over to the poster.")
            publisher.run(wait=True)
            return
    if pending and pending.get("slot") != key:
        log(f"Replacing an old unposted reel for slot {pending.get('slot')}.")
        notify.text(f"ℹ️ The reel for {pending.get('slot')} was never posted; replacing it with the {key} reel.")

    try:
        import growth
        lesson_script.WINNERS = growth.winners()
        if lesson_script.WINNERS:
            log("🧠 Learning from best hooks:", lesson_script.WINNERS[:200])
    except Exception as e:
        log("Learning loop skipped:", e)
    c = build_content(history, slot)
    final_video, duration, cover = generate_lesson_video(c["lesson"], c["lesson_num"], c["script"])

    log("☁️ Uploading to Supabase...")
    stamp = slots.now().strftime("%H%M%S")
    url = storage.upload_file(final_video, f"lessons/{key}-{stamp}.mp4")
    cover_url = None
    try:
        cover_url = storage.upload_file(cover, f"covers/{key}-{stamp}.jpg", "image/jpeg")
    except Exception as e:
        log("Cover upload failed (posting without cover):", e)

    if os.environ.get("DRY_RUN", "false").lower() == "true":
        log(f"🧪 DRY RUN - not queued or posted. Video: {url}")
        notify.video(final_video, f"🧪 Preview only (not posted): {c['topic']} ({duration:.0f}s)\n\n{c['caption'][:700]}", url)
        return

    post_at = time.time() if post_now else slot.timestamp()
    storage.put_json("pending.json", {
        "slot": key, "post_at": int(post_at), "video_url": url, "cover_url": cover_url, "caption": c["caption"],
        "topic": c["topic"], "type": c["type"], "lesson_num": c["lesson_num"], "fact_idx": c["fact_idx"],
        "trick_idx": c["trick_idx"], "keyword": c["keyword"], "freebie": c["script"].get("freebie", ""),
        "news_url": c.get("news_url"),
        "level": c["level"], "duration": round(duration, 1), "fact_check": c["script"].get("fact_check", "pass"),
        "hook": c["script"]["scenes"][0]["narration"], "headline": c["script"].get("headline", ""),
        "created_ts": int(time.time()), "attempts": 0, "status": "queued",
    })
    for prefix, keep in (("lessons", 30), ("covers", 30)):
        try:
            storage.cleanup(prefix, keep=keep)
        except Exception as e:
            log("Cleanup skipped:", e)

    when = "right now" if post_now or post_at <= time.time() else slots.fmt(post_at)
    how = {"auto": f"It will post automatically {when}.",
           "auto_unless_skip": f"It will post {when} unless you reply /skip.",
           "approve": f"Reply /post to publish it at {when} (or /postnow to publish immediately, /skip to discard)."}
    warn = "\n⚠️ Fact-check flagged issues - please watch before it posts." if c["script"].get("fact_check") == "warning" else ""
    notify.video(final_video, f"🎬 {c['topic']} ({duration:.0f}s)\n{how.get(C.REVIEW_MODE, how['approve'])}{warn}", url)
    _token_warning()
    log(f"✅ Reel ready in {time.time() - t0:.0f}s. Queued for {when}.")

    publisher.run(force=post_now, wait=True)       # posts now if due, or sleeps until the slot if it is close
    log(f"✅ Done in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    try:
        run_lesson_generation()
    except Exception as e:
        log(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        notify.text(f"❌ Reel generation failed (a backup run will retry):\n{str(e)[:800]}")
        sys.exit(1)
