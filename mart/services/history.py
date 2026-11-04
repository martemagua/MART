"""What an upload changed on a renewal or a task, and the renewal's history.

BM+ exports state, not events, so MART compares each upload with what it
had and records the difference (PLANNING §2.3: "record changes, not only
state"). An entry is dated by its upload: BM+ doesn't say when something
happened, only that the export of <report date> said so.
"""

from __future__ import annotations

from typing import Any

from mart.ingestion import overview as ov

# (field, label, is a date) — the facts worth a line in the history
RENEWAL_FIELDS = [
    ("workflow_status", "Workflow status", False), ("upcoming_strategy", "Strategy", False),
    ("insurer", "Insurer", False), ("insurer_upcoming", "Upcoming insurer", False),
    ("renewal_date", "Renewal date", True), ("kickoff_date", "Kick-off", True),
    ("local_meeting_date", "Local meeting", True), ("client_approval_date", "Client approval", True),
    ("expected_rate_change", "Expected rate change", False), ("benefit_owner", "Benefit owner", False),
    ("local_analyst", "Local analyst", False),
]
TASK_FIELDS = [
    ("task_status", "status", False), ("due_date", "due", True), ("assignee", "assignee", False),
    ("delegated_to", "delegated to", False), ("completed_date", "completed", True),
    ("review_approved_date", "peer review approved", True),
]
EVENTS = {"_seen": "first seen in the export", "_left": "no longer in the export",
          "_back": "back in the export", "_overview": "new overview entry"}
_LABELS = {f: (label, is_date) for f, label, is_date in RENEWAL_FIELDS + TASK_FIELDS}


def _blank(v: Any) -> Any:
    return None if v in (None, "") else v


def _diff(fields, old: dict[str, Any], new: dict[str, Any]) -> list[tuple[str, Any, Any]]:
    return [(f, _blank(old.get(f)), _blank(new.get(f))) for f, _, _ in fields
            if _blank(old.get(f)) != _blank(new.get(f))]


def _latest_entry(text: str | None) -> str | None:
    dates = [e["date"] for e in ov.entries(text) if e.get("date")]
    return max(dates) if dates else None


def renewal_changes(old: dict[str, Any], new: dict[str, Any]) -> list[tuple[str, Any, Any]]:
    """Changed facts between two versions of a renewal's fields, plus a newer
    overview entry (only streams the export carried differ at all)."""
    out = _diff(RENEWAL_FIELDS, old, new)
    before, after = _latest_entry(old.get("overview_all")), _latest_entry(new.get("overview_all"))
    if after and (not before or after > before):
        out.append(("_overview", before, after))
    return out


def task_changes(old: dict[str, Any], new: dict[str, Any]) -> list[tuple[str, Any, Any]]:
    return _diff(TASK_FIELDS, old, new)


def describe(rows: list[dict[str, Any]], task_names: dict[int, str]) -> list[dict[str, Any]]:
    """Changes grouped by upload, newest first, ready to show. A task's own
    "first seen" is only shown when it came after the first upload that
    brought this renewal's tasks (a stage task BM+ created later)."""
    task_seen = [r["upload_id"] for r in rows if r["item_kind"] == "task" and r["field"] == "_seen"]
    first_tasks = min(task_seen) if task_seen else None
    groups: dict[int, dict[str, Any]] = {}
    for r in rows:
        if r["item_kind"] == "task" and r["field"] == "_seen" and r["upload_id"] == first_tasks:
            continue
        g = groups.setdefault(r["upload_id"], {"upload_id": r["upload_id"], "report_date": r["report_date"],
                                               "committed_at": r["committed_at"], "lines": []})
        who = task_names.get(r["item_id"], "task") if r["item_kind"] == "task" else None
        fallback = (EVENTS.get(r["field"], r["field"]), r["field"] == "_overview")
        label, is_date = _LABELS.get(r["field"], fallback)
        g["lines"].append({"task": who, "event": r["field"] in EVENTS and r["field"] != "_overview",
                           "label": label, "old": r["old_value"], "new": r["new_value"], "is_date": is_date})
    return sorted(groups.values(), key=lambda g: g["upload_id"], reverse=True)
