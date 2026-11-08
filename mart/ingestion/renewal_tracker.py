"""Renewal Tracker export -> renewals, ready to preview and commit.

One Overview row = one renewal cycle (several lines of coverage share one
row). The renewal's KEY, in order of preference:

    1. BM+'s per-cycle id                         (same in both flavours)
    2. "policy:<stable id>:<renewal date>"        when only the stable id is there
    3. "name:<client|country|entity|policy|date>" when BM+ gave no id at all
                                                  ("Transitioned" renewals) -> flagged

Two rows can't share a key: an EXACT duplicate row is merged (and counted);
a different row with the same key gets "#2", "#3", … in export order.
Renewals are never merged by mistake. The name key stays short on purpose
(no insurer, no premium): a key that changed whenever BM+ updated a field
would make the same renewal look new at the next upload.

Rows without a client (seen in cross-client demo exports) can't belong to
anyone and are skipped, and the preview says how many.
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
from mart.ingestion.ids import bm_link, renewal_tracker_ids
from mart.ingestion.sheet import Col, key_value_sheet, norm, read_sheet
from mart.ingestion.specs import renewal_tracker as spec

CROSS_CLIENT, CLIENT = "cross_client", "client"


class NotThisTracker(ValueError):
    """The file is not a Renewal Tracker (or is missing what MART needs)."""


@dataclass
class RenewalRow:
    cycle_key: str
    client_name: str
    client_key: str
    excel_row: int
    ids: dict[str, str | None]
    fields: dict[str, Any]          # cleaned, promoted fields
    bm: dict[str, Any]              # every non-empty Overview cell
    id_missing: bool = False
    details: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        return content_hash(self.bm, self.details)


@dataclass
class ParsedTracker:
    flavour: str
    title: str | None
    info: dict[str, Any]
    renewals: list[RenewalRow]
    sheets_read: dict[str, int]                   # sheet -> header row
    sheets_missing: list[str]
    skipped_no_client: int = 0
    duplicates_merged: int = 0
    unmatched_detail_rows: int = 0

    @property
    def sheets_carried(self) -> tuple[str, ...]:
        """The detail sheets (keys of spec.DETAIL_SHEETS) this export has."""
        return tuple(k for k, (name, _) in spec.DETAIL_SHEETS.items() if name in self.sheets_read)

    @property
    def no_id_count(self) -> int:
        return sum(1 for r in self.renewals if r.id_missing)

    @property
    def report_date(self) -> str | None:
        return v.to_date(self.info.get("Report Date"))

    @property
    def report_time(self) -> str | None:
        t = self.info.get("Report Time")
        return str(t) if t else None


# ---------------------------------------------------------------------------
# Comparing an export with what MART has: content, not spelling
# ---------------------------------------------------------------------------
_NOT_CONTENT = {norm(h) for h in (*spec.IDENTITY_HEADERS, *spec.TEXT_STREAMS.values())}


def _header_key(full_key: str) -> str:
    return norm(full_key.split(" › ")[-1])


def currency_code(text: Any) -> str | None:
    """General Information's reporting currency, "US Dollar (USD)" -> "USD";
    a bare code passes; anything else -> None."""
    t = str(text or "").strip()
    m = re.search(r"\(([A-Z]{3})\)\s*$", t) or re.fullmatch(r"([A-Z]{3})", t)
    return m.group(1) if m else None


def insurer_or_provider(insurer: str | None, provider: str | None) -> str | None:
    """BM+'s "Insurer Not Found" gives way to the Provider column, when filled."""
    if insurer and insurer.strip().casefold() == spec.INSURER_NOT_FOUND.casefold() and provider:
        return provider
    return insurer


def _neutral(row: dict[str, Any]) -> dict[str, Any]:
    """A row without the cells that differ only by export flavour (ids, client
    name, the text streams) and with spelling-proof keys."""
    return {norm(k): val for k, val in row.items() if _header_key(k) not in _NOT_CONTENT}


