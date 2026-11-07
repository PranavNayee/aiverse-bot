"""Instagram admin jobs (run from the 'Pre-flight check' workflow):
    post-lesson <n>   - re-post an already-made lesson video to Instagram (e.g. after deleting it there)"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import instagram, storage, notify

cmd, args = sys.argv[1], sys.argv[2:]
if cmd == "post-lesson":
    n = int(args[0])
    history = storage.get_json("history.json", [])
    entry = next(h for h in reversed(history) if h.get("type") == "lesson" and h.get("lesson_num") == n)
    slot = entry["slot"]
    vids = [x for x in storage.list_names("lessons") if x.startswith(slot)]
    covers = [x for x in storage.list_names("covers") if x.startswith(slot)]
    if not vids:
        sys.exit(f"No stored video for slot {slot}")
    url = storage.public_url(f"lessons/{vids[-1]}")
    cover = storage.public_url(f"covers/{covers[-1]}") if covers else None
    topic = entry.get("topic", f"Lesson {n}")
    caption = (f"🤖 {entry.get('hook') or topic}\n\n📚 Lesson #{n} · Basics · {topic}\n\n"
               "AI ko simple Hinglish mein samjho - 60 seconds mein!\n\n"
               "💬 Koi doubt? Comment karo 👇 har sawaal ka jawab milega!\n"
               "Save karo baad ke liye aur us dost ko bhejo jo AI seekh raha hai 🔖\n"
               "Roz subah 8 baje naya AI video - follow karo 🔔\n\n"
               "#aiverse #aiinhindi #learnai #artificialintelligence #machinelearning #aiexplained")
    if instagram.already_posted(caption):
        sys.exit("Already on Instagram - not posting twice.")
    media_id = instagram.post_reel(url, caption, cover)
    entry["media_id"] = media_id; entry["posted_ts"] = int(time.time())
    storage.put_json("history.json", history)
    yt = f"\n▶️ YouTube: https://youtube.com/shorts/{entry['youtube_id']}" if entry.get("youtube_id") else ""
    notify.text(f"✅ Lesson #{n} re-posted to Instagram.{yt}")
    print(f"Posted Lesson #{n} to Instagram: media {media_id}")
else:
    sys.exit(__doc__)
