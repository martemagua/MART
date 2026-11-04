"""Turning raw BM+ cell values into clean values.

Two BM+ habits shape this module:

* **Dates carry a stray time.** BM+ stores midnight UTC and the export shows
  it in the local time of the policy's country: 01:00 (Europe), 05:30
  (India), 08:00 (Asia) — or 19:00 / 18:30 on the *previous* evening for the
  Americas. So a date is rounded to the NEAREST midnight: before noon → that
  day, from noon → the next day.
* **Empty is not zero.** Blank cells become None. Placeholders such as
  "TBC" are kept as text: in a strategy column "TBC" *is* the answer BM+ has.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any

NON_EXPIRING = "non expiring policy"


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).replace("\r\n", "\n").replace("_x000D_", "").replace("_x000d_", "").strip()
    return text or None


def nearest_midnight(dt: datetime) -> date:
    """The calendar day a BM+ date means (see module docstring).

    Only a "midnight UTC shown in local time" value (a whole or half hour, no
    seconds) is rounded. A real timestamp (the Task Tracker's "completed
    14:32:42.220") is an instant, and keeps its own date."""
    d = dt.date()
    if dt.second or dt.microsecond or dt.minute not in (0, 30):
        return d
    return d + timedelta(days=1) if dt.hour >= 12 else d


def to_date(value: Any) -> str | None:
    """ISO date (YYYY-MM-DD) or None. Text dates in ISO or DD.MM.YYYY form are
    accepted; anything else (e.g. "Non Expiring Policy") gives None."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return nearest_midnight(value).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d.%m.%Y", "%d %b %Y"):
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return nearest_midnight(parsed).isoformat()
    return None


def to_int(value: Any) -> int | None:
    """Whole number, or None. Accepts BM+'s "138 day(s)"; "N/A" gives None."""
    if value is None or value == "":
        return None
    m = re.match(r"\s*(-?\d+(?:\.\d+)?)", str(value))
    return int(float(m.group(1))) if m else None


def is_non_expiring(value: Any) -> bool:
    return isinstance(value, str) and value.strip().lower() == NON_EXPIRING


def person_name(value: Any) -> str | None:
    """BM+ sometimes writes a name twice ("Ann Lee Ann Lee"); keep it once."""
    text = clean_text(value)
    if not text:
        return None
    words = text.split()
    half = len(words) // 2
    if len(words) % 2 == 0 and half and words[:half] == words[half:]:
        return " ".join(words[:half])
    return text


def json_value(value: Any) -> Any:
    """A cell as it goes into the JSON copy of a row: dates as ISO dates,
    other datetimes as ISO timestamps, text cleaned, numbers unchanged."""
    if isinstance(value, datetime):
        if value.time().minute in (0, 30) and value.time().second == 0:
            return nearest_midnight(value).isoformat()
        return value.isoformat(timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)):
        return int(value) if isinstance(value, float) and value.is_integer() else value
    return clean_text(value)


_KEY_DROP = re.compile(r"[^a-z0-9]+")


def client_key(name: str) -> str:
    """Matching key for a client name: case, punctuation and spacing ignored,
    "&" read as "and"."""
    text = name.casefold().replace("&", " and ")
    return " ".join(_KEY_DROP.sub(" ", text).split())


def coverage_lines(lines_of_coverage: str | None) -> list[str]:
    """BM+'s Lines of Coverage cell -> its lines, in BM+'s order: split on
    commas, semicolons and line breaks, but never inside brackets
    ('Healthcare - Inpatient (Hospital, Surgical)' stays one line)."""
    out, depth, cur = [], 0, []
    for ch in lines_of_coverage or "":
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(depth - 1, 0)
        if ch in ",;\n" and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return [p.strip() for p in out if p.strip()]


def product_groups(lines_of_coverage: str | None) -> list[str]:
    """'Healthcare - Medical, Life - Basic Term Life' -> ['Healthcare', 'Life']."""
    groups: list[str] = []
    for part in coverage_lines(lines_of_coverage):
        group = part.split(" - ", 1)[0].strip()
        if group and group not in groups:
            groups.append(group)
    return groups
