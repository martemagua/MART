"""M3 day 1: the actual state of a renewal beside BM+'s (Martin, 05.11.2026;
QUESTIONS D1, D2, M3h). Martin's strategy wins on the cards, BM+'s is shown
beside it; "completed" is his, on a renewal or a whole bundle."""

from datetime import datetime

import pytest

from mart.repository.db import connection
from mart.services import actuals
from mart.services import client_service as cs
from mart.services import renewal_service as rs
from mart.services import upload_service as us
from mart.web import colors
from tests.conftest import get, post
from tests.fixtures import R, T, renewal_tracker, task_tracker

pytestmark = pytest.mark.usefixtures("configured")
POLAND = "Poland|2027-01-01"
JAN = datetime(2027, 1, 1, 1, 0)


def _commit(data: bytes, name: str) -> None:
    uid = us.stage(name, data)
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)


def _book(med="TBC", report="03 Nov 2026") -> tuple[int, dict[str, int]]:
    _commit(renewal_tracker([R(n=1, policy="Medical", strategy=med, renewal_date=JAN),
                             R(n=2, policy="Life", strategy="Remarketing", renewal_date=JAN)],
                            cross_overview=True, report_date=report), f"rt-{report}.xlsx")
    with connection() as conn:
        rows = {r["policy_name"]: r["id"] for r in conn.execute("SELECT id, policy_name FROM renewals")}
        cid = conn.execute("SELECT id FROM clients").fetchone()["id"]
    return cid, rows


def _card(cid: int, name: str) -> dict:
    renewals = cs.explorer(cid, bundle=POLAND)["selected"]["renewals"]
    return next(r for r in renewals if r["policy_name"] == name)


def test_strategy_state_rules():
    assert actuals.strategy_state(None, None, "TBC") is None
    assert actuals.strategy_state("Remarketing", "TBC", "remarketing") == "sync"
    assert actuals.strategy_state("Remarketing", "TBC", "TBC") == "behind"
    assert actuals.strategy_state("Remarketing", None, None) == "behind"
    assert actuals.strategy_state("Remarketing", "TBC", "Incumbent with Rate Guarantee") == "conflict"
    done = [{"state": "done"}, {"state": "skipped"}, {"state": "done"}]
    assert actuals.stages_done(done)
    assert not actuals.stages_done([{"state": "done"}, {"state": "doing"}])
    assert not actuals.stages_done([{"state": "skipped"}]) and not actuals.stages_done([])
    # one fixed list (Martin, 06.11.2026): BM+'s, with Canceled for Unknown / New Policy
    assert "Canceled" in actuals.STRATEGIES and "Unknown / New Policy" not in actuals.STRATEGIES
    assert all(colors.strategy_class(s) != "st-none" for s in actuals.STRATEGIES if s != "Canceled")


def test_my_strategy_wins_until_bm_catches_up_and_survives_uploads():
    cid, ids = _book(med="TBC")
    actuals.set_strategy(cid, ids["Medical"], "Remarketing", "agreed with HR on 28.10")
    a = _card(cid, "Medical")["actual"]
    assert (a["effective"], a["state"], a["differs"]) == ("Remarketing", "behind", True)
    assert a["bm_strategy"] == "TBC"
    assert _card(cid, "Life")["actual"]["strategy"] is None        # BM+'s counts
    # BM+ catches up: the difference goes away by itself
    _book(med="Remarketing", report="05 Nov 2026")
    a = _card(cid, "Medical")["actual"]
    assert (a["state"], a["caught_up"], a["differs"]) == ("sync", True, False)
    # BM+ then moves elsewhere: a conflict, mine still counts on the cards
    _book(med="Incumbent without Rate Guarantee", report="06 Nov 2026")
    a = _card(cid, "Medical")["actual"]
    assert (a["state"], a["effective"]) == ("conflict", "Remarketing")
    # cleared: BM+'s counts again; the history keeps every step
    actuals.set_strategy(cid, ids["Medical"], "")
    a = rs.detail(cid, ids["Medical"])["actual"]
    assert a["strategy"] is None and a["effective"] == "Incumbent without Rate Guarantee"
    assert [h["value"] for h in a["history"]] == [None, "Remarketing"]
    assert a["history"][1]["bm_value"] == "TBC" and a["history"][1]["reason"] == "agreed with HR on 28.10"


def test_bundle_strategy_mix_goes_by_mine():
    cid, ids = _book(med="TBC")
    actuals.set_strategy(cid, ids["Medical"], "Remarketing")
    # mine and BM+'s are counted apart: mine is drawn neutral
    assert cs.explorer(cid, bundle=POLAND)["selected"]["strategies"] == {("Remarketing", True): 1,
                                                                        ("Remarketing", False): 1}


