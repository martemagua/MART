"""The upload log and the staged rows of each upload."""

from __future__ import annotations

import json
import sqlite3
from typing import Any


def create_staged(conn: sqlite3.Connection, *, filename: str, sha256: str, size: int,
                  tracker: str, flavour: str, report_date: str | None,
                  report_time: str | None, info: dict[str, Any], preview: dict[str, Any],
                  rows: list[tuple[str, str, dict[str, Any]]]) -> int:
    cur = conn.execute(
        """INSERT INTO uploads (filename, file_sha256, file_size, tracker, flavour,
                                report_date, report_time, info_json, preview_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (filename, sha256, size, tracker, flavour, report_date, report_time,
         json.dumps(info, default=str), json.dumps(preview, default=str)),
    )
    upload_id = cur.lastrowid
    conn.executemany(
        "INSERT INTO staging_rows (upload_id, cycle_key, client_key, data_json) VALUES (?, ?, ?, ?)",
        [(upload_id, key, ckey, json.dumps(data, default=str)) for key, ckey, data in rows],
    )
    return upload_id


def get(conn: sqlite3.Connection, upload_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM uploads WHERE id = ?", (upload_id,)).fetchone()
    if row is None:
        return None
    out = dict(row)
    for col in ("info_json", "preview_json", "summary_json"):
        out[col[:-5]] = json.loads(out[col]) if out[col] else {}
    return out


def staged_rows(conn: sqlite3.Connection, upload_id: int) -> list[dict[str, Any]]:
    return [json.loads(r[0]) for r in conn.execute(
        "SELECT data_json FROM staging_rows WHERE upload_id = ? ORDER BY id", (upload_id,))]


def recent(conn: sqlite3.Connection, limit: int = 50) -> list[dict[str, Any]]:
    rows = conn.execute(
        """SELECT id, filename, tracker, flavour, report_date, report_time, status,
                  staged_at, committed_at, discarded_at, preview_json, summary_json
           FROM uploads ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["preview"] = json.loads(d.pop("preview_json") or "{}")
        d["summary"] = json.loads(d.pop("summary_json") or "{}")
        out.append(d)
    return out


def committed_same_file(conn: sqlite3.Connection, sha256: str, exclude_id: int) -> dict | None:
    row = conn.execute(
        """SELECT id, filename, committed_at FROM uploads
           WHERE file_sha256 = ? AND status = 'committed' AND id <> ?
           ORDER BY id DESC LIMIT 1""", (sha256, exclude_id)).fetchone()
    return dict(row) if row else None


def committed_of_tracker(conn: sqlite3.Connection, tracker: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        """SELECT id, filename, report_date, report_time, preview_json FROM uploads
           WHERE tracker = ? AND status = 'committed' ORDER BY id DESC""", (tracker,)).fetchall()
    return [{**dict(r), "preview": json.loads(r["preview_json"] or "{}")} for r in rows]


def mark_committed(conn: sqlite3.Connection, upload_id: int, summary: dict[str, Any]) -> None:
    conn.execute(
        """UPDATE uploads SET status = 'committed', committed_at = datetime('now'),
                              summary_json = ? WHERE id = ?""",
        (json.dumps(summary, default=str), upload_id))


def mark_discarded(conn: sqlite3.Connection, upload_id: int) -> None:
    conn.execute("UPDATE uploads SET status = 'discarded', discarded_at = datetime('now') "
                 "WHERE id = ?", (upload_id,))
    conn.execute("DELETE FROM staging_rows WHERE upload_id = ?", (upload_id,))


def last_committed(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute(
        """SELECT id, filename, committed_at, report_date FROM uploads WHERE status = 'committed'
           ORDER BY committed_at DESC, id DESC LIMIT 1""").fetchone()
    return dict(row) if row else None


def staged(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Uploads waiting for a commit or discard, oldest first."""
    rows = conn.execute(
        """SELECT id, filename, tracker, flavour, report_date, staged_at, preview_json
           FROM uploads WHERE status = 'staged' ORDER BY id""").fetchall()
    return [{**dict(r), "preview": json.loads(r["preview_json"] or "{}")} for r in rows]
