"""The bundle's edit mode acts on several renewals at once (Martin,
06.11.2026): your strategy, a proposal / quote, completed — for the ticked
renewals, or all of them with "Select all"."""

from datetime import datetime
from urllib.parse import urlencode

import pytest

from mart.repository.db import connection
from mart.services import actuals
from mart.services import client_service as cs
from mart.services import proposals as pr
from mart.services import renewal_service as rs
from mart.services import upload_service as us
from mart.web.framework import Request
from tests.conftest import get
from tests.fixtures import R, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")
POLAND = "Poland|2027-01-01"
JAN = datetime(2027, 1, 1, 1, 0)


def _book() -> tuple[int, dict[str, int]]:
    rows = [R(n=1, policy="Medical", renewal_date=JAN), R(n=2, policy="Life", renewal_date=JAN),
            R(n=3, policy="Dental", renewal_date=JAN)]
    uid = us.stage("rt.xlsx", renewal_tracker(rows, cross_overview=True))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)
    with connection() as conn:
        ids = {r["policy_name"]: r["id"] for r in conn.execute("SELECT id, policy_name FROM renewals")}
        cid = conn.execute("SELECT id FROM clients").fetchone()["id"]
    return cid, ids


def _post(app, path: str, pairs: list[tuple[str, str]]):
    """A form with repeated fields (the ticked renewals), as the browser sends it."""
    h = {"content-type": "application/x-www-form-urlencoded"}
    return app.handle(Request("POST", path, "", h, urlencode(pairs).encode()))


def _cards(cid: int) -> list[dict]:
    return cs.explorer(cid, bundle=POLAND)["selected"]["renewals"]


def _location(res) -> str:
    return dict(res.headers)["Location"]


def test_edit_mode_bar(app):
    cid, ids = _book()
    page = get(app, f"/clients/{cid}?bundle=Poland%7C2027-01-01&edit=1").body_bytes.decode()
    for action in ("Strategy…", "Proposal / quote…", "Completed…", "Move…", "Select all"):
        assert action in page, action
    assert page.count('form="bulk-form"') == 3 and f'name="premium_{ids["Life"]}"' in page
    assert "/bulk/strategy" in page and "/bulk/proposals" in page and "/bulk/completed" in page


def test_strategy_for_the_ticked_renewals(app):
    cid, ids = _book()
    back = f"/clients/{cid}?bundle=Poland%7C2027-01-01&edit=1"
    ticked = [("renewal", str(ids["Medical"])), ("renewal", str(ids["Life"]))]
    res = _post(app, f"/clients/{cid}/bulk/strategy", ticked + [("strategy", "Remarketing"),
                                                                 ("reason", "HR call"), ("back", back)])
    assert res.status == 303 and "edit=1" in _location(res)
    assert "Strategy+set+to+Remarketing" in _location(res)
    got = {r["policy_name"]: r["actual"]["strategy"] for r in _cards(cid)}
    assert got == {"Medical": "Remarketing", "Life": "Remarketing", "Dental": None}
    # the same again changes nothing; "go by BM+" drops it
    assert actuals.set_strategy_many(cid, [ids["Medical"], ids["Life"]], "Remarketing", "HR call") == 0
    assert actuals.set_strategy_many(cid, [ids["Medical"]], "") == 1
    page = get(app, _location(res)).body_bytes.decode()
    assert "Strategy set to Remarketing for 2 renewals." in page
    none_ticked = [("strategy", "Remarketing")]
    assert _post(app, f"/clients/{cid}/bulk/strategy", none_ticked).status == 400
    assert _post(app, f"/clients/{cid}/bulk/strategy", ticked + [("strategy", "Whatever")]).status == 400


