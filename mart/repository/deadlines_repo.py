"""Broker deadlines on bundles (schema migration 8): USER data, never
touched by uploads. All SQL for the `deadlines` table."""

from __future__ import annotations

import sqlite3
from typing import Any


def for_client(conn: sqlite3.Connection, client_id: int) -> list[dict[str, Any]]:
    """Every deadline of one client, newest first (open and history)."""
    return [dict(r) for r in conn.execute(
        "SELECT * FROM deadlines WHERE client_id = ? ORDER BY created_at DESC, id DESC", (client_id,))]


def open_one(conn: sqlite3.Connection, client_id: int, bundle_key: str) -> dict[str, Any] | None:
    r = conn.execute("""SELECT * FROM deadlines WHERE client_id = ? AND bundle_key = ? AND status = 'open'
                        ORDER BY id DESC LIMIT 1""", (client_id, bundle_key)).fetchone()
    return dict(r) if r else None


def all_open(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Open deadlines of MY clients (Home)."""
    return [dict(r) for r in conn.execute(
        """SELECT d.*, c.name AS client_name FROM deadlines d JOIN clients c ON c.id = d.client_id
            WHERE d.status = 'open' AND c.is_mine = 1 ORDER BY d.expected_date, d.id""")]


def add(conn: sqlite3.Connection, client_id: int, bundle_key: str, expected_date: str,
        promised_by: str | None, note: str | None, source: str, status: str = "open") -> int:
    closed = "datetime('now')" if status != "open" else "NULL"
    cur = conn.execute(
        f"""INSERT INTO deadlines (client_id, bundle_key, expected_date, promised_by, note, source, status,
                                   closed_at) VALUES (?, ?, ?, ?, ?, ?, ?, {closed})""",
        (client_id, bundle_key, expected_date, promised_by, note, source, status))
    return int(cur.lastrowid)


def close(conn: sqlite3.Connection, deadline_id: int, status: str) -> None:
    conn.execute("""UPDATE deadlines SET status = ?, closed_at = datetime('now')
                    WHERE id = ? AND status = 'open'""", (status, deadline_id))


def open_bundle_keys(conn: sqlite3.Connection, client_id: int) -> set[str]:
    """Bundles of a client with an open deadline (an emptied one stays visible)."""
    return {r["bundle_key"] for r in conn.execute(
        "SELECT DISTINCT bundle_key FROM deadlines WHERE client_id = ? AND status = 'open'", (client_id,))}
