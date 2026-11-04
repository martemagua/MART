"""One renewal, everything BM+ says about it: the renewal panel.

Tasks link to their renewal through the Task Tracker's `Policy ID`, which is
the Renewal Tracker's per-cycle id (verified on real exports); failing that,
through the stable Expiring Policy Unique ID + the renewal date. Tasks of an
older cycle of the same policy therefore never show as this cycle's.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from mart.ingestion import overview as ov
from mart.ingestion import renewal_tracker as rt
from mart.ingestion import task_tracker as tt
from mart.ingestion.ids import bm_link
from mart.ingestion.sheet import lookup, norm, section_items
from mart.ingestion.specs import renewal_tracker as rspec
from mart.ingestion.specs import task_tracker as tspec
from mart.repository import clients_repo, history_repo, renewals_repo, tasks_repo, uploads_repo
from mart.repository.db import connection
from mart.services import history

_STAGE_KEYS = {norm(s): s for s in tspec.STAGES}


class NotFound(LookupError):
    pass


def renewal_index(renewals: list[dict[str, Any]]) -> tuple[set[str], set[tuple[str, str]]]:
    """What a task can link to: the renewals' per-cycle ids, and their
    (stable policy id, renewal date) pairs."""
    return ({r["cycle_id"] for r in renewals if r.get("cycle_id")},
            {(r["expiring_policy_id"], r.get("renewal_date") or "") for r in renewals
             if r.get("expiring_policy_id")})


def links_to_renewal(index: tuple[set[str], set[tuple[str, str]]], task: dict[str, Any]) -> bool:
    """Does this task (its fields) belong to one of the indexed renewals? The
    same two rules as link_tasks."""
    cycles, pairs = index
    if task.get("policy_id") and task["policy_id"] in cycles:
        return True
    return bool(task.get("expiring_policy_id")) and \
        (task["expiring_policy_id"], task.get("review_date") or "") in pairs


def link_tasks(renewals: list[dict[str, Any]], tasks: list[dict[str, Any]]) -> dict[int, list[dict]]:
    """renewal id -> its tasks (this cycle only)."""
    by_policy: dict[str, list[dict]] = {}
    by_expiring: dict[tuple[str, str], list[dict]] = {}
    for t in tasks:
        if t.get("policy_id"):
            by_policy.setdefault(t["policy_id"], []).append(t)
        if t.get("expiring_policy_id"):
            by_expiring.setdefault((t["expiring_policy_id"], t.get("review_date") or ""), []).append(t)
    out: dict[int, list[dict]] = {}
    for r in renewals:
        found = list(by_policy.get(r.get("cycle_id") or "", []))
        ids = {t["task_key"] for t in found}
        for t in by_expiring.get((r.get("expiring_policy_id") or "", r.get("renewal_date") or ""), []):
            if t["task_key"] not in ids:
                found.append(t)
        out[r["id"]] = found
    return out


_NO_PROPOSALS = {norm(s) for s in tspec.NO_PROPOSALS_STRATEGIES}


def stages(tasks: list[dict[str, Any]], today: date | None = None,
           strategy: str | None = None) -> list[dict[str, Any]]:
    """The three BM+ stages in order, each from its task (missing = BM+ has not
    created it; skipped = the renewal's strategy has no such stage).
    Status is BM+'s own; only the peer-review facts are added."""
    today = today or date.today()
    by_stage: dict[str, dict] = {}
    for t in sorted(tasks, key=lambda t: (t.get("in_latest_export", 1), t.get("due_date") or "")):
        name = _STAGE_KEYS.get(norm(t.get("task_name")))
        if name:
            by_stage[name] = t            # the newest / in-export one wins
    out = []
    for name in tspec.STAGES:
        t = by_stage.get(name)
        if t is None:
            if name == "Proposals" and norm(strategy) in _NO_PROPOSALS:
                out.append({"name": name, "state": "skipped", "label": f"not needed ({strategy})"})
            else:
                out.append({"name": name, "state": "missing", "label": "not in BM+ yet"})
            continue
        f = t.get("fields") or {}
        state, past_due = tt.stage_state(t.get("task_status"))
        due = t.get("due_date")
        out.append({
            "name": name, "state": state, "past_due": past_due,
            "label": {"todo": "Not started", "doing": "In progress", "review": "Peer review pending",
                      "done": "Completed"}[state],
            "status": t.get("task_status"), "due_date": due,
            "days_to_due": (datetime.fromisoformat(due).date() - today).days if due else None,
            "assignee": f.get("assignee"), "delegated_to": f.get("delegated_to"),
            "completed_date": f.get("completed_date"), "completed_by": f.get("completed_by"),
            "review_approved_date": f.get("review_approved_date"),
            "review_approved_by": f.get("review_approved_by"),
            "review_pending_days": f.get("review_pending_days"),
            "review_rejected_count": f.get("review_rejected_count") or 0,
            "due_changed_count": f.get("due_changed_count") or 0,
            "original_due_date": f.get("original_due_date"),
            "in_latest_export": t.get("in_latest_export", 1),
            "bm_url": bm_link(f.get("task_ref")),
        })
    return out


def _proposal(p: dict[str, Any]) -> dict[str, Any]:
    out = {label: lookup(p, header, section) for label, header, section in rspec.PROPOSAL_COLUMNS}
    out["Insurer"] = rt.insurer_or_provider(out.get("Insurer"), lookup(p, *rspec.PROPOSAL_PROVIDER))
    return out


def _facts(row: dict[str, Any], spec_fields: list[tuple[str, str, str | None]]) -> list[tuple[str, Any]]:
    out = []
    for label, header, section in spec_fields:
        val = lookup(row, header, section)
        if val not in (None, "", 0, "N/A", "NA", "na", "n/a"):
            out.append((label, val))
    return out


def detail(client_id: int, renewal_id: int, today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    with connection() as conn:
        client = clients_repo.get(conn, client_id)
        r = renewals_repo.get(conn, renewal_id)
        if client is None or client["is_mine"] != 1 or r is None or r["client_id"] != client_id:
            raise NotFound("This renewal doesn't exist (or isn't one of your clients').")
        tasks = tasks_repo.for_client(conn, client_id)
        has_task_data = bool(tasks)
        older = _older_sections(conn, r)
        mine_tasks = link_tasks([r], tasks)[r["id"]]
        items = [("renewal", r["id"])] + [("task", t["id"]) for t in mine_tasks]
        changes = history_repo.for_items(conn, items)
    mine = mine_tasks
    f, d = r["fields"], r["details"]
    strategy = (d.get("strategy") or [{}])[0]
    savings = (d.get("savings") or [{}])[0]
    proposals = [_proposal(p) for p in d.get("proposals") or []]
    amounts = [(h, val) for h, val in section_items(savings, rspec.SAVINGS_AMOUNTS_SECTION)
               if isinstance(val, (int, float)) and val]
    questions = [(h, val) for h, val in section_items(strategy, rspec.CLIENT_QUESTIONS_SECTION) if val]
    others = sorted((t for t in mine if not _STAGE_KEYS.get(norm(t.get("task_name")))),
                    key=lambda t: t.get("due_date") or "")
    days = (datetime.fromisoformat(r["renewal_date"]).date() - today).days if r["renewal_date"] else None
    stages_ = stages(mine, today, r.get("upcoming_strategy"))
    return {
        "client": client, "renewal": r, "fields": f, "days_until": days,
        "stages": stages_, "has_task_data": has_task_data, "other_tasks": others,
        "strategy": _facts(strategy, rspec.STRATEGY_FIELDS),
        "last_renewal": _facts(strategy, rspec.LAST_RENEWAL_FIELDS),
        "claims": _facts(strategy, rspec.CLAIMS_FIELDS),
        "questions": questions,
        "proposals": proposals,
        "savings": _facts(savings, rspec.SAVINGS_FIELDS), "savings_amounts": amounts,
        "overview": ov.timeline(f.get("overview_all"), f.get("overview_client_ready"), today),
        "overview_state": ov.flag(f.get("overview_all"), f.get("overview_client_ready"))["state"],
        "feed": sorted(ov.entries(f.get("renewal_feed")), key=lambda e: e["date"], reverse=True),
        "bm": r["bm"],
        "older": older,
        "history": history.describe(changes, {t["id"]: t["task_name"] for t in mine}),
        "links": bm_links(f, stages_),
    }


def policy_number(details: dict[str, Any] | None) -> str | None:
    """The policy number BM+ gives on the detail sheets (Renewal Strategy,
    then Proposals, then Savings); None when no sheet has one."""
    for key in rspec.DETAIL_SHEETS:
        for row in (details or {}).get(key) or []:
            value = lookup(row, rspec.POLICY_NUMBER) if isinstance(row, dict) else None
            if value is not None and str(value).strip():
                return str(value).strip()
    return None


def bm_links(fields: dict[str, Any], stage_list: list[dict[str, Any]]) -> list[dict[str, str]]:
    """The renewal's links to BM+ for its "⋯" menu, best first. Only links BM+
    wrote in the exports. The renewal link the cross-client Renewal Tracker
    writes (`fields.bm_url`) does not open in BM+ (Martin, 04.11.2026), so it is
    kept but not offered. The policy link opens. The Task Tracker's task links
    all open the same page, the renewal's workspace in BM+, so ONE of them is
    offered as the renewal's link (Martin, 04.11.2026): the first stage's."""
    out = []
    if fields.get("bm_policy_url"):
        out.append({"label": "Policy in BM+", "url": fields["bm_policy_url"],
                    "title": "The expiring policy in BM+"})
    task_url = next((s["bm_url"] for s in stage_list if s.get("bm_url")), None)
    if task_url:
        out.append({"label": "Renewal in BM+", "url": task_url,
                    "title": "The renewal's workspace in BM+ (its tasks)"})
    return out


def _older_sections(conn, r: dict[str, Any]) -> dict[str, str | None]:
    """Detail sheets kept from an earlier export (the latest one didn't include
    that sheet): sheet key -> that export's report date."""
    out = {}
    for key, upload_id in ((r["details"] or {}).get("_from") or {}).items():
        if upload_id != r["last_upload_id"]:
            u = uploads_repo.get(conn, upload_id)
            out[key] = u["report_date"] if u else None
    return out
