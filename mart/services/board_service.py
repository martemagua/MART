"""One client's board (M3 day 6; Martin 05.11.2026, QUESTIONS C2–C4, M3d):
the columns of services/board, a card per BUNDLE, and moving a card.

The cards are the explorer's bundles (client_service.explorer), so the board
and the client page never disagree. Only the renewals in the latest export
are on it; an emptied bundle (kept for its notes) is not.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

from mart.repository import board_repo
from mart.repository.db import connection
from mart.services import actuals, board, client_service


class Invalid(ValueError):
    """Shown to the user as is."""


def _card(b: dict[str, Any]) -> dict[str, Any]:
    rs = b["renewals"]
    return {
        **b,
        "strategies": Counter(r["actual"]["key"] for r in rs).most_common(),
        "open_ids": [r["id"] for r in rs if not r["actual"]["completed"]],
        "dots": board.aggregate_stages(b["stage_lists"]),
        "search": " ".join(x for x in b["search"] + b["proposal_insurers"] if x),
    }


def board_of(client_id: int, today: date | None = None) -> dict[str, Any]:
    try:
        view = client_service.explorer(client_id, today=today, with_detail=False)
    except client_service.NotFound as exc:
        raise Invalid(str(exc)) from exc
    cols: dict[str, list[dict[str, Any]]] = {k: [] for k in board.ORDER}
    for items in view["groups"].values():
        for b in items:
            if b["renewals"]:
                cols[b["stage"]["column"]].append(_card(b))
    return {
        "client": view["client"], "filters": view["filters"], "has_task_data": view["has_task_data"],
        "columns": [{"key": k, "label": label, "hint": hint, "cards": cols[k]}
                    for k, label, hint in board.COLUMNS],
        "card_count": sum(len(c) for c in cols.values()),
        "moved": sum(1 for c in cols.values() for b in c if b["stage"]["mine"]),
    }


def set_stage(client_id: int, key: str, stage: str | None, reason: str | None = None,
              complete: bool = False, today: date | None = None) -> dict[str, Any]:
    """Record Martin's stage of a bundle (``stage`` empty = follow BM+ again).
    Moving it to the column BM+ has it in also means "follow BM+". With
    ``complete`` (only into Done), the bundle's open renewals are marked
    completed today as well (M3h). Returns the bundle."""
    stage = (stage or "").strip() or None
    if stage is not None and stage not in board.ORDER:
        raise Invalid("That is not a column of the board.")
    reason = (reason or "").strip() or None
    if reason and len(reason) > board.REASON_MAX:
        raise Invalid(f"The reason is too long (at most {board.REASON_MAX} characters).")
    try:
        view = client_service.explorer(client_id, today=today, with_detail=False)
    except client_service.NotFound as exc:
        raise Invalid(str(exc)) from exc
    b = next((b for items in view["groups"].values() for b in items if b["key"] == key and b["renewals"]),
             None)
    if b is None:
        raise Invalid("That bundle is not on this client's board.")
    bm = b["bm_stage"]["column"]
    if stage == bm:
        stage = None                                    # where BM+ has it: follow BM+ again
    # Store it unless it changes nothing: the same stage as stored, in the
    # column the card already shows, with no new reason. (QA 07.11.2026: the
    # check against the stored row alone dropped a move back to a stage that
    # BM+ had since passed, and a reason added to the current stage.)
    row = b["stage"]["row"] or {}
    unchanged = stage == row.get("stage") and (stage or bm) == b["stage"]["column"] \
        and (not reason or reason == row.get("reason"))
    if not unchanged:
        with connection() as conn:
            board_repo.add(conn, client_id, key, stage, bm, reason)
    if complete and (stage or bm) == "done":
        open_ids = [r["id"] for r in b["renewals"] if not r["actual"]["completed"]]
        if open_ids:
            actuals.set_completed(client_id, open_ids, (today or date.today()).isoformat(), reason)
    return b
