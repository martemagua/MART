"""Renewal cycles as MART keeps them (BM+ data, never user data)."""

from __future__ import annotations

import json
import sqlite3
from typing import Any


def stored_by_key(conn: sqlite3.Connection, keys: list[str]) -> dict[str, dict[str, Any]]:
    """What MART has for these renewal keys (fields and full row parsed)."""
    out: dict[str, dict[str, Any]] = {}
    for i in range(0, len(keys), 500):  # SQLite caps the number of ? per statement
        chunk = keys[i:i + 500]
        marks = ",".join("?" * len(chunk))
        for r in conn.execute(
                f"""SELECT id, cycle_key, client_id, content_hash, in_latest_export,
                           fields_json, bm_json
                    FROM renewals WHERE cycle_key IN ({marks})""", chunk):
            d = dict(r)
            d["fields"] = json.loads(d.pop("fields_json"))
            d["bm"] = json.loads(d.pop("bm_json"))
            out[r["cycle_key"]] = d
    return out


def in_export_for_clients(conn: sqlite3.Connection, client_ids: list[int]) -> dict[int, set[str]]:
    """Per client: the keys of its renewals that were in the latest export."""
    out: dict[int, set[str]] = {cid: set() for cid in client_ids}
    if not client_ids:
        return out
    marks = ",".join("?" * len(client_ids))
    for r in conn.execute(
            f"""SELECT client_id, cycle_key FROM renewals
                WHERE in_latest_export = 1 AND client_id IN ({marks})""", client_ids):
        out[r["client_id"]].add(r["cycle_key"])
    return out


_COLUMNS = ("cycle_id", "expiring_policy_id", "bm_renewal_id", "client_id", "country", "entity",
            "division", "region", "policy_name", "lines_of_coverage", "product_groups", "insurer",
            "start_date", "end_date", "non_expiring", "renewal_date", "kickoff_date",
            "workflow_status", "upcoming_strategy", "id_missing", "fields_json", "bm_json",
            "details_json", "content_hash")


def _values(row: dict[str, Any], client_id: int) -> dict[str, Any]:
    f, ids = row["fields"], row["ids"]
    return {
        "cycle_id": ids.get("cycle_id"), "expiring_policy_id": ids.get("expiring_policy_id"),
        "bm_renewal_id": ids.get("bm_renewal_id"), "client_id": client_id,
        "country": f.get("country"), "entity": f.get("entity"), "division": f.get("division"),
        "region": f.get("region"), "policy_name": f.get("policy_name"),
        "lines_of_coverage": f.get("lines_of_coverage"),
        "product_groups": json.dumps(f.get("product_groups") or []),
        "insurer": f.get("insurer"), "start_date": f.get("start_date"),
        "end_date": f.get("end_date"), "non_expiring": int(bool(f.get("non_expiring"))),
        "renewal_date": f.get("renewal_date"), "kickoff_date": f.get("kickoff_date"),
        "workflow_status": f.get("workflow_status"),
        "upcoming_strategy": f.get("upcoming_strategy"),
        "id_missing": int(bool(row.get("id_missing"))),
        "fields_json": json.dumps(f, default=str), "bm_json": json.dumps(row["bm"], default=str),
        "details_json": json.dumps(row.get("details") or {}, default=str),
        "content_hash": row["content_hash"],
    }


def save(conn: sqlite3.Connection, row: dict[str, Any], client_id: int, upload_id: int,
         existing_id: int | None, touched: bool) -> None:
    """Insert a new renewal, or update an existing one from a staged row.
    `touched` (decided by the service) sets updated_at."""
    vals = _values(row, client_id)
    if existing_id is None:
        cols = ", ".join(("cycle_key",) + _COLUMNS + ("first_upload_id", "last_upload_id"))
        marks = ", ".join("?" * (len(_COLUMNS) + 3))
        conn.execute(f"INSERT INTO renewals ({cols}) VALUES ({marks})",
                     [row["cycle_key"], *[vals[c] for c in _COLUMNS], upload_id, upload_id])
        return
    sets = ", ".join(f"{c} = ?" for c in _COLUMNS)
    conn.execute(
        f"""UPDATE renewals SET {sets}, last_upload_id = ?, in_latest_export = 1,
                left_export_at = NULL,
                updated_at = CASE WHEN ? THEN datetime('now') ELSE updated_at END
            WHERE id = ?""",
        [*[vals[c] for c in _COLUMNS], upload_id, int(touched), existing_id])


def mark_left_export(conn: sqlite3.Connection, keys: list[str]) -> None:
    for i in range(0, len(keys), 500):
        chunk = keys[i:i + 500]
        marks = ",".join("?" * len(chunk))
        conn.execute(f"""UPDATE renewals SET in_latest_export = 0, left_export_at = datetime('now')
                         WHERE in_latest_export = 1 AND cycle_key IN ({marks})""", chunk)


def totals(conn: sqlite3.Connection) -> dict[str, int]:
    row = conn.execute(
        """SELECT COUNT(*) FILTER (WHERE r.in_latest_export = 1) AS in_export,
                  COUNT(*) FILTER (WHERE r.in_latest_export = 0) AS left_export,
                  COUNT(DISTINCT r.client_id) AS clients
           FROM renewals r JOIN clients c ON c.id = r.client_id WHERE c.is_mine = 1""").fetchone()
    return dict(row)


def for_client(conn: sqlite3.Connection, client_id: int) -> list[dict[str, Any]]:
    """Every renewal MART has for a client (in the export or not), fields parsed."""
    rows = conn.execute(
        """SELECT id, cycle_key, cycle_id, expiring_policy_id, country, entity, policy_name,
                  lines_of_coverage, product_groups, insurer, start_date, end_date,
                  non_expiring, renewal_date, kickoff_date, workflow_status,
                  upcoming_strategy, id_missing, in_latest_export, left_export_at,
                  fields_json
           FROM renewals WHERE client_id = ?""", (client_id,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["fields"] = json.loads(d.pop("fields_json"))
        d["product_groups"] = json.loads(d["product_groups"] or "[]")
        out.append(d)
    return out


def overview_texts_for_mine(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Per renewal of my clients still in the export: the two overview texts and
    the bundle facts, for the Clients list (one query for all clients)."""
    rows = conn.execute(
        """SELECT r.client_id, r.country, r.renewal_date,
                  json_extract(r.fields_json, '$.overview_all') AS overview_all,
                  json_extract(r.fields_json, '$.overview_client_ready') AS overview_client_ready
           FROM renewals r JOIN clients c ON c.id = r.client_id
           WHERE c.is_mine = 1 AND r.in_latest_export = 1""").fetchall()
    return [dict(r) for r in rows]


def get(conn: sqlite3.Connection, renewal_id: int) -> dict[str, Any] | None:
    """One renewal with everything parsed: fields, the full Overview row and the
    Strategy / Proposals / Savings rows."""
    r = conn.execute("SELECT * FROM renewals WHERE id = ?", (renewal_id,)).fetchone()
    if r is None:
        return None
    d = dict(r)
    for col in ("fields_json", "bm_json", "details_json"):
        d[col[:-5]] = json.loads(d.pop(col) or "{}")
    d["product_groups"] = json.loads(d["product_groups"] or "[]")
    return d
