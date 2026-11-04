"""The small key/value store `user_state` (preferences, markers)."""

from __future__ import annotations

import sqlite3


def get(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM user_state WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def get_prefix(conn: sqlite3.Connection, prefix: str) -> dict[str, str]:
    return {r["key"]: r["value"] for r in conn.execute(
        "SELECT key, value FROM user_state WHERE key LIKE ? ESCAPE '\\'",
        (prefix.replace("_", "\\_") + "%",))}


def put(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("""INSERT INTO user_state (key, value, updated_at) VALUES (?, ?, datetime('now'))
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value,
                                                   updated_at = excluded.updated_at""", (key, value))
