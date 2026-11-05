"""M2 day 3: broker deadlines on bundles (Martin, 04.11.2026; QUESTIONS M2b,
E4, K4). A bundle's expected update date, prefilled from BM+'s expected-terms
date, paused stale clock while ahead, red once passed until Martin confirms."""

from datetime import date, datetime, timedelta

import pytest

from mart.repository.db import connection
from mart.services import bundle_service as bs
from mart.services import client_service as cs
from mart.services import deadlines as dl
from mart.services import upload_service as us
from tests.conftest import get, post
from tests.fixtures import R, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")
TODAY = date.today()
POLAND = "Poland|2027-01-01"


def _iso(days: int) -> str:
    return (TODAY + timedelta(days=days)).isoformat()


def _hdr(days_ago: int) -> str:
    return (TODAY - timedelta(days=days_ago)).strftime("%d %b %Y")


def _load(rows) -> int:
    uid = us.stage("rt.xlsx", renewal_tracker(rows, cross_overview=True))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)
    with connection() as conn:
        return conn.execute("SELECT id FROM clients").fetchone()["id"]


def _book(terms_med=None, terms_life=None) -> int:
    jan = datetime(2027, 1, 1, 1, 0)
    return _load([
        R(n=1, policy="Medical", renewal_date=jan, overview=f"{_hdr(30)}:\nOld news.",
          final_terms_date=datetime.combine(terms_med, datetime.min.time()) if terms_med else None),
        R(n=2, policy="Life", renewal_date=jan, overview=f"{_hdr(20)}:\nOld news.",
          final_terms_date=datetime.combine(terms_life, datetime.min.time()) if terms_life else None),
        R(n=3, policy="Dental", country="Spain", renewal_date=jan)])


def _poland(cid: int) -> dict:
    return cs.explorer(cid, bundle=POLAND)["selected"]


def test_effective_rules():
    t = date(2026, 11, 4)
    bm = [("Medical", "2026-11-20"), ("Life", "2026-11-12")]
    d = dl.effective([], bm, t)
    assert (d["expected_date"], d["source"], d["state"], d["days"]) == ("2026-11-12", "bm", "ahead", 8)
    assert dl.effective([], [("Medical", "2026-11-01")], t)["state"] == "passed"
    assert dl.effective([], [], t) is None
    mine = [{"id": 1, "expected_date": "2026-11-30", "status": "open", "source": "you", "promised_by": "A",
             "note": None, "created_at": "2026-11-02 10:00:00"}]
    d = dl.effective(mine, bm, t, newest_entry="2026-11-03")
    assert d["expected_date"] == "2026-11-30" and d["bm_differs"] and d["new_entry"] == "2026-11-03"
    assert dl.effective(mine, bm, t, newest_entry="2026-11-01")["new_entry"] is None
    # a BM+ date no later than one already closed is not offered again
    closed = [{**mine[0], "status": "confirmed", "expected_date": "2026-11-15"}]
    assert dl.effective(closed, bm, t) is None
    assert dl.effective(closed, [("x", "2026-12-01")], t)["expected_date"] == "2026-12-01"


def test_bm_prefill_and_paused_clock():
    cid = _book(terms_med=TODAY + timedelta(days=9), terms_life=TODAY + timedelta(days=5))
    s = _poland(cid)
    assert s["deadline"]["expected_date"] == _iso(5) and s["deadline"]["source"] == "bm"
    assert sorted(d for _, d in s["deadline"]["bm_dates"]) == [_iso(5), _iso(9)]
    # both overviews are old (30 and 20 days) but the promise is ahead: paused, not red
    assert {r["freshness"]["state"] for r in s["renewals"]} == {"paused"}
    assert s["freshness"]["state"] == "paused"
    spain = next(b for g in cs.explorer(cid)["groups"].values() for b in g if b["country"] == "Spain")
    assert spain["deadline"] is None


def test_passed_deadline_is_red_until_confirmed():
    cid = _book(terms_med=TODAY - timedelta(days=3))
    s = _poland(cid)
    assert s["deadline"]["state"] == "passed" and s["freshness"]["state"] == "red"
    dl.close(cid, POLAND, "confirmed", s["deadline"]["expected_date"])   # a BM+ one is stored when closed
    s = _poland(cid)
    assert s["deadline"] is None and s["deadline_history"][0]["status"] == "confirmed"
    assert s["deadline_history"][0]["source"] == "bm"


def test_set_replace_and_drop():
    cid = _book()
    assert _poland(cid)["deadline"] is None
    dl.set_deadline(cid, POLAND, _iso(7), "  Broker   A ", "final terms")
    dl.set_deadline(cid, POLAND, _iso(10), "Broker A")
    s = _poland(cid)
    assert (s["deadline"]["expected_date"], s["deadline"]["promised_by"]) == (_iso(10), "Broker A")
    assert [h["status"] for h in s["deadline_history"]] == ["replaced"]
    dl.close(cid, POLAND, "dropped", None)
    assert _poland(cid)["deadline"] is None
    for bad in ((cid, POLAND, "soon"), (cid, "nonsense", _iso(1)), (cid, "custom|999", _iso(1)),
                (999, POLAND, _iso(1))):
        with pytest.raises(dl.Invalid):
            dl.set_deadline(*bad)
    with pytest.raises(dl.Invalid):
        dl.close(cid, POLAND, "forgotten", None)


def test_follows_the_bundle_and_keeps_an_emptied_one():
    cid = _book()
    dl.set_deadline(cid, POLAND, _iso(4))
    with connection() as conn:
        ids = [r["id"] for r in conn.execute("SELECT id FROM renewals WHERE country = 'Poland'")]
    key = bs.move(cid, ids, bs.NEW, "Everything Poland")
    groups = cs.explorer(cid)["groups"].values()
    by_key = {b["key"]: b for g in groups for b in g}
    assert by_key[POLAND]["renewals"] == [] and by_key[POLAND]["deadline"]["expected_date"] == _iso(4)
    assert by_key[key]["deadline"] is None                                # the moved renewals left it


def test_through_the_pages(app):
    cid = _book(terms_med=TODAY + timedelta(days=6))
    page = get(app, f"/clients/{cid}?bundle=Poland%7C2027-01-01").body_bytes.decode()
    assert 'class="dl-line dl-ahead"' in page and "from BM+" in page and 'class="dl-badge dl-ahead"' in page
    back = f"/clients/{cid}?bundle=Poland%7C2027-01-01"
    r = post(app, f"/clients/{cid}/bundles/deadline", {"key": POLAND, "date": _iso(12),
                                                         "promised_by": "Broker A", "back": back})
    assert r.status == 303 and dict(r.headers)["Location"].endswith("#deadline")
    page = get(app, back).body_bytes.decode()
    assert "promised by Broker A" in page and "BM+ says" in page
    with connection() as conn:
        med = conn.execute("SELECT id FROM renewals WHERE policy_name = 'Medical'").fetchone()["id"]
    assert "Expected update" in get(app, f"/clients/{cid}/renewals/{med}").body_bytes.decode()
    r = post(app, f"/clients/{cid}/bundles/deadline/close", {"key": POLAND, "outcome": "confirmed",
                                                               "date": _iso(12), "back": back})
    assert r.status == 303 and "+ Expected update" in get(app, back).body_bytes.decode()
    assert post(app, f"/clients/{cid}/bundles/deadline", {"key": POLAND, "date": "x"}).status == 400
