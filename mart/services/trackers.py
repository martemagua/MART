"""One adapter per BM+ tracker, so the upload pipeline (stage → preview →
commit) is the same for all of them.

An adapter knows how to read its export, which repository stores its items,
how to tell new / changed / unchanged, and what to do after a client's
items are saved. Adding a tracker = one adapter here + its ingestion module.
"""

from __future__ import annotations

import io
import json
from dataclasses import asdict, dataclass, field
from typing import Any

import openpyxl

from mart.ingestion import renewal_tracker as rt
from mart.ingestion import task_tracker as tt
from mart.ingestion import values as v
from mart.ingestion.sheet import norm
from mart.ingestion.specs import renewal_tracker as rt_spec
from mart.ingestion.specs import task_tracker as tt_spec
from mart.repository import clients_repo, history_repo, renewals_repo, tasks_repo
from mart.services import history, renewal_service


class UnknownFile(ValueError):
    pass


@dataclass
class Parsed:
    flavour: str
    title: str | None
    info: dict[str, Any]
    report_date: str | None
    report_time: str | None
    items: list[dict[str, Any]]                    # each has key, client_key, client_name
    extra: dict[str, Any] = field(default_factory=dict)   # tracker-specific preview facts


def _record(conn, kind: str, item_id: int, upload_id: int, outcome: str, changes) -> None:
    """History: first seen / back in the export, and what changed."""
    if outcome == "new":
        history_repo.add_event(conn, kind, [item_id], upload_id, "_seen")
        return
    if outcome == "returned":
        history_repo.add_event(conn, kind, [item_id], upload_id, "_back")
    if outcome in ("changed", "returned"):
        entries = changes()
        if entries:
            history_repo.add(conn, kind, item_id, upload_id, entries)


def _outcome(stored: dict[str, Any] | None, row: dict[str, Any], changed_text: bool = False) -> str:
    if stored is None:
        return "new"
    if not stored["in_latest_export"]:
        return "returned"
    if stored["content_hash"] != row["content_hash"] or changed_text:
        return "changed"
    return "unchanged"


class RenewalAdapter:
    tracker, label, noun, nouns = rt_spec.TRACKER, rt_spec.LABEL, "renewal", "renewals"
    export_filters = rt_spec.EXPORT_FILTERS
    flag_label = "without BM+ id"

    def recognises(self, sheets: list[str]) -> bool:
        return rt_spec.DETECT_SHEET in sheets

    def parse(self, data: bytes) -> Parsed:
        p = rt.parse(data)
        items = []
        for r in p.renewals:
            d = asdict(r)
            d.update(key=r.cycle_key, content_hash=r.content_hash, flagged=r.id_missing,
                     sheets=p.sheets_carried)
            items.append(d)
        return Parsed(p.flavour, p.title, p.info, p.report_date, p.report_time, items, {
            "sheets_read": p.sheets_read, "sheets_missing": p.sheets_missing,
            "skipped_no_client": p.skipped_no_client, "duplicates_merged": p.duplicates_merged,
            "no_id": p.no_id_count, "unmatched_detail_rows": p.unmatched_detail_rows})

    def context(self, rows: list[dict[str, Any]]) -> tuple[str, ...]:
        return rt.carried_streams(rows)

    def keep(self, conn, client_id, rows):
        return rows

    def not_news(self, conn, upload, keys) -> set[str]:
        return set()

    def stored(self, conn, keys):
        return renewals_repo.stored_by_key(conn, keys)

    def in_export(self, conn, client_ids):
        return renewals_repo.in_export_for_clients(conn, client_ids)

    def mark_left(self, conn, keys, upload_id):
        history_repo.add_event(conn, "renewal", history_repo.ids_by_key(conn, "renewals", "cycle_key", keys),
                               upload_id, "_left")
        renewals_repo.mark_left_export(conn, keys)

    @staticmethod
    def _sheets(row) -> tuple[str, ...]:
        # rows staged before 0.4.1 carry no list: they had every sheet they had
        return tuple(row["sheets"]) if "sheets" in row else tuple(rt_spec.DETAIL_SHEETS)

    def outcome(self, row, stored, ctx) -> str:
        if stored is None:
            return _outcome(stored, row)
        # compare as if the sheets this export lacks were unchanged
        merged = rt.merge_details(row.get("details") or {}, stored["details"], self._sheets(row))
        compared = {**row, "content_hash": rt.content_hash(row["bm"], merged)}
        return _outcome(stored, compared, rt.text_changed(row, stored["fields"], ctx))

    def save(self, conn, row, stored, client_id, upload_id, ctx, outcome) -> None:
        sheets, before = self._sheets(row), (stored or {}).get("details") or {}
        merged = rt.merge_details(row.get("details") or {}, before, sheets)
        row["details"] = {**merged, "_from": rt.details_from(before, merged, sheets, upload_id)}
        row["content_hash"] = rt.content_hash(row["bm"], merged)
        if stored is not None:
            rt.keep_streams_not_carried(row, stored["fields"], stored["bm"], ctx)
            rt.keep_links(row, stored["fields"])
        rid = renewals_repo.save(conn, row, client_id, upload_id,
                                 existing_id=stored["id"] if stored else None,
                                 touched=outcome != "unchanged")
        _record(conn, "renewal", rid, upload_id, outcome,
                lambda: history.renewal_changes(stored["fields"], row["fields"]))

    def after_client(self, conn, client_id, rows, ctx, upload) -> None:
        # "Overview as of": only an export that actually carries the overview counts.
        if rows and ({"overview_all", "overview_client_ready"} & set(ctx)):
            clients_repo.set_overview_as_of(conn, client_id, upload["report_date"], upload["id"])


