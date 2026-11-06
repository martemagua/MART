"""The proposals Martin receives (M3 day 2; Martin 05.11.2026, QUESTIONS D1,
M3f): mostly recorded by him as the mails arrive, and used to COMPARE them.

* A **proposal** = one insurer + one variant: plan design as expiring or
  changed, and an optional label ("with dental"). It holds its **quotes**
  (Martin, 06.11.2026): first, revised…, final, each with the date it
  arrived, the annual premium + currency, the rate change the insurer quoted
  (%) and a note — so a negotiation is one entry, not a long list. Adding a
  quote for an insurer + variant that already has a proposal adds it there.
* **Compare**: each proposal's LATEST quote counts (final > revised >
  first, then the newer date); among those, the lowest premium per currency
  is marked, and each shows how far it moved from its first priced quote.
  One proposal can be marked **chosen**.
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
from mart.services import capabilities

ROUNDS = {"first": "First quote", "revised": "Revised quote", "final": "Final quote"}
PLAN_DESIGNS = {"as_expiring": "As expiring", "changed": "Changed"}
INSURER_MAX = 120
LABEL_MAX = 80
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


def _clean_proposal(form: dict[str, str | None]) -> dict[str, Any]:
    insurer = (form.get("insurer") or "").strip()
    if not insurer:
        raise Invalid("Which insurer is the proposal from?")
    if len(insurer) > INSURER_MAX:
        raise Invalid(f"The insurer's name is too long (at most {INSURER_MAX} characters).")
    design = (form.get("plan_design") or "as_expiring").strip()
    if design not in PLAN_DESIGNS:
        raise Invalid("Pick the plan design: as expiring or changed.")
    label = (form.get("label") or "").strip() or None
    if label and len(label) > LABEL_MAX:
        raise Invalid(f"The label is too long (at most {LABEL_MAX} characters).")
    return {"insurer": insurer, "plan_design": design, "label": label}


def _clean_quote(form: dict[str, str | None]) -> dict[str, Any]:
    rnd = (form.get("round") or "first").strip()
    if rnd not in ROUNDS:
        raise Invalid("Pick first, revised or final quote.")
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
    return {"round": rnd, "received_on": received, "premium": premium, "currency": currency,
            "rate_change": parse_number(form.get("rate_change"), thousands=False), "note": note}


# -- reading (pure) ----------------------------------------------------------------------
def _quote_key(q: dict[str, Any]) -> tuple:
    return (_ROUND_RANK.get(q["round"], 0), q.get("received_on") or "", q["id"])


def next_round(latest: str | None) -> str:
    """What the "+ Quote" form offers after the latest quote."""
    return "final" if latest == "final" else "revised" if latest else "first"


def _one(p: dict[str, Any]) -> dict[str, Any]:
    quotes = [{**q, "round_label": ROUNDS.get(q["round"], q["round"])}
              for q in sorted(p.get("quotes") or [], key=_quote_key)]
    latest = quotes[-1] if quotes else None
    first = next((q for q in quotes if q["premium"] is not None), None)
    moved = None
    if (latest and first and latest is not first and latest["premium"] is not None and first["premium"]
            and latest["currency"] == first["currency"]):
        moved = round((latest["premium"] - first["premium"]) / first["premium"] * 100, 1)
    return {**p, "quotes": quotes, "latest": latest, "first": first, "moved": moved,
            "design_label": PLAN_DESIGNS.get(p["plan_design"], p["plan_design"]),
            "next_round": next_round(latest["round"] if latest else None)}


def view(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """The comparison for one renewal: one item per proposal with its quotes
    in order, the latest one counting; the lowest latest premium per currency
    marked `lowest` (with two or more priced); plus the cards' summary."""
    items = [_one(p) for p in rows]
    priced = [i for i in items if i["latest"] and i["latest"]["premium"] is not None]
    lowest: dict[str | None, dict[str, Any]] = {}
    for i in priced:
        cur = i["latest"]["currency"]
        if cur not in lowest or i["latest"]["premium"] < lowest[cur]["latest"]["premium"]:
            lowest[cur] = i
    lowest_ids = {i["id"] for i in lowest.values()} if len(priced) > 1 else set()
    for i in items:
        i["lowest"] = i["id"] in lowest_ids
    items.sort(key=lambda i: (not (i["latest"] and i["latest"]["premium"] is not None),
                              (i["latest"] or {}).get("premium") or 0, i["insurer"].casefold()))
    return {"items": items, "count": len(items), "quotes": sum(len(i["quotes"]) for i in items),
            "insurers": sorted({i["insurer"] for i in items}, key=str.casefold),
            "chosen": next((i for i in items if i["chosen"]), None)}


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


