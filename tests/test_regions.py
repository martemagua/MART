"""M3 day 5: each client's own regions (Martin, 05.11.2026; QUESTIONS C4,
M3e): prefilled from BM+'s Region per country, changeable per client, and a
region filter in the explorer's side panel."""

from datetime import datetime
from urllib.parse import urlencode

import pytest

from mart.repository.db import connection
from mart.services import client_service as cs
from mart.services import regions
from mart.services import upload_service as us
from mart.web.framework import Request
from tests.conftest import get, post
from tests.fixtures import R, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")
JAN = datetime(2027, 1, 1, 1, 0)


def _book() -> int:
    rows = [R(n=1, policy="Medical", country="Poland", renewal_date=JAN),
            R(n=2, policy="Life", country="Canada", renewal_date=JAN),
            R(n=3, policy="Dental", country="Mexico", renewal_date=JAN)]
    uid = us.stage("rt.xlsx", renewal_tracker(rows, cross_overview=True))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)
    with connection() as conn:
        return conn.execute("SELECT id FROM clients").fetchone()["id"]


def test_bm_region_cleaned_and_commonest():
    assert regions.clean("EMEA, EMEA") == "EMEA" and regions.clean(" ") is None
    assert regions.clean("EMEA, APAC") == "EMEA, APAC"
    rows = regions.table([("Belgium", None, 1), ("Belgium", "EMEA", 2), ("Belgium", "EMEA, EMEA", 1),
                          ("Belgium", "Europe", 1), ("Chile", None, 1)], {"Chile": "LatAm"})
    assert [(r["country"], r["bm"], r["region"], r["renewals"]) for r in rows] == [
        ("Belgium", "EMEA", "EMEA", 5), ("Chile", None, "LatAm", 1)]


def test_set_per_client_and_back_to_bm(app):
    cid = _book()
    page = regions.for_client(cid)
    assert [(r["country"], r["region"]) for r in page["rows"]] == [("Canada", "EMEA"), ("Mexico", "EMEA"),
                                                                    ("Poland", "EMEA")]
    assert regions.save(cid, {"Canada": "North America", "Mexico": " LatAm ", "Poland": "emea"}) == 2
    got = {r["country"]: (r["region"], r["mine"]) for r in regions.for_client(cid)["rows"]}
    assert got == {"Canada": ("North America", "North America"), "Mexico": ("LatAm", "LatAm"),
                   "Poland": ("EMEA", None)}                          # = BM+'s: no override kept
    v = cs.explorer(cid)
    assert v["filters"]["regions"] == ["EMEA", "LatAm", "North America"]
    assert {b["country"]: b["region"] for items in v["groups"].values() for b in items} == {
        "Canada": "North America", "Mexico": "LatAm", "Poland": "EMEA"}
    regions.save(cid, {"Canada": ""})                                 # empty: BM+'s again
    assert regions.for_client(cid)["rows"][0]["region"] == "EMEA"
    with pytest.raises(regions.Invalid):
        regions.save(cid, {"Atlantis": "Myth"})
    with pytest.raises(regions.Invalid):
        regions.save(cid, {"Canada": "x" * 61})
    with pytest.raises(regions.Invalid):
        regions.for_client(cid + 1)


def test_pages(app):
    cid = _book()
    page = get(app, f"/clients/{cid}/regions").body_bytes.decode()
    assert "Regions · Acme Group" in page and 'name="country" value="Canada"' in page and "BM+ says" in page
    body = urlencode([("country", "Canada"), ("region", "North America"), ("country", "Mexico"),
                      ("region", ""), ("country", "Poland"), ("region", "")]).encode()
    res = app.handle(Request("POST", f"/clients/{cid}/regions", "",
                             {"content-type": "application/x-www-form-urlencoded"}, body))
    assert res.status == 303 and "Regions%20saved" in dict(res.headers)["Location"]
    explorer = get(app, f"/clients/{cid}").body_bytes.decode()
    assert 'data-f-multi="region"' in explorer and 'data-region="North America"' in explorer
    # several regions and countries can be ticked; each country carries its
    # region, so ticking a region narrows the countries (mart.js)
    assert 'data-f-multi="country"' in explorer and 'value="North America" data-f-opt' in explorer
    assert '<label data-region="North America"><input type="checkbox" value="Canada" data-f-opt>' in explorer
    board = get(app, f"/clients/{cid}/board").body_bytes.decode()
    assert 'data-f-multi="region"' in board and 'data-f-multi="country"' in board
    assert f'href="/clients/{cid}/regions"' in explorer
    assert post(app, f"/clients/{cid}/regions", {"country": "Canada"}).status == 400     # region missing
