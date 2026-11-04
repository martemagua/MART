"""BM+ ids inside the tracker cells (TRACKER_MAP.md §3, checked on real exports).

BM+ ids are 24-character hex strings. The same id appears bare in one
export flavour and inside a URL in the other:

* stable policy id (the same in every cycle)
    client-specific: `Policy Unique ID`, bare
    cross-client:    SECOND id in `…/policies/<cycle>;<stable>`
* per-cycle id (this renewal's upcoming policy; = the Task Tracker's "Policy ID")
    client-specific: `Renewal Unique ID`, bare
    cross-client:    FIRST id in that URL, and the last id of `…/renewals/<renewal>/<cycle>`
* BM+ renewal object
    cross-client:    first id of `…/renewals/<renewal>/<cycle>`

BM+ also writes the literal word `undefined` where an id is missing; it never
matches the 24-hex pattern, so it is simply "no id".
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_ID = r"[0-9a-f]{24}"
_BARE = re.compile(rf"^\s*({_ID})\s*$")
_POLICY_URL = re.compile(rf"/policies/({_ID}|undefined)(?:;({_ID}|undefined))?")
_RENEWAL_URL = re.compile(rf"/renewals/(?:v2/)?({_ID})(?:/({_ID}))?")
_CLIENT_URL = re.compile(rf"/client/({_ID})")


def _real(value: str | None) -> str | None:
    return value if value and value != "undefined" else None


@dataclass(frozen=True)
class RenewalIds:
    cycle_id: str | None          # per-cycle id
    expiring_policy_id: str | None  # stable id
    bm_renewal_id: str | None
    bm_client_id: str | None


def renewal_tracker_ids(policy_cell: str | None, renewal_cell: str | None) -> RenewalIds:
    """The ids of one Renewal Tracker row, from its Policy Unique ID and
    Renewal Unique ID cells (either flavour)."""
    policy = (policy_cell or "").strip()
    renewal = (renewal_cell or "").strip()
    cycle = stable = renewal_obj = client = None

    bare = _BARE.match(policy)
    if bare:                                   # client-specific: bare stable id
        stable = bare.group(1)
    else:
        m = _POLICY_URL.search(policy)
        if m:
            cycle, stable = _real(m.group(1)), _real(m.group(2))

    bare = _BARE.match(renewal)
    if bare:                                   # client-specific: bare per-cycle id
        cycle = cycle or bare.group(1)
    else:
        m = _RENEWAL_URL.search(renewal)
        if m:
            renewal_obj = m.group(1)
            cycle = cycle or m.group(2)

    for cell in (policy, renewal):
        m = _CLIENT_URL.search(cell)
        if m:
            client = m.group(1)
            break
    return RenewalIds(cycle, stable, renewal_obj, client)
