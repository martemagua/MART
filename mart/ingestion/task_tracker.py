"""Task Tracker export -> BM+ tasks, ready to preview and commit.

One row = one BM+ task. Its key is BM+'s task id (the `taskId` of the Task
ID link, or the last id in it). A task links to its renewal through
`Policy ID`, which is the Renewal Tracker's per-cycle id; failing that,
through the stable Expiring Policy Unique ID plus the renewal date.

The client-specific export holds the client's full task history (back to
2021, completed tasks included); the cross-client one is filtered by renewal
date. Both are snapshots "as filtered", so a task missing from a later
export is only marked "no longer in the export", never deleted.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
from dataclasses import dataclass, field
from typing import Any

import openpyxl

from mart.ingestion import values as v
from mart.ingestion.sheet import key_value_sheet, read_sheet
from mart.ingestion.specs import task_tracker as spec

CROSS_CLIENT, CLIENT = "cross_client", "client"
_ID = re.compile(r"[0-9a-f]{24}")
# Renewal tasks carry a 24-hex taskId; implementation tasks (Appointment,
# Upload Local Documents, Review ROR, Update Policies) a dashed UUID.
_TASK_PARAM = re.compile(r"taskId=([0-9A-Za-z-]{8,})")
_RENEWAL_URL = re.compile(r"/renewals/(?:v2/)?([0-9a-f]{24})")
_CLIENT_URL = re.compile(r"/client/([0-9a-f]{24})")


class NotThisTracker(ValueError):
    pass


@dataclass
class TaskRow:
    key: str
    client_name: str
    client_key: str
    excel_row: int
    fields: dict[str, Any]
    bm: dict[str, Any]
    ids: dict[str, str | None] = field(default_factory=dict)
    carried: tuple[str, ...] = ()      # fields whose column this export has

    @property
    def content_hash(self) -> str:
        """Same for the same task from either flavour (spec.COMPARED)."""
        payload = {k: self.fields.get(k) for k in spec.COMPARED}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str)
                              .encode("utf-8")).hexdigest()[:16]


@dataclass
class ParsedTasks:
    flavour: str
    title: str | None
    info: dict[str, Any]
    tasks: list[TaskRow]
    header_row: int
    skipped_no_client: int = 0
    skipped_no_id: int = 0

    @property
    def report_date(self) -> str | None:
        return v.to_date(self.info.get("Report Date"))

    @property
    def report_time(self) -> str | None:
        t = self.info.get("Report Time")
        return str(t) if t else None


def _task_id(cell: str | None) -> str | None:
    if not cell:
        return None
    m = _TASK_PARAM.search(cell)
    if m:
        return m.group(1)
    ids = _ID.findall(cell)
    return ids[-1] if ids else None


def _bare_or_first(cell: str | None, url_re: re.Pattern[str]) -> str | None:
    if not cell:
        return None
    m = url_re.search(cell)
    if m:
        return m.group(1)
    ids = _ID.findall(cell)
    return ids[0] if ids else None


def parse(data: bytes) -> ParsedTasks:
    try:
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001
        raise NotThisTracker(f"This file can't be read as an Excel workbook ({exc}).") from exc
    try:
        if spec.DETECT_SHEET not in wb.sheetnames:
            raise NotThisTracker(f"No “{spec.DETECT_SHEET}” sheet: this is not a Task Tracker export.")
        title, info = (key_value_sheet(wb[spec.INFO_SHEET]) if spec.INFO_SHEET in wb.sheetnames
                       else (None, {}))
        sheet = read_sheet(wb[spec.DETECT_SHEET], spec.COLUMNS)
        if sheet.missing:
            raise NotThisTracker("The Task Summary sheet is missing these columns: "
                                 + ", ".join(sheet.missing))
        flavour = CROSS_CLIENT if "client_name" in sheet.mapping else CLIENT
        client_title = v.clean_text(title) if flavour == CLIENT else None
        if flavour == CLIENT and (not client_title or client_title.lower() == spec.LABEL.lower()):
            raise NotThisTracker("This client-specific export doesn't say which client it is for "
                                 "(General Information, cell A1).")
        parsed = ParsedTasks(flavour, title, info, [], sheet.header_row)
        carried = tuple(c.field for c in spec.COLUMNS if c.field in sheet.mapping)
        seen: set[str] = set()
        for excel_row, cells in sheet.rows:
            client = client_title or v.clean_text(sheet.value(cells, "client_name"))
            if not client:
                parsed.skipped_no_client += 1
                continue
            f = _fields(sheet, cells)
            key = _task_id(f.get("task_ref"))
            if not key or key in seen:
                parsed.skipped_no_id += 1
                continue
            seen.add(key)
            ids = {"bm_renewal_id": _bare_or_first(f.get("renewal_ref"), _RENEWAL_URL),
                   "bm_client_id": next(iter(_CLIENT_URL.findall(f.get("task_ref") or "")), None)}
            parsed.tasks.append(TaskRow(key, client, v.client_key(client), excel_row, f,
                                        sheet.full_row(cells), ids, carried))
        return parsed
    finally:
        wb.close()


def _fields(sheet, cells: list[Any]) -> dict[str, Any]:
    f: dict[str, Any] = {}
    for col in spec.COLUMNS:
        raw = sheet.value(cells, col.field)
        if col.field in spec.DATE_FIELDS:
            f[col.field] = v.to_date(raw)
        elif col.field in spec.INT_FIELDS:
            f[col.field] = v.to_int(raw)
        elif col.field in spec.PERSON_FIELDS:
            f[col.field] = v.person_name(raw)
        else:
            f[col.field] = v.clean_text(raw)
    for idf in ("expiring_policy_id", "policy_id"):      # bare ids; guard against "undefined"
        ids = _ID.findall(f.get(idf) or "")
        f[idf] = ids[0] if ids else None
    if f.get("review_approved_by") in ("N/A",):
        f["review_approved_by"] = None
    return f


def stage_state(status: str | None) -> tuple[str, bool]:
    """BM+ task status -> (state, past_due). state: todo | doing | review | done.
    BM+ already did the date maths: trust "Past Due" rather than recompute."""
    raw = (status or "").strip().lower()
    past_due = "past due" in raw
    base = raw.replace(", past due", "").replace("past due", "").strip(" ,")
    state = {"not started": "todo", "in progress": "doing", "global review pending": "review",
             "completed": "done"}.get(base, "todo")
    return state, past_due
