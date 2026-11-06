"""Plan design changes per renewal (schema migration 13): USER data, never
touched by uploads. All SQL for `plan_changes`."""

from __future__ import annotations

import sqlite3
from typing import Any

DATE_OF = {"suggested": "suggested_on", "agreed": "agreed_on", "implemented": "implemented_on",
           "dropped": "dropped_on"}


def for_client(conn: sqlite3.Connection, client_id: int) -> dict[int, list[dict[str, Any]]]:
    """renewal id -> its plan design changes (one query for the client)."""
    out: dict[int, list[dict[str, Any]]] = {}
    for r in conn.execute(
            """SELECT c.* FROM plan_changes c JOIN renewals r ON r.id = c.renewal_id
                WHERE r.client_id = ? ORDER BY c.renewal_id, c.id""", (client_id,)):
        out.setdefault(r["renewal_id"], []).append(dict(r))
    return out


def for_renewal(conn: sqlite3.Connection, renewal_id: int) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(
        "SELECT * FROM plan_changes WHERE renewal_id = ? ORDER BY id", (renewal_id,))]


def get(conn: sqlite3.Connection, change_id: int) -> dict[str, Any] | None:
    r = conn.execute("SELECT * FROM plan_changes WHERE id = ?", (change_id,)).fetchone()
    return dict(r) if r else None


def add(conn: sqlite3.Connection, renewal_id: int, title: str, detail: str | None, status: str,
        on: str, source: str = "you") -> int:
    """A new change, suggested on `on`; when it starts further along (agreed /
    implemented / dropped), that state's date is `on` too."""
    cur = conn.execute("""INSERT INTO plan_changes (renewal_id, title, detail, status, source, suggested_on)
                          VALUES (?, ?, ?, 'suggested', ?, ?)""", (renewal_id, title, detail, source, on))
    cid = int(cur.lastrowid)
    if status != "suggested":
        set_status(conn, cid, status, on)
    return cid


def update(conn: sqlite3.Connection, change_id: int, title: str, detail: str | None) -> None:
    conn.execute("UPDATE plan_changes SET title = ?, detail = ?, updated_at = datetime('now') WHERE id = ?",
                 (title, detail, change_id))


def set_status(conn: sqlite3.Connection, change_id: int, status: str, on: str) -> None:
    """Move to a state on a date; the dates of the states it passed stay."""
    col = DATE_OF[status]
    conn.execute(f"UPDATE plan_changes SET status = ?, {col} = ?, updated_at = datetime('now') WHERE id = ?",
                 (status, on, change_id))


def delete(conn: sqlite3.Connection, change_id: int) -> None:
    conn.execute("DELETE FROM plan_changes WHERE id = ?", (change_id,))
