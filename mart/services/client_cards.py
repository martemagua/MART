"""The Clients page (Martin, 06.11.2026): ONE page to pick a client, a large
card each, leading to its board or its explorer. Built from the same data as
the client pages and Home (client_service.explorer, today.view), so a card
never disagrees with the page it opens; each client's explorer is built once.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

from mart.services import board, client_service
from mart.services import today as today_mod


def cards(today: date | None = None) -> list[dict[str, Any]]:
    today = today or date.today()
    rows = client_service.clients_overview(today)
    views = {c["id"]: client_service.explorer(c["id"], today=today, with_detail=False) for c in rows}
    counts = {c["id"]: c["counts"] for c in today_mod.view(today, views)["clients"]} if rows else {}
    out = []
    for c in rows:
        v = views[c["id"]]
        bundles = [b for items in v["groups"].values() for b in items if b["renewals"]]
        renewals = [r for b in bundles for r in b["renewals"]]
        on_board = Counter(b["stage"]["column"] for b in bundles)
        out.append({
            **c,
            "counts": counts.get(c["id"], {}),
            # the board in one row: how many bundles sit in each column
            "board": [{"key": k, "label": label, "hint": hint, "n": on_board[k]}
                      for k, label, hint in board.COLUMNS],
            "board_total": len(bundles),
            "moved": sum(1 for b in bundles if b["stage"]["mine"]),
            # what Martin recorded beside BM+
            "strategies_set": sum(1 for r in renewals if r["actual"]["strategy"]),
            "differs": sum(b["differs"] for b in bundles),
            "proposals": sum(b["proposal_count"] for b in bundles),
            "completed": sum(b["completed"] for b in bundles),
            "renewal_total": len(renewals),
            "countries": len(v["filters"]["countries"]),
            "regions": v["filters"]["regions"],
        })
    return out
