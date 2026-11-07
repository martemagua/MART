"""Plan design changes (M3 day 4, reshaped with Martin 07.11.2026): ONE change
covers several renewals, ends implemented or not implemented (with why), may
carry a premium effect; BM+'s text is split into one line per change, each
tracked or dismissed; the edit bar adds one change for the ticked renewals;
the client-wide overview; the first shape's rows carried over (migration 18)."""

from datetime import datetime
from urllib.parse import urlencode

import pytest

from mart.repository import schema
from mart.repository.db import connection
from mart.services import client_service as cs
from mart.services import plan_changes as pc
from mart.services import upload_service as us
from mart.web.framework import Request
from tests.conftest import get, post
from tests.fixtures import R, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")
POLAND = "Poland|2027-01-01"
JAN = datetime(2027, 1, 1, 1, 0)
TWO = "- Out-patient co-payment to be 90%\n-Chronic medication coverage to be 80%"
FORM = {"content-type": "application/x-www-form-urlencoded"}


def _book() -> tuple[int, dict[str, int]]:
    """One Polish bundle of three renewals; Medical and Life list the same two
    changes in BM+ (a bundled policy), Dental lists one of them."""
    rows = [R(n=1, policy="Medical", renewal_date=JAN, pdc_types=TWO, pdc_reasons="Employee feedback"),
            R(n=2, policy="Life", renewal_date=JAN, pdc_types=TWO),
            R(n=3, policy="Dental", renewal_date=JAN, pdc_types="Chronic medication coverage to be 80%")]
    uid = us.stage("rt.xlsx", renewal_tracker(rows, cross_overview=True))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)
    with connection() as conn:
        ids = {r["policy_name"]: r["id"] for r in conn.execute("SELECT id, policy_name FROM renewals")}
        cid = conn.execute("SELECT id FROM clients").fetchone()["id"]
    return cid, ids


def _bundle(cid: int) -> dict:
    return cs.explorer(cid, bundle=POLAND)["selected"]["plan_changes"]


def test_bm_text_becomes_one_line_per_change():
    assert pc.split_lines(TWO) == ["Out-patient co-payment to be 90%",
                                   "Chronic medication coverage to be 80%"]
    assert pc.split_lines("• Dental removed • Vision added\n1. Deductible 500\n\n") == [
        "Dental removed", "Vision added", "Deductible 500"]
    info = pc.bm_info({"pdc_considered": "Yes", "pdc_comments": "Add dental\n- Add dental\nVision added"}, {})
    assert info["considered"] == "Yes" and info["lines"] == ["Add dental", "Vision added"]
    assert pc.bm_info({"pdc_comments": "n/a"}, {})["lines"] == []
    assert pc.parse_cost("-2,5 %") == (-2.5, "%") and pc.parse_cost("-25'000 EUR") == (-25000, "EUR")
    assert pc.parse_cost("EUR -25'000") == (-25000, "EUR") and pc.parse_cost("+1,200") == (1200, None)
    assert pc.parse_cost("") == (None, None)
    with pytest.raises(pc.Invalid):
        pc.parse_cost("25k")


def test_a_bm_line_tracked_covers_every_renewal_that_lists_it():
    cid, ids = _book()
    v = _bundle(cid)
    lines = {ln["text"]: ln for ln in v["bm"]["lines"]}
    chronic = lines["Chronic medication coverage to be 80%"]
    assert chronic["of"] == 3 and chronic["state"] == "new" and v["bm"]["new"] == 2
    assert v["bm"]["considered"] is None and v["bm"]["reason"] == "Employee feedback"
    # tracked from the Medical renewal: it covers all three that list it
    cid1 = pc.track_bm(cid, chronic["text"], [ids["Medical"], ids["Life"], ids["Dental"]])
    v = _bundle(cid)
    c = v["items"][0]
    assert (c["title"], c["outcome"], c["source"], c["all_bundle"]) == (chronic["text"], "open", "bm", True)
    assert c["detail"] == "Reason in BM+: Employee feedback"
    assert {ln["text"]: ln["state"] for ln in v["bm"]["lines"]}[chronic["text"]] == "tracked"
    # the renewal panel shows it too, and the other line of Medical still to look at
    p = pc.panel(cid, [ids["Medical"], ids["Life"], ids["Dental"]], focus=ids["Dental"])
    assert [i["id"] for i in p["items"]] == [cid1] and [ln["state"] for ln in p["bm"]["lines"]] == ["tracked"]
    # dismissed on Life only: Medical still offers it; tracking it then
    co = "Out-patient co-payment to be 90%"
    pc.dismiss_bm(cid, co, [ids["Life"]])
    p = pc.panel(cid, [ids["Medical"], ids["Life"]], focus=ids["Life"])
    assert {ln["text"]: ln["state"] for ln in p["bm"]["lines"]}[co] == "dismissed"
    line = {ln["text"]: ln for ln in _bundle(cid)["bm"]["lines"]}[co]
    assert line["state"] == "new" and line["pending_ids"] == [ids["Medical"]]
    second = pc.track_bm(cid, co, line["pending_ids"])
    # Life offered again and tracked: it joins the same change, never a second one
    pc.dismiss_bm(cid, co, [ids["Life"]], undo=True)
    assert pc.track_bm(cid, co, [ids["Life"]]) == second
    assert len(_bundle(cid)["items"]) == 2 and _bundle(cid)["bm"]["new"] == 0
    with pytest.raises(pc.Invalid):
        pc.track_bm(cid, "Not in BM+ at all", [ids["Medical"]])