def test_completed_on_a_renewal_and_on_the_whole_bundle(app):
    cid, ids = _book()
    base = f"/clients/{cid}"
    res = post(app, f"{base}/completed", {"rid": str(ids["Medical"]), "date": "2026-12-20",
                                         "back": f"{base}/renewals/{ids['Medical']}"})
    assert res.status == 303 and dict(res.headers)["Location"].endswith("#actual")
    s = cs.explorer(cid, bundle=POLAND)["selected"]
    assert s["completed"] == 1 and s["open_ids"] == [ids["Life"]]
    # the whole bundle: only the open one changes, the first keeps its date
    body = {"rid": [str(ids["Medical"]), str(ids["Life"])], "date": "2026-12-28"}
    assert actuals.set_completed(cid, [int(x) for x in body["rid"]], body["date"]) == 1
    assert _card(cid, "Medical")["actual"]["completed"] == "2026-12-20"
    assert _card(cid, "Life")["actual"]["completed"] == "2026-12-28"
    page = get(app, f"{base}?bundle=Poland%7C2027-01-01").body_bytes.decode()
    assert "2 of 2" in page and "completed 20.12.2026" in page and 'title="All renewals completed"' in page
    # taken back
    actuals.set_completed(cid, [ids["Life"]], None, undo=True)
    assert _card(cid, "Life")["actual"]["completed"] is None
    with pytest.raises(actuals.Invalid):
        actuals.set_completed(cid, [ids["Life"]], "not a date")
    with pytest.raises(actuals.Invalid):
        actuals.set_completed(cid, [9999], None)
    with pytest.raises(actuals.Invalid):
        actuals.set_completed(cid + 1, [ids["Life"]], None)


def test_completed_is_suggested_once_bm_stages_are_done(app):
    cid, ids = _book(med="Remarketing")
    _commit(task_tracker([T(n=1, task_name=n, status="Completed")
                          for n in ("Renewal Strategy", "Proposals", "Update Policy")]), "tt.xlsx")
    a = rs.detail(cid, ids["Medical"])["actual"]
    assert a["suggest_completed"] and not rs.detail(cid, ids["Life"])["actual"]["suggest_completed"]
    page = get(app, f"/clients/{cid}/renewals/{ids['Medical']}").body_bytes.decode()
    assert "BM+&#39;s stages are all done" in page or "BM+'s stages are all done" in page
    actuals.set_completed(cid, [ids["Medical"]], None)
    assert not rs.detail(cid, ids["Medical"])["actual"]["suggest_completed"]


def test_panel_and_card_show_it(app):
    cid, ids = _book(med="TBC")
    base = f"/clients/{cid}"
    res = post(app, f"{base}/renewals/{ids['Medical']}/strategy",
               {"strategy": "Remarketing", "reason": "HR call", "back": f"{base}/renewals/{ids['Medical']}"})
    assert res.status == 303 and dict(res.headers)["Location"].endswith("#actual")
    panel = get(app, f"{base}/renewals/{ids['Medical']}").body_bytes.decode()
    assert 'id="actual"' in panel and "≠ BM+: TBC" in panel and "HR call" in panel
    assert panel.index('id="actual"') < panel.index('id="mine"')              # in the header (0.9.19)
    card = get(app, f"{base}?bundle=Poland%7C2027-01-01").body_bytes.decode()
    assert "≠ BM+: TBC" in card
    # set by you: neutral with a ✎, never BM+'s colour
    assert 'class="pill pill-st st-mine"' in card and "✎ Remarketing" in card and "set by you" not in card
    assert 'renewal-card st-mine' in card
    # only the listed strategies; "Canceled" is one of them
    res = post(app, f"{base}/renewals/{ids['Medical']}/strategy", {"strategy": "Something else"})
    assert res.status == 400
    actuals.set_strategy(cid, ids["Life"], "Canceled")
    assert _card(cid, "Life")["actual"]["state"] == "behind"
    assert 'class="pill pill-st st-mine" title="Your strategy, set in MART">✎ Canceled' in \
        get(app, f"{base}?bundle=Poland%7C2027-01-01").body_bytes.decode()


def test_editing_only_the_reason_keeps_a_conflict_with_bm(app):
    """QA 07.11.2026: changing just the reason stored BM+'s CURRENT value as
    "BM+ then", so a conflict (BM+ moved since) turned into "behind"."""
    cid, ids = _book(med="TBC")
    actuals.set_strategy(cid, ids["Medical"], "Remarketing", "HR call")
    _book(med="Incumbent with Rate Guarantee", report="10 Nov 2026")      # BM+ moves elsewhere
    assert _card(cid, "Medical")["actual"]["state"] == "conflict"
    actuals.set_strategy(cid, ids["Medical"], "Remarketing", "HR call of 28.10")
    a = _card(cid, "Medical")["actual"]
    assert a["state"] == "conflict" and a["strategy_reason"] == "HR call of 28.10"


def test_the_board_and_the_stages_go_by_martins_strategy(app):
    """QA 07.11.2026: Martin's strategy wins on the board too. With his
    "Incumbent with Rate Guarantee" (no proposals needed) and the strategy
    task done, the card is at Update Policy, not Proposals."""
    cid, ids = _book(med="TBC")
    _commit(task_tracker([T(n=1, task_name="Renewal Strategy", status="Completed")]), "tt.xlsx")
    from mart.services import board
    stages = rs.detail(cid, ids["Medical"])["stages"]
    assert board.renewal_column(stages) == "proposals"                  # BM+ says TBC
    actuals.set_strategy(cid, ids["Medical"], "Incumbent with Rate Guarantee")
    stages = rs.detail(cid, ids["Medical"])["stages"]
    assert [s["state"] for s in stages] == ["done", "skipped", "missing"]
    assert board.renewal_column(stages) == "update_policy"
    medical = next(r for r in cs.explorer(cid, bundle=POLAND)["selected"]["renewals"]
                   if r["policy_name"] == "Medical")
    assert [s["state"] for s in medical["stages"]] == ["done", "skipped", "missing"]
