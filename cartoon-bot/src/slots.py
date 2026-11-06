"""Posting-slot maths. A 'slot' is one daily posting time (default 08:00 Asia/Kolkata).
Everything is keyed by the slot's local date, which makes the bot idempotent: one reel per slot, ever."""
import datetime as dt
import config as C

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo(C.TIMEZONE)
except Exception:                                   # no tz database: assume IST
    TZ = dt.timezone(dt.timedelta(hours=5, minutes=30))


def now():
    return dt.datetime.now(TZ)


def _post_time():
    h, m = (int(x) for x in C.POST_TIME.split(":"))
    return dt.time(h, m)


def slot_on(day):
    """The posting datetime (tz-aware) on local date `day`."""
    return dt.datetime.combine(day, _post_time(), tzinfo=TZ)


def upcoming_slot(at=None, grace_minutes=None):
    """The slot a reel generated NOW should go out in.
    If today's slot passed less than `grace_minutes` ago we still target today (a late reel beats no reel)."""
    at = at or now()
    grace = C.LATE_GRACE_MINUTES if grace_minutes is None else grace_minutes
    today = slot_on(at.date())
    if at <= today + dt.timedelta(minutes=grace):
        return today
    return slot_on(at.date() + dt.timedelta(days=1))


def key(slot):
    return slot.date().isoformat()


def is_weekend(slot):
    return slot.weekday() in (5, 6)                 # Saturday / Sunday of the POSTING day


def fmt(ts_or_dt):
    d = ts_or_dt if isinstance(ts_or_dt, dt.datetime) else dt.datetime.fromtimestamp(ts_or_dt, TZ)
    return d.astimezone(TZ).strftime("%a %d %b, %I:%M %p")