def test_one_change_for_several_renewals_and_its_outcome():
    cid, ids = _book()
    m, life = ids["Medical"], ids["Life"]
    new = pc.add(cid, [m, life], "Deductible 500 → 1'000", "to cut cost", cost="-3,5 %")
    c = _bundle(cid)["items"][0]
    assert c["covers"] and [r["id"] for r in c["covers"]] == sorted([m, life]) and not c["all_bundle"]
    assert (c["cost_amount"], c["cost_unit"], c["cost_input"]) == (-3.5, "%", "-3.5 %")
    with pytest.raises(pc.Invalid):                       # not implemented needs a why
        pc.set_outcome(cid, new, "not_implemented", "")
    pc.set_outcome(cid, new, "not_implemented", "client declined")
    c = _bundle(cid)["items"][0]
    assert (c["outcome"], c["reason"]) == ("not_implemented", "client declined") and c["decided_on"]
    pc.set_outcome(cid, new, "implemented")
    c = _bundle(cid)["items"][0]
    assert (c["reason"], c["takes_effect"]) == (None, "2027-01-01")
    pc.edit(cid, new, "Deductible 500 → 1'500", None, "-25'000 EUR", [m])
    c = pc.panel(cid, [m, life], focus=m)["items"][0]
    assert (c["title"], c["renewal_ids"], c["cost_unit"]) == ("Deductible 500 → 1'500", [m], "EUR")
    assert pc.panel(cid, [m, life], focus=life)["items"] == []
    renewals = cs.explorer(cid, bundle=POLAND)["selected"]["renewals"]
    cards = {r["policy_name"]: r["plan_changes"] for r in renewals}
    assert cards["Medical"]["implemented"] == 1 and cards["Life"]["count"] == 0
    for bad in (lambda: pc.add(cid, [m], ""), lambda: pc.add(cid, [m], "x", outcome="done"),
                lambda: pc.add(cid, [m], "x" * 201), lambda: pc.add(cid, [], "x"),
                lambda: pc.add(cid + 1, [m], "x"), lambda: pc.add(cid, [m], "x", cost="1.2m"),
                lambda: pc.edit(cid, new, "x", None, None, [])):
        with pytest.raises(pc.Invalid):
            bad()
    pc.delete(cid, new)
    assert _bundle(cid)["count"] == 0
    with pytest.raises(pc.Invalid):
        pc.delete(cid, new)


def test_the_edit_bar_adds_one_change_and_the_overview(app):
    cid, ids = _book()
    pairs = [("renewal", str(ids["Life"])), ("renewal", str(ids["Dental"])),
             ("pdc_title", "Harmonise waiting periods"), ("pdc_detail", ""), ("pdc_cost", ""),
             ("pdc_outcome", "open"), ("pdc_reason", ""),
             ("back", f"/clients/{cid}?bundle=Poland%7C2027-01-01&edit=1")]
    body = urlencode(pairs).encode()
    res = app.handle(Request("POST", f"/clients/{cid}/bulk/plan-changes", "", FORM, body))
    assert res.status == 303 and "covering+2+renewals" in dict(res.headers)["Location"]
    v = _bundle(cid)
    assert v["count"] == 1 and v["items"][0]["renewal_ids"] == sorted([ids["Life"], ids["Dental"]])
    pc.add(cid, [ids["Medical"]], "Dental removed", outcome="implemented")
    ov = pc.client_overview(cid)
    assert ov["total"] == 2 and ov["counts"] == {"open": 1, "implemented": 1, "not_implemented": 0}
    assert len(pc.client_overview(cid, "implemented")["items"]) == 1
    page = get(app, f"/clients/{cid}/plan-changes?outcome=open").body_bytes.decode()
    assert "Plan design changes · Acme Group" in page and "Harmonise waiting periods" in page
    assert "Dental removed" not in page and f"/clients/{cid}/renewals/{ids['Life']}#plan-changes" in page
    bundle = get(app, f"/clients/{cid}?bundle=Poland%7C2027-01-01").body_bytes.decode()
    assert "Plan design: 1 open" in bundle and "1 open · 1 implemented" in bundle
    assert 'id="plan-changes"' in bundle


