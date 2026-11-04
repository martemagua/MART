"""Time limits and other tweakable numbers, edited under Settings → Time limits.

Stored in the database (`user_state`, keys `pref:<name>`), not in the
settings file: they belong to the data, travel with it and are in the
backups. Each preference is declared once here, with its default and range,
so a new one is a single entry.
"""

from __future__ import annotations

from dataclasses import dataclass

from mart.repository import state_repo
from mart.repository.db import connection


@dataclass(frozen=True)
class Pref:
    name: str
    label: str
    default: int
    minimum: int
    maximum: int
    unit: str
    help: str


PREFS: dict[str, Pref] = {p.name: p for p in [
    Pref("overview_data_stale_days", "Overview data out of date after", 7, 1, 90, "days",
         "The overview comes from single-client exports. When the last one for a client is "
         "older than this, MART highlights it, so old comments aren't read as current."),
    Pref("overview_amber_days", "Overview getting old after", 7, 1, 90, "days",
         "A renewal turns amber when its newest overview entry (by the date written on it) "
         "is at least this old."),
    Pref("overview_red_days", "Overview stale after", 14, 1, 180, "days",
         "A renewal turns red when its newest overview entry is at least this old. "
         "Never earlier than the amber limit."),
    Pref("overview_new_days", "Overview entry counts as new for", 7, 0, 60, "days",
         "Entries dated within this many days are marked new. 0 = no new marks."),
]}


def get(name: str) -> int:
    p = PREFS[name]
    with connection() as conn:
        raw = state_repo.get(conn, f"pref:{name}")
    try:
        value = int(raw) if raw is not None else p.default
    except ValueError:
        return p.default
    return min(max(value, p.minimum), p.maximum)


def all_values() -> dict[str, int]:
    return {name: get(name) for name in PREFS}


def save(values: dict[str, str]) -> list[str]:
    """Validate and store; returns error messages (nothing stored if any)."""
    errors, clean = [], {}
    for name, raw in values.items():
        p = PREFS.get(name)
        if p is None:
            continue
        try:
            n = int(str(raw).strip())
            if not p.minimum <= n <= p.maximum:
                raise ValueError
        except ValueError:
            errors.append(f"{p.label}: a whole number from {p.minimum} to {p.maximum} {p.unit}.")
            continue
        clean[name] = n
    if not errors:
        with connection() as conn:
            for name, n in clean.items():
                state_repo.put(conn, f"pref:{name}", str(n))
    return errors
