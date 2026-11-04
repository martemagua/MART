"""What each upload changed (append-only)."""

from __future__ import annotations

import sqlite3
from typing import Any


def add(conn: sqlite3.Connection, kind: str, item_id: int, upload_id: int,
        entries: list[tuple[str, Any, Any]]) -> None:
    conn.executemany(
        """INSERT INTO changes (item_kind, item_id, upload_id, field, old_value, new_value)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [(kind, item_id, upload_id, f, None if o is None else str(o), None if n is None else str(n))
         for f, o, n in entries])


def add_event(conn: sqlite3.Connection, kind: str, item_ids: list[int], upload_id: int, event: str) -> None:
    conn.executemany(
        "INSERT INTO changes (item_kind, item_id, upload_id, field) VALUES (?, ?, ?, ?)",
        [(kind, i, upload_id, event) for i in item_ids])


def for_items(conn: sqlite3.Connection, items: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Every change of these items, newest upload first, with the upload's dates."""
    if not items:
        return []
    where = " OR ".join("(c.item_kind = ? AND c.item_id = ?)" for _ in items)
    return [dict(r) for r in conn.execute(
        f"""SELECT c.*, u.report_date, u.committed_at, u.filename FROM changes c
            JOIN uploads u ON u.id = c.upload_id
            WHERE {where} ORDER BY c.upload_id DESC, c.id""", [x for i in items for x in i])]


def ids_by_key(conn: sqlite3.Connection, table: str, key_column: str, keys: list[str]) -> list[int]:
    """Row ids for business keys (renewals.cycle_key / tasks.task_key)."""
    if table not in ("renewals", "tasks") or key_column not in ("cycle_key", "task_key"):
        raise ValueError(table)
    out: list[int] = []
    for i in range(0, len(keys), 500):
        chunk = keys[i:i + 500]
        out += [r["id"] for r in conn.execute(
            f"SELECT id FROM {table} WHERE {key_column} IN ({','.join('?' * len(chunk))})", chunk)]
    return out