def test_panel_and_routes(app):
    cid, ids = _book()
    m = ids["Medical"]
    base, back = f"/clients/{cid}", f"/clients/{cid}/renewals/{m}"
    panel = get(app, back).body_bytes.decode()
    assert "In BM+" in panel and "BM+ suggests" not in panel and panel.count("+ Track") == 2
    assert panel.index('id="strat-h"') < panel.index('id="pdc-h"') < panel.index('id="myprop-h"')  # Strategy
    body = urlencode([("line", "Out-patient co-payment to be 90%"), ("cover", m), ("cover", ids["Life"]),
                      ("back", back)]).encode()
    res = app.handle(Request("POST", f"{base}/plan-changes/track", "", FORM, body))
    assert res.status == 303 and dict(res.headers)["Location"].endswith("#plan-changes")
    body = urlencode([("title", "Vision added"), ("outcome", "open"), ("cost", ""), ("cover", m),
                      ("back", back)]).encode()
    assert app.handle(Request("POST", f"{base}/plan-changes/add", "", FORM, body)).status == 303
    assert post(app, f"{base}/plan-changes/add", {"title": "x"}).status == 400              # no renewal
    items = pc.panel(cid, [m], focus=m)["items"]
    vision = next(i for i in items if i["title"] == "Vision added")
    assert post(app, f"{base}/plan-changes/{vision['id']}/outcome",
                {"outcome": "not_implemented", "reason": "", "back": back}).status == 400
    assert post(app, f"{base}/plan-changes/{vision['id']}/outcome",
                {"outcome": "not_implemented", "reason": "insurer refused", "back": back}).status == 303
    panel = get(app, back).body_bytes.decode()
    assert "Why not: insurer refused" in panel and "tracked below" in panel and panel.count("+ Track") == 1
    res = post(app, f"{base}/plan-changes/{vision['id']}/save", {"title": "Vision added (glasses)",
                                                                  "cost": "+0.5 %", "back": back})
    assert res.status == 303 and "+0.5 %" in get(app, back).body_bytes.decode()
    assert post(app, f"{base}/plan-changes/{vision['id']}/delete", {"back": back}).status == 303
    edit = get(app, f"{base}?bundle=Poland%7C2027-01-01&edit=1").body_bytes.decode()
    assert "Plan design…" in edit and "/bulk/plan-changes" in edit


def test_the_first_shape_is_carried_over():
    """Migration 18 on rows of the first shape (migration 13): suggested /
    agreed → open, implemented → implemented, dropped → not implemented, a
    dismissed BM+ suggestion stays dismissed, a taken-over one stays tracked."""
    cid, ids = _book()
    m = ids["Medical"]
    whole = TWO[:200]
    with connection() as conn:
        rows = [(m, "Agreed one", "agreed", "you", None), (m, "Done one", "implemented", "you", "2027-01-01"),
                (m, "Dropped one", "dropped", "you", None), (m, whole, "suggested", "bm", None),
                (ids["Life"], whole, "dropped", "bm", None)]
        for rid, title, status, source, impl in rows:
            conn.execute("""INSERT INTO plan_changes (renewal_id, title, status, source, suggested_on,
                            implemented_on) VALUES (?, ?, ?, ?, '2026-10-01', ?)""",
                         (rid, title, status, source, impl))
        for t in ("design_change_renewals", "design_changes", "design_change_dismissed"):
            conn.execute(f"DELETE FROM {t}")
        sql = dict(schema.MIGRATIONS)[18]
        conn.executescript(sql[sql.index("-- carried over"):])
    v = _bundle(cid)
    got = {c["title"]: c["outcome"] for c in v["items"]}
    assert got == {"Agreed one": "open", "Done one": "implemented", "Dropped one": "not_implemented",
                   whole: "open"}
    assert next(c for c in v["items"] if c["title"] == "Done one")["decided_on"] == "2027-01-01"
    # the old whole-text take-over counts for both of Medical's lines; Life's dismissal for both of its
    assert [ln["state"] for ln in pc.panel(cid, [m], focus=m)["bm"]["lines"]] == ["tracked", "tracked"]
    p = pc.panel(cid, [ids["Life"]], focus=ids["Life"])
    assert [ln["state"] for ln in p["bm"]["lines"]] == ["dismissed", "dismissed"]
