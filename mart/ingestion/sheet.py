"""Reading one BM+ sheet: find the header row, label every column with its
section, map spec fields to columns, and keep a full copy of each row.

BM+ layout (TRACKER_MAP.md §2): a few title rows, then a SECTION row with
merged group labels ("Premium Information (Expiring Policy Period)"), then
the HEADER row, then data. The header row moves (4, 5 or 6) between sheets
and flavours, so it is found by looking for the spec's required headers.

Headers repeat across sections ("Insurer" for expiring and upcoming) and
even inside one section (two "Email" columns). A spec column can therefore
name a `section` (substring of the section label) and/or an `after` header
(the first matching column to the right of that header).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from mart.ingestion.values import json_value

_NORM = re.compile(r"[^a-z0-9]+")
HEADER_SCAN_ROWS = 15


def norm(text: Any) -> str:
    """Header/section matching key: case, spacing, punctuation and Excel's
    `_x000D_` line-break artefacts ignored."""
    s = str(text or "").replace("_x000D_", "").replace("_x000d_", "").lower()
    return _NORM.sub("", s)


@dataclass(frozen=True)
class Col:
    field: str
    header: str
    section: str | None = None   # substring of the section label
    after: str | None = None     # header this column follows (to its right)
    required: bool = False
    aliases: tuple[str, ...] = ()  # other names BM+ uses for the same column

    @property
    def names(self) -> tuple[str, ...]:
        return (self.header, *self.aliases)


@dataclass
class SheetData:
    name: str
    header_row: int                       # 1-based Excel row
    columns: list[tuple[str, str]]        # (section, header) per column index
    mapping: dict[str, int]               # spec field -> column index
    rows: list[tuple[int, list[Any]]]     # (Excel row, cells)
    missing: list[str] = field(default_factory=list)  # required headers not found

    def value(self, cells: list[Any], fld: str) -> Any:
        idx = self.mapping.get(fld)
        return cells[idx] if idx is not None and idx < len(cells) else None

    def full_row(self, cells: list[Any]) -> dict[str, Any]:
        """Every non-empty cell, keyed 'Section › Header' (a repeat inside the
        same section gets ' (2)', ' (3)'), so nothing in the export is lost."""
        out: dict[str, Any] = {}
        for i, (section, header) in enumerate(self.columns):
            if i >= len(cells) or not header:
                continue
            v = json_value(cells[i])
            if v in (None, ""):
                continue
            key = f"{section} › {header}" if section else header
            base, n = key, 2
            while key in out:
                key, n = f"{base} ({n})", n + 1
            out[key] = v
        return out


def _find_header_row(raw: list[tuple[Any, ...]], required: list[Col]) -> int | None:
    """The first row holding every required column (under any of its names)."""
    for i, row in enumerate(raw[:HEADER_SCAN_ROWS]):
        present = {norm(v) for v in row if v not in (None, "")}
        if all(any(norm(n) in present for n in c.names) for c in required):
            return i
    return None


def _sections(raw: list[tuple[Any, ...]], header_idx: int, width: int) -> list[str]:
    """Section label per column: the row just above the header, merged labels
    carried to the right."""
    if header_idx == 0:
        return [""] * width
    above = list(raw[header_idx - 1]) + [None] * width
    out, current = [], ""
    for v in above[:width]:
        if v not in (None, ""):
            current = " ".join(str(v).split())
        out.append(current)
    return out


def read_sheet(ws: Any, spec: list[Col]) -> SheetData:
    raw = list(ws.iter_rows(values_only=True))
    required = [c for c in spec if c.required]
    hidx = _find_header_row(raw, required)
    if hidx is None:
        return SheetData(ws.title, 0, [], {}, [], missing=[c.header for c in required])

    headers = [" ".join(str(v).replace("_x000D_", "").replace("_x000d_", "").split())
               if v not in (None, "") else "" for v in raw[hidx]]
    width = len(headers)
    sections = _sections(raw, hidx, width)
    normed = [norm(h) for h in headers]

    mapping: dict[str, int] = {}
    for col in spec:
        targets = {norm(n) for n in col.names}
        start = 0
        if col.after:
            after = norm(col.after)
            pos = next((i for i, h in enumerate(normed) if h == after), None)
            if pos is None:
                continue
            start = pos + 1
        for i in range(start, width):
            if normed[i] not in targets:
                continue
            if col.section and norm(col.section) not in norm(sections[i]):
                continue
            mapping[col.field] = i
            break

    rows = []
    for offset, row in enumerate(raw[hidx + 1:], start=hidx + 2):
        cells = list(row)
        if any(v not in (None, "") for v in cells):
            rows.append((offset, cells))
    missing = [c.header for c in spec if c.required and c.field not in mapping]
    return SheetData(ws.title, hidx + 1, list(zip(sections, headers, strict=True)), mapping, rows, missing)


def key_value_sheet(ws: Any, max_rows: int = 40) -> tuple[str | None, dict[str, Any]]:
    """BM+'s 'General Information' sheet: a title in A1 and label/value pairs
    in columns A/B. Returns (first title cell, {label: value})."""
    title = None
    pairs: dict[str, Any] = {}
    for row in ws.iter_rows(max_row=max_rows, max_col=2, values_only=True):
        label, value = (row + (None, None))[:2]
        if label in (None, ""):
            continue
        label = " ".join(str(label).split())
        if title is None:
            title = label
        if value not in (None, ""):
            pairs[label.rstrip(":")] = json_value(value)
    return title, pairs


def lookup(row: dict[str, Any], header: str, section: str | None = None) -> Any:
    """A value from a full row copy ('Section › Header' keys, repeats suffixed
    ' (2)'), by header and optional section substring, spelling-proof."""
    want, sect = norm(header), norm(section) if section else None
    for key, value in row.items():
        sec, _, head = key.rpartition(" › ")
        head = re.sub(r" \(\d+\)$", "", head)
        if norm(head) == want and (sect is None or sect in norm(sec)):
            return value
    return None


def section_items(row: dict[str, Any], section: str) -> list[tuple[str, Any]]:
    """(header, value) pairs of one section of a full row copy, in order."""
    sect = norm(section)
    return [(key.rpartition(" › ")[2], value) for key, value in row.items()
            if sect in norm(key.rpartition(" › ")[0])]
