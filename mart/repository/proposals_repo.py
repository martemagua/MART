"""The proposals Martin records: USER data, never touched by uploads. All SQL
for `proposals` (one per insurer + variant, migration 10) and
`proposal_quotes` (its quotes: first, revised…, final, migration 12)."""

from __future__ import annotations

import sqlite3
from typing import Any

PROPOSAL_FIELDS = ("insurer", "plan_design", "label")
QUOTE_FIELDS = ("round", "received_on", "premium", "currency", "rate_change", "note")
_PROPOSAL_COLS = "p.id, p.renewal_id, p.insurer, p.plan_design, p.label, p.chosen, p.created_at, p.updated_at"


def _with_quotes(conn: sqlite3.Connection, proposals: list[dict[str, Any]], where: str,
                 args: tuple) -> list[dict[str, Any]]:
    by_id = {p["id"]: {**p, "quotes": []} for p in proposals}
    for q in conn.execute(f"""SELECT q.* FROM proposal_quotes q JOIN proposals p ON p.id = q.proposal_id
                              {where} ORDER BY q.id""", args):
        if q["proposal_id"] in by_id:
            by_id[q["proposal_id"]]["quotes"].append(dict(q))
    return list(by_id.values())


def for_client(conn: sqlite3.Connection, client_id: int) -> dict[int, list[dict[str, Any]]]:
    """renewal id -> its proposals, each with its quotes (two queries for the client)."""
    where = "JOIN renewals r ON r.id = p.renewal_id WHERE r.client_id = ?"
    rows = [dict(r) for r in conn.execute(f"SELECT {_PROPOSAL_COLS} FROM proposals p {where} ORDER BY p.id",
                                          (client_id,))]
    out: dict[int, list[dict[str, Any]]] = {}
    for p in _with_quotes(conn, rows, where, (client_id,)):
        out.setdefault(p["renewal_id"], []).append(p)
    return out


def for_renewal(conn: sqlite3.Connection, renewal_id: int) -> list[dict[str, Any]]:
    rows = [dict(r) for r in conn.execute(
        f"SELECT {_PROPOSAL_COLS} FROM proposals p WHERE p.renewal_id = ? ORDER BY p.id", (renewal_id,))]
    return _with_quotes(conn, rows, "WHERE p.renewal_id = ?", (renewal_id,))


def get(conn: sqlite3.Connection, proposal_id: int) -> dict[str, Any] | None:
    r = conn.execute(f"SELECT {_PROPOSAL_COLS} FROM proposals p WHERE p.id = ?", (proposal_id,)).fetchone()
    return dict(r) if r else None


def get_quote(conn: sqlite3.Connection, quote_id: int) -> dict[str, Any] | None:
    r = conn.execute("SELECT * FROM proposal_quotes WHERE id = ?", (quote_id,)).fetchone()
    return dict(r) if r else None


def find(conn: sqlite3.Connection, renewal_id: int, insurer: str, plan_design: str,
         label: str | None) -> dict[str, Any] | None:
    """The proposal of this renewal from the same insurer, plan design and
    label (ignoring case and spacing), if there is one."""
    r = conn.execute(
        f"""SELECT {_PROPOSAL_COLS} FROM proposals p
             WHERE p.renewal_id = ? AND lower(trim(p.insurer)) = lower(trim(?)) AND p.plan_design = ?
               AND lower(trim(coalesce(p.label, ''))) = lower(trim(coalesce(?, '')))
             ORDER BY p.id LIMIT 1""", (renewal_id, insurer, plan_design, label)).fetchone()
    return dict(r) if r else None


def insurers_of_client(conn: sqlite3.Connection, client_id: int, country: str | None) -> list[str]:
    """Every insurer name already used on this client's renewals or proposals
    IN THIS COUNTRY (the add form's suggestions, after the network partners)."""
    return [r[0] for r in conn.execute(
        """SELECT name FROM (SELECT insurer AS name FROM renewals WHERE client_id = ? AND country IS ?
                             UNION SELECT p.insurer FROM proposals p JOIN renewals r ON r.id = p.renewal_id
                                    WHERE r.client_id = ? AND r.country IS ?)
            WHERE name IS NOT NULL AND name <> '' ORDER BY name COLLATE NOCASE""",
        (client_id, country, client_id, country))]


def add(conn: sqlite3.Connection, renewal_id: int, values: dict[str, Any]) -> int:
    cur = conn.execute("INSERT INTO proposals (renewal_id, insurer, plan_design, label) VALUES (?, ?, ?, ?)",
                       (renewal_id, *(values[f] for f in PROPOSAL_FIELDS)))
    return int(cur.lastrowid)


def update(conn: sqlite3.Connection, proposal_id: int, values: dict[str, Any]) -> None:
    conn.execute("""UPDATE proposals SET insurer = ?, plan_design = ?, label = ?, updated_at = datetime('now')
                    WHERE id = ?""", (*(values[f] for f in PROPOSAL_FIELDS), proposal_id))


def delete(conn: sqlite3.Connection, proposal_id: int) -> None:
    conn.execute("DELETE FROM proposal_quotes WHERE proposal_id = ?", (proposal_id,))
    conn.execute("DELETE FROM proposals WHERE id = ?", (proposal_id,))


def add_quote(conn: sqlite3.Connection, proposal_id: int, values: dict[str, Any]) -> int:
    cols = ", ".join(QUOTE_FIELDS)
    marks = ", ?" * len(QUOTE_FIELDS)
    cur = conn.execute(f"INSERT INTO proposal_quotes (proposal_id, {cols}) VALUES (?{marks})",
                       (proposal_id, *(values[f] for f in QUOTE_FIELDS)))
    conn.execute("UPDATE proposals SET updated_at = datetime('now') WHERE id = ?", (proposal_id,))
    return int(cur.lastrowid)


def update_quote(conn: sqlite3.Connection, quote_id: int, values: dict[str, Any]) -> None:
    sets = ", ".join(f"{f} = ?" for f in QUOTE_FIELDS)
    conn.execute(f"UPDATE proposal_quotes SET {sets}, updated_at = datetime('now') WHERE id = ?",
                 (*(values[f] for f in QUOTE_FIELDS), quote_id))


def delete_quote(conn: sqlite3.Connection, quote_id: int) -> None:
    conn.execute("DELETE FROM proposal_quotes WHERE id = ?", (quote_id,))


def set_chosen(conn: sqlite3.Connection, renewal_id: int, proposal_id: int | None) -> None:
    """Mark ONE proposal of a renewal as chosen (None: none)."""
    conn.execute("""UPDATE proposals SET chosen = (id = ?), updated_at = datetime('now')
                    WHERE renewal_id = ? AND chosen <> (id = ?)""",
                 (proposal_id or 0, renewal_id, proposal_id or 0))
