"""Notes and to-dos: what Martin writes. All SQL for both tables.

Both hang on a target (scope, ref); see schema migration 4.
"""

from __future__ import annotations

import sqlite3
from typing import Any

_TODO_ORDER = "done_at IS NOT NULL, due_date IS NULL, due_date, id"


def _targets_clause(targets: list[tuple[str, str]]) -> tuple[str, list[str]]:
    if not targets:
        return "0", []
    return " OR ".join("(scope = ? AND ref = ?)" for _ in targets), [x for t in targets for x in t]


# -- notes ------------------------------------------------------------------------------
def notes_for(conn: sqlite3.Connection, targets: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """Notes on any of these targets, newest first."""
    where, args = _targets_clause(targets)
    return [dict(r) for r in conn.execute(
        f"SELECT * FROM notes WHERE {where} ORDER BY created_at DESC, id DESC", args)]


def add_note(conn: sqlite3.Connection, scope: str, ref: str, client_id: int, body: str) -> int:
    cur = conn.execute("INSERT INTO notes (scope, ref, client_id, body) VALUES (?, ?, ?, ?)",
                       (scope, ref, client_id, body))
    return int(cur.lastrowid)


def get_note(conn: sqlite3.Connection, note_id: int) -> dict[str, Any] | None:
    r = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return dict(r) if r else None


def update_note(conn: sqlite3.Connection, note_id: int, body: str) -> None:
    conn.execute("UPDATE notes SET body = ?, updated_at = datetime('now') WHERE id = ?", (body, note_id))


def delete_note(conn: sqlite3.Connection, note_id: int) -> None:
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))


# -- to-dos -----------------------------------------------------------------------------
def todos_for(conn: sqlite3.Connection, targets: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """To-dos on any of these targets: open first (by due date), then done."""
    where, args = _targets_clause(targets)
    return [dict(r) for r in conn.execute(f"SELECT * FROM todos WHERE {where} ORDER BY {_TODO_ORDER}", args)]


def all_todos(conn: sqlite3.Connection, done_since: str | None) -> list[dict[str, Any]]:
    """Every open to-do, and those done since `done_since` (UTC; None = all done ones)."""
    rows = conn.execute(
        """SELECT t.*, c.name AS client_name FROM todos t JOIN clients c ON c.id = t.client_id
            WHERE t.done_at IS NULL OR ? IS NULL OR t.done_at >= ?
            ORDER BY t.done_at IS NOT NULL, t.due_date IS NULL, t.due_date, t.id""",
        (done_since, done_since))
    return [dict(r) for r in rows]


def counts_by_target(conn: sqlite3.Connection, client_id: int) -> dict[tuple[str, str], dict[str, int]]:
    """(scope, ref) -> {"notes": n, "todos": open to-dos} for one client."""
    out: dict[tuple[str, str], dict[str, int]] = {}
    for r in conn.execute("""SELECT scope, ref, COUNT(*) AS n FROM notes
                             WHERE client_id = ? GROUP BY scope, ref""", (client_id,)):
        out.setdefault((r["scope"], r["ref"]), {"notes": 0, "todos": 0})["notes"] = r["n"]
    for r in conn.execute("""SELECT scope, ref, COUNT(*) AS n FROM todos
                             WHERE client_id = ? AND done_at IS NULL GROUP BY scope, ref""", (client_id,)):
        out.setdefault((r["scope"], r["ref"]), {"notes": 0, "todos": 0})["todos"] = r["n"]
    return out


def add_todo(conn: sqlite3.Connection, scope: str, ref: str, client_id: int, title: str,
             due_date: str | None) -> int:
    cur = conn.execute("INSERT INTO todos (scope, ref, client_id, title, due_date) VALUES (?, ?, ?, ?, ?)",
                       (scope, ref, client_id, title, due_date))
    return int(cur.lastrowid)


def get_todo(conn: sqlite3.Connection, todo_id: int) -> dict[str, Any] | None:
    r = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    return dict(r) if r else None


def update_todo(conn: sqlite3.Connection, todo_id: int, title: str, due_date: str | None) -> None:
    conn.execute("UPDATE todos SET title = ?, due_date = ?, updated_at = datetime('now') WHERE id = ?",
                 (title, due_date, todo_id))


def set_done(conn: sqlite3.Connection, todo_id: int, done: bool) -> None:
    conn.execute("""UPDATE todos SET done_at = CASE WHEN ? THEN datetime('now') END,
                    updated_at = datetime('now') WHERE id = ?""", (int(done), todo_id))


def delete_todo(conn: sqlite3.Connection, todo_id: int) -> None:
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))


def client_target_counts(conn: sqlite3.Connection) -> dict[int, dict[str, int]]:
    """client id -> {"notes", "todos" (open)} written on the client itself."""
    out: dict[int, dict[str, int]] = {}
    for r in conn.execute("""SELECT client_id, COUNT(*) AS n FROM notes
                             WHERE scope = 'client' GROUP BY client_id"""):
        out.setdefault(r["client_id"], {"notes": 0, "todos": 0})["notes"] = r["n"]
    for r in conn.execute("""SELECT client_id, COUNT(*) AS n FROM todos
                             WHERE scope = 'client' AND done_at IS NULL GROUP BY client_id"""):
        out.setdefault(r["client_id"], {"notes": 0, "todos": 0})["todos"] = r["n"]
    return out