def content_hash(bm: dict[str, Any], details: dict[str, list[dict[str, Any]]]) -> str:
    """Same for the same data from either flavour. The text streams are
    compared separately (text_changed), because each flavour carries others."""
    payload = json.dumps({"bm": _neutral(bm),
                          "details": {s: [_neutral(r) for r in rows] for s, rows in sorted(details.items())
                                      if not s.startswith("_")}},
                         sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def merge_details(new: dict[str, list[dict[str, Any]]], stored: dict[str, Any],
                  carried: tuple[str, ...] | list[str]) -> dict[str, list[dict[str, Any]]]:
    """The detail sheets as they stand after this export: a sheet the export
    has is the truth (no rows = none any more); a sheet it doesn't have keeps
    what MART already had. Trackers can be created without some sheets, and a
    missing sheet is not news."""
    out = {}
    for key in spec.DETAIL_SHEETS:
        rows = new.get(key) if key in carried else stored.get(key)
        if rows:
            out[key] = rows
    return out


def details_from(stored: dict[str, Any], merged: dict[str, Any], carried, upload_id: int) -> dict[str, int]:
    """Per detail sheet: the upload it was last read from."""
    before = stored.get("_from") or {}
    return {k: (upload_id if k in carried else before[k]) for k in merged if k in carried or k in before}


LINK_FIELDS = ("bm_url", "bm_policy_url")


def keep_links(row: dict[str, Any], stored_fields: dict[str, Any]) -> None:
    """Only the cross-client export writes the BM+ links; a single-client
    export after it must not lose them."""
    for f in LINK_FIELDS:
        if not row["fields"].get(f) and stored_fields.get(f):
            row["fields"][f] = stored_fields[f]


def carried_streams(rows: list[dict[str, Any]]) -> tuple[str, ...]:
    """The text streams this export actually fills: those with text in at least
    one renewal (see specs.renewal_tracker.TEXT_STREAMS)."""
    return tuple(f for f in spec.TEXT_STREAMS
                 if any((r["fields"].get(f) or "").strip() for r in rows))


def text_changed(row: dict[str, Any], stored_fields: dict[str, Any],
                 carried: tuple[str, ...]) -> bool:
    """Did a text stream this export carries change?"""
    return any((row["fields"].get(f) or None) != (stored_fields.get(f) or None) for f in carried)


def keep_streams_not_carried(row: dict[str, Any], stored_fields: dict[str, Any],
                             stored_bm: dict[str, Any], carried: tuple[str, ...]) -> dict[str, Any]:
    """An export that leaves a text stream empty everywhere must not blank the
    text an earlier export brought in: streams it doesn't carry keep the stored
    text, in the fields and in the full row copy."""
    for f, header in spec.TEXT_STREAMS.items():
        if f in carried:
            continue
        row["fields"][f] = stored_fields.get(f)
        h = norm(header)
        for k in [k for k in row["bm"] if _header_key(k) == h]:
            del row["bm"][k]
        row["bm"].update({k: val for k, val in stored_bm.items() if _header_key(k) == h})
    return row


def _cycle_key(ids, client_key: str, country: Any, entity: Any, policy_name: Any,
               renewal_date: str | None) -> tuple[str, bool]:
    if ids.cycle_id:
        return ids.cycle_id, False
    if ids.expiring_policy_id:
        return f"policy:{ids.expiring_policy_id}:{renewal_date or '?'}", False
    parts = [client_key] + [v.client_key(str(x or "")) for x in (country, entity, policy_name)]
    return "name:" + "|".join(parts + [renewal_date or "?"]), True


def _client_of(sheet_value: Any, flavour: str, title: str | None) -> str | None:
    if flavour == CLIENT:
        return title
    return v.clean_text(sheet_value)


_DETAIL_EXTRA = [Col("country", "Country"), Col("entity", "Entity"),
                 Col("renewal_date", "Annual Renewal/Review Date")]


def parse(data: bytes) -> ParsedTracker:
    try:
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001  (any unreadable file gets the same answer)
        raise NotThisTracker(f"This file can't be read as an Excel workbook ({exc}).") from exc
    try:
        names = wb.sheetnames
        if spec.DETECT_SHEET not in names:
            for sheet, what in spec.OTHER_TRACKERS.items():
                if sheet in names:
                    raise NotThisTracker(f"This looks like {what}, not a Renewal Tracker.")
            raise NotThisTracker(f"No “{spec.DETECT_SHEET}” sheet: this is not a Renewal Tracker export.")

        title, info = (key_value_sheet(wb[spec.INFO_SHEET]) if spec.INFO_SHEET in names
                       else (None, {}))
        overview = read_sheet(wb[spec.DETECT_SHEET], spec.OVERVIEW)
        if overview.missing:
            raise NotThisTracker("The Renewal Overview sheet is missing these columns: "
                                 + ", ".join(overview.missing))
        flavour = CROSS_CLIENT if "client_name" in overview.mapping else CLIENT
        client_title = None
        if flavour == CLIENT:
            client_title = v.clean_text(title)
            if not client_title or client_title.lower() == spec.LABEL.lower():
                raise NotThisTracker("This client-specific export doesn't say which client it "
                                     "is for (General Information, cell A1).")

        parsed = ParsedTracker(flavour, title, info, [], {spec.DETECT_SHEET: overview.header_row}, [])
        by_key: dict[str, RenewalRow] = {}
        for excel_row, cells in overview.rows:
            client = _client_of(overview.value(cells, "client_name"), flavour, client_title)
            if not client:
                parsed.skipped_no_client += 1
                continue
            row = _overview_row(overview, cells, excel_row, client)
            base, n = row.cycle_key, 2
            while row.cycle_key in by_key:
                if by_key[row.cycle_key].bm == row.bm:
                    break
                row.cycle_key, n = f"{base}#{n}", n + 1
            if row.cycle_key in by_key:          # exact duplicate row
                parsed.duplicates_merged += 1
                continue
            by_key[row.cycle_key] = row

        for key, (sheet_name, cols) in spec.DETAIL_SHEETS.items():
            if sheet_name not in names:
                parsed.sheets_missing.append(sheet_name)
                continue
            sheet = read_sheet(wb[sheet_name], cols + _DETAIL_EXTRA)
            if sheet.missing:
                parsed.sheets_missing.append(sheet_name)
                continue
            parsed.sheets_read[sheet_name] = sheet.header_row
            for _excel_row, cells in sheet.rows:
                client = _client_of(sheet.value(cells, "client_name"), flavour, client_title)
                if not client:
                    continue
                ids = renewal_tracker_ids(v.clean_text(sheet.value(cells, "policy_ref")),
                                          v.clean_text(sheet.value(cells, "renewal_ref")))
                ckey, id_missing = _cycle_key(ids, v.client_key(client), sheet.value(cells, "country"),
                                              sheet.value(cells, "entity"), sheet.value(cells, "policy_name"),
                                              v.to_date(sheet.value(cells, "renewal_date")))
                if id_missing:
                    # No id: the name key can't tell same-named renewals apart,
                    # so detail rows are only attached when the match is unique.
                    matches = [k for k in by_key if k == ckey or k.startswith(ckey + "#")]
                    if len(matches) != 1:
                        parsed.unmatched_detail_rows += 1
                        continue
                    ckey = matches[0]
                target = by_key.get(ckey)
                if target is None:
                    parsed.unmatched_detail_rows += 1
                    continue
                target.details.setdefault(key, []).append(sheet.full_row(cells))
        parsed.renewals = list(by_key.values())
        return parsed
    finally:
        wb.close()


def _overview_row(sheet, cells: list[Any], excel_row: int, client: str) -> RenewalRow:
    f: dict[str, Any] = {}
    for col in spec.OVERVIEW:
        raw = sheet.value(cells, col.field)
        if col.field in spec.DATE_FIELDS:
            f[col.field] = v.to_date(raw)
        elif col.field in spec.PERSON_FIELDS:
            f[col.field] = v.person_name(raw)
        elif col.field == "n_locs":
            f[col.field] = v.to_int(raw)
        else:
            f[col.field] = v.clean_text(raw)
    f["insurer"] = insurer_or_provider(f.get("insurer"), f.get("provider"))
    f["insurer_upcoming"] = insurer_or_provider(f.get("insurer_upcoming"), f.get("provider_upcoming"))
    f["non_expiring"] = v.is_non_expiring(sheet.value(cells, "end_date"))
    f["product_groups"] = v.product_groups(f.get("lines_of_coverage"))
    f["bm_url"] = bm_link(f.get("renewal_ref"))          # cross-client exports only
    f["bm_policy_url"] = bm_link(f.get("policy_ref"))
    ids = renewal_tracker_ids(f.get("policy_ref"), f.get("renewal_ref"))
    ckey = v.client_key(client)
    cycle_key, id_missing = _cycle_key(ids, ckey, f.get("country"), f.get("entity"),
                                       f.get("policy_name"), f.get("renewal_date"))
    return RenewalRow(
        cycle_key=cycle_key, client_name=client, client_key=ckey, excel_row=excel_row,
        ids={"cycle_id": ids.cycle_id, "expiring_policy_id": ids.expiring_policy_id,
             "bm_renewal_id": ids.bm_renewal_id, "bm_client_id": ids.bm_client_id},
        fields=f, bm=sheet.full_row(cells), id_missing=id_missing,
    )
