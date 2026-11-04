"""Moving renewals between bundles (user data; nothing in BM+ changes).

Martin's rules (04.11.2026): renewals move individually or several at once;
into an existing custom bundle of the same country, or into a new one he
names; and back to their default bundle (country + renewal date). A bundle
never mixes countries. The placement hangs on the renewal (MART's id), so it
survives every upload.
"""

from __future__ import annotations

from mart.repository import bundles_repo, clients_repo, renewals_repo
from mart.repository.db import connection
from mart.services import bundles as bx

NAME_MAX = 120
DEFAULT = "default"     # move target: back to the renewal's default bundle
NEW = "new"             # move target: a new custom bundle


class Invalid(ValueError):
    """Shown to the user as is."""


def _name(name: str | None) -> str:
    text = " ".join((name or "").split())
    if not text:
        raise Invalid("A new bundle needs a name.")
    if len(text) > NAME_MAX:
        raise Invalid(f"A bundle name can have at most {NAME_MAX} characters.")
    return text


def move(client_id: int, renewal_ids: list[int], target: str, new_name: str | None = None) -> str:
    """Move renewals to `target` ("default", "new" or a custom bundle id).
    Returns the key of the bundle they are in now (where to go next)."""
    with connection() as conn:
        client = clients_repo.get(conn, client_id)
        if not client or client["is_mine"] != 1:
            raise Invalid("This client is not one of yours.")
        rows = [renewals_repo.get(conn, i) for i in dict.fromkeys(renewal_ids)]
        if not rows or any(r is None or r["client_id"] != client_id for r in rows):
            raise Invalid("Select the renewals to move first.")
        countries = {r["country"] or "—" for r in rows}
        if len(countries) > 1:
            raise Invalid("A bundle keeps to one country: select renewals of one country.")
        country = countries.pop()
        ids = [r["id"] for r in rows]
        if target == DEFAULT:
            bundles_repo.place(conn, ids, None)
            r = rows[0]
            return bx.default_key(r["country"], r["renewal_date"])
        if target == NEW:
            bid = bundles_repo.create(conn, client_id, country, _name(new_name))
        else:
            custom = bundles_repo.custom_bundles(conn, client_id).get(int(target) if target.isdigit() else -1)
            if custom is None:
                raise Invalid("This bundle doesn't exist.")
            if custom["country"] != country:
                raise Invalid(f"“{custom['name']}” is a {custom['country']} bundle: "
                              "a bundle keeps to one country.")
            bid = custom["id"]
        bundles_repo.place(conn, ids, bid)
        return bx.custom_key(bid)


def rename(client_id: int, key: str, name: str | None) -> str:
    """Name a bundle. A custom bundle must keep a name; a default bundle's
    name can be cleared (it is then country + date again)."""
    with connection() as conn:
        client = clients_repo.get(conn, client_id)
        if not client or client["is_mine"] != 1:
            raise Invalid("This client is not one of yours.")
        bundle_id = bx.custom_id(key)
        if bundle_id is not None:
            if bundle_id not in bundles_repo.custom_bundles(conn, client_id):
                raise Invalid("This bundle doesn't exist.")
            bundles_repo.rename(conn, bundle_id, _name(name))
        elif bx.is_default_key(key):
            bundles_repo.set_name(conn, client_id, key, _name(name) if (name or "").strip() else None)
        else:
            raise Invalid("This bundle doesn't exist.")
    return key
