"""The proposals Martin receives (M3 day 2; Martin 05.11.2026, QUESTIONS D1,
M3f): mostly recorded by him as the mails arrive, and used to COMPARE them.

* One row per quote: insurer, round (first / revised / final), the date it
  arrived, the annual premium + currency, the rate change the insurer quoted
  (%), whether the plan design is as expiring or changed, a note.
* **Compare**: per insurer, its LATEST quote counts (final > revised > first,
  then the newer date); among those, the lowest premium per currency is
  marked. One proposal can be marked **chosen**.
* BM+'s own Proposals sheet stays apart, for reference (BM+ data, read-only):
  it often fills late.
* USER data: an upload never touches it.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from mart.repository import clients_repo, proposals_repo, renewals_repo
from mart.repository.db import connection

ROUNDS = {"first": "First quote", "revised": "Revised quote", "final": "Final quote"}
PLAN_DESIGNS = {"as_expiring": "As expiring", "changed": "Changed"}
INSURER_MAX = 120
NOTE_MAX = 1_000
_ROUND_RANK = {"first": 0, "revised": 1, "final": 2}
_CURRENCY = re.compile(r"^[A-Z]{3}$")


class Invalid(ValueError):
    """Shown to the user as is."""


# -- numbers as people type them ------------------------------------------------------
def parse_number(text: str | None, thousands: bool = True) -> float | None:
    """'120 000', "120'000", '120.000,50', '120,000.50', '+8', '-3,5 %' ->
    float; empty -> None. With one separator only, it is a thousands
    separator when exactly three digits follow and `thousands` is on (a
    premium), else the decimal point (a rate)."""
    if not (text or "").strip():
        return None
    if not re.search(r"\d", text):
        raise Invalid(f"“{text}” isn't a number.")
    s = re.sub(r"[\s'’%+]|[A-Za-z€$£]", "", text)
    neg = s.startswith("-")
    s = s.lstrip("-")
    if "," in s and "." in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        s = s.replace("." if dec == "," else ",", "").replace(dec, ".")
    elif s.count(",") + s.count(".") > 0:
        sep = "," if "," in s else "."
        parts = s.split(sep)
        if len(parts) > 2 or (thousands and len(parts[-1]) == 3):
            s = "".join(parts)
        else:
            s = ".".join(parts)
    if not re.fullmatch(r"\d+(\.\d+)?", s):
        raise Invalid(f"“{text}” isn't a number.")
    value = float(s)
    return -value if neg else value


def _clean(form: dict[str, str | None]) -> dict[str, Any]:
    insurer = (form.get("insurer") or "").strip()
    if not insurer:
        raise Invalid("Which insurer is the proposal from?")
    if len(insurer) > INSURER_MAX:
        raise Invalid(f"The insurer's name is too long (at most {INSURER_MAX} characters).")
    rnd = (form.get("round") or "first").strip()
    if rnd not in ROUNDS:
        raise Invalid("Pick first, revised or final quote.")
    design = (form.get("plan_design") or "as_expiring").strip()
    if design not in PLAN_DESIGNS:
        raise Invalid("Pick the plan design: as expiring or changed.")
    received = (form.get("received_on") or "").strip()
    try:
        received = date.fromisoformat(received).isoformat() if received else date.today().isoformat()
    except ValueError as exc:
        raise Invalid("That date isn't valid.") from exc
    premium = parse_number(form.get("premium"))
    if premium is not None and premium < 0:
        raise Invalid("A premium can't be negative.")
    currency = (form.get("currency") or "").strip().upper() or None
    if currency and not _CURRENCY.match(currency):
        raise Invalid("The currency is a three-letter code, e.g. EUR.")
    note = (form.get("note") or "").strip() or None
    if note and len(note) > NOTE_MAX:
        raise Invalid(f"The note is too long (at most {NOTE_MAX} characters).")
    return {"insurer": insurer, "round": rnd, "received_on": received, "premium": premium,
            "currency": currency if premium is not None or currency else None,
            "rate_change": parse_number(form.get("rate_change"), thousands=False),
            "plan_design": design, "note": note}


# -- reading (pure) ----------------------------------------------------------------------
def _latest_key(p: dict[str, Any]) -> tuple:
    return (_ROUND_RANK.get(p["round"], 0), p.get("received_on") or "", p["id"])


def view(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """The comparison for one renewal: every quote, each insurer's latest one
    marked `current`, the lowest current premium per currency marked `lowest`;
    plus the short summary the cards show."""
    latest: dict[str, dict[str, Any]] = {}
    for p in rows:
        key = p["insurer"].casefold()
        if key not in latest or _latest_key(p) > _latest_key(latest[key]):
            latest[key] = p
    current_ids = {p["id"] for p in latest.values()}
    lowest: dict[str | None, dict[str, Any]] = {}
    for p in latest.values():
        if p["premium"] is not None and (p["currency"] not in lowest
                                         or p["premium"] < lowest[p["currency"]]["premium"]):
            lowest[p["currency"]] = p
    multi = len([p for p in latest.values() if p["premium"] is not None]) > 1
    lowest_ids = {p["id"] for p in lowest.values()} if multi else set()
    items = sorted(({**p, "current": p["id"] in current_ids, "lowest": p["id"] in lowest_ids,
                     "round_label": ROUNDS.get(p["round"], p["round"]),
                     "design_label": PLAN_DESIGNS.get(p["plan_design"], p["plan_design"])}
                    for p in rows),
                   key=lambda p: (not p["current"], p["premium"] is None, p["premium"] or 0,
                                  p["insurer"].casefold()))
    chosen = next((p for p in items if p["chosen"]), None)
    return {"items": items, "count": len(rows),
            "insurers": sorted({p["insurer"] for p in rows}, key=str.casefold),
            "chosen": chosen}


# -- writing ----------------------------------------------------------------------------
def _renewal_of_mine(conn, client_id: int, renewal_id: int) -> dict[str, Any]:
    client = clients_repo.get(conn, client_id)
    r = renewals_repo.get(conn, renewal_id)
    if client is None or client["is_mine"] != 1 or r is None or r["client_id"] != client_id:
        raise Invalid("This renewal doesn't exist (or isn't one of your clients').")
    return r


def _proposal_of_mine(conn, client_id: int, proposal_id: int) -> dict[str, Any]:
    p = proposals_repo.get(conn, proposal_id)
    if p is None:
        raise Invalid("This proposal doesn't exist any more.")
    _renewal_of_mine(conn, client_id, p["renewal_id"])
    return p


def add(client_id: int, renewal_id: int, form: dict[str, str | None]) -> int:
    values = _clean(form)
    with connection() as conn:
        _renewal_of_mine(conn, client_id, renewal_id)
        return proposals_repo.add(conn, renewal_id, values)


def edit(client_id: int, proposal_id: int, form: dict[str, str | None]) -> None:
    values = _clean(form)
    with connection() as conn:
        _proposal_of_mine(conn, client_id, proposal_id)
        proposals_repo.update(conn, proposal_id, values)


def delete(client_id: int, proposal_id: int) -> None:
    with connection() as conn:
        _proposal_of_mine(conn, client_id, proposal_id)
        proposals_repo.delete(conn, proposal_id)


def choose(client_id: int, proposal_id: int, chosen: bool) -> None:
    """Mark this proposal as the chosen one of its renewal (or un-mark it)."""
    with connection() as conn:
        p = _proposal_of_mine(conn, client_id, proposal_id)
        proposals_repo.set_chosen(conn, p["renewal_id"], proposal_id if chosen else None)


def insurer_suggestions(client_id: int) -> list[str]:
    with connection() as conn:
        return proposals_repo.insurers_of_client(conn, client_id)
