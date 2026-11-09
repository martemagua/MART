"""The stewardship (M3 day 9, Martin 08.11.2026): what a client's renewals
achieved over its reporting period, for the yearly stewardship meeting.

* **Reporting period**: a year starting on the 1st of the client's own
  month (calendar year unless set; `PERIOD_KEY` in `user_state`), or from /
  until dates for a one-off. A renewal is IN the period when its renewal
  date falls inside it — said on the page, so it is clear which policies
  count. A renewal BM+ no longer exports stays in its period.
* **Savings** per renewal, in one currency: hard savings = expiring premium
  − final premium; cost avoidance = first quote − final premium (of the
  chosen proposal ★); unrealized savings = final premium − the cheapest
  option the client didn't take. MART suggests them from Martin's quotes
  and BM+'s expiring premium (only in the same currency, never converted);
  what he confirms wins. A plan design change not implemented is not an
  unrealized saving (Martin).
* **Key learning**: one line per renewal, from the post-renewal review.
* USER data in `renewal_reviews`; BM+ is never changed.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Any

from mart.ingestion.sheet import lookup, norm
from mart.ingestion.specs import renewal_tracker as rspec
from mart.repository import (
    actuals_repo,
    clients_repo,
    plan_changes_repo,
    proposals_repo,
    renewals_repo,
    reviews_repo,
    state_repo,
)
from mart.repository.db import connection
from mart.services import actuals, plan_changes, proposals

PERIOD_KEY = "stewardship_start:{}"
MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
KINDS = {"hard": "Hard savings", "avoidance": "Cost avoidance", "unrealized": "Unrealized savings"}
HINTS = {
    "hard": "expiring premium − final premium",
    "avoidance": "first quote − final premium",
    "unrealized": "final premium − the cheapest option the client didn't take",
}
NOTE_MAX = 1_000
CHECK_SHARE = 0.5  # a suggested saving above half its base premium is flagged
_COLS = {"hard": "hard_savings", "avoidance": "cost_avoidance", "unrealized": "unrealized_savings"}
_CLOSING = next(h for label, h, _s in rspec.PROPOSAL_COLUMNS if label == "Closing premium")


class Invalid(ValueError):
    """Shown to the user as is."""


# -- the reporting period (pure) ---------------------------------------------------------
def period(
    start_month: int = 1,
    year: int | None = None,
    today: date | None = None,
    frm: str | None = None,
    until: str | None = None,
) -> dict[str, Any]:
    """The reporting year starting on the 1st of `start_month` in `year` (the
    one running today when not given), or the dates given."""
    today = today or date.today()
    if frm or until:
        try:
            a = date.fromisoformat(frm) if frm else date(1900, 1, 1)
            b = date.fromisoformat(until) if until else date(2999, 12, 31)
        except ValueError as exc:
            raise Invalid("Those dates aren't valid.") from exc
        if b < a:
            raise Invalid("The period ends before it starts.")
        return {
            "from": a.isoformat(),
            "until": b.isoformat(),
            "custom": True,
            "year": None,
            "label": f"{a.strftime('%d.%m.%Y')} – {b.strftime('%d.%m.%Y')}",
        }
    if year is None:
        year = today.year if today.month >= start_month else today.year - 1
    a = date(year, start_month, 1)
    b = (date(year + 1, start_month, 1) if start_month > 1 else date(year + 1, 1, 1)) - timedelta(days=1)
    label = str(year) if start_month == 1 else f"{year}/{str(year + 1)[2:]}"
    return {
        "from": a.isoformat(),
        "until": b.isoformat(),
        "custom": False,
        "year": year,
        "label": label,
        "start_month": start_month,
        "running": a <= today <= b,
    }


def in_period(r: dict[str, Any], p: dict[str, Any]) -> bool:
    return bool(r.get("renewal_date")) and p["from"] <= r["renewal_date"] <= p["until"]


# -- savings (pure) ------------------------------------------------------------------------
def expiring_premium(bm: dict[str, Any] | None, details: dict[str, Any] | None) -> float | None:
    """BM+'s expiring annual premium (the client's reporting currency): the
    Overview's expiring premium, else the Proposals sheet's closing premium."""
    v = lookup(bm or {}, "Annual Premium (reporting currency)", "Premium Information (Expiring")
    if isinstance(v, (int, float)) and v > 0:
        return float(v)
    for p in (details or {}).get("proposals") or []:
        v = lookup(p, _CLOSING) if isinstance(p, dict) else None
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    return None


def suggest(pv: dict[str, Any], expiring: float | None, reporting_currency: str | None) -> dict[str, Any]:
    """MART's suggestion from the proposals view (`proposals.view`): the three
    savings with what each was worked out from, or why there is none."""
    chosen = pv.get("chosen")
    final = (chosen or {}).get("latest")
    out: dict[str, Any] = {"currency": None, "why": None, **{k: None for k in KINDS}}
    if not chosen or not final or final.get("premium") is None:
        out["why"] = "Mark the chosen proposal ★ (with its final premium) and MART suggests the savings."
        return out
    cur, fp = final.get("currency"), final["premium"]
    out["currency"] = cur
    if expiring is not None and cur == reporting_currency:
        out["hard"] = {
            "amount": max(expiring - fp, 0.0),
            "basis": [("expiring (BM+)", expiring), ("final", fp)],
        }
    elif expiring is not None and not reporting_currency:
        out["hard_why"] = (
            "MART doesn't know the client's reporting currency yet, which BM+'s expiring premium "
            "is in: a single-client Renewal Tracker names it, upload one."
        )
    elif expiring is not None:
        out["hard_why"] = (
            f"BM+'s expiring premium is in the reporting currency ({reporting_currency}); "
            f"the final quote is in {cur or 'no stated currency'}."
        )
    first = chosen.get("first")
    if first and first.get("premium") is not None and first.get("currency") == cur:
        out["avoidance"] = {
            "amount": max(first["premium"] - fp, 0.0),
            "basis": [("first quote", first["premium"]), ("final", fp)],
        }
    others = [
        i["latest"]["premium"]
        for i in pv.get("items") or []
        if i["id"] != chosen["id"]
        and i.get("latest")
        and i["latest"].get("premium") is not None
        and i["latest"].get("currency") == cur
    ]
    if others:
        low = min(others)
        out["unrealized"] = {
            "amount": max(fp - low, 0.0),
            "basis": [("final", fp), ("cheapest not taken", low)],
        }
    # a saving of more than half of what it is measured against is more likely
    # quotes for another cover (one line of a bundled policy) than a saving
    for k, base in (("hard", expiring), ("avoidance", (first or {}).get("premium")), ("unrealized", fp)):
        if out[k] and base and out[k]["amount"] > base * CHECK_SHARE:
            out[k]["check"] = True
    return out


def review(row: dict[str, Any] | None, sug: dict[str, Any]) -> dict[str, Any]:
    """What counts: Martin's confirmed figures, else MART's suggestion."""
    row = row or {}
    confirmed = bool(row.get("savings_confirmed_at"))
    if confirmed:
        amounts = {k: row.get(c) for k, c in _COLS.items()}
        currency = row.get("currency")
    else:
        amounts = {k: (sug.get(k) or {}).get("amount") for k in KINDS}
        currency = sug.get("currency")
    return {
        "confirmed": confirmed,
        "amounts": amounts,
        "currency": currency,
        "note": row.get("savings_note"),
        "key_learning": row.get("key_learning"),
        "suggestion": sug,
        "any": any(v for v in amounts.values()),
    }


# -- one renewal (the panel) --------------------------------------------------------------
def for_renewal(client_id: int, renewal_id: int) -> dict[str, Any]:
    with connection() as conn:
        client = clients_repo.get(conn, client_id)
        r = renewals_repo.get(conn, renewal_id)
        if client is None or r is None or r["client_id"] != client_id:
            raise Invalid("This renewal doesn't exist.")
        pv = proposals.view(proposals_repo.for_renewal(conn, renewal_id))
        row = reviews_repo.get(conn, renewal_id)
    exp = expiring_premium(r["bm"], r["details"])
    return {
        **review(row, suggest(pv, exp, client.get("reporting_currency"))),
        "reporting_currency": client.get("reporting_currency"),
    }


# -- writing --------------------------------------------------------------------------------
def _renewal_of_mine(conn, client_id: int, renewal_id: int) -> dict[str, Any]:
    client = clients_repo.get(conn, client_id)
    r = renewals_repo.get(conn, renewal_id)
    if client is None or client["is_mine"] != 1 or r is None or r["client_id"] != client_id:
        raise Invalid("This renewal doesn't exist (or isn't one of your clients').")
    return r


def _amount(text: str | None, what: str) -> float | None:
    try:
        v = proposals.parse_number(text)
    except proposals.Invalid as exc:
        raise Invalid(f"{what}: {exc}") from exc
    if v is not None and v < 0:
        raise Invalid(f"{what} can't be negative: enter 0 when there was none.")
    return v


def save_savings(
    client_id: int,
    renewal_id: int,
    hard: str | None,
    avoidance: str | None,
    unrealized: str | None,
    currency: str | None,
    note: str | None,
) -> None:
    """Martin confirms (or corrects) the savings; an empty field = none of that kind (0)."""
    values = [
        (_amount(t, KINDS[k]) or 0.0)
        for k, t in (("hard", hard), ("avoidance", avoidance), ("unrealized", unrealized))
    ]
    cur = (currency or "").strip().upper() or None
    if cur and not (len(cur) == 3 and cur.isalpha()):
        raise Invalid("The currency is a three-letter code, e.g. EUR.")
    note = (note or "").strip() or None
    if note and len(note) > NOTE_MAX:
        raise Invalid(f"The note is too long (at most {NOTE_MAX} characters).")
    with connection() as conn:
        _renewal_of_mine(conn, client_id, renewal_id)
        reviews_repo.set_savings(conn, renewal_id, *values, cur, note)


def reset_savings(client_id: int, renewal_id: int) -> None:
    """Forget the confirmed figures: MART's suggestion counts again."""
    with connection() as conn:
        _renewal_of_mine(conn, client_id, renewal_id)
        reviews_repo.clear_savings(conn, renewal_id)


