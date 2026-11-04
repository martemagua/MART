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


def is_default_key(key: str) -> bool:
    country, sep, rdate = key.partition("|")
    return bool(sep) and country != CUSTOM and "|" not in rdate and (rdate == NO_DATE or rdate[:4].isdigit())


def split_default(key: str) -> tuple[str, str | None]:
    """(country, renewal date or None) of a default key."""
    country, _, rdate = key.partition("|")
    return country, None if rdate == NO_DATE else rdate
