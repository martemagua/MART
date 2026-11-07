"""Plan design changes (M3 day 4, reshaped with Martin 07.11.2026): what
changes in a policy's benefit design (a co-payment, a limit, a coverage
percentage…) and, in the end, whether it was implemented, and if not, why.
For the renewal itself, the post-renewal review and the yearly stewardship
meeting.

* ONE change covers ONE OR MORE renewals: many renewals are one bundled
  policy over several entities, or one policy split by line of coverage.
  Added from the bundle it covers all of the bundle's renewals unless some
  are unticked; added from a renewal, that renewal (others can be ticked).
* Its outcome: **open** (on the table) → **implemented** (takes effect with
  the renewal) or **not implemented**, with why. Brokers and insurers
  propose them; who proposed one is not recorded (Martin).
* An optional premium effect: an amount in a currency, or a % (it rarely
  comes up, but it is worth keeping when it does).
* **In BM+**: the Renewal Strategy sheet's "Types of plan design changes"
  and the Overview's "Plan Design Comments", split into one line per change.
  Each line can be tracked (it becomes a change, covering every renewal of
  the bundle whose BM+ text has the same line) or dismissed for those
  renewals. BM+ is never changed.
* USER data: an upload never touches it.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from mart.ingestion.sheet import lookup, norm
from mart.ingestion.specs import renewal_tracker as rspec
from mart.repository import clients_repo, plan_changes_repo, renewals_repo
from mart.repository.db import connection
from mart.services import proposals

OUTCOMES = {"open": "Open", "implemented": "Implemented", "not_implemented": "Not implemented"}
TITLE_MAX = 200
DETAIL_MAX = 1_000
_YES = {"yes", "y", "true", "1"}
_TYPES = next(h for label, h, _s in rspec.STRATEGY_FIELDS if label == "Types of plan design changes")
_REASONS = next(h for label, h, _s in rspec.STRATEGY_FIELDS if label == "Reasons for plan design changes")
_CONSIDERED = next(h for label, h, _s in rspec.STRATEGY_FIELDS if label == "Plan design changes considered?")
_BULLET = re.compile(r"^\s*(?:[-–—•*·]+|\d{1,2}[.)])\s*")


class Invalid(ValueError):
    """Shown to the user as is."""


# -- BM+'s text (pure) ---------------------------------------------------------------------
def _text(value: Any) -> str | None:
    text = str(value or "").replace("_x000D_", "").strip()
    return None if norm(text) in ("", "na", "none", "no", "tbc") else text


def split_lines(text: str | None) -> list[str]:
    """BM+'s free text → one line per change: split at line breaks and bullets,
    the bullet itself dropped ("- Out-patient co-payment 90%\\n-Chronic …")."""
    out: list[str] = []
    for raw in re.split(r"[\r\n•]+", text or ""):
        line = _BULLET.sub("", raw).strip(" ;,")
        if norm(line) and line not in out:
            out.append(line[:TITLE_MAX])
    return out


def bm_info(fields: dict[str, Any] | None, details: dict[str, Any] | None) -> dict[str, Any]:
    """What BM+ says about plan design changes for this renewal: considered?,
    the reason, and the changes as lines (the Strategy sheet's types first,
    then the Overview's comments, each line once). `whole` = the keys of the
    unsplit texts, which a change taken over before 0.9.29 carries."""
    f = fields or {}
    strategy = next((r for r in (details or {}).get("strategy") or [] if isinstance(r, dict)), {})
    considered = str((lookup(strategy, _CONSIDERED) if strategy else None) or f.get("pdc_considered") or "")
    texts = [_text(lookup(strategy, _TYPES)) if strategy else None, _text(f.get("pdc_comments"))]
    lines: list[str] = []
    for t in texts:
        for line in split_lines(t):
            if norm(line) not in {norm(x) for x in lines}:
                lines.append(line)
    return {"considered": considered.strip() or None,
            "reason": (_text(lookup(strategy, _REASONS)) if strategy else None) or "",
            "lines": lines, "whole": {norm(t[:TITLE_MAX]) for t in texts if t}}


# -- reading (pure) -------------------------------------------------------------------------
def _label(r: dict[str, Any]) -> str:
    """"Medical (Acme Polska)": a renewal among its bundle's."""
    name = r.get("policy_name") or "—"
    return f"{name} ({r['entity']})" if r.get("entity") else name


def _line_key(c: dict[str, Any]) -> str | None:
    return norm(c["bm_line"]) if c.get("bm_line") else None


def _line_state(key: str, info: dict[str, Any], rid: int, changes: list[dict[str, Any]],
                dismissed: set[str]) -> str:
    """'tracked' / 'dismissed' / 'new' for one BM+ line on one renewal."""
    keys = {key} | info["whole"]
    if any(_line_key(c) in keys and rid in c["renewal_ids"] for c in changes):
        return "tracked"
    if {norm(d) for d in dismissed} & keys:
        return "dismissed"
    return "new"


def view(changes: list[dict[str, Any]], renewals: list[dict[str, Any]],
         dismissed: dict[int, set[str]] | None = None, known: dict[int, dict[str, Any]] | None = None,
         focus: int | None = None, with_bm: bool = True) -> dict[str, Any]:
    """The plan design changes of a bundle (`renewals`), or of one renewal of
    it (`focus`): the changes (open first), the counts, BM+'s lines with what
    became of each, and the bundle's renewals for the "covers" tick boxes.
    `known` names renewals a change covers outside the bundle."""
    dismissed = dismissed or {}
    by_id = {**(known or {}), **{r["id"]: r for r in renewals}}
    bundle_ids = [r["id"] for r in renewals]
    if focus is not None:
        shown = [c for c in changes if focus in c["renewal_ids"]]
    else:
        shown = [c for c in changes if set(c["renewal_ids"]) & set(bundle_ids)]
    order = {"open": 0, "implemented": 1, "not_implemented": 2}
    choices = [{"id": r["id"], "label": _label(r)} for r in renewals]
    items = []
    for c in sorted(shown, key=lambda c: (order[c["outcome"]], c["id"])):
        covers = [by_id[i] for i in c["renewal_ids"] if i in by_id]
        dates = sorted(r["renewal_date"] for r in covers if r.get("renewal_date"))
        items.append({**c, "outcome_label": OUTCOMES[c["outcome"]], "covers": covers,
                      "cover_labels": [_label(r) for r in covers],
                      "all_bundle": set(bundle_ids) <= set(c["renewal_ids"]) and len(bundle_ids) > 1,
                      "takes_effect": dates[0] if dates else None, "cost_input": cost_input(c),
                      # its ✎ form ticks among the bundle's renewals + those it covers elsewhere
                      "choices": choices + [{"id": r["id"], "label": _label(r)} for r in covers
                                            if r["id"] not in bundle_ids]})
    counts = {k: sum(1 for c in shown if c["outcome"] == k) for k in OUTCOMES}
    out = {"items": items, "count": len(items), "counts": counts, "bm": None, "focus": focus,
           "renewals": choices}
    if with_bm:
        out["bm"] = _bm_view(changes, renewals, dismissed, focus)
    return out


def _bm_view(changes: list[dict[str, Any]], renewals: list[dict[str, Any]], dismissed: dict[int, set[str]],
             focus: int | None) -> dict[str, Any] | None:
    bundle_ids = [r["id"] for r in renewals]
    # BM+'s lines: of the focus renewal (each also covering the bundle's other
    # renewals with the same line), or of the whole bundle
    infos = {r["id"]: bm_info(r.get("fields"), r.get("details")) for r in renewals}
    own = [focus] if focus is not None else bundle_ids
    lines: dict[str, dict[str, Any]] = {}
    for rid in own:
        for line in infos.get(rid, {}).get("lines", []):
            lines.setdefault(norm(line), {"text": line, "key": norm(line)})
    bm_lines = []
    for key, ln in lines.items():
        having = [rid for rid in bundle_ids if key in {norm(x) for x in infos[rid]["lines"]}]
        states = {rid: _line_state(key, infos[rid], rid, changes, dismissed.get(rid, set()))
                  for rid in having}
        pending = [rid for rid, s in states.items() if s == "new"]
        mine = states.get(focus) if focus is not None else None
        state = mine or ("new" if pending else "tracked" if "tracked" in states.values() else "dismissed")
        bm_lines.append({**ln, "renewal_ids": having, "pending_ids": pending, "state": state,
                         "dismissed_ids": [rid for rid, s in states.items() if s == "dismissed"],
                         "of": len(having)})
    considered = next((infos[rid]["considered"] for rid in own if infos.get(rid, {}).get("considered")), None)
    reason = next((infos[rid]["reason"] for rid in own if infos.get(rid, {}).get("reason")), "")
    if not (considered or bm_lines):
        return None
    return {"considered": considered, "reason": reason, "lines": bm_lines,
            "new": sum(1 for ln in bm_lines if ln["state"] == "new")}


def counts_for(changes: list[dict[str, Any]], renewal_id: int) -> dict[str, int]:
    """A renewal card's counts by outcome."""
    mine = [c for c in changes if renewal_id in c["renewal_ids"]]
    return {"count": len(mine), **{k: sum(1 for c in mine if c["outcome"] == k) for k in OUTCOMES}}


def cost_input(c: dict[str, Any]) -> str:
    """The stored premium effect as it is typed back: "-2.5 %", "-25000 EUR"."""
    a = c.get("cost_amount")
    if a is None:
        return ""
    num = f"{a:g}" if abs(a) < 1e15 else str(a)
    return f"{num} {c.get('cost_unit') or ''}".strip()


def parse_cost(text: str | None) -> tuple[float | None, str | None]:
    """The premium effect as typed: "-2,5 %" → (-2.5, '%'); "-25'000 EUR" /
    "EUR -25'000" → (-25000, 'EUR'); "-25'000" → (-25000, None); "" → none."""
    text = (text or "").strip()
    if not text:
        return None, None
    unit = "%" if "%" in text else None
    if unit is None:
        m = re.search(r"^\s*([A-Z]{3})\s|\s([A-Z]{3})\s*$", text)
        unit = (m.group(1) or m.group(2)) if m else None
    try:
        return proposals.parse_number(text, thousands=unit != "%"), unit
    except proposals.Invalid as exc:
        raise Invalid(f"The premium effect: {exc}") from exc


# -- writing --------------------------------------------------------------------------------
def _clean(title: str | None, detail: str | None) -> tuple[str, str | None]:
    title = " ".join((title or "").split())
    if not title:
        raise Invalid("What is the plan design change?")
    if len(title) > TITLE_MAX:
        raise Invalid(f"Keep the change short (at most {TITLE_MAX} characters); the detail can say more.")
    detail = (detail or "").strip() or None
    if detail and len(detail) > DETAIL_MAX:
        raise Invalid(f"The detail is too long (at most {DETAIL_MAX} characters).")
    return title, detail


def _outcome(outcome: str | None, reason: str | None) -> tuple[str, str | None, str | None]:
    outcome = (outcome or "open").strip()
    if outcome not in OUTCOMES:
        raise Invalid("Pick open, implemented or not implemented.")
    reason = (reason or "").strip() or None
    if outcome == "not_implemented" and not reason:
        raise Invalid("Why wasn't it implemented? A few words are enough.")
    if reason and len(reason) > DETAIL_MAX:
        raise Invalid(f"The reason is too long (at most {DETAIL_MAX} characters).")
    return outcome, reason if outcome == "not_implemented" else None, \
        None if outcome == "open" else date.today().isoformat()


def _ids(renewal_ids: list[Any] | None) -> list[int]:
    out = []
    for x in renewal_ids or []:
        try:
            out.append(int(x))
        except (TypeError, ValueError) as exc:
            raise Invalid("That renewal doesn't exist.") from exc
    return list(dict.fromkeys(out))


def _mine(conn, client_id: int, renewal_ids: list[int]) -> list[dict[str, Any]]:
    client = clients_repo.get(conn, client_id)
    if client is None or client["is_mine"] != 1:
        raise Invalid("This client is not one of yours (or doesn't exist).")
    if not renewal_ids:
        raise Invalid("Tick at least one renewal it applies to.")
    out = []
    for rid in renewal_ids:
        r = renewals_repo.get(conn, rid)
        if r is None or r["client_id"] != client_id:
            raise Invalid("This renewal doesn't exist (or isn't one of this client's).")
        out.append(r)
    return out


def _change_of_mine(conn, client_id: int, change_id: int) -> dict[str, Any]:
    c = plan_changes_repo.get(conn, change_id)
    if c is None or c["client_id"] != client_id:
        raise Invalid("This plan design change doesn't exist any more.")
    _mine(conn, client_id, c["renewal_ids"] or [])
    return c


def add(client_id: int, renewal_ids: list[Any], title: str | None, detail: str | None = None,
        outcome: str | None = None, reason: str | None = None, cost: str | None = None) -> int:
    """One change covering these renewals (the panel's "+ Change", the bundle's
    and the edit bar's)."""
    title, detail = _clean(title, detail)
    outcome, reason, decided = _outcome(outcome, reason)
    amount, unit = parse_cost(cost)
    ids = _ids(renewal_ids)
    with connection() as conn:
        _mine(conn, client_id, ids)
        return plan_changes_repo.add(conn, client_id, ids, title, detail, outcome, reason, decided,
                                     amount, unit)


def _bm_holders(conn, client_id: int, line: str | None, renewal_ids: list[Any]) -> tuple[str, list[dict]]:
    key = norm(line)
    if not key:
        raise Invalid("Which of BM+'s lines?")
    rs = [r for r in _mine(conn, client_id, _ids(renewal_ids))
          if key in {norm(x) for x in bm_info(r["fields"], r["details"])["lines"]}]
    if not rs:
        raise Invalid("BM+ doesn't list that change on these renewals (any more).")
    return key, rs


def track_bm(client_id: int, line: str | None, renewal_ids: list[Any]) -> int:
    """Track one of BM+'s lines as a change, open, covering those of
    `renewal_ids` whose BM+ text has it. A change already tracked from the
    same line for this client takes the new renewals in, so there is never a
    second one."""
    with connection() as conn:
        key, holders = _bm_holders(conn, client_id, line, renewal_ids)
        info = bm_info(holders[0]["fields"], holders[0]["details"])
        text = next(x for x in info["lines"] if norm(x) == key)
        ids = [r["id"] for r in holders]
        plan_changes_repo.undismiss(conn, ids, [text])
        same = [c for c in plan_changes_repo.for_client(conn, client_id) if _line_key(c) == key]
        if same:
            c = same[0]
            plan_changes_repo.set_covers(conn, c["id"], c["renewal_ids"] + ids)
            return c["id"]
        detail = f"Reason in BM+: {info['reason']}" if info["reason"] else None
        return plan_changes_repo.add(conn, client_id, ids, text, detail, source="bm", bm_line=text)


def dismiss_bm(client_id: int, line: str | None, renewal_ids: list[Any], undo: bool = False) -> None:
    """Not a change for these renewals: BM+'s line is no longer offered there
    (`undo` offers it again)."""
    with connection() as conn:
        key, holders = _bm_holders(conn, client_id, line, renewal_ids)
        texts = [x for r in holders for x in bm_info(r["fields"], r["details"])["lines"] if norm(x) == key]
        ids = [r["id"] for r in holders]
        if undo:
            whole = {k for r in holders for k in bm_info(r["fields"], r["details"])["whole"]}
            stored = plan_changes_repo.dismissed(conn, ids)
            plan_changes_repo.undismiss(conn, ids, [d for ds in stored.values() for d in ds
                                                    if norm(d) == key or norm(d) in whole])
        else:
            plan_changes_repo.dismiss(conn, ids, texts[0])


def edit(client_id: int, change_id: int, title: str | None, detail: str | None, cost: str | None = None,
         renewal_ids: list[Any] | None = None) -> None:
    """New wording / premium effect, and (when given) the renewals it covers."""
    title, detail = _clean(title, detail)
    amount, unit = parse_cost(cost)
    with connection() as conn:
        _change_of_mine(conn, client_id, change_id)
        plan_changes_repo.update(conn, change_id, title, detail, amount, unit)
        if renewal_ids is not None:
            ids = _ids(renewal_ids)
            _mine(conn, client_id, ids)
            plan_changes_repo.set_covers(conn, change_id, ids)


def set_outcome(client_id: int, change_id: int, outcome: str | None, reason: str | None = None) -> None:
    outcome, reason, decided = _outcome(outcome, reason)
    with connection() as conn:
        _change_of_mine(conn, client_id, change_id)
        plan_changes_repo.set_outcome(conn, change_id, outcome, reason, decided)


def delete(client_id: int, change_id: int) -> None:
    with connection() as conn:
        _change_of_mine(conn, client_id, change_id)
        plan_changes_repo.delete(conn, change_id)


# -- pages ----------------------------------------------------------------------------------
def panel(client_id: int, bundle_ids: list[int], focus: int | None = None) -> dict[str, Any]:
    """The block for a renewal panel (`focus`) or a bundle, loaded on its own
    (the renewal page has the bundle without its detail sheets)."""
    ids = list(dict.fromkeys(bundle_ids + ([focus] if focus is not None else [])))
    with connection() as conn:
        everyone = {r["id"]: r for r in renewals_repo.for_client(conn, client_id)}
        details = renewals_repo.details_of(conn, ids)
        changes = plan_changes_repo.for_renewals(conn, ids)
        dismissed = plan_changes_repo.dismissed(conn, ids)
    renewals = [{**everyone[i], "details": details.get(i) or {}} for i in ids if i in everyone]
    return view(changes, renewals, dismissed, everyone, focus)


def client_overview(client_id: int, outcome: str | None = None) -> dict[str, Any]:
    """Every plan design change of a client, by the date of the first renewal
    it covers; `outcome` filters (None = all)."""
    with connection() as conn:
        client = clients_repo.get(conn, client_id)
        if client is None or client["is_mine"] != 1:
            raise Invalid("This client is not one of yours (or doesn't exist).")
        changes = plan_changes_repo.for_client(conn, client_id)
        everyone = {r["id"]: r for r in renewals_repo.for_client(conn, client_id)}
    v = view(changes, list(everyone.values()), known=everyone, with_bm=False)
    rows = v["items"]
    counts = {k: sum(1 for c in rows if c["outcome"] == k) for k in OUTCOMES}
    if outcome in OUTCOMES:
        rows = [c for c in rows if c["outcome"] == outcome]
    rows.sort(key=lambda c: (c["takes_effect"] or "9999", c["id"]))
    return {"items": rows, "counts": counts, "total": sum(counts.values()), "outcome": outcome}
