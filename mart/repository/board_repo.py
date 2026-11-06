"""The board's stages of bundles (schema migration 15): USER data, never
touched by uploads. All SQL for the `bundle_stages` table.

Append-only: the newest row per (client, bundle) is the current stage; a row
with a NULL stage means "follow BM+ again"; the older rows are the history."""

from __future__ import annotations

import sqlite3
from typing import Any


def current(conn: sqlite3.Connection, client_id: int) -> dict[str, dict[str, Any]]:
    """bundle key -> its current row (only where Martin's stage is set)."""
    out: dict[str, dict[str, Any]] = {}
    for r in conn.execute(
            """SELECT * FROM bundle_stages WHERE client_id = ? AND id IN (
                   SELECT MAX(id) FROM bundle_stages WHERE client_id = ? GROUP BY bundle_key)""",
            (client_id, client_id)):
        if r["stage"] is not None:
            out[r["bundle_key"]] = dict(r)
    return out


def history(conn: sqlite3.Connection, client_id: int, bundle_key: str) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(
        "SELECT * FROM bundle_stages WHERE client_id = ? AND bundle_key = ? ORDER BY id DESC",
        (client_id, bundle_key))]


def add(conn: sqlite3.Connection, client_id: int, bundle_key: str, stage: str | None,
        bm_stage: str | None, reason: str | None) -> int:
    cur = conn.execute(
        "INSERT INTO bundle_stages (client_id, bundle_key, stage, bm_stage, reason) VALUES (?, ?, ?, ?, ?)",
        (client_id, bundle_key, stage, bm_stage, reason))
    return int(cur.lastrowid)
