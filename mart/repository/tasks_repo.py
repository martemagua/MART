"""BM+ tasks as MART keeps them (BM+ data, never user data)."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

_COLUMNS = ("client_id", "policy_id", "expiring_policy_id", "bm_renewal_id", "task_name",
            "task_category", "task_status", "country", "policy_name", "review_date", "assignee",
            "due_date", "completed_date", "fields_json", "bm_json", "content_hash")


def stored_by_key(conn: sqlite3.Connection, keys: list[str]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for i in range(0, len(keys), 500):
        chunk = keys[i:i + 500]
        marks = ",".join("?" * len(chunk))
        for r in conn.execute(
                f"""SELECT id, task_key, client_id, content_hash, in_latest_export, fields_json
                    FROM tasks WHERE task_key IN ({marks})""", chunk):
            out[r["task_key"]] = dict(r)
    return out


def in_export_for_clients(conn: sqlite3.Connection, client_ids: list[int]) -> dict[int, set[str]]:
    out: dict[int, set[str]] = {cid: set() for cid in client_ids}
    if not client_ids:
        return out
    marks = ",".join("?" * len(client_ids))
    for r in conn.execute(f"""SELECT client_id, task_key FROM tasks
                              WHERE in_latest_export = 1 AND client_id IN ({marks})""", client_ids):
        out[r["client_id"]].add(r["task_key"])
    return out


def merged_fields(row: dict[str, Any], existing: dict[str, Any] | None) -> dict[str, Any]:
    """The task's fields after this export: what the export has no column for
    is kept from before (one flavour lacks columns the other has)."""
    if not existing:
        return row["fields"]
    carried = set(row.get("carried") or row["fields"])
    return {**json.loads(existing.get("fields_json") or "{}"),
            **{k: val for k, val in row["fields"].items() if k in carried}}


def save(conn: sqlite3.Connection, row: dict[str, Any], client_id: int, upload_id: int,
         existing: dict[str, Any] | None, touched: bool) -> int:
    """Insert or update (fields: merged_fields). The raw BM+ copy is the last
    export's own row."""
    existing_id = existing["id"] if existing else None
    f, bm = merged_fields(row, existing), row["bm"]
    vals = {
        "client_id": client_id, "policy_id": f.get("policy_id"),
        "expiring_policy_id": f.get("expiring_policy_id"),
        "bm_renewal_id": (row.get("ids") or {}).get("bm_renewal_id"),
        "task_name": f.get("task_name"), "task_category": f.get("task_category"),
        "task_status": f.get("task_status"), "country": f.get("country"),
        "policy_name": f.get("policy_name"), "review_date": f.get("review_date"),
        "assignee": f.get("assignee"), "due_date": f.get("due_date"),
        "completed_date": f.get("completed_date"),
        "fields_json": json.dumps(f, default=str), "bm_json": json.dumps(bm, default=str),
        "content_hash": row["content_hash"],
    }
    if existing_id is None:
        cols = ", ".join(("task_key",) + _COLUMNS + ("first_upload_id", "last_upload_id"))
        marks = ", ".join("?" * (len(_COLUMNS) + 3))
        cur = conn.execute(f"INSERT INTO tasks ({cols}) VALUES ({marks})",
                           [row["key"], *[vals[c] for c in _COLUMNS], upload_id, upload_id])
        return int(cur.lastrowid)
    sets = ", ".join(f"{c} = ?" for c in _COLUMNS)
    conn.execute(
        f"""UPDATE tasks SET {sets}, last_upload_id = ?, in_latest_export = 1, left_export_at = NULL,
                updated_at = CASE WHEN ? THEN datetime('now') ELSE updated_at END
            WHERE id = ?""",
        [*[vals[c] for c in _COLUMNS], upload_id, int(touched), existing_id])
    return existing_id


def delete(conn: sqlite3.Connection, keys: list[str]) -> None:
    """Tasks that belong to no renewal MART has (Martin, 04.11.2026: such
    tasks are discarded). BM+ data only; nothing the user wrote."""
    for i in range(0, len(keys), 500):
        chunk = keys[i:i + 500]
        marks = ",".join("?" * len(chunk))
        conn.execute(f"""DELETE FROM changes WHERE item_kind = 'task'
                         AND item_id IN (SELECT id FROM tasks WHERE task_key IN ({marks}))""", chunk)
        conn.execute(f"DELETE FROM tasks WHERE task_key IN ({marks})", chunk)


# the task dates a Task Tracker can be filtered by -> where they are stored
_DATE_COLUMNS = {"review_date": "review_date", "due_date": "due_date",
                 "completed_date": "completed_date",
                 "start_date": "json_extract(fields_json, '$.start_date')"}


def dates(conn: sqlite3.Connection, keys: list[str], field: str) -> dict[str, str | None]:
    """task key -> one of its dates."""
    column = _DATE_COLUMNS[field]
    out: dict[str, str | None] = {}
    for i in range(0, len(keys), 500):
        chunk = keys[i:i + 500]
        for r in conn.execute(f"SELECT task_key, {column} AS d FROM tasks "
                              f"WHERE task_key IN ({','.join('?' * len(chunk))})", chunk):
            out[r["task_key"]] = r["d"]
    return out


def mark_left_export(conn: sqlite3.Connection, keys: list[str]) -> None:
    for i in range(0, len(keys), 500):
        chunk = keys[i:i + 500]
        marks = ",".join("?" * len(chunk))
        conn.execute(f"""UPDATE tasks SET in_latest_export = 0, left_export_at = datetime('now')
                         WHERE in_latest_export = 1 AND task_key IN ({marks})""", chunk)


def for_client(conn: sqlite3.Connection, client_id: int) -> list[dict[str, Any]]:
    """All tasks MART has for a client, fields parsed (for linking to renewals)."""
    out = []
    for r in conn.execute(
            """SELECT id, task_key, policy_id, expiring_policy_id, task_name, task_category,
                      task_status, review_date, assignee, due_date, completed_date,
                      in_latest_export, fields_json
               FROM tasks WHERE client_id = ?""", (client_id,)):
        d = dict(r)
        d["fields"] = json.loads(d.pop("fields_json"))
        out.append(d)
    return out


def count_for_client(conn: sqlite3.Connection, client_id: int) -> int:
    return conn.execute("SELECT COUNT(*) FROM tasks WHERE client_id = ?", (client_id,)).fetchone()[0]
