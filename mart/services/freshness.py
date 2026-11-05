"""Overview freshness (M2, Martin 04.11.2026; QUESTIONS E1–E3).

How long a renewal's overview has been quiet, from the date written on its
newest entry (the `DD MMM YYYY:` header), across the WHOLE overview: the
client-ready one and the full one alike ("client ready" is a toggle that is
sometimes forgotten). Two steps, both in Settings → Time limits:

* ``fresh`` — newest entry younger than the amber limit (7 days)
* ``amber`` — at least the amber limit, under the red one (14 days)
* ``red``   — at least the red limit
* ``none``  — no dated entry at all

An entry is **new** when it is dated within the last ``overview_new_days``.
A broker deadline that is still ahead **pauses** the clock (``paused``,
M2 day 3): no amber or red until its date has passed.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from mart.ingestion import overview as ov
from mart.services import preferences

RANK = {"none": 0, "fresh": 1, "paused": 1, "amber": 2, "red": 3}
LABEL = {"none": "no overview entry yet", "fresh": "recent", "amber": "getting old", "red": "stale",
         "paused": "waiting for the promised update"}


def limits(today: date | None = None) -> dict[str, Any]:
    """The three limits, read once per page; red never below amber."""
    today = today or date.today()
    amber = preferences.get("overview_amber_days")
    red = max(preferences.get("overview_red_days"), amber)
    new = preferences.get("overview_new_days")
    return {"today": today, "amber": amber, "red": red, "new_days": new,
            "new_since": (today - timedelta(days=new)).isoformat() if new else None}


def latest(fields: dict[str, Any]) -> str | None:
    """Date of the newest entry in either overview text."""
    return ov.latest_date(fields.get("overview_all"), fields.get("overview_client_ready"))


def of(latest_iso: str | None, lim: dict[str, Any]) -> dict[str, Any]:
    """{state, age_days, latest, label} for one renewal."""
    if not latest_iso:
        return {"state": "none", "age_days": None, "latest": None, "label": LABEL["none"]}
    age = (lim["today"] - datetime.fromisoformat(latest_iso).date()).days
    state = "red" if age >= lim["red"] else "amber" if age >= lim["amber"] else "fresh"
    return {"state": state, "age_days": age, "latest": latest_iso, "label": LABEL[state]}


def worst(items: list[dict[str, Any]]) -> dict[str, Any]:
    """A bundle's freshness: its quietest renewal (red > amber > fresh > none)."""
    if not items:
        return {"state": "none", "age_days": None, "latest": None, "label": LABEL["none"]}
    return max(items, key=lambda f: (RANK[f["state"]], f["age_days"] or 0))


def pause(f: dict[str, Any], deadline: dict[str, Any] | None) -> dict[str, Any]:
    """Amber / red is paused while the bundle's broker deadline is ahead."""
    if deadline and deadline["state"] == "ahead" and f["state"] in ("amber", "red"):
        return {**f, "state": "paused", "label": LABEL["paused"]}
    return f
