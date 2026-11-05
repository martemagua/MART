"""The BM+ renewal overview: dated entries, and what the client hasn't been given.

BM+ writes two free-text overviews per renewal: **all** (internal, the
superset) and **client ready** (what may be shown to the client). Both are
dated entries starting with a `DD MMM YYYY:` header at the start of a line.
The colon and the line start are what tell an entry header from a date
mentioned inside an entry ("reply by 20 Aug 2026"). Entries are NOT in date
order.

What MART shows (the approach MAPT NEO proved, reimplemented here):

* the **timeline**: every entry of the full overview, newest first, each
  marked `internal_only` when it isn't (fully) in the client-ready overview;
* the **lines** missing from client-ready, compared line by line with
  spacing and capitals ignored, so formatting differences don't count;
* a compact **flag** for lists: missing client-ready version, how many lines
  are internal only, or no overview at all.

BM+ itself also writes "(not client ready)" into some entry headers; such an
entry counts as internal only even if its text appears in both.
"""

from __future__ import annotations

import difflib
import re
from datetime import date, datetime
from functools import lru_cache
from typing import Any

# An entry header STARTS a line. (MAPT only required the colon, so "quotes are
# expected by 15 Nov 2026: three insurers" inside a body split the entry.)
ENTRY_RE = re.compile(r"^[ \t]*(\d{1,2})[ \t]+([A-Za-z]{3,9})[ \t]+(\d{4})[ \t]*:", re.MULTILINE)
NOT_CLIENT_READY_RE = re.compile(r"\(\s*not\s+client[\s-]*ready\s*\)", re.IGNORECASE)
_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
_WS = re.compile(r"\s+")


def _iso(day: str, month_word: str, year: str) -> str | None:
    month = _MONTHS.get(month_word[:3].lower())
    if not month:
        return None
    try:
        return date(int(year), month, int(day)).isoformat()
    except ValueError:
        return None


def entries(text: Any) -> list[dict[str, str]]:
    """The dated entries in the order they appear: [{date, text}], text
    including its header line. Text before the first header is the preamble."""
    if not text:
        return []
    s = str(text)
    hits = [(m.start(), _iso(*m.groups())) for m in ENTRY_RE.finditer(s)]
    hits = [(pos, d) for pos, d in hits if d]
    out = []
    for i, (pos, d) in enumerate(hits):
        end = hits[i + 1][0] if i + 1 < len(hits) else len(s)
        out.append({"date": d, "text": s[pos:end].strip()})
    return out


def preamble(text: Any) -> str | None:
    """Whatever stands before the first dated entry (a heading, a standing note)."""
    if not text:
        return None
    s = str(text)
    m = ENTRY_RE.search(s)
    head = (s[: m.start()] if m else s).strip()
    return head or None


def latest_date(*texts: Any) -> str | None:
    """Newest entry date across the given overview texts."""
    return _latest_date(*(t if isinstance(t, str) or t is None else str(t) for t in texts))


# The texts only change with an upload, but every page reads them: both
# verdicts are cached by the texts themselves (bounded, so memory stays small).
@lru_cache(maxsize=8192)
def _latest_date(*texts: str | None) -> str | None:
    dates = [e["date"] for t in texts for e in entries(t)]
    return max(dates) if dates else None


def _lines(text: Any) -> list[str]:
    return [ln.strip() for ln in str(text or "").splitlines() if ln.strip()]


def _norm(line: str) -> str:
    return _WS.sub(" ", line).strip().lower()


def _internal_lines(all_lines: list[str], cr_lines: list[str]) -> list[bool]:
    """Per line of the full overview: is it missing from client-ready?"""
    if not cr_lines:
        return [True] * len(all_lines)
    matcher = difflib.SequenceMatcher(a=[_norm(x) for x in cr_lines],
                                      b=[_norm(x) for x in all_lines], autojunk=False)
    internal = [False] * len(all_lines)
    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            for j in range(j1, j2):
                internal[j] = True
    return internal


def timeline(all_text: Any, client_ready_text: Any, today: date | None = None) -> dict[str, Any]:
    """Everything a renewal's overview section needs.

    {
      "entries": [{date, text, internal_only, marked_not_ready, body: [{text, internal}]}]
                  newest first; `body` = the entry's lines without its date header,
      "preamble": str | None,
      "latest": "YYYY-MM-DD" | None,  "age_days": int | None,
      "internal_entries": int, "internal_lines": int, "total_lines": int,
      "has_all": bool, "has_client_ready": bool,
    }

    Only the client-ready overview present (no "all")? Then it is shown as is,
    nothing marked: there is nothing it could be missing.
    """
    has_all, has_cr = bool(_lines(all_text)), bool(_lines(client_ready_text))
    base = all_text if has_all else client_ready_text
    cr_lines = _lines(client_ready_text) if has_all else _lines(base)
    cr_norm = [_norm(x) for x in cr_lines]
    out_entries = []
    internal_total = lines_total = 0
    for e in entries(base):
        lines = _lines(e["text"])
        flags = _internal_lines(lines, cr_lines) if has_all else [False] * len(lines)
        # SequenceMatcher works on the whole text; per entry, a line is also
        # "in client-ready" when it appears there anywhere (entries move).
        flags = [f and _norm(ln) not in cr_norm for ln, f in zip(lines, flags, strict=True)]
        marked = bool(NOT_CLIENT_READY_RE.search(lines[0])) if lines else False
        internal_only = has_all and (marked or any(flags))
        internal_total += sum(flags)
        lines_total += len(lines)
        body = []
        for i, (ln, f) in enumerate(zip(lines, flags, strict=True)):
            text = ln
            if i == 0:                      # the header line: date (and a marker) shown apart
                text = NOT_CLIENT_READY_RE.sub("", ENTRY_RE.sub("", ln, count=1)).strip()
            if text:
                body.append({"text": text, "internal": f})
        out_entries.append({"date": e["date"], "text": e["text"], "internal_only": internal_only,
                            "marked_not_ready": marked, "body": body})
    out_entries.sort(key=lambda x: x["date"], reverse=True)
    latest = out_entries[0]["date"] if out_entries else None
    age = ((today or date.today()) - datetime.fromisoformat(latest).date()).days if latest else None
    return {
        "entries": out_entries,
        "preamble": preamble(base),
        "latest": latest, "age_days": age,
        "internal_entries": sum(1 for e in out_entries if e["internal_only"]),
        "internal_lines": internal_total, "total_lines": lines_total,
        "has_all": has_all, "has_client_ready": has_cr,
    }


def flag(all_text: Any, client_ready_text: Any) -> dict[str, Any]:
    """Compact verdict for lists: {state, internal_entries, latest}.

    state: "empty"      no overview at all (new renewal, or a forgotten one)
           "no_cr"      a full overview, but no client-ready version
           "gaps"       client-ready misses some entries
           "ok"         everything in the full overview is client-ready
    """
    state, internal, n, latest = _flag(*(t if isinstance(t, str) or t is None else str(t)
                                         for t in (all_text, client_ready_text)))
    age = (date.today() - datetime.fromisoformat(latest).date()).days if latest else None
    return {"state": state, "internal_entries": internal, "entries": n, "latest": latest, "age_days": age}


@lru_cache(maxsize=8192)
def _flag(all_text: str | None, client_ready_text: str | None) -> tuple[str, int, int, str | None]:
    """The verdict without today's date in it, so it can be cached."""
    t = timeline(all_text, client_ready_text)
    if not t["has_all"] and not t["has_client_ready"]:
        state = "empty"
    elif t["has_all"] and not t["has_client_ready"]:
        state = "no_cr"
    elif t["internal_entries"]:
        state = "gaps"
    else:
        state = "ok"
    return state, t["internal_entries"], len(t["entries"]), t["latest"]
