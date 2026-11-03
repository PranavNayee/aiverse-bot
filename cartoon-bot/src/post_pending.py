import os, sys, time, traceback
import config as C, storage, instagram, notify
from util import log

MAX_ATTEMPTS = 3

def main():
    force = os.environ.get("FORCE_POST", "false").lower() == "true"
    p = storage.get_json("pending.json", None)
    if not p:
        log("Nothing pending."); return
    age = time.time() - p["created_ts"]
    cmd = None if force else notify.latest_command(p["created_ts"])

    if cmd == "skip":
        storage.delete("pending.json")
        notify.text(f"🗑️ Discarded: {p['topic']}")
        return
    due = force or cmd == "post" or (C.REVIEW_MODE == "auto_unless_skip" and age >= C.REVIEW_HOURS * 3600)
    if not due:
        log(f"Waiting for approval (age {age/60:.0f} min)."); return
    if p.get("attempts", 0) >= MAX_ATTEMPTS and not force:
        log("Too many failed attempts; use the manual workflow with force_post."); return

    try:
        media_id = instagram.post_reel(p["video_url"], p["caption"], p.get("cover_url"))
    except Exception:
        err = traceback.format_exc(); log(err)
        p["attempts"] = p.get("attempts", 0) + 1
        storage.put_json("pending.json", p)
        extra = "\nI will retry automatically." if p["attempts"] < MAX_ATTEMPTS else \
                "\nGiving up for now. Fix the problem, then run 'Post approved reel' manually with force_post = true."
        notify.text(f"❌ Instagram posting failed ({p['attempts']}/{MAX_ATTEMPTS}):\n{err[-1200:]}{extra}")
        sys.exit(1)

    history = storage.get_json("history.json", [])
    for h in reversed(history):
        if h.get("date") == p["date"] and h.get("topic") == p["topic"]:
            h["media_id"] = media_id; break
    storage.put_json("history.json", history)
    storage.delete("pending.json")
    notify.text(f"✅ Posted to Instagram: {p['topic']}")

if __name__ == "__main__":
    main()
