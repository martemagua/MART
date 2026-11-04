"""How Martin arranges a client's bundles: splits and joins (user data)."""

from __future__ import annotations

import json
import sqlite3


def splits(conn: sqlite3.Connection, client_id: int) -> dict[str, list[str]]:
    """base key -> the fields its bundle is split by."""
    return {r["base_key"]: json.loads(r["fields_json"]) for r in conn.execute(
        "SELECT base_key, fields_json FROM bundle_splits WHERE client_id = ?", (client_id,))}


def set_split(conn: sqlite3.Connection, client_id: int, base_key: str, fields: list[str]) -> None:
    if not fields:
        conn.execute("DELETE FROM bundle_splits WHERE client_id = ? AND base_key = ?", (client_id, base_key))
        return
    conn.execute("""INSERT INTO bundle_splits (client_id, base_key, fields_json) VALUES (?, ?, ?)
                    ON CONFLICT (client_id, base_key)
                    DO UPDATE SET fields_json = excluded.fields_json, updated_at = datetime('now')""",
                 (client_id, base_key, json.dumps(fields)))


def joins(conn: sqlite3.Connection, client_id: int) -> dict[str, str]:
    """from key -> into key."""
    return {r["from_key"]: r["into_key"] for r in conn.execute(
        "SELECT from_key, into_key FROM bundle_joins WHERE client_id = ?", (client_id,))}


def join(conn: sqlite3.Connection, client_id: int, from_key: str, into_key: str) -> None:
    conn.execute("""INSERT INTO bundle_joins (client_id, from_key, into_key) VALUES (?, ?, ?)
                    ON CONFLICT (client_id, from_key) DO UPDATE SET into_key = excluded.into_key""",
                 (client_id, from_key, into_key))


def unjoin(conn: sqlite3.Connection, client_id: int, from_key: str) -> None:
    conn.execute("DELETE FROM bundle_joins WHERE client_id = ? AND from_key = ?", (client_id, from_key))
