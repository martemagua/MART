"""Each client's regions (M3 day 5; Martin 05.11.2026, QUESTIONS C4, M3e):
clients split the world differently (one has "Americas", another "LatAm" +
"North America"), so a country's region is set PER CLIENT.

* Prefilled from BM+'s Region column (M3e: use the existing regions): per
  country the commonest value BM+ writes, cleaned ("EMEA, EMEA" -> "EMEA").
* Martin can change any country's region for that client; empty (or the
  same as BM+'s) goes back to BM+'s. BM+ itself is never changed.
* The explorer's side panel filters by region; the board (day 6) will too.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from mart.repository import clients_repo, regions_repo
from mart.repository.db import connection

REGION_MAX = 60


class Invalid(ValueError):
    """Shown to the user as is."""


def clean(region: str | None) -> str | None:
    """BM+'s region as one name: "EMEA, EMEA" -> "EMEA"; empty -> None."""
    parts = [p.strip() for p in (region or "").split(",") if p.strip()]
    return parts[0] if parts and all(p.casefold() == parts[0].casefold() for p in parts) else \
        (", ".join(dict.fromkeys(parts)) or None)


def table(bm_rows: list[tuple[str, str | None, int]], mine: dict[str, str]) -> list[dict[str, Any]]:
    """One row per country: BM+'s region (the commonest), Martin's, the one
    that counts, and how many renewals (pure)."""
    by_country: dict[str, Counter] = {}
    renewals: Counter = Counter()
    for country, region, n in bm_rows:
        renewals[country] += n
        cleaned = clean(region)
        if cleaned:
            by_country.setdefault(country, Counter())[cleaned] += n
    out = []
    for country in sorted(set(renewals) | set(mine), key=str.casefold):
        bm = by_country[country].most_common(1)[0][0] if country in by_country else None
        out.append({"country": country, "bm": bm, "mine": mine.get(country),
                    "region": mine.get(country) or bm, "renewals": renewals.get(country, 0)})
    return out


def of_client(conn, client_id: int) -> dict[str, str | None]:
    """country -> the region that counts for this client (in a connection the
    caller holds: the explorer reads it with everything else)."""
    return {r["country"]: r["region"] for r in table(regions_repo.bm_regions(conn, client_id),
                                                     regions_repo.overrides(conn, client_id))}


def for_client(client_id: int) -> dict[str, Any]:
    """The Regions page: every country of the client with its regions."""
    with connection() as conn:
        _mine(conn, client_id)
        rows = table(regions_repo.bm_regions(conn, client_id), regions_repo.overrides(conn, client_id))
    return {"rows": rows, "regions": sorted({r["region"] for r in rows if r["region"]}, key=str.casefold),
            "changed": sum(1 for r in rows if r["mine"])}


def save(client_id: int, regions: dict[str, str | None]) -> int:
    """Save the regions of several countries at once (country -> text). An
    empty one, or one equal to BM+'s, goes back to BM+'s. Returns how many
    countries now have a region of Martin's."""
    with connection() as conn:
        _mine(conn, client_id)
        rows = {r["country"]: r for r in table(regions_repo.bm_regions(conn, client_id),
                                               regions_repo.overrides(conn, client_id))}
        for country, text in regions.items():
            if country not in rows:
                raise Invalid(f"{country} isn't one of this client's countries.")
            text = " ".join((text or "").split())
            if len(text) > REGION_MAX:
                raise Invalid(f"A region's name is at most {REGION_MAX} characters.")
            same = text.casefold() == (rows[country]["bm"] or "").casefold()
            regions_repo.set_region(conn, client_id, country, None if not text or same else text)
        return len(regions_repo.overrides(conn, client_id))


def _mine(conn, client_id: int) -> None:
    client = clients_repo.get(conn, client_id)
    if client is None or client["is_mine"] != 1:
        raise Invalid("This client is not one of yours (or doesn't exist).")
