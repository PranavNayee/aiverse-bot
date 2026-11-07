"""Growth engine (runs every few hours from engage.yml):
  * stats   - pulls each reel's insights (views, reach, likes, comments, shares, saves, watch time) -> stats.json
  * learn   - the best hooks are fed back into the script writer (lesson_script.WINNERS)
  * replies - answers genuine viewer comments in the channel's language (engagement boosts reach)
  * report  - weekly Telegram report: totals, best/worst reel, follower growth, what to do next
Needs the token permissions instagram_manage_insights (stats) and instagram_manage_comments (replies);
anything missing is skipped with a clear Telegram note instead of crashing."""
import datetime as dt, os, re, sys, time, requests
import config as C, storage, notify, slots, llm
from instagram import GRAPH, _check
from util import log

MAX_REPLIES = int(os.environ.get("MAX_REPLIES_PER_RUN", "12"))
METRICS = ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions", "ig_reels_avg_watch_time"]
FALLBACK_METRICS = ["reach", "likes", "comments", "shares", "saved"]


def _get(path, **params):
    params["access_token"] = C.IG_ACCESS_TOKEN()
    return _check(requests.get(f"{GRAPH}/{path}", params=params, timeout=60))


def media_insights(mid):
    for metrics in (METRICS, FALLBACK_METRICS):
        try:
            j = _get(f"{mid}/insights", metric=",".join(metrics))
            return {d["name"]: (d.get("values") or [{}])[0].get("value", 0) for d in j.get("data", [])}
        except RuntimeError as e:
            last = e
    raise last


def score(s):
    """Reach-weighted engagement: shares/saves are what the algorithm rewards most."""
    return (s.get("shares", 0) * 4 + s.get("saved", 0) * 3 + s.get("comments", 0) * 2 + s.get("likes", 0)
            + s.get("views", s.get("reach", 0)) / 50)


def refresh_stats(limit=25):
    history = storage.get_json("history.json", [])
    stats = storage.get_json("stats.json", {})
    posted = [h for h in history if str(h.get("media_id", "")).isdigit()][-limit:]
    ok, err = 0, None
    for h in posted:
        mid = str(h["media_id"])
        try:
            m = media_insights(mid)
        except RuntimeError as e:
            err = str(e); continue
        stats[mid] = {**stats.get(mid, {}), **m, "topic": h.get("topic"), "hook": h.get("hook", ""),
                      "type": h.get("type"), "posted_ts": h.get("posted_ts"), "updated": int(time.time())}
        ok += 1
    if ok:
        storage.put_json("stats.json", stats)
    log(f"Stats refreshed for {ok}/{len(posted)} reels" + (f" (last error: {err[:150]})" if err else ""))
    return stats, (err if not ok and posted else None)


def winners(n=3):
    """Text for the script writer: the best hooks so far (needs >= 4 reels with stats)."""
    try:
        stats = storage.get_json("stats.json", {})
    except Exception:
        return ""
    rows = [s for s in stats.values() if s.get("hook")]
    if len(rows) < 4:
        return ""
    best = sorted(rows, key=score, reverse=True)[:n]
    return " | ".join(f'"{s["hook"]}" ({s.get("views", s.get("reach", 0))} views, {s.get("shares", 0)} shares)'
                      for s in best)


# ---------------------------------------------------------------- comment replies
REPLY_PROMPT = """You manage the Instagram channel "{name}", which teaches AI/ML in short animated reels ({lang}).
Reel topic: {topic}
A viewer (@{user}) commented: "{text}"

Decide if the channel should reply. Reply to genuine questions, doubts, thanks, compliments and topic requests.
Do NOT reply to spam, links, self-promotion, hate, abuse, politics, religion, or anything you are unsure about.
If you reply: max 2 short sentences, warm and human, in the SAME language/style as the comment
(Hinglish in Roman script if they wrote Hinglish), accurate, no links, no promises, at most 1 emoji.
If they asked something the reel did not cover, give a one-line answer and say a future lesson may cover it.
Return ONLY JSON: {{"reply": true|false, "text": "..."}}"""


INTROS = ["@{user} Ye lo 👇", "@{user} Here you go 🙌", "@{user} Aapke liye 👇", "@{user} Done! 👇", "@{user} Lo ji 🔖"]
_LAST_ERR = None


def _reply(cid, message):
    global _LAST_ERR
    try:
        _check(requests.post(f"{GRAPH}/{cid}/replies", data={"message": message, "access_token": C.IG_ACCESS_TOKEN()},
                             timeout=60))
        _LAST_ERR = None
        return True
    except RuntimeError as e:
        _LAST_ERR = str(e)
        log("Reply failed:", _LAST_ERR[:150])
        return False


