"""Money and time helpers shared by services.

All money is integer paise. Timestamps are UTC ISO 8601. Calendar-month
filtering uses the configured reporting timezone.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def reporting_tz() -> ZoneInfo:
    return ZoneInfo(get_settings().reporting_timezone)


def month_bounds(month: str | None = None) -> tuple[str, str, str]:
    """Return inclusive start, exclusive end (UTC ISO) and the month label.

    The bounds are computed in the reporting timezone then expressed as UTC so
    that a single stored occurred_at column (UTC) can be filtered correctly.
    """
    tz = reporting_tz()
    now = datetime.now(tz)
    if month:
        year, mon = month.split("-")
        start_local = datetime(int(year), int(mon), 1, tzinfo=tz)
    else:
        start_local = datetime(now.year, now.month, 1, tzinfo=tz)
    # Next month start.
    if start_local.month == 12:
        end_local = datetime(start_local.year + 1, 1, 1, tzinfo=tz)
    else:
        end_local = datetime(start_local.year, start_local.month + 1, 1, tzinfo=tz)
    start_utc = start_local.astimezone(timezone.utc).isoformat()
    end_utc = end_local.astimezone(timezone.utc).isoformat()
    label = f"{start_local.year:04d}-{start_local.month:02d}"
    return start_utc, end_utc, label


def format_inr(paise: int) -> str:
    rupees = paise / 100
    return f"₹{rupees:,.2f}"
