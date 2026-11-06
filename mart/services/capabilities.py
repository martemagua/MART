"""The Insurer Capability Database in use (Martin, 06.11.2026): which local
insurers partner with which international network in a country, and what
they can do there (fully insured, multinational pool, global insurance
program, captive). It helps choose the insurers to ask for proposals in a
remarketing, and shows whether a network stands behind an insurer.

Insurer names are matched WITHIN a country only, ignoring case, accents,
punctuation and the usual legal / generic words ("Allianz" =
"Allianz Lebensversicherungs-AG"); one name's words starting the other's
is a match. A reference list for all clients: an upload replaces it whole.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from mart.ingestion import countries
from mart.repository import capabilities_repo
from mart.repository.db import connection

CAPS = (("fully_insured", "Fully insured", None), ("pool", "Pool", "pool_share"),
        ("gip", "Global program", "gip_share"), ("captive", "Captive", "captive_share"))
_GENERIC = set("""ag sa s a spa sas sarl ltd limited inc co company companies corp corporation plc
    gmbh nv bv se sae cv de del la le les du des the of and y e et und group grupo holding holdings
    insurance insurances insurer assurance assurances assurer reassurance seguros seguro seguradora
    aseguradora compania compagnie cia versicherung versicherungs lebensversicherung
    lebensversicherungs life vida vie leben general generales mutual mutua bhd berhad pt tbk jsc
    oao pjsc ooo as asa ab oy kk sigorta takaful assicurazioni assicurazione""".split())


def insurer_words(name: str | None) -> tuple[str, ...]:
    """'Allianz Lebensversicherungs-AG' -> ('allianz',)."""
    text = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().casefold()
    words = [w for w in re.split(r"[^a-z0-9]+", text) if w]
    kept = tuple(w for w in words if w not in _GENERIC and len(w) > 1)
    return kept or tuple(words)


def same_insurer(a: str | None, b: str | None) -> bool:
    wa, wb = insurer_words(a), insurer_words(b)
    if not wa or not wb:
        return False
    short, long_ = sorted((wa, wb), key=len)
    return long_[:len(short)] == short


# -- reading -----------------------------------------------------------------------------
def loaded() -> dict[str, Any]:
    with connection() as conn:
        return capabilities_repo.summary(conn)


def _count(nets: list[dict[str, Any]], cap: str) -> int:
    """On how many lines of risk this capability is offered (by any network)."""
    return len({line["line"] for n in nets for line in n["lines"] if line[cap]})


def _group(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rows of one country -> one entry per local insurer (its spellings in
    the different networks merged: "Manulife" = "Manulife Financial
    Corporation – Canadian Division"), its networks and, per network, the
    lines of risk with what can be done."""
    groups: list[dict[str, Any]] = []
    for r in rows:
        ins = next((g for g in groups if any(same_insurer(r["insurer"], n) for n in g["names"])), None)
        if ins is None:
            ins = {"names": [], "networks": {}}
            groups.append(ins)
        if r["insurer"] not in ins["names"]:
            ins["names"].append(r["insurer"])
        net = ins["networks"].setdefault(r["network"], {"network": r["network"], "insurer": r["insurer"],
                                                         "lines": []})
        net["lines"].append(r)
    out = []
    for ins in groups:
        nets = sorted(ins["networks"].values(), key=lambda n: n["network"].casefold())
        for n in nets:
            n["pools"] = any(line["pool"] for line in n["lines"])
            n["local"] = any(line["fully_insured"] for line in n["lines"])
        lines = {line["line"] for n in nets for line in n["lines"]}
        names = sorted(ins["names"], key=len)
        out.append({"insurer": names[0], "names": names, "networks": nets,
                    "network_names": [n["network"] for n in nets],
                    "pools": any(n["pools"] for n in nets), "lines": len(lines),
                    "local_lines": _count(nets, "fully_insured"), "pool_lines": _count(nets, "pool")})
    return sorted(out, key=lambda i: i["insurer"].casefold())


def for_country(country: str | None, network: str | None = None, line: str | None = None) -> dict[str, Any]:
    """The local partners of a country (optionally of one network / line)."""
    ck = countries.key(country)
    with connection() as conn:
        rows = capabilities_repo.in_country(conn, ck) if ck else []
        without = capabilities_repo.no_partner_networks(conn, ck) if ck else []
    if network:
        rows = [r for r in rows if r["network"] == network]
    if line:
        rows = [r for r in rows if r["line"] == line]
    return {"country": country, "partners": _group(rows), "without": without}


def networks_of(country: str | None, names: list[str | None],
                partners: list[dict[str, Any]] | None = None) -> dict[str, list[str]]:
    """name -> the networks its local partner(s) in `country` belong to (one
    query for all names, none when `partners` is given; [] when no match)."""
    if partners is None:
        partners = for_country(country)["partners"] if country else []
    out: dict[str, list[str]] = {}
    for name in {n for n in names if n}:
        nets = sorted({net for p in partners if any(same_insurer(name, n) for n in p["names"])
                       for net in p["network_names"]}, key=str.casefold)
        out[name] = nets
    return out


def browse() -> dict[str, Any]:
    """Every country with its partners, by region (the Insurers page's start)."""
    with connection() as conn:
        rows = capabilities_repo.countries(conn)
        summary = capabilities_repo.summary(conn)
    regions: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        regions.setdefault(r["region"] or "Other", []).append(r)
    return {"regions": dict(sorted(regions.items())), "summary": summary,
            "countries": [r["country"] for r in rows]}


def filters() -> dict[str, list[str]]:
    with connection() as conn:
        return {"networks": capabilities_repo.distinct(conn, "network"),
                "lines": capabilities_repo.distinct(conn, "line")}