def test_enter_in_the_edit_bar_never_clears_a_strategy(app):
    """QA 07.11.2026: Enter in any edit-bar field submitted the form with its
    first button, "Set the strategy", whose empty default cleared the strategy
    of every ticked renewal. The default button is now a disabled one, and an
    empty strategy is refused; "go by BM+" is an explicit choice."""
    cid, ids = _book()
    ticked = [("renewal", str(ids["Medical"])), ("renewal", str(ids["Life"]))]
    _post(app, f"/clients/{cid}/bulk/strategy", ticked + [("strategy", "Remarketing")])
    page = get(app, f"/clients/{cid}?bundle=Poland%7C2027-01-01&edit=1").body_bytes.decode()
    form = page[page.index('id="bulk-form"'):]
    assert form.index('<button type="submit" disabled hidden') < form.index('formaction=')   # the default
    res = _post(app, f"/clients/{cid}/bulk/strategy", ticked + [("strategy", ""), ("insurer", "Allianz")])
    assert res.status == 400
    assert {r["policy_name"]: r["actual"]["strategy"] for r in _cards(cid)}["Life"] == "Remarketing"
    res = _post(app, f"/clients/{cid}/bulk/strategy", ticked + [("strategy", "bm")])
    assert "back+to+BM" in _location(res)
    assert {r["policy_name"]: r["actual"]["strategy"] for r in _cards(cid)}["Life"] is None


def test_proposal_for_the_whole_bundle_with_its_own_premiums(app):
    cid, ids = _book()
    allin = [("renewal", str(i)) for i in ids.values()]
    form = [("insurer", "Allianz"), ("plan_design", "as_expiring"), ("label", ""), ("round", "first"),
            ("received_on", "2026-11-02"), ("currency", "EUR"), ("rate_change", "+6"), ("note", "one offer"),
            ("premium_" + str(ids["Medical"]), "120'000"), ("premium_" + str(ids["Life"]), "15.000"),
            ("premium_" + str(ids["Dental"]), "")]
    res = _post(app, f"/clients/{cid}/bulk/proposals", allin + form + [("back", f"/clients/{cid}?edit=1")])
    assert res.status == 303 and "Proposal+from+Allianz+added+to+3+renewals" in _location(res)
    med = rs.detail(cid, ids["Medical"])["my_proposals"]["items"][0]
    assert (med["insurer"], med["latest"]["premium"], med["latest"]["rate_change"]) == ("Allianz", 120000, 6)
    assert rs.detail(cid, ids["Life"])["my_proposals"]["items"][0]["latest"]["premium"] == 15000
    assert rs.detail(cid, ids["Dental"])["my_proposals"]["items"][0]["latest"]["premium"] is None
    # the final quote for two of them joins their proposal: the negotiation goes on
    pr.add_many(cid, [ids["Medical"], ids["Life"]],
                {"insurer": "allianz", "plan_design": "as_expiring", "round": "final", "currency": "EUR"},
                {ids["Medical"]: "112000", ids["Life"]: "14000"})
    med = rs.detail(cid, ids["Medical"])["my_proposals"]
    assert med["count"] == 1 and len(med["items"][0]["quotes"]) == 2
    assert med["items"][0]["latest"]["premium"] == 112000
    # all or nothing: one bad premium changes none of them
    with pytest.raises(pr.Invalid):
        pr.add_many(cid, [ids["Medical"], ids["Dental"]], {"insurer": "AXA"},
                    {ids["Medical"]: "1000", ids["Dental"]: "lots"})
    assert all(not any(i["insurer"] == "AXA" for i in rs.detail(cid, r)["my_proposals"]["items"])
               for r in ids.values())
    assert _post(app, f"/clients/{cid}/bulk/proposals", allin + [("insurer", "")]).status == 400
    with pytest.raises(pr.Invalid):
        pr.add_many(cid + 1, [ids["Medical"]], {"insurer": "AXA"}, {})


def test_completed_for_the_ticked_renewals(app):
    cid, ids = _book()
    actuals.set_completed(cid, [ids["Life"]], "2026-12-01")
    pairs = [("renewal", str(ids["Medical"])), ("renewal", str(ids["Life"])), ("date", "2026-12-20"),
             ("completed_note", "all approved"), ("back", f"/clients/{cid}?edit=1")]
    res = _post(app, f"/clients/{cid}/bulk/completed", pairs)
    assert res.status == 303 and "1+renewal+marked+completed+%281+already+were%29" in _location(res)
    got = {r["policy_name"]: r["actual"]["completed"] for r in _cards(cid)}
    assert got == {"Medical": "2026-12-20", "Life": "2026-12-01", "Dental": None}


def test_back_never_leaves_mart(app):
    cid, ids = _book()
    res = _post(app, f"/clients/{cid}/bulk/strategy", [("renewal", str(ids["Medical"])), ("strategy", "TBC"),
                                                       ("back", "https://example.com/x")])
    assert _location(res).startswith(f"/clients/{cid}?")
