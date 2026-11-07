"""The ONLY code path that publishes to Instagram. Shared by the generator and the poster workflow.

Guarantees:
  * posts at the slot time (sleeps until it if the job started early - GitHub cron is often hours late or skipped)
  * never posts the same reel twice: storage claim-lock + a check of the account's latest posts
  * history is written only after a SUCCESSFUL post, so a failed/skipped day never burns a lesson number
"""
import re, time, uuid, traceback
import config as C, storage, instagram, notify, slots, youtube, facebook
from util import log

MAX_ATTEMPTS = 3
CLAIM_TTL = 15 * 60


def due_at(p):
    t = float(p.get("post_at") or p.get("created_ts") or 0)
    if C.REVIEW_MODE == "auto_unless_skip":
        t = max(t, float(p.get("created_ts", 0)) + C.REVIEW_HOURS * 3600)
    return t


def _command(p):
    try:
        return notify.latest_command(int(p.get("created_ts", 0)))
    except Exception as e:
        log("Telegram command check failed (ignored):", e)
        return None


def _record(p, media_id):
    history = storage.get_json("history.json", [])
    history.append({
        "date": p.get("slot"), "slot": p.get("slot"), "type": p.get("type", "lesson"),
        "lesson_num": p.get("lesson_num"), "fact_idx": p.get("fact_idx"), "trick_idx": p.get("trick_idx"),
        "level": p.get("level"), "keyword": p.get("keyword"), "freebie": p.get("freebie", ""),
        "news_url": p.get("news_url"),
        "topic": p.get("topic", ""), "duration": p.get("duration"), "fact_check": p.get("fact_check"),
        "media_id": media_id, "posted_ts": int(time.time()), "hook": p.get("hook", ""),
        "youtube_id": p.get("youtube_id"),
    })
    storage.put_json("history.json", history[-400:])


def _claim(slot_key):
    """Optimistic lock in Supabase so two overlapping jobs can't both publish."""
    cur = storage.get_json("pending.json", None)
    if not cur or cur.get("slot") != slot_key:
        log("Pending reel changed or already handled by another job.")
        return None
    if cur.get("status") == "publishing" and time.time() - cur.get("claim_ts", 0) < CLAIM_TTL:
        log("Another job is publishing this reel right now - leaving it to that job.")
        return None
    me = uuid.uuid4().hex
    cur.update(status="publishing", claim=me, claim_ts=int(time.time()))
    storage.put_json("pending.json", cur)
    time.sleep(5)
    back = storage.get_json("pending.json", None)
    if not back or back.get("claim") != me:
        log("Lost the publish lock to another job.")
        return None
    return back


def publish(p, force=False):
    if p.get("attempts", 0) >= MAX_ATTEMPTS and not force:
        log("Too many failed attempts; run 'Post approved reel' manually with force_post = true.")
        return "gave_up"
    p = _claim(p.get("slot"))
    if not p:
        return "busy"
    if instagram.already_posted(p["caption"]):
        log("This reel is already on Instagram - not posting it again.")
        _record(p, "already-posted")
        storage.delete("pending.json")
        return "duplicate"
    try:
        media_id = instagram.post_reel(p["video_url"], p["caption"], p.get("cover_url"))
    except Exception:
        err = traceback.format_exc(); log(err)
        p["attempts"] = p.get("attempts", 0) + 1
        p["status"] = "queued"; p.pop("claim", None)
        storage.put_json("pending.json", p)
        extra = ("\nI will retry automatically on the next run." if p["attempts"] < MAX_ATTEMPTS else
                 "\nGiving up for now. Fix the problem, then run 'Post approved reel' with force_post = true.")
        notify.text(f"❌ Instagram posting failed ({p['attempts']}/{MAX_ATTEMPTS}):\n{err[-1200:]}{extra}")
        raise
    yt = ""
    if youtube.enabled():
        try:
            p["youtube_id"] = youtube.upload(p["video_url"], p["caption"], p.get("headline"), p.get("topic"),
                                             re.findall(r"#\w+", p["caption"]))
            youtube.add_to_playlist(p["youtube_id"], p.get("type"))
            yt = f"\n▶️ YouTube Short: https://youtube.com/shorts/{p['youtube_id']}"
        except Exception as e:
            log("YouTube cross-post failed:", e)
            yt = f"\n⚠️ YouTube upload failed: {str(e)[:300]}"
    if facebook.enabled():
        try:
            p["fb_id"] = facebook.post_reel(p["video_url"], p["caption"])
            yt += "\n📘 Facebook Reel posted"
        except Exception as e:
            log("Facebook cross-post failed:", e)
            yt += f"\n⚠️ Facebook failed: {str(e)[:200]}"
    _record(p, media_id)
    storage.delete("pending.json")
    notify.text(f"✅ Posted to Instagram ({slots.fmt(time.time())}): {p.get('topic', '')}{yt}")
    return "posted"


def run(force=False, wait=True):
    """Post the pending reel if it is due (sleeping until the slot when it is close). Returns a status string."""
    p = storage.get_json("pending.json", None)
    if not p:
        log("Nothing pending.")
        return "nothing"
    p.setdefault("slot", p.get("date", "legacy"))
    if force:
        return publish(p, force=True)

    while True:
        cmd = _command(p)
        if cmd == "skip":
            storage.delete("pending.json")
            notify.text(f"🗑️ Discarded: {p.get('topic', 'pending reel')}")
            return "skipped"
        if cmd == "post_now":
            return publish(p)
        if C.REVIEW_MODE == "approve" and cmd != "post":
            log(f"Waiting for your /post in Telegram (slot {slots.fmt(due_at(p))}).")
            return "awaiting_approval"
        wait_s = due_at(p) - time.time()
        if wait_s <= 0:
            return publish(p)
        if not wait or wait_s > C.MAX_WAIT_MINUTES * 60:
            log(f"Not due yet - scheduled for {slots.fmt(due_at(p))} ({wait_s/3600:.1f} h from now).")
            return "not_due"
        nap = min(wait_s, 600)                     # wake every <=10 min to honour a late /skip
        log(f"Sleeping {nap/60:.1f} min - posting at {slots.fmt(due_at(p))}.")
        time.sleep(nap)
        p = storage.get_json("pending.json", None)
        if not p:
            log("Pending reel was handled elsewhere while waiting.")
            return "nothing"
        p.setdefault("slot", p.get("date", "legacy"))