def save_learning(client_id: int, renewal_id: int, text: str | None) -> None:
    text = " ".join((text or "").split()) or None
    if text and len(text) > NOTE_MAX:
        raise Invalid(f"Keep the key learning short (at most {NOTE_MAX} characters).")
    with connection() as conn:
        _renewal_of_mine(conn, client_id, renewal_id)
        reviews_repo.set_learning(conn, renewal_id, text)


def start_month_of(conn, client_id: int) -> int:
    v = state_repo.get(conn, PERIOD_KEY.format(client_id))
    return int(v) if v and v.isdigit() and 1 <= int(v) <= 12 else 1


def set_start_month(client_id: int, month: str | None) -> None:
    if not (month or "").isdigit() or not 1 <= int(month) <= 12:
        raise Invalid("Pick the month the client's reporting year starts in.")
    with connection() as conn:
        client = clients_repo.get(conn, client_id)
        if client is None or client["is_mine"] != 1:
            raise Invalid("This client is not one of yours (or doesn't exist).")
        state_repo.put(conn, PERIOD_KEY.format(client_id), str(int(month)))


# -- the page -------------------------------------------------------------------------------
def view(
    client_id: int,
    year: int | None = None,
    frm: str | None = None,
    until: str | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """The client's renewals in the reporting period, by country, each with
    what it achieved; and the period's summary."""
    with connection() as conn:
        client = clients_repo.get(conn, client_id)
        if client is None or client["is_mine"] != 1:
            raise Invalid("This client is not one of yours (or doesn't exist).")
        start = start_month_of(conn, client_id)
        p = period(start, year, today, frm, until)
        rs = [r for r in renewals_repo.for_client(conn, client_id) if in_period(r, p)]
        ids = [r["id"] for r in rs]
        details, bms = renewals_repo.details_of(conn, ids), renewals_repo.bm_of(conn, ids)
        acts, props = actuals_repo.for_client(conn, client_id), proposals_repo.for_client(conn, client_id)
        changes, reviews = (
            plan_changes_repo.for_client(conn, client_id),
            reviews_repo.for_client(conn, client_id),
        )
    cur_rep = client.get("reporting_currency")
    rows = []
    for r in sorted(
        rs, key=lambda r: (r["country"] or "", r["renewal_date"], (r["policy_name"] or "").casefold())
    ):
        a = actuals.view(acts.get(r["id"], []), r.get("upcoming_strategy"))
        pv = proposals.view(props.get(r["id"], []))
        rev = review(
            reviews.get(r["id"]),
            suggest(pv, expiring_premium(bms.get(r["id"]), details.get(r["id"])), cur_rep),
        )
        mine = [c for c in changes if r["id"] in c["renewal_ids"]]
        chosen = pv["chosen"]
        new_insurer = (chosen or {}).get("insurer") or r["fields"].get("insurer_upcoming")
        rows.append(
            {
                **r,
                "strategy": a["effective"],
                "strategy_mine": bool(a["strategy"]),
                "remarketed": norm(a["effective"]) == "remarketing",
                "completed": a["completed"],
                "proposals": pv,
                "new_insurer": new_insurer,
                "insurer_changed": bool(
                    new_insurer and r.get("insurer") and norm(new_insurer) != norm(r["insurer"])
                ),
                "expected_change": r["fields"].get("expected_rate_change"),
                "changes": {k: [c for c in mine if c["outcome"] == k] for k in plan_changes.OUTCOMES},
                "review": rev,
            }
        )
    countries: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for x in rows:
        countries[x["country"] or "—"].append(x)
    return {
        "client": client,
        "period": p,
        "start_month": start,
        "months": MONTHS,
        "countries": dict(countries),
        "summary": summary(rows),
        "reporting_currency": cur_rep,
        "kinds": KINDS,
        "hints": HINTS,
    }


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """The period in numbers; savings per currency, never added across them."""
    savings: dict[str | None, Counter] = defaultdict(Counter)
    for x in rows:
        rv = x["review"]
        for k, v in rv["amounts"].items():
            if v:
                savings[rv["currency"]][k] += v
    change_ids = {k: {c["id"] for x in rows for c in x["changes"][k]} for k in plan_changes.OUTCOMES}
    return {
        "renewals": len(rows),
        "completed": sum(1 for x in rows if x["completed"]),
        "countries": len({x["country"] for x in rows}),
        "strategies": Counter(x["strategy"] or "—" for x in rows).most_common(),
        "remarketed": sum(1 for x in rows if x["remarketed"]),
        "insurer_changed": sum(1 for x in rows if x["insurer_changed"]),
        "proposals": sum(x["proposals"]["count"] for x in rows),
        "insurers": len({i for x in rows for i in x["proposals"]["insurers"]}),
        "savings": {cur: dict(c) for cur, c in sorted(savings.items(), key=lambda kv: kv[0] or "")},
        "confirmed": sum(1 for x in rows if x["review"]["confirmed"]),
        "suggested": sum(1 for x in rows if not x["review"]["confirmed"] and x["review"]["any"]),
        "changes": {k: len(v) for k, v in change_ids.items()},
        "learnings": sum(1 for x in rows if x["review"]["key_learning"]),
    }
