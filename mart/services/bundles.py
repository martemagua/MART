"""Bundle keys.

A renewal is in its **default bundle** (same client, country and renewal
date), key ``<country>|<renewal date>``, unless Martin moved it into a
**custom bundle**: a named bundle of the same country, key ``custom|<id>``
(bundles_repo). A custom bundle's renewals may renew on different dates.
"""

from __future__ import annotations

NO_DATE = "none"
CUSTOM = "custom"


def default_key(country: str | None, renewal_date: str | None) -> str:
    return f"{country or '—'}|{renewal_date or NO_DATE}"


def custom_key(bundle_id: int) -> str:
    return f"{CUSTOM}|{bundle_id}"


def custom_id(key: str) -> int | None:
    """The custom bundle id in a key, or None for a default bundle."""
    kind, _, rest = key.partition("|")
    return int(rest) if kind == CUSTOM and rest.isdigit() else None
