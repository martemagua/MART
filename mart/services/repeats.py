"""Repeating to-dos (M3 day 8; Martin 05.11.2026, QUESTIONS M3b): the
standard options only — every N days, every N weeks (on chosen weekdays),
every N months. No working-day rule, no holiday calendar. Pure: no database.

Ticking a repeating to-do done creates the next one with the next date
(notes_service.set_done). The next date counts from the to-do's due date
(today when it has none), so a to-do ticked a day late keeps its rhythm;
one ticked so late that the next date has passed too moves on until it is
after today, so a repeat is never born overdue.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Any

from mart.services.todo_details import Invalid

UNITS = {"day": ("day", "days"), "week": ("week", "weeks"), "month": ("month", "months")}
MAX_EVERY = {"day": 365, "week": 52, "month": 24}
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def clean(unit: str | None, every: str | int | None, weekdays: list[str] | None,
          due: str | None, today: date | None = None) -> dict[str, Any] | None:
    """The repeat as the form sends it → what is stored, or None (doesn't
    repeat). `due` (ISO) anchors a monthly repeat's day of the month."""
    unit = (unit or "").strip()
    if not unit:
        return None
    if unit not in UNITS:
        raise Invalid("A to-do repeats every N days, weeks or months.")
    try:
        n = int(str(every).strip() or "1") if every is not None else 1     # blank = 1; 0 is refused below
    except ValueError as exc:
        raise Invalid("Repeat every how many? Write a whole number.") from exc
    if not 1 <= n <= MAX_EVERY[unit]:
        raise Invalid(f"Repeat every 1 to {MAX_EVERY[unit]} {UNITS[unit][1]}.")
    days = sorted({int(d) for d in weekdays or [] if str(d).strip().isdigit() and 0 <= int(d) <= 6})
    if weekdays and len(days) != len({str(d).strip() for d in weekdays if str(d).strip()}):
        raise Invalid("Pick the weekdays from the list.")
    anchor = date.fromisoformat(due) if due else (today or date.today())
    return {"repeat_unit": unit, "repeat_every": n,
            "repeat_weekdays": ",".join(map(str, days)) if unit == "week" and days else None,
            "repeat_day": anchor.day if unit == "month" else None}


def _add_months(d: date, n: int, day: int) -> date:
    y, m = divmod(d.month - 1 + n, 12)
    year, month = d.year + y, m + 1
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def _step(spec: dict[str, Any], d: date) -> date:
    n, unit = spec["repeat_every"], spec["repeat_unit"]
    if unit == "day":
        return d + timedelta(days=n)
    if unit == "month":
        return _add_months(d, n, spec.get("repeat_day") or d.day)
    days = [int(x) for x in (spec.get("repeat_weekdays") or "").split(",") if x != ""]
    if not days:
        return d + timedelta(weeks=n)
    later = [w for w in days if w > d.weekday()]               # still this week
    monday = d - timedelta(days=d.weekday())
    if later:
        return monday + timedelta(days=later[0])
    return monday + timedelta(weeks=n, days=days[0])


def next_due(spec: dict[str, Any], due: str | None, today: date | None = None) -> date:
    """The next one's due date: one step after `due` (or today), and after
    today however late the last one was ticked."""
    today = today or date.today()
    d = _step(spec, date.fromisoformat(due) if due else today)
    for _ in range(10_000):                                    # a far-overdue daily one is still finite
        if d > today:
            return d
        d = _step(spec, d)
    return d


def describe(spec: dict[str, Any] | None) -> str | None:
    """"every month", "every 2 weeks on Mon, Thu", "every 3 days"."""
    if not spec or not spec.get("repeat_unit"):
        return None
    n, unit = spec["repeat_every"] or 1, spec["repeat_unit"]
    one, many = UNITS[unit]
    text = f"every {one}" if n == 1 else f"every {n} {many}"
    days = [WEEKDAYS[int(x)] for x in (spec.get("repeat_weekdays") or "").split(",") if x != ""]
    if unit == "week" and days:
        text += " on " + ", ".join(days)
    return text
