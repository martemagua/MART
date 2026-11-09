"""A renewal's post-renewal review for the stewardship (schema migration 19):
the savings Martin confirmed and his key learning. USER data, never touched
by uploads. All SQL for `renewal_reviews`."""

from __future__ import annotations

import sqlite3
from typing import Any


def for_client(conn: sqlite3.Connection, client_id: int) -> dict[int, dict[str, Any]]:
    """renewal id -> its review (one query for the client)."""
    return {
        r["renewal_id"]: dict(r)
        for r in conn.execute(
            """SELECT v.* FROM renewal_reviews v JOIN renewals r ON r.id = v.renewal_id
            WHERE r.client_id = ?""",
            (client_id,),
        )
    }


def get(conn: sqlite3.Connection, renewal_id: int) -> dict[str, Any] | None:
    r = conn.execute("SELECT * FROM renewal_reviews WHERE renewal_id = ?", (renewal_id,)).fetchone()
    return dict(r) if r else None


def _ensure(conn: sqlite3.Connection, renewal_id: int) -> None:
    conn.execute("INSERT OR IGNORE INTO renewal_reviews (renewal_id) VALUES (?)", (renewal_id,))


def set_savings(
    conn: sqlite3.Connection,
    renewal_id: int,
    hard: float | None,
    avoidance: float | None,
    unrealized: float | None,
    currency: str | None,
    note: str | None,
) -> None:
    _ensure(conn, renewal_id)
    conn.execute(
        """UPDATE renewal_reviews SET hard_savings = ?, cost_avoidance = ?, unrealized_savings = ?,
                           currency = ?, savings_note = ?, savings_confirmed_at = datetime('now'),
                           updated_at = datetime('now') WHERE renewal_id = ?""",
        (hard, avoidance, unrealized, currency, note, renewal_id),
    )


def clear_savings(conn: sqlite3.Connection, renewal_id: int) -> None:
    """Back to MART's suggestion."""
    conn.execute(
        """UPDATE renewal_reviews SET hard_savings = NULL, cost_avoidance = NULL,
                           unrealized_savings = NULL, currency = NULL, savings_note = NULL,
                           savings_confirmed_at = NULL, updated_at = datetime('now') WHERE renewal_id = ?""",
        (renewal_id,),
    )


def set_learning(conn: sqlite3.Connection, renewal_id: int, text: str | None) -> None:
    _ensure(conn, renewal_id)
    conn.execute(
        "UPDATE renewal_reviews SET key_learning = ?, updated_at = datetime('now') WHERE renewal_id = ?",
        (text, renewal_id),
    )
