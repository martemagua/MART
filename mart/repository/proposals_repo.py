"""The proposals Martin records (schema migration 10): USER data, never
touched by uploads. All SQL for the `proposals` table."""

from __future__ import annotations

import sqlite3
from typing import Any

FIELDS = ("insurer", "round", "received_on", "premium", "currency", "rate_change", "plan_design", "note")


def for_client(conn: sqlite3.Connection, client_id: int) -> dict[int, list[dict[str, Any]]]:
    """renewal id -> its proposals (one query for the whole client)."""
    out: dict[int, list[dict[str, Any]]] = {}
    for r in conn.execute(
            """SELECT p.* FROM proposals p JOIN renewals r ON r.id = p.renewal_id
                WHERE r.client_id = ? ORDER BY p.renewal_id, p.id""", (client_id,)):
        out.setdefault(r["renewal_id"], []).append(dict(r))
    return out


def for_renewal(conn: sqlite3.Connection, renewal_id: int) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(
        "SELECT * FROM proposals WHERE renewal_id = ? ORDER BY id", (renewal_id,))]


def get(conn: sqlite3.Connection, proposal_id: int) -> dict[str, Any] | None:
    r = conn.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
    return dict(r) if r else None


def insurers_of_client(conn: sqlite3.Connection, client_id: int) -> list[str]:
    """Every insurer name already used on this client's renewals or proposals
    (the add form's suggestions)."""
    return [r[0] for r in conn.execute(
        """SELECT name FROM (SELECT insurer AS name FROM renewals WHERE client_id = ?
                             UNION SELECT p.insurer FROM proposals p JOIN renewals r ON r.id = p.renewal_id
                                    WHERE r.client_id = ?)
            WHERE name IS NOT NULL AND name <> '' ORDER BY name COLLATE NOCASE""", (client_id, client_id))]


def add(conn: sqlite3.Connection, renewal_id: int, values: dict[str, Any]) -> int:
    cols = ", ".join(FIELDS)
    cur = conn.execute(f"INSERT INTO proposals (renewal_id, {cols}) VALUES (?{', ?' * len(FIELDS)})",
                       (renewal_id, *(values[f] for f in FIELDS)))
    return int(cur.lastrowid)


def update(conn: sqlite3.Connection, proposal_id: int, values: dict[str, Any]) -> None:
    sets = ", ".join(f"{f} = ?" for f in FIELDS)
    conn.execute(f"UPDATE proposals SET {sets}, updated_at = datetime('now') WHERE id = ?",
                 (*(values[f] for f in FIELDS), proposal_id))


def delete(conn: sqlite3.Connection, proposal_id: int) -> None:
    conn.execute("DELETE FROM proposals WHERE id = ?", (proposal_id,))


def set_chosen(conn: sqlite3.Connection, renewal_id: int, proposal_id: int | None) -> None:
    """Mark ONE proposal of a renewal as chosen (None: none)."""
    conn.execute("""UPDATE proposals SET chosen = (id = ?), updated_at = datetime('now')
                    WHERE renewal_id = ? AND chosen <> (id = ?)""",
                 (proposal_id or 0, renewal_id, proposal_id or 0))