class TaskAdapter:
    tracker, label, noun, nouns = tt_spec.TRACKER, tt_spec.LABEL, "task", "tasks"
    export_filters = tt_spec.EXPORT_FILTERS
    flag_label = ""

    def recognises(self, sheets: list[str]) -> bool:
        return tt_spec.DETECT_SHEET in sheets

    def parse(self, data: bytes) -> Parsed:
        p = tt.parse(data)
        items = []
        for t in p.tasks:
            d = asdict(t)
            d.update(content_hash=t.content_hash, flagged=False)
            items.append(d)
        return Parsed(p.flavour, p.title, p.info, p.report_date, p.report_time, items, {
            "sheets_read": {tt_spec.DETECT_SHEET: p.header_row}, "sheets_missing": [],
            "skipped_no_client": p.skipped_no_client, "skipped_no_id": p.skipped_no_id})

    def context(self, rows):
        return ()

    def keep(self, conn, client_id, rows):
        """Only renewal tasks (Renewal Workspace) of a renewal MART has
        (Martin, 04.11.2026: the renewals are the backbone; a task that can't
        be linked is discarded; implementation and contract tasks are not
        MART's concern)."""
        if client_id is None or not rows:
            return []
        index = renewal_service.renewal_index(renewals_repo.for_client(conn, client_id))
        return [r for r in rows if _wanted(index, r["fields"])]

    def not_news(self, conn, upload, keys) -> set[str]:
        """Stored tasks outside the export's own period: missing from it is
        not news. BM+ records the period on General Information."""
        info = upload.get("info") or {}
        column = _PERIOD_COLUMN.get(norm(info.get("Date Type")))
        start, end = v.to_date(info.get("Date: From")), v.to_date(info.get("Date: To"))
        if not (column and start and end and keys):
            return set()
        return {k for k, d in tasks_repo.dates(conn, sorted(keys), column).items()
                if not d or not start <= d <= end}

    def stored(self, conn, keys):
        return tasks_repo.stored_by_key(conn, keys)

    def in_export(self, conn, client_ids):
        return tasks_repo.in_export_for_clients(conn, client_ids)

    def mark_left(self, conn, keys, upload_id):
        history_repo.add_event(conn, "task", history_repo.ids_by_key(conn, "tasks", "task_key", keys),
                               upload_id, "_left")
        tasks_repo.mark_left_export(conn, keys)

    def outcome(self, row, stored, ctx) -> str:
        return _outcome(stored, row)

    def save(self, conn, row, stored, client_id, upload_id, ctx, outcome) -> None:
        before = json.loads(stored["fields_json"] or "{}") if stored else {}
        tid = tasks_repo.save(conn, row, client_id, upload_id, existing=stored,
                              touched=outcome != "unchanged")
        _record(conn, "task", tid, upload_id, outcome,
                lambda: history.task_changes(before, tasks_repo.merged_fields(row, stored)))

    def after_client(self, conn, client_id, rows, ctx, upload) -> None:
        # tasks loaded before 0.4.4 that belong to no renewal MART has
        index = renewal_service.renewal_index(renewals_repo.for_client(conn, client_id))
        orphans = [t["task_key"] for t in tasks_repo.for_client(conn, client_id)
                   if not _wanted(index, t)]
        tasks_repo.delete(conn, orphans)


def _wanted(index, task: dict[str, Any]) -> bool:
    return (norm(task.get("task_category")) == norm(tt_spec.RENEWAL_CATEGORY)
            and renewal_service.links_to_renewal(index, task))


# Task Tracker "Date Type" (General Information) -> the task date it filters
# on (the options BM+ offers, Martin 04.11.2026). "Not Specified" = no period.
_PERIOD_COLUMN = {norm("Renewal Date"): "review_date", norm("Task Start Date"): "start_date",
                  norm("Task Due Date"): "due_date", norm("Task Complete Date"): "completed_date"}

ADAPTERS = [RenewalAdapter(), TaskAdapter()]
BY_TRACKER = {a.tracker: a for a in ADAPTERS}
_OTHER = {"Benefit Details": "a Benefit Tracker (its upload comes in v2)"}


def detect(data: bytes):
    """The adapter for this file, or UnknownFile with a plain reason."""
    try:
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True)
        sheets = wb.sheetnames
        wb.close()
    except Exception as exc:  # noqa: BLE001
        raise UnknownFile(f"This file can't be read as an Excel workbook ({exc}).") from exc
    for a in ADAPTERS:
        if a.recognises(sheets):
            return a
    for sheet, what in _OTHER.items():
        if sheet in sheets:
            raise UnknownFile(f"This looks like {what}.")
    raise UnknownFile("This is neither a Renewal Tracker nor a Task Tracker export "
                      "(no “Renewal Overview” or “Task Summary” sheet).")
