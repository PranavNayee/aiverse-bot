"""Small YouTube admin jobs (run from the 'Pre-flight check' workflow):
    delete <video_id> [<video_id> ...]   - permanently delete videos from the connected channel
    playlist <video_id> <kind>           - add a video to its series playlist
    post-lesson <n>                      - upload an already-posted Instagram lesson to YouTube (public),
                                           add it to the course playlist and record it in history"""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import youtube, storage

tok = youtube._access_token()
ch = youtube._api("GET", "channels", tok, params={"part": "snippet", "mine": "true"})["items"][0]["snippet"]["title"]
print("Connected channel:", ch)
if ch.strip().lower() != os.environ.get("YT_EXPECTED_CHANNEL", "AIVerse").lower():
    sys.exit(f"Refusing: connected channel is {ch!r}")
cmd, args = sys.argv[1], sys.argv[2:]

if cmd == "delete":
    for vid in args:
        youtube._api("DELETE", "videos", tok, params={"id": vid})
        print("Deleted", vid)

elif cmd == "post-lesson":
    n = int(args[0])
    history = storage.get_json("history.json", [])
    entry = next(h for h in reversed(history) if h.get("type") == "lesson" and h.get("lesson_num") == n)
    if entry.get("youtube_id"):
        sys.exit(f"Lesson #{n} is already on YouTube: {entry['youtube_id']}")
    slot = entry["slot"]
    names = [x for x in storage.list_names("lessons") if x.startswith(slot)]
    if not names:
        sys.exit(f"No stored video for slot {slot}")
    url = storage.public_url(f"lessons/{names[-1]}")
    topic = entry.get("topic", f"Lesson {n}")
    headline = f"{topic} | AI Course Lesson #{n} in Hinglish"
    caption = (f"📚 Lesson #{n} · {topic}\n\n{entry.get('hook', '')}\n\n"
               "Roz subah 8 baje ek naya AI lesson - Subscribe karo! 🔔\n\n"
               "#aiverse #aiinhindi #learnai #machinelearning #artificialintelligence #shorts")
    vid = youtube.upload(url, caption, headline, topic, ["#aiinhindi", "#learnai", "#aiverse"])
    youtube.add_to_playlist(vid, "lesson", tok)
    entry["youtube_id"] = vid
    storage.put_json("history.json", history)
    st = youtube._api("GET", "videos", tok, params={"part": "status", "id": vid})["items"][0]["status"]
    print(f"Posted Lesson #{n} to YouTube: https://youtube.com/shorts/{vid} (privacy: {st.get('privacyStatus')})")
elif cmd == "playlist":                                  # playlist <video_id> <lesson|trick|fun_fact>
    youtube.add_to_playlist(args[0], args[1], tok)
else:
    sys.exit(__doc__)
