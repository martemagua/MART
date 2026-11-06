"""Reading the Insurer Capability Database (specs/insurer_capability.py).

A GLOBAL reference list, not per client: each upload replaces the stored
one as a whole. Values are cleaned as people typed them: "yes" / "No " /
"N0" -> 1 / 0, an unusual answer ("No (CI:Yes)") is kept as text beside it;
quota shares 0–1 -> a fraction, a text range ("80% to 99%") kept as text;
network names in one spelling ("MAXIS" / "Maxis" -> the commoner one).
"""

from __future__ import annotations

import hashlib
import io
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import openpyxl

from mart.ingestion import countries
from mart.ingestion.specs import insurer_capability as spec


class NotThisTracker(ValueError):
    pass


def _h(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().rstrip("?").strip().casefold()


_COLUMNS = {_h(k): v for k, v in spec.COLUMNS.items()}
_NETWORK = {_h(k) for k in spec.NETWORK_HEADERS}


@dataclass
class Parsed:
    sheet: str
    header_row: int
    rows: list[dict[str, Any]]
    networks: list[str]
    countries: int
    insurers: int
    skipped: int = 0
    unusual: dict[str, int] = field(default_factory=dict)


def yes_no(value: Any) -> tuple[int | None, str | None]:
    """-> (1 / 0 / None, the text when it isn't a plain yes or no)."""
    text = str(value or "").strip()
    low = text.casefold()
    if low in ("yes", "y"):
        return 1, None
    if low in ("no", "n", "n0"):
        return 0, None
    if not text:
        return None, None
    return (1 if low.startswith("y") else 0 if low.startswith("n") else None), text


def share(value: Any) -> tuple[float | None, str | None]:
    """A quota share -> (fraction 0–1, the text when it isn't a number)."""
    if isinstance(value, (int, float)):
        return round(float(value) / (100 if value > 1 else 1), 4), None
    text = str(value or "").strip()
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*%", text)
    if m:
        return round(float(m.group(1).replace(",", ".")) / 100, 4), None
    return None, text or None


def _header(ws) -> tuple[int, dict[int, str]] | None:
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=15, values_only=True), start=1):
        cols = {j: _COLUMNS[_h(v)] for j, v in enumerate(row) if _h(v) in _COLUMNS}
        if all(f in cols.values() for f in spec.REQUIRED):
            insurer = next(j for j, f in cols.items() if f == "insurer")
            net = next((j for j, v in enumerate(row) if _h(v) in _NETWORK), None)
            if net is None and insurer > 0 and insurer - 1 not in cols:
                net = insurer - 1           # the export leaves this header blank (a stray number)
            if net is None:
                return None
            cols[net] = "network"
            return i, cols
    return None


def _fold(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.casefold())


def _spellings(values) -> dict[str, str]:
    """folded spelling -> the commonest way it is written."""
    best: dict[str, str] = {}
    for name, _n in Counter(values).most_common():
        best.setdefault(_fold(name), name)
    return best


def key(row: dict[str, Any]) -> str:
    return "|".join([row["network"].casefold(), row["country_key"], (row["insurer"] or "").casefold(),
                     row["line"].casefold()])


def content_hash(row: dict[str, Any]) -> str:
    keep = {k: v for k, v in row.items() if k not in ("key", "content_hash")}
    return hashlib.sha256(json.dumps(keep, sort_keys=True, default=str).encode()).hexdigest()[:16]


def parse(data: bytes) -> Parsed:
    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    try:
        names = [spec.DETECT_SHEET] + [n for n in wb.sheetnames if n != spec.DETECT_SHEET]
        found = None
        for name in names:
            if name in wb.sheetnames:
                found = _header(wb[name])
                if found:
                    ws = wb[name]
                    break
        if not found:
            raise NotThisTracker("This doesn't look like the Insurer Capability Database (no sheet with "
                                 "“Country of cover issuance”, a network column, “Insurer name” and "
                                 "“Line of risk”).")
        header_row, cols = found
        raw: list[dict[str, Any]] = []
        skipped, unusual = 0, Counter()
        for values in ws.iter_rows(min_row=header_row + 1, values_only=True):
            cells = {f: values[j] if j < len(values) else None for j, f in cols.items()}
            network = str(cells.get("network") or "").strip()
            country = str(cells.get("country") or "").strip()
            line = str(cells.get("line") or "").strip()
            if not (network and country and line):
                skipped += int(any(v not in (None, "") for v in values))
                continue
            insurer = str(cells.get("insurer") or "").strip()
            row: dict[str, Any] = {
                "network": network, "region": str(cells.get("region") or "").strip() or None,
                "country": country, "country_key": countries.key(country),
                "insurer": None if insurer.casefold() in spec.NO_PARTNER else insurer,
                "line": line, "comments": str(cells.get("comments") or "").strip() or None}
            for f in spec.YES_NO:
                row[f], row[f + "_text"] = yes_no(cells.get(f))
                unusual[f] += int(row[f + "_text"] is not None)
            for f in spec.SHARES:
                row[f], row[f + "_text"] = share(cells.get(f))
            raw.append(row)
    finally:
        wb.close()
    # one spelling per network and per line of risk: the commonest
    # (MAXIS ×1323 / Maxis ×224 -> MAXIS; "Workers Compensation" ×1 -> "Worker's …")
    best = {f: _spellings(r[f] for r in raw) for f in ("network", "line")}
    rows: dict[str, dict[str, Any]] = {}
    for r in raw:
        r["network"] = best["network"][_fold(r["network"])]
        r["line"] = best["line"][_fold(r["line"])]
        r["key"] = key(r)
        r["content_hash"] = content_hash(r)
        rows[r["key"]] = r       # a repeat counts once (64 in the 2025 file, 62 identical)
    out = list(rows.values())
    return Parsed(ws.title, header_row, out, sorted(set(best["network"].values()), key=str.casefold),
                  len({r["country_key"] for r in out}),
                  len({(r["country_key"], r["insurer"]) for r in out if r["insurer"]}),
                  skipped, {k: v for k, v in unusual.items() if v})
