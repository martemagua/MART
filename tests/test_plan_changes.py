"""M3 day 4: plan design changes per renewal, suggested → agreed →
implemented (or dropped), BM+'s suggestion taken over or dismissed, several
renewals at once, and the client-wide overview."""

from datetime import date, datetime
from urllib.parse import urlencode

import pytest

from mart.repository.db import connection
from mart.services import client_service as cs
from mart.services import plan_changes as pc
from mart.services import renewal_service as rs
from mart.services import upload_service as us
from mart.web.framework import Request
from tests.conftest import get, post
from tests.fixtures import R, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")
POLAND = "Poland|2027-01-01"
JAN = datetime(2027, 1, 1, 1, 0)
TODAY = date.today().isoformat()


def _book() -> tuple[int, dict[str, int]]:
    rows = [R(n=1, policy="Medical", renewal_date=JAN, pdc_types="Dental removed", pdc_reasons="cost"),
            R(n=2, policy="Life", renewal_date=JAN), R(n=3, policy="Dental", renewal_date=JAN)]
    uid = us.stage("rt.xlsx", renewal_tracker(rows, cross_overview=True))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)
    with connection() as conn:
        ids = {r["policy_name"]: r["id"] for r in conn.execute("SELECT id, policy_name FROM renewals")}
        cid = conn.execute("SELECT id FROM clients").fetchone()["id"]
    return cid, ids


def test_a_change_moves_through_its_states():
    cid, ids = _book()
    m = ids["Medical"]
    cid_ = pc.add(cid, m, "Deductible 500 → 1'000", "to cut cost", on="2026-10-01")
    pc.set_status(cid, cid_, "agreed", "2026-10-20")
    pc.set_status(cid, cid_, "implemented", "2027-01-01")
    v = rs.detail(cid, m)["plan_changes"]
    c = v["items"][0]
    assert (c["status"], c["since"], c["suggested_on"], c["agreed_on"]) == ("implemented", "2027-01-01",
                                                                          "2026-10-01", "2026-10-20")
    assert v["counts"]["implemented"] == 1 and v["live"] == 1
    pc.edit(cid, cid_, "Deductible 500 → 1'500", None)
    assert rs.detail(cid, m)["plan_changes"]["items"][0]["title"] == "Deductible 500 → 1'500"
    dropped = pc.add(cid, m, "Vision added", status="dropped")
    v = rs.detail(cid, m)["plan_changes"]
    assert [i["status"] for i in v["items"]] == ["implemented", "dropped"] and v["live"] == 1
    assert v["items"][1]["since"] == TODAY
    pc.delete(cid, dropped)
    assert rs.detail(cid, m)["plan_changes"]["count"] == 1
    for bad in (lambda: pc.add(cid, m, ""), lambda: pc.add(cid, m, "x", status="done"),
                lambda: pc.add(cid, m, "x" * 201), lambda: pc.add(cid, m, "x", on="31.12.2026"),
                lambda: pc.set_status(cid, cid_, "maybe"), lambda: pc.add(cid + 1, m, "x"),
                lambda: pc.delete(cid, dropped)):
        with pytest.raises(pc.Invalid):
            bad()


def test_bm_suggestion_taken_over_or_dismissed():
    cid, ids = _book()
    m = ids["Medical"]
    v = rs.detail(cid, m)["plan_changes"]
    assert v["bm"] == {"title": "Dental removed", "detail": "cost"} and v["count"] == 0
    assert rs.detail(cid, ids["Life"])["plan_changes"]["bm"] is None
    pc.take_bm(cid, m)
    v = rs.detail(cid, m)["plan_changes"]
    assert v["bm"] is None and v["items"][0]["source"] == "bm" and v["items"][0]["status"] == "suggested"
    assert pc.take_bm(cid, m) is None                       # offered once only
    # dismissed elsewhere: stored as dropped, not offered again
    assert pc.bm_suggestion({"pdc_considered": "Yes", "pdc_comments": "Add dental"}, {}) == {
        "title": "Add dental", "detail": ""}
    assert pc.bm_suggestion({"pdc_considered": "No", "pdc_comments": "Add dental"}, {}) is None