def _quote_of_mine(conn, client_id: int, quote_id: int) -> dict[str, Any]:
    q = proposals_repo.get_quote(conn, quote_id)
    if q is None:
        raise Invalid("This quote doesn't exist any more.")
    _proposal_of_mine(conn, client_id, q["proposal_id"])
    return q


def _add(conn, renewal_id: int, proposal: dict[str, Any], quote: dict[str, Any]) -> int:
    existing = proposals_repo.find(conn, renewal_id, proposal["insurer"], proposal["plan_design"],
                                   proposal["label"])
    pid = existing["id"] if existing else proposals_repo.add(conn, renewal_id, proposal)
    proposals_repo.add_quote(conn, pid, quote)
    return pid


def add(client_id: int, renewal_id: int, form: dict[str, str | None]) -> int:
    """A new proposal with its first quote; for an insurer + variant that
    already has one, the quote joins it. Returns the proposal's id."""
    proposal, quote = _clean_proposal(form), _clean_quote(form)
    with connection() as conn:
        _renewal_of_mine(conn, client_id, renewal_id)
        return _add(conn, renewal_id, proposal, quote)


def add_many(client_id: int, renewal_ids: list[int], form: dict[str, str | None],
             premiums: dict[int, str | None]) -> int:
    """The same proposal / quote for several renewals at once (the bundle's
    edit mode, Martin 06.11.2026): one insurer, variant, round, date, rate
    and note, each renewal with its own premium (`premiums`, as typed).
    Where that insurer + variant already has a proposal, the quote joins it.
    All or nothing. Returns how many renewals got one."""
    if not renewal_ids:
        raise Invalid("Tick at least one renewal first.")
    proposal = _clean_proposal(form)
    quotes = {rid: _clean_quote({**form, "premium": premiums.get(rid)}) for rid in renewal_ids}
    with connection() as conn:
        for rid in renewal_ids:
            _renewal_of_mine(conn, client_id, rid)
            _add(conn, rid, proposal, quotes[rid])
    return len(renewal_ids)


def insurer_choices(client_id: int, country: str | None) -> dict[str, Any]:
    """What the insurer field suggests for a country: its network partners
    (Insurer Capability Database) first, then this client's insurers there."""
    with connection() as conn:
        mine = proposals_repo.insurers_of_client(conn, client_id, country)
    partners = capabilities.for_country(country)["partners"] if country else []
    return {"partners": partners, "insurers": mine}


def edit(client_id: int, proposal_id: int, form: dict[str, str | None]) -> None:
    """The proposal itself: insurer, plan design, label (its quotes stay)."""
    values = _clean_proposal(form)
    with connection() as conn:
        _proposal_of_mine(conn, client_id, proposal_id)
        proposals_repo.update(conn, proposal_id, values)


def delete(client_id: int, proposal_id: int) -> None:
    with connection() as conn:
        _proposal_of_mine(conn, client_id, proposal_id)
        proposals_repo.delete(conn, proposal_id)


def add_quote(client_id: int, proposal_id: int, form: dict[str, str | None]) -> int:
    values = _clean_quote(form)
    with connection() as conn:
        _proposal_of_mine(conn, client_id, proposal_id)
        return proposals_repo.add_quote(conn, proposal_id, values)


def edit_quote(client_id: int, quote_id: int, form: dict[str, str | None]) -> None:
    values = _clean_quote(form)
    with connection() as conn:
        _quote_of_mine(conn, client_id, quote_id)
        proposals_repo.update_quote(conn, quote_id, values)


def delete_quote(client_id: int, quote_id: int) -> None:
    """Delete one quote; the proposal stays (even without quotes)."""
    with connection() as conn:
        _quote_of_mine(conn, client_id, quote_id)
        proposals_repo.delete_quote(conn, quote_id)


def choose(client_id: int, proposal_id: int, chosen: bool) -> None:
    """Mark this proposal as the chosen one of its renewal (or un-mark it)."""
    with connection() as conn:
        p = _proposal_of_mine(conn, client_id, proposal_id)
        proposals_repo.set_chosen(conn, p["renewal_id"], proposal_id if chosen else None)
