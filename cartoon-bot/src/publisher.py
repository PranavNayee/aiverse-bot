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
        "news_url": p.get("news_url"), "alert_idx": p.get("alert_idx"),
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
        log("Too many failed attempts; archiving stuck reel so subsequent slots are not blocked.")
        storage.put_json(f"failed_{p.get('slot')}.json", p)
        storage.delete("pending.json")
        return "gave_up"

    p = _claim(p.get("slot"))
    if not p:
        return "busy"

    # 1. Instagram Reel
    media_id = None
    ig_err = None
    try:
        if instagram.already_posted(p["caption"]):
            log("This reel is already on Instagram - skipping IG re-post.")
            media_id = "already-posted"
        else:
            media_id = instagram.post_reel(p["video_url"], p["caption"], p.get("cover_url"))
            log("Instagram reel posted successfully:", media_id)
    except Exception as e:
        ig_err = traceback.format_exc()
        log("Instagram post failed:\n", ig_err)

    # 2. YouTube Shorts (independent of Instagram success)
    yt = ""
    yt_id = None
    if youtube.enabled():
        try:
            yt_id = youtube.upload(p["video_url"], p["caption"], p.get("headline"), p.get("topic"),
                                   re.findall(r"#\w+", p["caption"]))
            p["youtube_id"] = yt_id
            youtube.add_to_playlist(yt_id, p.get("type"))
            if p.get("thumb_url"):
                try:
                    import requests as rq
                    with open("/tmp/aiverse_thumb.jpg", "wb") as fh:
                        fh.write(rq.get(p["thumb_url"], timeout=60).content)
                    youtube.set_thumbnail(yt_id, "/tmp/aiverse_thumb.jpg")
                except Exception as e:
                    log("Thumbnail step skipped:", e)
            yt = f"\n▶️ YouTube Short: https://youtube.com/shorts/{yt_id}"
            log("YouTube Short posted successfully:", yt_id)
        except Exception as e:
            log("YouTube cross-post failed:", e)
            yt = f"\n⚠️ YouTube upload failed: {str(e)[:300]}"

    # 3. Facebook Reel
    if facebook.enabled():
        try:
            p["fb_id"] = facebook.post_reel(p["video_url"], p["caption"])
            yt += "\n📘 Facebook Reel posted"
            log("Facebook Reel posted successfully")
        except Exception as e:
            log("Facebook cross-post failed:", e)
            yt += f"\n⚠️ Facebook failed: {str(e)[:200]}"

    # 4. Handle results: at least one platform succeeded
    if media_id or yt_id:
        _record(p, media_id or f"yt-{yt_id}")
        storage.delete("pending.json")
        status_lines = []
        if media_id and media_id != "already-posted":
            status_lines.append(f"✅ Posted to Instagram ({slots.fmt(time.time())}): {p.get('topic', '')}")
        elif media_id == "already-posted":
            status_lines.append(f"ℹ️ Reel was already on Instagram: {p.get('topic', '')}")
        else:
            status_lines.append(f"⚠️ Instagram post failed, but cross-posted successfully: {p.get('topic', '')}")
            if ig_err:
                short_err = ig_err.strip().splitlines()[-1][:200]
                status_lines.append(f"IG issue: {short_err}")
        if yt:
            status_lines.append(yt)
        notify.text("\n".join(status_lines))
        return "posted"

    # 5. All destinations failed: retry or archive
    p["attempts"] = p.get("attempts", 0) + 1
    p["status"] = "queued"
    p.pop("claim", None)

    if p["attempts"] < MAX_ATTEMPTS:
        storage.put_json("pending.json", p)
        err_msg = ig_err or "All posting destinations failed."
        notify.text(f"❌ Posting failed ({p['attempts']}/{MAX_ATTEMPTS}):\n{err_msg[-600:]}\nWill retry automatically on next run.")
        raise RuntimeError(f"Posting failed (attempt {p['attempts']}): {err_msg.strip().splitlines()[-1]}")
    else:
        storage.put_json(f"failed_{p.get('slot')}.json", p)
        storage.delete("pending.json")
        notify.text(f"❌ Giving up on reel {p.get('slot')} after {MAX_ATTEMPTS} failed attempts.\nArchived to avoid blocking the queue.")
        log(f"Archived stuck reel to failed_{p.get('slot')}.json to unblock queue.")
        return "gave_up"


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