def test_several_renewals_at_once_and_the_overview(app):
    cid, ids = _book()
    pairs = [("renewal", str(ids["Life"])), ("renewal", str(ids["Dental"])),
             ("pdc_title", "Harmonise waiting periods"), ("pdc_detail", ""), ("pdc_status", "agreed"),
             ("pdc_on", "2026-11-05"), ("back", f"/clients/{cid}?bundle=Poland%7C2027-01-01&edit=1")]
    form = {"content-type": "application/x-www-form-urlencoded"}
    body = urlencode(pairs).encode()
    res = app.handle(Request("POST", f"/clients/{cid}/bulk/plan-changes", "", form, body))
    assert res.status == 303 and "Plan+design+change+added+to+2+renewals" in dict(res.headers)["Location"]
    renewals = cs.explorer(cid, bundle=POLAND)["selected"]["renewals"]
    cards = {r["policy_name"]: r["plan_changes"] for r in renewals}
    assert cards["Life"]["counts"]["agreed"] == 1 and cards["Medical"]["count"] == 0
    assert cs.explorer(cid, bundle=POLAND)["selected"]["pdc_counts"]["agreed"] == 2
    with pytest.raises(pc.Invalid):
        pc.add_many(cid, [], "x")
    pc.add(cid, ids["Medical"], "Dental removed", status="implemented")
    ov = pc.client_overview(cid)
    assert ov["total"] == 3 and ov["counts"] == {"suggested": 0, "agreed": 2, "implemented": 1, "dropped": 0}
    assert len(pc.client_overview(cid, "implemented")["items"]) == 1
    page = get(app, f"/clients/{cid}/plan-changes?status=agreed").body_bytes.decode()
    assert "Plan design changes · Acme Group" in page and "Harmonise waiting periods" in page
    assert "Dental removed" not in page and f"/clients/{cid}/renewals/{ids['Life']}#plan-changes" in page
    bundle = get(app, f"/clients/{cid}?bundle=Poland%7C2027-01-01").body_bytes.decode()
    assert "Plan design: 1 agreed" in bundle and "2 agreed · 1 implemented" in bundle


def test_panel_and_routes(app):
    cid, ids = _book()
    base, back = f"/clients/{cid}", f"/clients/{cid}/renewals/{ids['Medical']}"
    panel = get(app, back).body_bytes.decode()
    assert "Plan design changes" in panel and "BM+ suggests" in panel and "Dental removed" in panel
    assert panel.index('id="strat-h"') < panel.index('id="pdc-h"') < panel.index('id="myprop-h"')  # Strategy
    res = post(app, f"{base}/renewals/{ids['Medical']}/plan-changes/bm", {"keep": "0", "back": back})
    assert res.status == 303
    panel = get(app, back).body_bytes.decode()
    assert "BM+ suggests" not in panel and "dropped" in panel
    res = post(app, f"{base}/renewals/{ids['Medical']}/plan-changes",
               {"title": "Vision added", "status": "suggested", "on": "", "back": back})
    assert res.status == 303 and dict(res.headers)["Location"].endswith("#plan-changes")
    assert post(app, f"{base}/renewals/{ids['Medical']}/plan-changes", {"title": ""}).status == 400
    items = rs.detail(cid, ids["Medical"])["plan_changes"]["items"]
    new = next(i for i in items if i["title"] == "Vision added")
    res = post(app, f"{base}/plan-changes/{new['id']}/status", {"status": "agreed", "back": back})
    assert res.status == 303
    assert "agreed" in get(app, back).body_bytes.decode()
    edit = get(app, f"{base}?bundle=Poland%7C2027-01-01&edit=1").body_bytes.decode()
    assert "Plan design…" in edit and "/bulk/plan-changes" in edit
