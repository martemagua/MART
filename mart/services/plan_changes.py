"""Plan design changes (M3 day 4; Martin 05.11.2026, QUESTIONS D1): an
overview of the suggested plan design changes per renewal and whether they
were implemented, for the renewal itself and for the yearly stewardship
meeting.

* A change = what changes (a title, an optional detail) and where it stands:
  **suggested → agreed → implemented**, or **dropped**, each state with the
  date it was reached (default today). The dates of earlier states stay.
* **BM+ suggests**: the Renewal Strategy sheet's "Types of plan design
  changes" (with its reasons), else the Overview's "Plan Design Comments"
  when changes are considered. Shown as a suggestion until Martin takes it
  over (it becomes a change, `source = 'bm'`) or dismisses it (stored as a
  dropped one, so it is not offered again). BM+ is never changed.
* Several renewals at once from the bundle's edit mode (`add_many`).
* A client-wide overview lists every change by state.
* USER data: an upload never touches it.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from mart.ingestion.sheet import lookup, norm
from mart.ingestion.specs import renewal_tracker as rspec
from mart.repository import clients_repo, plan_changes_repo, renewals_repo
from mart.repository.db import connection

STATUSES = {"suggested": "Suggested", "agreed": "Agreed", "implemented": "Implemented", "dropped": "Dropped"}
TITLE_MAX = 200
DETAIL_MAX = 1_000
_YES = {"yes", "y", "true", "1"}
_TYPES = next(h for label, h, _s in rspec.STRATEGY_FIELDS if label == "Types of plan design changes")
_REASONS = next(h for label, h, _s in rspec.STRATEGY_FIELDS if label == "Reasons for plan design changes")
_CONSIDERED = next(h for label, h, _s in rspec.STRATEGY_FIELDS if label == "Plan design changes considered?")


class Invalid(ValueError):
    """Shown to the user as is."""


# -- reading (pure) ----------------------------------------------------------------------
def _text(value: Any) -> str | None:
    text = str(value or "").strip()
    return None if norm(text) in ("", "n a", "na", "none", "no", "tbc", "-") else text


def bm_suggestion(fields: dict[str, Any] | None, details: dict[str, Any] | None) -> dict[str, str] | None:
    """What BM+ says about plan design changes for this renewal, if anything:
    the Strategy sheet's types (+ reasons), else the Overview's comments when
    changes are considered."""
    for row in (details or {}).get("strategy") or []:
        if not isinstance(row, dict):
            continue
        types = _text(lookup(row, _TYPES))
        if types:
            return {"title": types[:TITLE_MAX], "detail": _text(lookup(row, _REASONS)) or ""}
        if norm(lookup(row, _CONSIDERED)) in _YES:
            break
    f = fields or {}
    if norm(f.get("pdc_considered")) in _YES:
        comments = _text(f.get("pdc_comments"))
        if comments:
            return {"title": comments[:TITLE_MAX], "detail": ""}
    return None


def view(rows: list[dict[str, Any]], bm: dict[str, str] | None = None) -> dict[str, Any]:
    """The renewal's changes (open ones first) with each one's current date,
    the counts by state, and BM+'s suggestion unless already taken over or
    dismissed (a change with source 'bm')."""
    order = {"suggested": 0, "agreed": 1, "implemented": 2, "dropped": 3}
    items = sorted(({**c, "status_label": STATUSES[c["status"]],
                     "since": c.get(plan_changes_repo.DATE_OF[c["status"]])} for c in rows),
                   key=lambda c: (order[c["status"]], c["id"]))
    counts = {s: sum(1 for c in rows if c["status"] == s) for s in STATUSES}
    taken = any(c["source"] == "bm" for c in rows)
    return {"items": items, "count": len(rows), "counts": counts,
            "live": len(rows) - counts["dropped"],
            "bm": bm if bm and not taken else None}


# -- writing -----------------------------------------------------------------------------
def _clean(title: str | None, detail: str | None, status: str | None, on: str | None) -> tuple:
    title = (title or "").strip()
    if not title:
        raise Invalid("What is the plan design change?")
    if len(title) > TITLE_MAX:
        raise Invalid(f"Keep the change short (at most {TITLE_MAX} characters); the detail can say more.")
    detail = (detail or "").strip() or None
    if detail and len(detail) > DETAIL_MAX:
        raise Invalid(f"The detail is too long (at most {DETAIL_MAX} characters).")
    status = (status or "suggested").strip()
    if status not in STATUSES:
        raise Invalid("Pick suggested, agreed, implemented or dropped.")
    return title, detail, status, _date(on)


def _date(on: str | None) -> str:
    try:
        return date.fromisoformat((on or "").strip() or date.today().isoformat()).isoformat()
    except ValueError as exc:
        raise Invalid("That date isn't valid.") from exc


def _renewal_of_mine(conn, client_id: int, renewal_id: int) -> dict[str, Any]:
    client = clients_repo.get(conn, client_id)
    r = renewals_repo.get(conn, renewal_id)
    if client is None or client["is_mine"] != 1 or r is None or r["client_id"] != client_id:
        raise Invalid("This renewal doesn't exist (or isn't one of your clients').")
    return r


def _change_of_mine(conn, client_id: int, change_id: int) -> dict[str, Any]:
    c = plan_changes_repo.get(conn, change_id)
    if c is None:
        raise Invalid("This plan design change doesn't exist any more.")
    _renewal_of_mine(conn, client_id, c["renewal_id"])
    return c


def add(client_id: int, renewal_id: int, title: str | None, detail: str | None = None,
        status: str | None = None, on: str | None = None) -> int:
    return add_many(client_id, [renewal_id], title, detail, status, on)[0]


def add_many(client_id: int, renewal_ids: list[int], title: str | None, detail: str | None = None,
             status: str | None = None, on: str | None = None) -> list[int]:
    """The same change on several renewals (the bundle's edit mode); all or nothing."""
    if not renewal_ids:
        raise Invalid("Tick at least one renewal first.")
    title, detail, status, on = _clean(title, detail, status, on)
    with connection() as conn:
        for rid in renewal_ids:
            _renewal_of_mine(conn, client_id, rid)
        return [plan_changes_repo.add(conn, rid, title, detail, status, on) for rid in renewal_ids]


def take_bm(client_id: int, renewal_id: int, keep: bool = True) -> int | None:
    """Take BM+'s suggestion over as a suggested change (keep), or dismiss it
    (stored as dropped, so it is not offered again)."""
    with connection() as conn:
        r = _renewal_of_mine(conn, client_id, renewal_id)
        bm = bm_suggestion(r["fields"], r["details"])
        if bm is None or any(c["source"] == "bm" for c in plan_changes_repo.for_renewal(conn, renewal_id)):
            return None
        today = date.today().isoformat()
        return plan_changes_repo.add(conn, renewal_id, bm["title"], bm["detail"] or None,
                                     "suggested" if keep else "dropped", today, source="bm")


def edit(client_id: int, change_id: int, title: str | None, detail: str | None) -> None:
    title, detail, _s, _d = _clean(title, detail, None, None)
    with connection() as conn:
        _change_of_mine(conn, client_id, change_id)
        plan_changes_repo.update(conn, change_id, title, detail)


def set_status(client_id: int, change_id: int, status: str | None, on: str | None = None) -> None:
    status = (status or "").strip()
    if status not in STATUSES:
        raise Invalid("Pick suggested, agreed, implemented or dropped.")
    on = _date(on)
    with connection() as conn:
        _change_of_mine(conn, client_id, change_id)
        plan_changes_repo.set_status(conn, change_id, status, on)


def delete(client_id: int, change_id: int) -> None:
    with connection() as conn:
        _change_of_mine(conn, client_id, change_id)
        plan_changes_repo.delete(conn, change_id)


# -- the client-wide overview ---------------------------------------------------------
def client_overview(client_id: int, status: str | None = None) -> dict[str, Any]:
    """Every plan design change of a client, with its renewal, newest state
    date first; `status` filters (None = all)."""
    with connection() as conn:
        client = clients_repo.get(conn, client_id)
        if client is None or client["is_mine"] != 1:
            raise Invalid("This client is not one of yours (or doesn't exist).")
        by_renewal = plan_changes_repo.for_client(conn, client_id)
        renewals = {r["id"]: r for r in renewals_repo.for_client(conn, client_id)}
    rows = []
    for rid, changes in by_renewal.items():
        r = renewals.get(rid)
        if r is None:
            continue
        for c in view(changes)["items"]:
            rows.append({**c, "renewal": r})
    counts = {s: sum(1 for c in rows if c["status"] == s) for s in STATUSES}
    if status in STATUSES:
        rows = [c for c in rows if c["status"] == status]
    rows.sort(key=lambda c: (c["renewal"].get("renewal_date") or "9999", c["renewal"].get("country") or "",
                             c["renewal"].get("policy_name") or "", c["id"]))
    return {"items": rows, "counts": counts, "total": sum(counts.values()), "status": status}
