"""Broker deadlines on bundles (M2 day 3; Martin 04.11.2026, QUESTIONS
M2b, E4, K4): the date Martin expects an update on a bundle's renewals.

* One **open** deadline per bundle; setting a new one replaces it.
* **BM+ prefill**: without an open deadline of his, a bundle gets the
  earliest "Expected date to receive the final renewal terms" of its
  renewals, unless a deadline he already closed was as late or later. It is
  only stored once he acts on it (confirm / drop / change).
* **State** by today: ``ahead`` (today or later) pauses the stale clock of
  the bundle's renewals; ``passed`` stays red until he confirms it.
* **Confirmed by Martin only** (E4); MART points out an overview entry dated
  on or after the day a stored deadline was set.
* It hangs on the bundle key, like bundle notes: a renewal moved elsewhere
  follows its new bundle's deadline.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from mart.ingestion.sheet import lookup
from mart.ingestion.specs import renewal_tracker as rspec
from mart.repository import bundles_repo, clients_repo, deadlines_repo
from mart.repository.db import connection
from mart.services import bundles as bx

PROMISED_MAX = 120
NOTE_MAX = 1_000


class Invalid(ValueError):
    """Shown to the user as is."""


# -- reading ----------------------------------------------------------------------------
def bm_date(details: dict[str, Any] | None) -> str | None:
    """BM+'s expected-terms date of one renewal (Renewal Strategy sheet)."""
    for row in (details or {}).get("strategy") or []:
        value = lookup(row, rspec.EXPECTED_TERMS) if isinstance(row, dict) else None
        text = str(value or "").strip()[:10]
        try:
            return date.fromisoformat(text).isoformat()
        except ValueError:
            continue
    return None


def _state(expected: str, today: date) -> dict[str, Any]:
    days = (date.fromisoformat(expected) - today).days
    return {"days": days, "state": "ahead" if days >= 0 else "passed"}


def effective(rows: list[dict[str, Any]], bm: list[tuple[str, str]], today: date,
              newest_entry: str | None = None) -> dict[str, Any] | None:
    """A bundle's current deadline. `rows` = its stored deadlines (newest
    first), `bm` = (policy name, BM+ date) of its renewals, `newest_entry` =
    the newest overview entry date among them."""
    open_row = next((r for r in rows if r["status"] == "open"), None)
    closed = [r["expected_date"] for r in rows if r["status"] in ("confirmed", "dropped")]
    bm_first = min((d for _, d in bm), default=None)
    if open_row:
        d = {**open_row}
    elif bm_first and (not closed or bm_first > max(closed)):
        d = {"id": None, "expected_date": bm_first, "promised_by": None, "note": None, "source": "bm",
             "status": "open", "created_at": None}
    else:
        return None
    since = (d["created_at"] or "")[:10]
    d.update(_state(d["expected_date"], today),
             bm_date=bm_first, bm_dates=sorted(bm, key=lambda x: x[1]),
             bm_differs=bool(open_row and bm_first and bm_first != d["expected_date"]),
             new_entry=newest_entry if since and newest_entry and newest_entry >= since else None)
    return d


def for_bundles(client_id: int, bundles: dict[str, dict[str, Any]], bm_of: dict[int, str | None],
                newest_of: dict[int, str | None], today: date) -> dict[str, dict[str, Any]]:
    """bundle key -> {"current": its deadline or None, "history": the closed
    ones, newest first}, for one client's explorer."""
    with connection() as conn:
        rows = deadlines_repo.for_client(conn, client_id)
    by_key: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_key.setdefault(r["bundle_key"], []).append(r)
    out = {}
    for key, b in bundles.items():
        bm = [(r["policy_name"] or "—", bm_of[r["id"]]) for r in b["renewals"] if bm_of.get(r["id"])]
        newest = max((newest_of[r["id"]] for r in b["renewals"] if newest_of.get(r["id"])), default=None)
        mine = by_key.get(key, [])
        out[key] = {"current": effective(mine, bm, today, newest),
                    "history": [r for r in mine if r["status"] != "open"]}
    return out


# -- writing ----------------------------------------------------------------------------
def _check(conn, client_id: int, key: str) -> None:
    client = clients_repo.get(conn, client_id)
    if not client or client["is_mine"] != 1:
        raise Invalid("This client is not one of yours.")
    custom = bx.custom_id(key)
    if custom is not None and custom not in bundles_repo.custom_bundles(conn, client_id):
        raise Invalid("This bundle doesn't exist.")
    if custom is None and not bx.is_default_key(key):
        raise Invalid("This bundle doesn't exist.")


def _date(value: str | None) -> str:
    try:
        return date.fromisoformat((value or "").strip()).isoformat()
    except ValueError as exc:
        raise Invalid("The expected date isn't a date.") from exc


def _text(value: str | None, limit: int, what: str) -> str | None:
    text = " ".join((value or "").split()) or None
    if text and len(text) > limit:
        raise Invalid(f"{what} can have at most {limit} characters.")
    return text


def set_deadline(client_id: int, key: str, expected: str | None, promised_by: str | None = None,
                 note: str | None = None) -> int:
    """Set (or change) the bundle's expected update date; the open one, if
    any, is kept in the history as replaced."""
    with connection() as conn:
        _check(conn, client_id, key)
        d, who, text = _date(expected), _text(promised_by, PROMISED_MAX, "'Promised by'"), \
            _text(note, NOTE_MAX, "A note")
        current = deadlines_repo.open_one(conn, client_id, key)
        if current:
            deadlines_repo.close(conn, current["id"], "replaced")
        return deadlines_repo.add(conn, client_id, key, d, who, text, "you")


def close(client_id: int, key: str, outcome: str, shown_date: str | None) -> None:
    """Confirm the update arrived, or drop the deadline. A BM+ suggestion
    (not stored yet) is stored closed with the date that was shown."""
    if outcome not in ("confirmed", "dropped"):
        raise Invalid("Unknown action.")
    with connection() as conn:
        _check(conn, client_id, key)
        current = deadlines_repo.open_one(conn, client_id, key)
        if current:
            deadlines_repo.close(conn, current["id"], outcome)
        else:
            deadlines_repo.add(conn, client_id, key, _date(shown_date), None, None, "bm", outcome)
