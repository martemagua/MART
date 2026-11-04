"""Schema migrations: the single source of truth for the database layout.

`MIGRATIONS` is APPEND-ONLY. Each entry is (version, sql). `ensure_schema()`
applies every entry above the database's `PRAGMA user_version`, each in its
own transaction, and runs on every start. Never edit an applied migration;
add a new one.
"""

from __future__ import annotations

from pathlib import Path

from mart.repository.db import connect

MIGRATIONS: list[tuple[int, str]] = [
    (1, """
        -- Small key/value store for app state (e.g. "last seen" markers).
        CREATE TABLE user_state (
            key         TEXT PRIMARY KEY,
            value       TEXT,
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """),
]

LATEST_VERSION = MIGRATIONS[-1][0]


def current_version(path: Path | None = None) -> int:
    conn = connect(path)
    try:
        return conn.execute("PRAGMA user_version").fetchone()[0]
    finally:
        conn.close()


def ensure_schema(path: Path | None = None) -> int:
    """Create or upgrade the database. Returns the schema version."""
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(path)
    try:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        for number, sql in MIGRATIONS:
            if number <= version:
                continue
            # executescript() commits first; wrap explicitly so a failing
            # migration leaves the version untouched.
            conn.executescript(f"BEGIN;\n{sql}\nPRAGMA user_version = {int(number)};\nCOMMIT;")
            version = number
        return version
    finally:
        conn.close()