def reply_comments(days=14):
    eng = storage.get_json("engage.json", {})
    done = set(eng.get("replied", []))
    me = (eng.get("username") or "").lower()
    if not me:
        me = str(_get(C.IG_USER_ID(), fields="username").get("username", "")).lower()
        eng["username"] = me
    history = storage.get_json("history.json", [])
    cutoff = time.time() - days * 86400
    recent = [h for h in history if str(h.get("media_id", "")).isdigit() and (h.get("posted_ts") or 0) >= cutoff][-10:]
    lang = "English" if C.LANGUAGE_MODE == "english_only" else "Hinglish"
    sent, err = 0, None
    for h in reversed(recent):
        try:
            cs = _get(f"{h['media_id']}/comments", fields="id,text,username,timestamp,replies{username}", limit=50)
        except RuntimeError as e:
            err = str(e); break
        for c in cs.get("data", []):
            if sent >= MAX_REPLIES:
                break
            cid, user, text = c["id"], (c.get("username") or "").lower(), (c.get("text") or "").strip()
            if cid in done or not text or user == me:
                continue
            if any((r.get("username") or "").lower() == me for r in (c.get("replies") or {}).get("data", [])):
                done.add(cid); continue
            done.add(cid)
            kw, freebie = (h.get("keyword") or "").strip(), (h.get("freebie") or "").strip()
            if kw and freebie and re.search(rf"\b{re.escape(kw)}\b", text, re.I):
                intro = INTROS[sum(map(ord, user)) % len(INTROS)].format(user=user)
                if _reply(cid, f"{intro}\n\n{freebie}"[:2000]):
                    sent += 1; log(f"  sent {kw} freebie to @{user}"); time.sleep(4)
                continue
            if re.search(r"https?://|www\.", text) or len(text) > 600:
                continue
            try:
                d = llm.generate_json(REPLY_PROMPT.format(name=C.SERIES_NAME, lang=lang, topic=h.get("topic", ""),
                                                          user=user, text=text[:500]), temperature=0.5)
            except Exception as e:
                log("Reply writer failed:", e); continue
            reply = re.sub(r"https?://\S+", "", str(d.get("text", ""))).strip()[:300]
            if not d.get("reply") or not reply:
                continue
            if _reply(cid, reply):
                sent += 1
                log(f"  replied to @{user}: {reply[:80]}")
                time.sleep(4)                                   # be gentle - look human, avoid spam limits
            elif _LAST_ERR:
                err = _LAST_ERR; break
    eng["replied"] = list(done)[-3000:]
    storage.put_json("engage.json", eng)
    log(f"Replied to {sent} comments")
    return sent, err


# ---------------------------------------------------------------- weekly report
def weekly_report(stats):
    week_ago = time.time() - 7 * 86400
    rows = [s for s in stats.values() if (s.get("posted_ts") or 0) >= week_ago]
    try:
        followers = _get(C.IG_USER_ID(), fields="followers_count").get("followers_count")
    except Exception:
        followers = None
    eng = storage.get_json("engage.json", {})
    prev = eng.get("followers_last_week")
    eng["followers_last_week"] = followers
    storage.put_json("engage.json", eng)
    if not rows:
        return notify.text("📊 Weekly report: no reel stats this week yet (insights permission may be missing).")
    tot = lambda k: sum(int(s.get(k, 0) or 0) for s in rows)
    best = max(rows, key=score); worst = min(rows, key=score)
    views = tot("views") or tot("reach")
    growth = f" ({followers - prev:+d} this week)" if isinstance(prev, int) and isinstance(followers, int) else ""
    tips = []
    if views and tot("shares") / max(views, 1) < 0.005:
        tips.append("Shares are low: the bot now asks viewers to send reels to a friend - keep hooks punchy.")
    if best.get("type") == "fun_fact" and worst.get("type") == "lesson":
        tips.append("Fun facts beat lessons this week - consider more surprising hooks in lessons.")
    msg = (f"📊 Weekly report ({len(rows)} reels)\n"
           f"👀 Views: {views:,}  ❤️ Likes: {tot('likes'):,}  💬 Comments: {tot('comments'):,}\n"
           f"🔁 Shares: {tot('shares'):,}  🔖 Saves: {tot('saved'):,}\n"
           f"👥 Followers: {followers if followers is not None else '?'}{growth}\n\n"
           f"🏆 Best: {best.get('topic')} - {best.get('views', best.get('reach', 0))} views, {best.get('shares', 0)} shares\n"
           f"🐢 Weakest: {worst.get('topic')} - {worst.get('views', worst.get('reach', 0))} views\n"
           f"🧠 The script writer now learns from your best hooks automatically.")
    if tips:
        msg += "\n\n💡 " + "\n💡 ".join(tips)
    notify.text(msg)


def main():
    notes = []
    stats, err = refresh_stats()
    if err:
        notes.append(f"Reel stats unavailable: {err[:200]}\n→ Give the token the 'instagram_manage_insights' permission.")
    if os.environ.get("AUTO_REPLY", "true").lower() == "true":
        try:
            _, err = reply_comments()
            if err:
                notes.append(f"Comment replies unavailable: {err[:200]}\n→ Give the token the 'instagram_manage_comments' permission.")
        except Exception as e:
            notes.append(f"Comment replies failed: {str(e)[:200]}")
    # weekly report once per ISO week, on Sunday evening (local time)
    now = slots.now()
    eng = storage.get_json("engage.json", {})
    week = now.strftime("%G-W%V")
    if (now.weekday() == 6 and now.hour >= 18 or os.environ.get("FORCE_REPORT") == "true") and eng.get("report_week") != week:
        weekly_report(stats)
        eng = storage.get_json("engage.json", {}); eng["report_week"] = week; storage.put_json("engage.json", eng)
    if notes:
        eng = storage.get_json("engage.json", {})
        key = now.strftime("%Y-%m-%d")
        if eng.get("notes_day") != key:              # at most one warning per day
            notify.text("⚠️ Growth engine:\n\n" + "\n\n".join(notes))
            eng["notes_day"] = key; storage.put_json("engage.json", eng)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback; traceback.print_exc()
        sys.exit(1)
