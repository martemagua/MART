"""Clients and their renewals, bundled for the client explorer.

A **bundle** is the renewals of one client that renew together: same
country, same renewal date, split further or joined as Martin arranged it
(services/bundles.py; day 6). The explorer shows the bundles in a side panel,
grouped by renewal month or by country, and the selected bundle's renewals
in the middle, each with its overview compared against the client-ready one.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Any

from mart.ingestion import overview as ov
from mart.repository import bundles_repo, clients_repo, renewals_repo, tasks_repo
from mart.repository.db import connection
from mart.services import bundles as bx
from mart.services import preferences, renewal_service

GROUPINGS = ("date", "country")
NO_DATE = "none"
_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"]


class NotFound(LookupError):
    pass


def bundle_key(country: str | None, renewal_date: str | None) -> str:
    return f"{country or '—'}|{renewal_date or NO_DATE}"


def _days_until(iso: str | None, today: date) -> int | None:
    return (datetime.fromisoformat(iso).date() - today).days if iso else None


def _month_label(iso: str | None) -> str:
    if not iso:
        return "No renewal date"
    d = datetime.fromisoformat(iso).date()
    return f"{_MONTHS[d.month - 1]} {d.year}"


def overview_freshness(as_of: str | None, today: date) -> dict[str, Any]:
    """How old the client's overview data is: the report date of the last
    export that carried the overview (in practice a single-client export)."""
    limit = preferences.get("overview_data_stale_days")
    if not as_of:
        return {"as_of": None, "age_days": None, "stale": True, "limit": limit}
    age = (today - datetime.fromisoformat(as_of).date()).days
    return {"as_of": as_of, "age_days": age, "stale": age > limit, "limit": limit}


def clients_overview(today: date | None = None) -> list[dict[str, Any]]:
    """My clients for the Clients list: renewals, bundles, next renewal, how
    many renewals have overview issues, and how old the overview data is."""
    today = today or date.today()
    with connection() as conn:
        mine = clients_repo.mine_summary(conn)
        texts = renewals_repo.overview_texts_for_mine(conn)
    stats: dict[int, dict[str, Any]] = {c["id"]: {"bundles": set(), "flags": Counter()} for c in mine}
    for t in texts:
        s = stats.get(t["client_id"])
        if s is None:
            continue
        s["bundles"].add(bundle_key(t["country"], t["renewal_date"]))
        s["flags"][ov.flag(t["overview_all"], t["overview_client_ready"])["state"]] += 1
    out = []
    for c in mine:
        s = stats[c["id"]]
        out.append({**c, "bundles": len(s["bundles"]), "flags": dict(s["flags"]),
                    "days_until": _days_until(c["next_renewal"], today),
                    "freshness": overview_freshness(c.get("overview_as_of"), today)})
    return out


def _enrich(r: dict[str, Any], today: date) -> dict[str, Any]:
    f = r["fields"]
    timeline = ov.timeline(f.get("overview_all"), f.get("overview_client_ready"), today)
    state = ov.flag(f.get("overview_all"), f.get("overview_client_ready"))["state"]
    upcoming = f.get("insurer_upcoming")
    return {
        **r,
        "insurer_upcoming": upcoming if upcoming and upcoming != r["insurer"] else None,
        "benefit_owner": f.get("benefit_owner"),
        "local_analyst": f.get("local_analyst"),
        "pdc_considered": f.get("pdc_considered"),
        "overview": timeline,
        "overview_state": state,
        "feed": ov.entries(f.get("renewal_feed")),
    }


def _with_stages(r: dict[str, Any], stage_list: list[dict[str, Any]]) -> dict[str, Any]:
    return {**r, "stages": stage_list, "links": renewal_service.bm_links(r["fields"], stage_list)}


def _policy_number(tasks: list[dict[str, Any]]) -> str | None:
    return next(((t.get("fields") or {}).get("policy_number") for t in tasks
                 if (t.get("fields") or {}).get("policy_number")), None)


def _mine(conn, client_id: int) -> dict[str, Any]:
    client = clients_repo.get(conn, client_id)
    if client is None or client["is_mine"] != 1:
        raise NotFound("This client is not one of yours (or doesn't exist).")
    return client


def explorer(client_id: int, bundle: str | None = None, group: str = "date",
             show_all: bool = False, today: date | None = None,
             renewal_id: int | None = None) -> dict[str, Any]:
    """The explorer's side panel (bundles, grouped) and the selected bundle:
    the one asked for, else the one holding `renewal_id`, else the next to
    renew. A key that no longer exists (split or joined since) leads to the
    bundle that now holds its renewals."""
    today = today or date.today()
    group = group if group in GROUPINGS else "date"
    with connection() as conn:
        client = _mine(conn, client_id)
        renewals = renewals_repo.for_client(conn, client_id)
        tasks = tasks_repo.for_client(conn, client_id)
        splits, joins = bundles_repo.splits(conn, client_id), bundles_repo.joins(conn, client_id)

    left_count = sum(1 for r in renewals if not r["in_latest_export"])
    shown = [r for r in renewals if show_all or r["in_latest_export"]]
    linked = renewal_service.link_tasks(shown, tasks)

    bundles: dict[str, dict[str, Any]] = {}
    where: dict[int, str] = {}
    for r in shown:
        base = bundle_key(r["country"], r["renewal_date"])
        own = bx.own_key(r, base, splits, _policy_number(linked[r["id"]]))
        key = bx.resolve(own, joins)
        where[r["id"]] = key
        country, rdate = bx.base_of(key).split("|", 1)
        rdate = None if rdate == NO_DATE else rdate
        b = bundles.setdefault(key, {
            "key": key, "country": country, "renewal_date": rdate, "extra": bx.label(key),
            "days_until": _days_until(rdate, today), "renewals": [],
            "flags": Counter(), "left": 0, "search": [], "bases": set(), "joined": {},
        })
        b["bases"].add(base)
        if own != key:
            b["joined"][own] = f"{r['country'] or '—'} · {bx.label(own)}".rstrip(" ·")
        b["renewals"].append(r)
        f = r["fields"]
        b["flags"][ov.flag(f.get("overview_all"), f.get("overview_client_ready"))["state"]] += 1
        b["left"] += int(not r["in_latest_export"])
        b["search"] += [r["policy_name"] or "", r["entity"] or "", r["insurer"] or "", b["extra"]]
    ordered = sorted(bundles.values(), key=lambda b: (b["renewal_date"] or "9999", b["country"], b["extra"]))

    groups: dict[str, list[dict[str, Any]]] = {}
    for b in sorted(ordered, key=lambda b: (b["country"], b["renewal_date"] or "9999", b["extra"])) \
            if group == "country" else ordered:
        label = b["country"] if group == "country" else _month_label(b["renewal_date"])
        groups.setdefault(label, []).append(b)

    selected = _find(bundles, bundle, joins, where.get(renewal_id) if renewal_id else None)
    if selected is None and ordered:
        upcoming = [b for b in ordered if b["days_until"] is not None and b["days_until"] >= 0]
        selected = (upcoming or ordered)[0]
    detail = None
    if selected:
        stage_of = {r["id"]: renewal_service.stages(linked[r["id"]], today, r.get("upcoming_strategy"))
                    for r in selected["renewals"]}
        items = sorted((_with_stages(_enrich(r, today), stage_of[r["id"]]) for r in selected["renewals"]),
                       key=lambda r: ((r["policy_name"] or "").casefold(), r["entity"] or ""))
        detail = {
            **selected, "renewals": items,
            "entities": sorted({r["entity"] for r in items if r["entity"]}),
            "insurers": sorted({r["insurer"] for r in items if r["insurer"]}),
            "strategies": Counter(r["upcoming_strategy"] or "—" for r in items),
            "statuses": Counter(r["workflow_status"] or "—" for r in items),
            "split_by": splits.get(bx.base_of(selected["key"]), []),
            # same country first, then by date: the likely join is a sibling
            "join_targets": sorted(((k, b) for k, b in bundles.items() if k != selected["key"]),
                                   key=lambda kb: (kb[1]["country"] != selected["country"],
                                                   kb[1]["renewal_date"] or "9999", kb[1]["extra"])),
        }
    return {
        "client": client, "groups": groups, "bundle_count": len(ordered),
        "renewal_count": len(shown), "left_count": left_count, "show_all": show_all,
        "group": group, "selected": detail, "has_task_data": bool(tasks),
        "freshness": overview_freshness(client.get("overview_as_of"), today),
        "live_keys": set(bundles), "split_options": bx.SPLIT_FIELDS,
    }


def _find(bundles: dict[str, dict[str, Any]], key: str | None, joins: dict[str, str],
          renewal_key: str | None) -> dict[str, Any] | None:
    if renewal_key:
        return bundles.get(renewal_key)
    if not key:
        return None
    if key in bundles:
        return bundles[key]
    if bx.resolve(key, joins) in bundles:            # joined since
        return bundles[bx.resolve(key, joins)]
    base = bx.base_of(key)                           # split / unsplit since
    return next((b for b in bundles.values() if base in b["bases"]), None)


# -- arranging bundles (user data) ------------------------------------------------------
def set_split(client_id: int, key: str, fields: list[str]) -> None:
    """Split the bundle's base (country + date) by these fields; [] = no split."""
    bad = [f for f in fields if f not in bx.SPLIT_FIELDS]
    if bad:
        raise ValueError(f"Can't split by {', '.join(bad)}.")
    with connection() as conn:
        _mine(conn, client_id)
        bundles_repo.set_split(conn, client_id, bx.base_of(key), [f for f in bx.SPLIT_FIELDS if f in fields])


def join(client_id: int, from_key: str, into_key: str) -> None:
    with connection() as conn:
        _mine(conn, client_id)
        joins = bundles_repo.joins(conn, client_id)
        if not into_key or bx.resolve(into_key, {**joins, from_key: into_key}) == from_key \
                or bx.resolve(into_key, joins) == from_key:
            raise ValueError("A bundle can't be joined into itself.")
        bundles_repo.join(conn, client_id, from_key, into_key)


def unjoin(client_id: int, from_key: str) -> None:
    with connection() as conn:
        _mine(conn, client_id)
        bundles_repo.unjoin(conn, client_id, from_key)
