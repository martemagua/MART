"""Custom bundles and which renewals sit in them (user data)."""

from __future__ import annotations

import sqlite3
from typing import Any


def custom_bundles(conn: sqlite3.Connection, client_id: int) -> dict[int, dict[str, Any]]:
    return {r["id"]: dict(r) for r in conn.execute(
        "SELECT * FROM custom_bundles WHERE client_id = ? ORDER BY country, name, id", (client_id,))}


def placements(conn: sqlite3.Connection, client_id: int) -> dict[int, int]:
    """renewal id -> custom bundle id, for one client's renewals."""
    return {r["renewal_id"]: r["bundle_id"] for r in conn.execute(
        """SELECT rb.renewal_id, rb.bundle_id FROM renewal_bundles rb
           JOIN custom_bundles b ON b.id = rb.bundle_id WHERE b.client_id = ?""", (client_id,))}


def create(conn: sqlite3.Connection, client_id: int, country: str, name: str) -> int:
    cur = conn.execute("INSERT INTO custom_bundles (client_id, country, name) VALUES (?, ?, ?)",
                       (client_id, country, name))
    return int(cur.lastrowid)


def rename(conn: sqlite3.Connection, bundle_id: int, name: str) -> None:
    conn.execute("UPDATE custom_bundles SET name = ?, updated_at = datetime('now') WHERE id = ?",
                 (name, bundle_id))


def place(conn: sqlite3.Connection, renewal_ids: list[int], bundle_id: int | None) -> None:
    """Move renewals into a custom bundle, or back to their default (None)."""
    for rid in renewal_ids:
        if bundle_id is None:
            conn.execute("DELETE FROM renewal_bundles WHERE renewal_id = ?", (rid,))
        else:
            conn.execute("""INSERT INTO renewal_bundles (renewal_id, bundle_id) VALUES (?, ?)
                            ON CONFLICT (renewal_id) DO UPDATE SET bundle_id = excluded.bundle_id,
                            moved_at = datetime('now')""", (rid, bundle_id))


def all_custom(conn: sqlite3.Connection) -> dict[int, dict[str, Any]]:
    """Every custom bundle (for naming targets in lists across clients)."""
    return {r["id"]: dict(r) for r in conn.execute("SELECT * FROM custom_bundles")}
