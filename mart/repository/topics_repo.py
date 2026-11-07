"""Client topics (schema migration 16): USER data, never touched by uploads.
All SQL for `client_topics`, and for which topic a client note / to-do sits
in (`topic_id`, NULL = General) and whether a note is pinned."""

from __future__ import annotations

import sqlite3
from typing import Any

FIELDS = ("name", "color", "country", "status")


def for_client(conn: sqlite3.Connection, client_id: int) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(
        "SELECT * FROM client_topics WHERE client_id = ? ORDER BY position, id", (client_id,))]


def by_id(conn: sqlite3.Connection, ids: set[int]) -> dict[int, dict[str, Any]]:
    """topic id -> topic, for the To-dos page's chips (one query)."""
    if not ids:
        return {}
    marks = ",".join("?" * len(ids))
    return {r["id"]: dict(r) for r in conn.execute(f"SELECT * FROM client_topics WHERE id IN ({marks})",
                                                    sorted(ids))}


def get(conn: sqlite3.Connection, topic_id: int) -> dict[str, Any] | None:
    r = conn.execute("SELECT * FROM client_topics WHERE id = ?", (topic_id,)).fetchone()
    return dict(r) if r else None


def add(conn: sqlite3.Connection, client_id: int, values: dict[str, Any]) -> int:
    pos = conn.execute("SELECT COALESCE(MAX(position), 0) + 1 FROM client_topics WHERE client_id = ?",
                       (client_id,)).fetchone()[0]
    cur = conn.execute(
        """INSERT INTO client_topics (client_id, name, color, country, status, position)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (client_id, *[values[f] for f in FIELDS], pos))
    return int(cur.lastrowid)


def update(conn: sqlite3.Connection, topic_id: int, values: dict[str, Any]) -> None:
    sets = ", ".join(f"{f} = ?" for f in FIELDS)
    conn.execute(f"UPDATE client_topics SET {sets}, updated_at = datetime('now') WHERE id = ?",
                 (*[values[f] for f in FIELDS], topic_id))


def delete(conn: sqlite3.Connection, topic_id: int) -> None:
    """The topic goes; its notes and to-dos stay, in General."""
    conn.execute("UPDATE notes SET topic_id = NULL WHERE topic_id = ?", (topic_id,))
    conn.execute("UPDATE todos SET topic_id = NULL WHERE topic_id = ?", (topic_id,))
    conn.execute("DELETE FROM client_topics WHERE id = ?", (topic_id,))


def set_topic(conn: sqlite3.Connection, table: str, item_id: int, topic_id: int | None) -> None:
    if table not in ("notes", "todos"):
        raise ValueError(table)
    conn.execute(f"UPDATE {table} SET topic_id = ? WHERE id = ?", (topic_id, item_id))


def set_pinned(conn: sqlite3.Connection, note_id: int, pinned: bool) -> None:
    conn.execute("UPDATE notes SET pinned_at = CASE WHEN ? THEN datetime('now') ELSE NULL END WHERE id = ?",
                 (int(pinned), note_id))
