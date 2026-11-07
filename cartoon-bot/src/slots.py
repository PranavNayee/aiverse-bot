"""Posting-slot maths. Slots are the daily posting times (default 08:00 and 19:00, Asia/Kolkata).
Every slot has a unique key, which makes the bot idempotent: one reel per slot, ever.
Key of the FIRST daily slot is the plain date ("2026-11-08"), later slots add the time ("2026-11-08-1900")."""
import datetime as dt
import config as C

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo(C.TIMEZONE)
except Exception:                                   # no tz database: assume IST
    TZ = dt.timezone(dt.timedelta(hours=5, minutes=30))


def now():
    return dt.datetime.now(TZ)


def times():
    out = []
    for t in C.POST_TIMES:
        h, m = (int(x) for x in t.split(":"))
        out.append(dt.time(h, m))
    return sorted(out)


def slot_on(day, idx=0):
    """The posting datetime (tz-aware) of slot number `idx` on local date `day`."""
    return dt.datetime.combine(day, times()[idx], tzinfo=TZ)


def index(slot):
    t = slot.timetz().replace(tzinfo=None)
    ts = times()
    return ts.index(t) if t in ts else 0


def key(slot):
    i = index(slot)
    return slot.date().isoformat() if i == 0 else f"{slot.date().isoformat()}-{slot.strftime('%H%M')}"


def _all_around(at):
    out = []
    for d in (-1, 0, 1, 2):
        day = at.date() + dt.timedelta(days=d)
        out += [slot_on(day, i) for i in range(len(times()))]
    return sorted(out)


def grace_for(slot):
    """How late a reel may still go out in this slot (never runs into the next slot)."""
    ss = _all_around(slot)
    nxt = next((s for s in ss if s > slot), slot + dt.timedelta(days=1))
    gap = (nxt - slot).total_seconds() / 60
    return max(30, min(C.LATE_GRACE_MINUTES, gap - 60))


def upcoming_slot(at=None, done=(), grace_minutes=None):
    """The next slot a reel made NOW should go out in, skipping slots whose key is in `done`.
    A slot that passed less than its grace period ago still counts (a late reel beats no reel)."""
    at = at or now()
    for s in _all_around(at):
        g = grace_minutes if grace_minutes is not None else grace_for(s)
        if s + dt.timedelta(minutes=g) >= at and key(s) not in done:
            return s
    return slot_on(at.date() + dt.timedelta(days=2))


def is_weekend(slot):
    return slot.weekday() in (5, 6)                 # Saturday / Sunday of the POSTING day


def fmt(ts_or_dt):
    d = ts_or_dt if isinstance(ts_or_dt, dt.datetime) else dt.datetime.fromtimestamp(ts_or_dt, TZ)
    return d.astimezone(TZ).strftime("%a %d %b, %I:%M %p")
