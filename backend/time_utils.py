from datetime import datetime, time, timedelta


def get_local_day_range_ms(now=None):
    """
    Return the current local calendar day as (date, start_ms, end_ms).

    The returned range is [start, end), so records at exactly midnight
    belong to the new day and are never counted twice.
    """

    if now is None:
        now = datetime.now().astimezone()
    elif now.tzinfo is None:
        now = now.astimezone()

    day = now.date()

    start = datetime.combine(
        day,
        time.min,
        tzinfo=now.tzinfo
    )

    end = datetime.combine(
        day + timedelta(days=1),
        time.min,
        tzinfo=now.tzinfo
    )

    return (
        day.isoformat(),
        int(start.timestamp() * 1000),
        int(end.timestamp() * 1000)
    )
