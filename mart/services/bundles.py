"""Which bundle a renewal is in, with Martin's splits and joins applied.

A bundle key is ``<country>|<renewal date>`` by default (the base key). A
**split** of a base key by some fields adds their values:
``<country>|<date>|entity=Acme%20Polska;insurer=PZU`` (values %-quoted, so
any text is safe in a key). A **join** sends every renewal of one bundle key
to another (``from_key -> into_key``), followed through chains, never round
in circles. Both are user data (bundles_repo); nothing here touches BM+.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, unquote

# The fields a bundle can be split by, in display order. Policy number is
# not in the Renewal Tracker; it comes from the renewal's BM+ tasks.
SPLIT_FIELDS = {"entity": "Entity", "insurer": "Insurer", "policy_name": "Policy name",
                "policy_number": "Policy number"}
NONE = "—"


def base_of(key: str) -> str:
    """The base key (country|date) of any bundle key."""
    return "|".join(key.split("|")[:2])


def parts_of(key: str) -> list[tuple[str, str]]:
    """The split values in a key, as (field, value)."""
    extra = key.split("|", 2)[2] if key.count("|") >= 2 else ""
    out = []
    for item in filter(None, extra.split(";")):
        field, _, value = item.partition("=")
        out.append((field, unquote(value)))
    return out


def split_key(base: str, values: list[tuple[str, str | None]]) -> str:
    if not values:
        return base
    return base + "|" + ";".join(f"{f}={quote(v or NONE, safe=' ')}" for f, v in values)


def resolve(key: str, joins: dict[str, str]) -> str:
    """Follow joins from a key to the bundle it ends up in."""
    seen = {key}
    while key in joins and joins[key] not in seen:
        key = joins[key]
        seen.add(key)
    return key


def own_key(r: dict[str, Any], base: str, splits: dict[str, list[str]],
            policy_number: str | None = None) -> str:
    """The renewal's bundle key before joins: its base, split as set up."""
    fields = [f for f in splits.get(base, []) if f in SPLIT_FIELDS]
    values = [(f, policy_number if f == "policy_number" else r.get(f)) for f in fields]
    return split_key(base, values)


def label(key: str) -> str:
    """What a split adds to the bundle's name, e.g. "Acme Polska · PZU"."""
    return " · ".join(v for _, v in parts_of(key))
