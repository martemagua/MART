"""The actual state of renewals (schema migration 9): USER data beside BM+'s,
never touched by uploads. All SQL for the `renewal_actuals` table.

Append-only: the newest row per (renewal, field) is the current value; a row
with a NULL value clears it; the older rows are the history."""

from __future__ import annotations

import sqlite3
from typing import Any


def for_client(conn: sqlite3.Connection, client_id: int) -> dict[int, list[dict[str, Any]]]:
    """renewal id -> its rows, newest first (one query for the whole client)."""
    out: dict[int, list[dict[str, Any]]] = {}
    for r in conn.execute(
            """SELECT a.* FROM renewal_actuals a JOIN renewals r ON r.id = a.renewal_id
                WHERE r.client_id = ? ORDER BY a.renewal_id, a.id DESC""", (client_id,)):
        out.setdefault(r["renewal_id"], []).append(dict(r))
    return out


def for_renewal(conn: sqlite3.Connection, renewal_id: int) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(
        "SELECT * FROM renewal_actuals WHERE renewal_id = ? ORDER BY id DESC", (renewal_id,))]


def add(conn: sqlite3.Connection, renewal_id: int, field: str, value: str | None,
        bm_value: str | None, reason: str | None) -> int:
    cur = conn.execute(
        "INSERT INTO renewal_actuals (renewal_id, field, value, bm_value, reason) VALUES (?, ?, ?, ?, ?)",
        (renewal_id, field, value, bm_value, reason))
    return int(cur.lastrowid)
