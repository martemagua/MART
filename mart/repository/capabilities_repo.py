"""The Insurer Capability Database (schema migration 11): a GLOBAL reference
list, replaced as a whole by each upload. All SQL for `insurer_capabilities`."""

from __future__ import annotations

import sqlite3
from typing import Any

COLUMNS = ("cap_key", "network", "region", "country", "country_key", "insurer", "line",
           "fully_insured", "fully_insured_text", "pool", "pool_text", "pool_share", "pool_share_text",
           "gip", "gip_text", "gip_share", "gip_share_text", "captive", "captive_text",
           "captive_share", "captive_share_text", "comments", "content_hash", "upload_id")


def hashes(conn: sqlite3.Connection) -> dict[str, str]:
    """cap_key -> content hash of what is stored (to preview an upload)."""
    return {r[0]: r[1] for r in conn.execute("SELECT cap_key, content_hash FROM insurer_capabilities")}


def replace_all(conn: sqlite3.Connection, rows: list[dict[str, Any]], upload_id: int) -> None:
    conn.execute("DELETE FROM insurer_capabilities")
    marks = ", ".join("?" * len(COLUMNS))
    conn.executemany(
        f"INSERT INTO insurer_capabilities ({', '.join(COLUMNS)}) VALUES ({marks})",
        [tuple(upload_id if c == "upload_id" else r["key"] if c == "cap_key" else r.get(c)
               for c in COLUMNS) for r in rows])


def in_country(conn: sqlite3.Connection, country_key: str) -> list[dict[str, Any]]:
    """Every partner row of one country (all networks, all lines)."""
    return [dict(r) for r in conn.execute(
        """SELECT * FROM insurer_capabilities WHERE country_key = ? AND insurer IS NOT NULL
            ORDER BY insurer COLLATE NOCASE, network, line""", (country_key,))]


def no_partner_networks(conn: sqlite3.Connection, country_key: str) -> list[str]:
    """Networks with no partner in this country."""
    return [r[0] for r in conn.execute(
        """SELECT DISTINCT network FROM insurer_capabilities WHERE country_key = ?
            AND network NOT IN (SELECT network FROM insurer_capabilities
                                 WHERE country_key = ? AND insurer IS NOT NULL)
            ORDER BY network""", (country_key, country_key))]


def countries(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every country with its key, region and how many partners it has."""
    return [dict(r) for r in conn.execute(
        """SELECT country_key, MIN(country) AS country, MIN(region) AS region,
                  COUNT(DISTINCT insurer) AS partners
             FROM insurer_capabilities GROUP BY country_key ORDER BY MIN(country) COLLATE NOCASE""")]


def summary(conn: sqlite3.Connection) -> dict[str, Any]:
    r = conn.execute(
        """SELECT COUNT(*) AS rows, COUNT(DISTINCT network) AS networks,
                  COUNT(DISTINCT country_key) AS countries,
                  COUNT(DISTINCT country_key || '|' || insurer) AS partners, MAX(upload_id) AS upload_id
             FROM insurer_capabilities""").fetchone()
    return dict(r)


def distinct(conn: sqlite3.Connection, column: str) -> list[str]:
    """The networks or lines of risk in the list (the Insurers page's filters)."""
    if column not in ("network", "line"):
        raise ValueError(column)
    return [r[0] for r in conn.execute(
        f"SELECT DISTINCT {column} FROM insurer_capabilities ORDER BY {column} COLLATE NOCASE")]
