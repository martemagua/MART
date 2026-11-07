"""Home's "Today" (M2 day 4, Martin 04.11.2026): one list of what needs
Martin, then a card per client. Built from the same explorer data as the
client pages (client_service.explorer), so the freshness, the paused clock
and the broker deadlines can never disagree with what a client page shows.

Today lists:
* broker deadlines **passed** (not confirmed) and **due within 7 days**;
* to-dos **overdue or due today**, and every **urgent** one;
* bundles gone **red** (no overview entry for the red limit, not paused,
  not already listed for a passed deadline);
* overview entries **dated since yesterday** (new news).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from urllib.parse import quote

from mart.repository import clients_repo
from mart.repository.db import connection
from mart.services import client_service, notes_service

SOON_DAYS = 7
SHOWN = 10          # per list; the rest is "N more" (each client page has them all)


def _bundle_label(b: dict[str, Any]) -> str:
    if b["custom_id"]:
        return b["extra"]
    parts = [_dmy(b["renewal_date"]) if b["renewal_date"] else None, b["extra"]]
    return " · ".join(x for x in parts if x) or "no date"


def _dmy(iso: str) -> str:
    return f"{iso[8:10]}.{iso[5:7]}.{iso[:4]}"


def _cap(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"items": items[:SHOWN], "more": max(len(items) - SHOWN, 0), "total": len(items)}


def view(today: date | None = None, views: dict[int, dict[str, Any]] | None = None) -> dict[str, Any]:
    """`views` = the clients' explorer views when the caller has them already
    (the Clients page), so each is built once per request."""
    today = today or date.today()
    since = (today - timedelta(days=1)).isoformat()
    with connection() as conn:
        mine = clients_repo.mine_summary(conn)
    todos = notes_service.todo_list(today=today)["open"]
    passed, soon, stale, new = [], [], [], []
    cards = []
    for c in mine:
        v = (views or {}).get(c["id"]) or client_service.explorer(c["id"], today=today, with_detail=False)
        base = f"/clients/{c['id']}"
        counts = {"passed": 0, "soon": 0, "stale": 0, "new": 0,
                  "todos": sum(1 for t in todos if t["client_id"] == c["id"])}
        for b in (b for items in v["groups"].values() for b in items):
            item = {"client": c["name"], "client_id": c["id"], "country": b["country"],
                    "label": _bundle_label(b), "url": f"{base}?bundle={quote(b['key'], safe='')}",
                    "renewal_date": b["renewal_date"]}
            d = b["deadline"]
            # a bundle whose renewals are all marked completed needs nothing more
            # (QA 07.11.2026): no "gone quiet", and no BM+-suggested date; a
            # deadline Martin set himself still counts
            done = bool(b["renewals"]) and b["completed"] == len(b["renewals"])
            if done and d and d["id"] is None:
                d = None
            if d and d["state"] == "passed":
                passed.append({**item, "deadline": d})
                counts["passed"] += 1
            elif d and d["days"] <= SOON_DAYS:
                soon.append({**item, "deadline": d})
                counts["soon"] += 1
            # a bundle already listed for its passed deadline isn't listed again as quiet
            if b["freshness"]["state"] == "red" and b["renewals"] and not done \
                    and not (d and d["state"] == "passed"):
                reds = sum(1 for r in b["renewals"] if r["freshness"]["state"] == "red")
                stale.append({**item, "freshness": b["freshness"], "red": reds, "of": len(b["renewals"])})
                counts["stale"] += 1
            for r in b["renewals"]:
                latest = r["freshness"]["latest"]
                if latest and latest >= since:
                    new.append({**item, "policy": r["policy_name"] or "—", "entry_date": latest,
                                "url": f"{base}/renewals/{r['id']}"})
                    counts["new"] += 1
        cards.append({**c, "counts": counts, "attention": counts["passed"] + counts["stale"] + counts["new"]})
    due = [t for t in todos if t["urgency"] == "urgent" or (t["days"] is not None and t["days"] <= 0)]
    # renewals still ahead first (soonest first), then those already past their date (latest first)
    t = today.isoformat()

    def when(x: dict[str, Any]) -> str:
        return x["renewal_date"] or "9999"
    stale = sorted((x for x in stale if when(x) >= t), key=when) + \
        sorted((x for x in stale if when(x) < t), key=when, reverse=True)
    return {
        "today": today,
        "deadlines_passed": _cap(sorted(passed, key=lambda x: x["deadline"]["expected_date"])),
        "deadlines_soon": _cap(sorted(soon, key=lambda x: x["deadline"]["expected_date"])),
        "todos": _cap(due), "stale": _cap(stale),
        "new": _cap(sorted(new, key=lambda x: x["entry_date"], reverse=True)),
        "clients": sorted(cards, key=lambda c: (-c["attention"], c["name"].casefold())),
        "nothing": not (passed or soon or due or stale or new),
    }
