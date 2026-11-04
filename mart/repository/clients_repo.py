"""Clients and the "is this one of mine?" choice."""

from __future__ import annotations

import sqlite3
from typing import Any


def by_keys(conn: sqlite3.Connection, keys: list[str]) -> dict[str, dict[str, Any]]:
    if not keys:
        return {}
    marks = ",".join("?" * len(keys))
    rows = conn.execute(f"SELECT * FROM clients WHERE client_key IN ({marks})", keys).fetchall()
    return {r["client_key"]: dict(r) for r in rows}


def upsert(conn: sqlite3.Connection, key: str, name: str, bm_client_id: str | None,
           is_mine: bool) -> int:
    """Create or update a client; returns its id. The newest spelling of the
    name wins, the BM+ client id is kept once known."""
    row = conn.execute("SELECT id FROM clients WHERE client_key = ?", (key,)).fetchone()
    if row is None:
        cur = conn.execute(
            "INSERT INTO clients (name, client_key, bm_client_id, is_mine) VALUES (?, ?, ?, ?)",
            (name, key, bm_client_id, int(is_mine)))
        return cur.lastrowid
    conn.execute(
        """UPDATE clients SET name = ?, bm_client_id = COALESCE(?, bm_client_id),
                              is_mine = ?, updated_at = datetime('now') WHERE id = ?""",
        (name, bm_client_id, int(is_mine), row["id"]))
    return row["id"]


def mine_summary(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """My clients with their renewal counts (renewals still in the export)."""
    rows = conn.execute(
        """SELECT c.id, c.name,
                  COUNT(r.id) FILTER (WHERE r.in_latest_export = 1) AS renewals,
                  MIN(r.renewal_date) FILTER (WHERE r.in_latest_export = 1
                                              AND r.renewal_date >= date('now')) AS next_renewal
           FROM clients c LEFT JOIN renewals r ON r.client_id = c.id
           WHERE c.is_mine = 1
           GROUP BY c.id ORDER BY c.name COLLATE NOCASE""").fetchall()
    return [dict(r) for r in rows]
