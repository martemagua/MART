"""Each client's regions (schema migration 14): Martin's overrides (USER data)
and BM+'s Region column per country. All SQL for `client_regions`."""

from __future__ import annotations

import sqlite3


def overrides(conn: sqlite3.Connection, client_id: int) -> dict[str, str]:
    """country -> the region Martin set for this client."""
    return {r["country"]: r["region"] for r in conn.execute(
        "SELECT country, region FROM client_regions WHERE client_id = ?", (client_id,))}


def bm_regions(conn: sqlite3.Connection, client_id: int) -> list[tuple[str, str | None, int]]:
    """(country, BM+'s region as written, how many renewals) for the client."""
    return [(r[0], r[1], r[2]) for r in conn.execute(
        """SELECT country, region, COUNT(*) FROM renewals
            WHERE client_id = ? AND country IS NOT NULL AND country <> ''
            GROUP BY country, region""", (client_id,))]


def set_region(conn: sqlite3.Connection, client_id: int, country: str, region: str | None) -> None:
    """Store an override, or remove it (None: BM+'s region counts again)."""
    if region is None:
        conn.execute("DELETE FROM client_regions WHERE client_id = ? AND country = ?", (client_id, country))
    else:
        conn.execute("""INSERT INTO client_regions (client_id, country, region) VALUES (?, ?, ?)
                        ON CONFLICT (client_id, country)
                        DO UPDATE SET region = excluded.region, updated_at = datetime('now')""",
                     (client_id, country, region))
