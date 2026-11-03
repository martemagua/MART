"""Database connections.

One SQLite file (`<data folder>/mart.db`). Connections are short-lived: open,
work, close. That keeps the file free between requests, so a backup or a
move of the data folder never fights an open handle (which matters on
Windows).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from mart import settings as settings_mod


class NotConfigured(RuntimeError):
    """MART has no settings yet; the user must go through /setup."""


def db_path() -> Path:
    s = settings_mod.load()
    if s is None:
        raise NotConfigured("MART has not been set up yet.")
    return s.db_path


def connect(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path or db_path()), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """`with connection() as conn:` commits on success, rolls back on error,
    and always closes."""
    conn = connect(path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
