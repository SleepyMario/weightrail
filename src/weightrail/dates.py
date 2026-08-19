from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo


TAIPEI = ZoneInfo("Asia/Taipei")


def taipei_today() -> date:
    return taipei_date_from_datetime(datetime.now(timezone.utc))


def taipei_date_from_datetime(value: datetime) -> date:
    return value.astimezone(TAIPEI).date()
