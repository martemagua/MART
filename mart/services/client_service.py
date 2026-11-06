"""Clients and their renewals, bundled for the client explorer.

A **bundle** is the renewals of one client that renew together: by default
the same country and renewal date; Martin can move renewals into named
custom bundles of the same country (services/bundles.py, bundle_service).
The explorer shows the bundles in a side panel, grouped by renewal month,
and the selected bundle's renewals in the middle, each with its overview
compared against the client-ready one.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Any

from mart.ingestion import overview as ov
from mart.repository import (
    actuals_repo,
    bundles_repo,
    clients_repo,
    deadlines_repo,
    notes_repo,
    proposals_repo,
    renewals_repo,
    tasks_repo,
)
from mart.repository.db import connection
from mart.services import actuals, deadlines, freshness, preferences, proposals, renewal_service
from mart.services import bundles as bx

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
        s["bundles"].add(bx.custom_key(t["custom_bundle_id"]) if t["custom_bundle_id"]
                         else bundle_key(t["country"], t["renewal_date"]))
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
        "policy_number": renewal_service.policy_number(r.get("details")),
        "local_analyst": f.get("local_analyst"),
        "pdc_considered": f.get("pdc_considered"),
        "overview": timeline,
        "overview_state": state,
        "feed": ov.entries(f.get("renewal_feed")),
    }


def _with_stages(r: dict[str, Any], stage_list: list[dict[str, Any]]) -> dict[str, Any]:
    return {**r, "stages": stage_list, "links": renewal_service.bm_links(r["fields"], stage_list)}


def _mine(conn, client_id: int) -> dict[str, Any]:
    client = clients_repo.get(conn, client_id)
    if client is None or client["is_mine"] != 1:
        raise NotFound("This client is not one of yours (or doesn't exist).")
    return client


def _new_bundle(key: str, country: str, today: date, custom: dict[str, Any] | None = None,
                name: str | None = None) -> dict[str, Any]:
    """`extra` = the bundle's name: a custom bundle's own, or the one Martin
    gave a default bundle."""
    return {"key": key, "country": country, "renewal_date": None, "last_date": None, "days_until": None,
            "extra": custom["name"] if custom else (name or ""),
            "custom_id": custom["id"] if custom else None,
            "renewals": [], "flags": Counter(), "left": 0, "completed": 0, "search": []}


def explorer(client_id: int, bundle: str | None = None,
             show_all: bool = False, today: date | None = None,
             renewal_id: int | None = None) -> dict[str, Any]:
    """The explorer's side panel (bundles, grouped) and the selected bundle:
    the one asked for, else the one holding `renewal_id`, else the first in
    the panel. A renewal is in its default bundle (country + date) unless Martin
    moved it into a custom bundle (services/bundles.py)."""
    today = today or date.today()
    with connection() as conn:
        client = _mine(conn, client_id)
        renewals = renewals_repo.for_client(conn, client_id)
        tasks = tasks_repo.for_client(conn, client_id)
        customs = bundles_repo.custom_bundles(conn, client_id)
        placed = bundles_repo.placements(conn, client_id)
        names = bundles_repo.names(conn, client_id)
        # a bundle all of whose renewals moved away stays while it carries
        # notes, open to-dos or an open broker deadline
        with_notes = notes_repo.bundle_keys_with_content(conn, client_id) | \
            deadlines_repo.open_bundle_keys(conn, client_id)
        details = renewals_repo.details_of(conn, [r["id"] for r in renewals])
        actual_rows = actuals_repo.for_client(conn, client_id)
        proposal_rows = proposals_repo.for_client(conn, client_id)

    lim = freshness.limits(today)
    fresh_of = {r["id"]: freshness.of(freshness.latest(r["fields"]), lim) for r in renewals}
    left_count = sum(1 for r in renewals if not r["in_latest_export"])
    shown = [r for r in renewals if show_all or r["in_latest_export"]]
    linked = renewal_service.link_tasks(shown, tasks)

    bundles: dict[str, dict[str, Any]] = {}
    where: dict[int, str] = {}
    for r in shown:
        custom = customs.get(placed.get(r["id"]))
        key = bx.custom_key(custom["id"]) if custom else bx.default_key(r["country"], r["renewal_date"])
        where[r["id"]] = key
        b = bundles.setdefault(key, _new_bundle(key, (custom or r)["country"] or "—", today, custom,
                                                names.get(key)))
        rd = r["renewal_date"]
        if rd and (b["renewal_date"] is None or rd < b["renewal_date"]):
            b["renewal_date"] = rd
        if rd and (b["last_date"] is None or rd > b["last_date"]):
            b["last_date"] = rd
        # Martin's actual state (strategy, completed) beside BM+'s
        r["actual"] = actuals.view(actual_rows.get(r["id"], []), r.get("upcoming_strategy"))
        b["renewals"].append(r)
        b["completed"] += int(bool(r["actual"]["completed"]))
        f = r["fields"]
        b["flags"][ov.flag(f.get("overview_all"), f.get("overview_client_ready"))["state"]] += 1
        b["left"] += int(not r["in_latest_export"])
        b["search"] += [r["policy_name"] or "", r["entity"] or "", r["insurer"] or "", b["extra"]]
    # a bundle all of whose renewals moved away stays while it carries notes
    # or open to-dos, so nothing written is lost
    for key in sorted(with_notes - set(bundles)):
        custom = customs.get(bx.custom_id(key)) if bx.custom_id(key) is not None else None
        if custom:
            bundles[key] = _new_bundle(key, custom["country"], today, custom)
        elif bx.is_default_key(key):
            country, rdate = bx.split_default(key)
            bundles[key] = {**_new_bundle(key, country, today, None, names.get(key)), "renewal_date": rdate}
    # broker deadlines (BM+ prefill from the expected-terms date); one that is
    # still ahead pauses the stale clock of the bundle's renewals
    dl = deadlines.for_bundles(client_id, bundles, {i: deadlines.bm_date(d) for i, d in details.items()},
                               {i: f["latest"] for i, f in fresh_of.items()}, today)
    for key, b in bundles.items():
        b["days_until"] = _days_until(b["renewal_date"], today)
        b["deadline"] = dl[key]["current"]
        b["deadline_history"] = dl[key]["history"]
        for r in b["renewals"]:
            fresh_of[r["id"]] = freshness.pause(fresh_of[r["id"]], b["deadline"])
            r["freshness"] = fresh_of[r["id"]]      # Home reads it from the bundles
        b["freshness"] = freshness.worst([fresh_of[r["id"]] for r in b["renewals"]])
    ordered = sorted(bundles.values(), key=lambda b: (b["renewal_date"] or "9999", b["country"], b["extra"]))

    groups: dict[str, list[dict[str, Any]]] = {}
    for b in ordered:
        groups.setdefault(_month_label(b["renewal_date"]), []).append(b)

    # nothing asked for: the bundle at the top of the side panel, so the page
    # opens at the top (Martin, 04.11.2026)
    selected = bundles.get(where.get(renewal_id) if renewal_id else (bundle or "")) \
        or next((b for items in groups.values() for b in items), None)
    detail = None
    if selected:
        stage_of = {r["id"]: renewal_service.stages(linked[r["id"]], today, r.get("upcoming_strategy"))
                    for r in selected["renewals"]}
        items = sorted((_with_stages(_enrich({**r, "details": details.get(r["id"]),
                                              "freshness": fresh_of[r["id"]],
                                              "actual": actuals.view(actual_rows.get(r["id"], []),
                                                                     r.get("upcoming_strategy"),
                                                                     stage_of[r["id"]]),
                                              "proposals": proposals.view(proposal_rows.get(r["id"], []))},
                                             today),
                                     stage_of[r["id"]]) for r in selected["renewals"]),
                       key=lambda r: ((r["policy_name"] or "").casefold(), r["entity"] or ""))
        detail = {
            **selected, "renewals": items,
            "entities": sorted({r["entity"] for r in items if r["entity"]}),
            "insurers": sorted({r["insurer"] for r in items if r["insurer"]}),
            "strategies": Counter((r["actual"]["effective"] or "—", bool(r["actual"]["strategy"]))
                                  for r in items),
            "open_ids": [r["id"] for r in items if not r["actual"]["completed"]],
            "proposal_count": sum(r["proposals"]["count"] for r in items),
            "proposal_insurers": sorted({i for r in items for i in r["proposals"]["insurers"]},
                                        key=str.casefold),
            "statuses": Counter(r["workflow_status"] or "—" for r in items),
            "move_targets": move_targets(customs, bundles, selected["country"], selected["custom_id"]),
        }
    return {
        "client": client, "groups": groups, "bundle_count": len(ordered),
        "renewal_count": len(shown), "left_count": left_count, "show_all": show_all,
        "selected": detail, "has_task_data": bool(tasks),
        "freshness": overview_freshness(client.get("overview_as_of"), today),
        "where": where, "filters": panel_filters(ordered, shown), "fresh_limits": lim,
    }


def panel_filters(bundles: list[dict[str, Any]], renewals: list[dict[str, Any]]) -> dict[str, Any]:
    """The side panel's filters: the client's countries (a dropdown), and the
    first and last renewal date (where the "from" / "until" calendars open)."""
    dates = sorted(r["renewal_date"] for r in renewals if r["renewal_date"])
    return {"countries": sorted({b["country"] for b in bundles}),
            "first": dates[0] if dates else None, "last": dates[-1] if dates else None}


def move_targets(customs: dict[int, dict[str, Any]], bundles: dict[str, dict[str, Any]],
                 country: str, current: int | None) -> list[dict[str, Any]]:
    """The custom bundles of this country a renewal can be moved into (an
    empty one too: it is kept for reuse), with how many renewals each holds."""
    return [{"id": c["id"], "name": c["name"],
             "count": len(bundles.get(bx.custom_key(c["id"]), {}).get("renewals", []))}
            for c in customs.values() if c["country"] == country and c["id"] != current]
