"""The ACTUAL state of a renewal, kept beside BM+'s (M3 day 1; Martin
05.11.2026, QUESTIONS D1, D2, M3h; PLANNING §1d).

* **Strategy**: Martin's own, next to BM+'s Upcoming Renewal Strategy. Each
  time it is set, MART also stores BM+'s value at that moment, so it can tell:
  ``sync`` (the same; ``caught_up`` when BM+ only got there after Martin set
  it), ``behind`` (BM+ has not moved since: still blank or still the old
  value) or ``conflict`` (BM+ moved to something else). It is only SHOWN:
  nothing becomes a to-do (D2). When an upload brings BM+ in line, the
  difference goes away by itself.
* **Completed**: only Martin marks it (with a date), on a renewal or a whole
  bundle at once (M3h). MART suggests it once BM+'s three stages are done.
* On the board and the cards **Martin's strategy wins**; BM+ stays the record
  and is shown beside it.

Append-only (`actuals_repo`): changing or clearing a value adds a row.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from mart.ingestion.sheet import norm
from mart.repository import actuals_repo, clients_repo, renewals_repo
from mart.repository.db import connection

FIELDS = ("strategy", "completed")
# BM+'s Upcoming Renewal Strategy values (the same list as web/colors.py)
STRATEGIES = ("Remarketing", "Incumbent without Rate Guarantee", "Incumbent with Rate Guarantee",
              "Non-expiring", "Unknown / New Policy", "TBC")
STRATEGY_MAX = 120
REASON_MAX = 500


class Invalid(ValueError):
    """Shown to the user as is."""


# -- reading (pure) ----------------------------------------------------------------------
def current(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """field -> its current row (rows newest first; a cleared field is left out)."""
    out: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    for row in rows:
        if row["field"] in seen:
            continue
        seen.add(row["field"])
        if row["value"] is not None:
            out[row["field"]] = row
    return out


def strategy_state(mine: str | None, bm_then: str | None, bm_now: str | None) -> str | None:
    """sync / behind / conflict (None when Martin set nothing)."""
    if not mine:
        return None
    if norm(mine) == norm(bm_now):
        return "sync"
    if not norm(bm_now) or norm(bm_now) == norm(bm_then):
        return "behind"
    return "conflict"


def stages_done(stage_list: list[dict[str, Any]] | None) -> bool:
    """BM+'s three stages all completed (a skipped one counts), at least one done."""
    states = [s["state"] for s in stage_list or []]
    return bool(states) and "done" in states and all(s in ("done", "skipped") for s in states)


def view(rows: list[dict[str, Any]], bm_strategy: str | None,
         stage_list: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """What the panel and the cards show for one renewal."""
    now = current(rows)
    s, c = now.get("strategy"), now.get("completed")
    state = strategy_state(s["value"] if s else None, s["bm_value"] if s else None, bm_strategy)
    return {
        "strategy": s["value"] if s else None,
        "strategy_reason": s["reason"] if s else None,
        "strategy_set_at": s["created_at"] if s else None,
        "bm_strategy": bm_strategy,
        "state": state,
        "caught_up": state == "sync" and norm(s["bm_value"]) != norm(s["value"]),
        "differs": state in ("behind", "conflict"),
        # the strategy the board and the cards go by: Martin's, else BM+'s
        "effective": (s["value"] if s else None) or bm_strategy,
        "completed": c["value"] if c else None,
        "completed_reason": c["reason"] if c else None,
        "suggest_completed": not c and stages_done(stage_list),
        "history": rows,
    }


# -- writing -----------------------------------------------------------------------------
def _clean(text: str | None, limit: int, what: str) -> str | None:
    text = (text or "").strip()
    if len(text) > limit:
        raise Invalid(f"{what} is too long (at most {limit} characters).")
    return text or None


def _renewals_of_mine(conn, client_id: int, renewal_ids: list[int]) -> list[dict[str, Any]]:
    client = clients_repo.get(conn, client_id)
    if client is None or client["is_mine"] != 1:
        raise Invalid("This client is not one of yours (or doesn't exist).")
    out = []
    for rid in renewal_ids:
        r = renewals_repo.get(conn, rid)
        if r is None or r["client_id"] != client_id:
            raise Invalid("This renewal doesn't exist (or isn't this client's).")
        out.append(r)
    if not out:
        raise Invalid("No renewal chosen.")
    return out


def set_strategy(client_id: int, renewal_id: int, value: str | None, reason: str | None = None) -> None:
    """Martin's strategy for a renewal; empty clears it (BM+'s shows again)."""
    value = _clean(value, STRATEGY_MAX, "The strategy")
    reason = _clean(reason, REASON_MAX, "The reason")
    with connection() as conn:
        r = _renewals_of_mine(conn, client_id, [renewal_id])[0]
        now = current(actuals_repo.for_renewal(conn, renewal_id)).get("strategy")
        if (now["value"] if now else None) == value and (value is None or (now and now["reason"] == reason)):
            return                                  # nothing changed
        actuals_repo.add(conn, renewal_id, "strategy", value, r.get("upcoming_strategy"), reason)


def set_completed(client_id: int, renewal_ids: list[int], on: str | None,
                  reason: str | None = None, undo: bool = False) -> int:
    """Mark renewals completed on a date (default today), or take it back
    (`undo`). Renewals already in that state are left as they are. Returns
    how many changed."""
    reason = _clean(reason, REASON_MAX, "The reason")
    if not undo:
        try:
            on = date.fromisoformat((on or "").strip() or date.today().isoformat()).isoformat()
        except ValueError as exc:
            raise Invalid("That date isn't valid.") from exc
    changed = 0
    with connection() as conn:
        for r in _renewals_of_mine(conn, client_id, renewal_ids):
            done = current(actuals_repo.for_renewal(conn, r["id"])).get("completed")
            if bool(done) != undo:
                continue
            actuals_repo.add(conn, r["id"], "completed", None if undo else on,
                             r.get("workflow_status"), reason)
            changed += 1
    return changed
