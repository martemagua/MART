"""The board's stages (M3 day 6; Martin 05.11.2026, QUESTIONS C2, C3, M3d;
PLANNING §1d, §5). Pure: no database.

* A renewal's stage comes from BM+'s three stages (Renewal Strategy →
  Proposals → Update Policy) and whether Martin marked it completed:
  ``renewal_column``.
* A card is a BUNDLE (C2). Until Martin moves it, it sits at its LEAST
  advanced renewal's stage, with "2 of 3 at Proposals" on it (M3d):
  ``bundle_column``.
* Martin can move a card anywhere; MART keeps his stage beside BM+'s, with
  BM+'s stage at that moment (``place``). Moving a card back to where BM+ has
  it means "follow BM+ again": nothing of his is kept then.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

# The renewal pipeline (Martin, 06.11.2026: "a general guideline for the
# Renewal Pipeline"): each column, and what has to be true for a card to sit
# there, shown under each column's title and with the stage picked.
COLUMNS = (
    ("not_started", "Not started", "The renewal has not been kicked off."),
    ("strategy", "Strategy", "The renewal has been kicked off; the strategy is pending."),
    ("proposals", "Proposals / Marketing",
     "The strategy is decided; terms and proposals for the renewal are being collected."),
    ("decision", "Decision",
     "The final proposals from the insurer(s) are in; the client's decision is pending."),
    ("update_policy", "Update Policy",
     "The renewal is confirmed with the client; the data in BM+ needs to be updated."),
    ("review", "Post-renewal review",
     "Review all data, note key learnings, savings and plan design changes, and check that "
     "the policy documents are uploaded to BM+."),
    ("done", "Done", "All tasks have been completed."),
)
LABELS = {key: label for key, label, _ in COLUMNS}
HINTS = {key: hint for key, _, hint in COLUMNS}
ORDER = {key: i for i, (key, _, _) in enumerate(COLUMNS)}
REASON_MAX = 200


def renewal_column(stage_list: list[dict[str, Any]], completed: bool = False) -> str:
    """Where ONE renewal stands. Done = Martin marked it completed (only he
    does, M3h); Post-renewal review = BM+'s three stages are done but it is
    not marked completed yet. Otherwise the furthest BM+ stage at work:
    Proposals done (or not needed, then Update Policy is next) and Update
    Policy not started = the Decision."""
    if completed:
        return "done"
    by = {s["name"]: s["state"] for s in stage_list or []}
    strategy, props, update = (by.get("Renewal Strategy", "missing"), by.get("Proposals", "missing"),
                               by.get("Update Policy", "missing"))
    if update == "done":
        return "review"
    if update in ("doing", "review"):
        return "update_policy"
    if props in ("doing", "review"):
        return "proposals"
    if props == "done":
        return "decision"
    if strategy == "done":
        return "update_policy" if props == "skipped" else "proposals"
    if strategy in ("doing", "review"):
        return "strategy"
    return "not_started"


def bundle_column(columns: list[str]) -> dict[str, Any]:
    """The bundle's stage = its least advanced renewal's (M3d), and how many
    of its renewals are there ("2 of 3 at Proposals")."""
    if not columns:
        return {"column": "not_started", "at": 0, "total": 0, "mixed": False, "spread": []}
    least = min(columns, key=ORDER.__getitem__)
    counts = Counter(columns)
    return {"column": least, "at": counts[least], "total": len(columns), "mixed": len(counts) > 1,
            "spread": [(LABELS[c], counts[c]) for c in ORDER if counts[c]]}


def place(bm: str, row: dict[str, Any] | None) -> dict[str, Any]:
    """Where the card sits: Martin's stage, beside BM+'s.

    ``row`` = Martin's current stage (``stage``, BM+'s stage when he set it in
    ``bm_stage``), None when he never moved it or moved it back to BM+'s.

    * He moved it AHEAD of BM+ (the usual case: he knows more than BM+):
      it stays there while BM+ is behind (``behind``); once BM+ gets there or
      further, the card follows BM+ again (``caught_up`` while they agree).
    * He moved it BACK (BM+ shows more than is true): it stays there while
      BM+ hasn't moved (``held``); if BM+ moves on, he should look
      (``conflict``); if BM+ comes back to his stage or below, BM+ again.
    """
    mine = row["stage"] if row else None
    if not mine or mine not in ORDER:
        return {"column": bm, "bm": bm, "mine": None, "state": None, "row": None}
    then = row.get("bm_stage") if row.get("bm_stage") in ORDER else bm
    if ORDER[mine] > ORDER[then]:                       # set ahead of BM+
        if ORDER[bm] < ORDER[mine]:
            column, state = mine, "behind"
        else:
            column, state = bm, "caught_up" if bm == mine else None
    elif ORDER[bm] <= ORDER[mine]:                      # set back; BM+ came back down
        column, state = bm, "caught_up" if bm == mine else None
    else:
        column, state = mine, "held" if bm == then else "conflict"
    return {"column": column, "bm": bm, "mine": mine if column == mine and state != "caught_up" else None,
            "state": state, "row": row}


def aggregate_stages(stage_lists: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """BM+'s three stages for a whole bundle, for the card's dots: a stage is
    done when every renewal's is (a skipped one counts), not started when
    none has started, else in progress ("2 of 3 completed")."""
    out = []
    for i, first in enumerate(stage_lists[0] if stage_lists else []):
        states = [sl[i]["state"] for sl in stage_lists if i < len(sl)]
        finished = sum(s in ("done", "skipped") for s in states)
        late = any(sl[i].get("past_due") for sl in stage_lists if i < len(sl))
        if len(set(states)) == 1:
            state, label = states[0], stage_lists[0][i]["label"]
        elif finished == len(states):
            state, label = "done", "Completed"
        elif all(s in ("missing", "todo") for s in states):
            state, label = "todo", "Not started"
        else:
            state, label = "doing", "In progress"
        if len(states) > 1:
            label += f" ({finished} of {len(states)} completed)"
        out.append({"name": first["name"], "state": state, "label": label, "past_due": late})
    return out
