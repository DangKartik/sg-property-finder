"""Time-zone and commute-window helpers."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

SGT = timezone(timedelta(hours=8), name="Asia/Singapore")
CBD_LATITUDE = 1.2830
CBD_LONGITUDE = 103.8513
MORNING_PEAK = time(hour=8, minute=30)


def nextWeekdayPeak(now: datetime | None = None) -> datetime:
    """Return the next weekday 08:30 SGT.

    If `now` is a weekday before 08:30, today's peak is returned; otherwise the
    next weekday is used. Naive datetimes are interpreted as SGT.
    """
    if now is None:
        now = datetime.now(SGT)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=SGT)
    else:
        now = now.astimezone(SGT)

    candidate = now.replace(hour=MORNING_PEAK.hour, minute=MORNING_PEAK.minute, second=0, microsecond=0)
    if now >= candidate or candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate
