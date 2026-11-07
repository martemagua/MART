"""Plan design changes (schema migration 18): USER data, never touched by
uploads. One change covers one or more renewals (`design_change_renewals`);
a line of BM+'s text Martin dismissed for a renewal sits in
`design_change_dismissed`. All SQL for them. (`plan_changes`, migration 13,
is the first shape: carried over into these tables, no longer read.)"""

from __future__ import annotations

import sqlite3
from typing import Any

_COLS = "c.id, c.client_id, c.title, c.detail, c.outcome, c.reason, c.decided_on, c.cost_amount, " \
        "c.cost_unit, c.source, c.bm_line, c.created_at, c.updated_at"


def _with_covers(conn: sqlite3.Connection, rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    out = [dict(r) for r in rows]
    if not out:
        return out
    marks = ",".join("?" * len(out))
    covers: dict[int, list[int]] = {}
    for r in conn.execute(f"""SELECT change_id, renewal_id FROM design_change_renewals
                               WHERE change_id IN ({marks}) ORDER BY renewal_id""", [c["id"] for c in out]):
        covers.setdefault(r["change_id"], []).append(r["renewal_id"])
    for c in out:
        c["renewal_ids"] = covers.get(c["id"], [])
    return out


def for_client(conn: sqlite3.Connection, client_id: int) -> list[dict[str, Any]]:
    """Every change of the client, each with the renewals it covers (two queries)."""
    return _with_covers(conn, conn.execute(
        f"SELECT {_COLS} FROM design_changes c WHERE c.client_id = ? ORDER BY c.id", (client_id,)).fetchall())


def for_renewals(conn: sqlite3.Connection, renewal_ids: list[int]) -> list[dict[str, Any]]:
    """The changes covering any of these renewals."""
    if not renewal_ids:
        return []
    marks = ",".join("?" * len(renewal_ids))
    return _with_covers(conn, conn.execute(
        f"""SELECT DISTINCT {_COLS} FROM design_changes c JOIN design_change_renewals l ON l.change_id = c.id
             WHERE l.renewal_id IN ({marks}) ORDER BY c.id""", list(renewal_ids)).fetchall())


def get(conn: sqlite3.Connection, change_id: int) -> dict[str, Any] | None:
    rows = _with_covers(conn, conn.execute(f"SELECT {_COLS} FROM design_changes c WHERE c.id = ?",
                                           (change_id,)).fetchall())
    return rows[0] if rows else None


def add(conn: sqlite3.Connection, client_id: int, renewal_ids: list[int], title: str, detail: str | None,
        outcome: str = "open", reason: str | None = None, decided_on: str | None = None,
        cost_amount: float | None = None, cost_unit: str | None = None, source: str = "you",
        bm_line: str | None = None) -> int:
    cur = conn.execute(
        """INSERT INTO design_changes (client_id, title, detail, outcome, reason, decided_on, cost_amount,
                                       cost_unit, source, bm_line)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (client_id, title, detail, outcome, reason, decided_on, cost_amount, cost_unit, source, bm_line))
    cid = int(cur.lastrowid)
    set_covers(conn, cid, renewal_ids)
    return cid


def update(conn: sqlite3.Connection, change_id: int, title: str, detail: str | None,
           cost_amount: float | None, cost_unit: str | None) -> None:
    conn.execute("""UPDATE design_changes SET title = ?, detail = ?, cost_amount = ?, cost_unit = ?,
                           updated_at = datetime('now') WHERE id = ?""",
                 (title, detail, cost_amount, cost_unit, change_id))


def set_covers(conn: sqlite3.Connection, change_id: int, renewal_ids: list[int]) -> None:
    conn.execute("DELETE FROM design_change_renewals WHERE change_id = ?", (change_id,))
    conn.executemany("INSERT INTO design_change_renewals (change_id, renewal_id) VALUES (?, ?)",
                     [(change_id, rid) for rid in dict.fromkeys(renewal_ids)])


def set_outcome(conn: sqlite3.Connection, change_id: int, outcome: str, reason: str | None,
                decided_on: str | None) -> None:
    conn.execute("""UPDATE design_changes SET outcome = ?, reason = ?, decided_on = ?,
                           updated_at = datetime('now') WHERE id = ?""",
                 (outcome, reason, decided_on, change_id))


def delete(conn: sqlite3.Connection, change_id: int) -> None:
    conn.execute("DELETE FROM design_change_renewals WHERE change_id = ?", (change_id,))
    conn.execute("DELETE FROM design_changes WHERE id = ?", (change_id,))


def dismissed(conn: sqlite3.Connection, renewal_ids: list[int]) -> dict[int, set[str]]:
    """renewal id -> the BM+ lines dismissed for it (as stored)."""
    out: dict[int, set[str]] = {}
    if not renewal_ids:
        return out
    marks = ",".join("?" * len(renewal_ids))
    for r in conn.execute(f"""SELECT renewal_id, line FROM design_change_dismissed
                               WHERE renewal_id IN ({marks})""",
                          list(renewal_ids)):
        out.setdefault(r["renewal_id"], set()).add(r["line"])
    return out


def dismissed_of_client(conn: sqlite3.Connection, client_id: int) -> dict[int, set[str]]:
    """The same for every renewal of a client (one query)."""
    out: dict[int, set[str]] = {}
    for r in conn.execute("""SELECT d.renewal_id, d.line FROM design_change_dismissed d
                              JOIN renewals r ON r.id = d.renewal_id WHERE r.client_id = ?""", (client_id,)):
        out.setdefault(r["renewal_id"], set()).add(r["line"])
    return out


def dismiss(conn: sqlite3.Connection, renewal_ids: list[int], line: str) -> None:
    conn.executemany("INSERT OR IGNORE INTO design_change_dismissed (renewal_id, line) VALUES (?, ?)",
                     [(rid, line) for rid in renewal_ids])


def undismiss(conn: sqlite3.Connection, renewal_ids: list[int], lines: list[str]) -> None:
    for rid in renewal_ids:
        conn.executemany("DELETE FROM design_change_dismissed WHERE renewal_id = ? AND line = ?",
                         [(rid, ln) for ln in lines])
