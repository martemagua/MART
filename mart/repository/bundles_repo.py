"""Custom bundles and which renewals sit in them (user data)."""

from __future__ import annotations

import sqlite3
from typing import Any


def custom_bundles(conn: sqlite3.Connection, client_id: int) -> dict[int, dict[str, Any]]:
    return {r["id"]: dict(r) for r in conn.execute(
        "SELECT * FROM custom_bundles WHERE client_id = ? ORDER BY country, name, id", (client_id,))}


def placements(conn: sqlite3.Connection, client_id: int) -> dict[int, int]:
    """renewal id -> custom bundle id, for one client's renewals."""
    return {r["renewal_id"]: r["bundle_id"] for r in conn.execute(
        """SELECT rb.renewal_id, rb.bundle_id FROM renewal_bundles rb
           JOIN custom_bundles b ON b.id = rb.bundle_id WHERE b.client_id = ?""", (client_id,))}


def create(conn: sqlite3.Connection, client_id: int, country: str, name: str) -> int:
    cur = conn.execute("INSERT INTO custom_bundles (client_id, country, name) VALUES (?, ?, ?)",
                       (client_id, country, name))
    return int(cur.lastrowid)


def rename(conn: sqlite3.Connection, bundle_id: int, name: str) -> None:
    conn.execute("UPDATE custom_bundles SET name = ?, updated_at = datetime('now') WHERE id = ?",
                 (name, bundle_id))


def place(conn: sqlite3.Connection, renewal_ids: list[int], bundle_id: int | None) -> None:
    """Move renewals into a custom bundle, or back to their default (None)."""
    for rid in renewal_ids:
        if bundle_id is None:
            conn.execute("DELETE FROM renewal_bundles WHERE renewal_id = ?", (rid,))
        else:
            conn.execute("""INSERT INTO renewal_bundles (renewal_id, bundle_id) VALUES (?, ?)
                            ON CONFLICT (renewal_id) DO UPDATE SET bundle_id = excluded.bundle_id,
                            moved_at = datetime('now')""", (rid, bundle_id))


def all_custom(conn: sqlite3.Connection) -> dict[int, dict[str, Any]]:
    """Every custom bundle (for naming targets in lists across clients)."""
    return {r["id"]: dict(r) for r in conn.execute("SELECT * FROM custom_bundles")}


def names(conn: sqlite3.Connection, client_id: int) -> dict[str, str]:
    """default bundle key -> the name Martin gave it."""
    return {r["bundle_key"]: r["name"] for r in conn.execute(
        "SELECT bundle_key, name FROM bundle_names WHERE client_id = ?", (client_id,))}


def set_name(conn: sqlite3.Connection, client_id: int, key: str, name: str | None) -> None:
    if not name:
        conn.execute("DELETE FROM bundle_names WHERE client_id = ? AND bundle_key = ?", (client_id, key))
        return
    conn.execute("""INSERT INTO bundle_names (client_id, bundle_key, name) VALUES (?, ?, ?)
                    ON CONFLICT (client_id, bundle_key) DO UPDATE SET name = excluded.name""",
                 (client_id, key, name))


# -- following a renewal date that BM+ changed (QA 07.11.2026) -------------------------
# A default bundle's key is "<country>|<renewal date>", so when BM+ moves a
# renewal date everything Martin put on the bundle would stay on the old key.
_KEYED = ("bundle_stages", "deadlines", "bundle_names")


def date_moves(conn: sqlite3.Connection, client_id: int, upload_id: int) -> list[dict[str, Any]]:
    """The renewal date changes this upload recorded for the client's renewals
    (history `changes`), with each renewal's country."""
    return [dict(r) for r in conn.execute(
        """SELECT r.id, r.country, c.old_value AS old_date, c.new_value AS new_date
             FROM changes c JOIN renewals r ON r.id = c.item_id
            WHERE c.upload_id = ? AND c.item_kind = 'renewal' AND c.field = 'renewal_date'
              AND r.client_id = ?""", (upload_id, client_id))]


def default_members(conn: sqlite3.Connection, client_id: int, country: str | None,
                    renewal_date: str | None) -> int:
    """How many of the client's renewals sit in this default bundle now (not
    moved into a custom one)."""
    return conn.execute(
        """SELECT COUNT(*) FROM renewals r
            WHERE r.client_id = ? AND r.country IS ? AND r.renewal_date IS ?
              AND r.id NOT IN (SELECT rb.renewal_id FROM renewal_bundles rb)""",
        (client_id, country, renewal_date)).fetchone()[0]


def has_user_data(conn: sqlite3.Connection, client_id: int, key: str, ref: str) -> bool:
    """Does anything of Martin's hang on this bundle key (stage, deadline, name,
    notes, to-dos)?"""
    for table in _KEYED:
        if conn.execute(f"SELECT 1 FROM {table} WHERE client_id = ? AND bundle_key = ? LIMIT 1",
                        (client_id, key)).fetchone():
            return True
    return any(conn.execute(f"SELECT 1 FROM {t} WHERE client_id = ? AND scope = 'bundle' AND ref = ? LIMIT 1",
                            (client_id, ref)).fetchone() for t in ("notes", "todos"))


def rekey(conn: sqlite3.Connection, client_id: int, old: str, new: str, old_ref: str, new_ref: str) -> None:
    """Move everything Martin put on bundle `old` to bundle `new`."""
    for table in _KEYED:
        conn.execute(f"UPDATE {table} SET bundle_key = ? WHERE client_id = ? AND bundle_key = ?",
                     (new, client_id, old))
    for table in ("notes", "todos"):
        conn.execute(f"UPDATE {table} SET ref = ? WHERE client_id = ? AND scope = 'bundle' AND ref = ?",
                     (new_ref, client_id, old_ref))
