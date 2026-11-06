"""M3 day 2: the proposals Martin receives, recorded by him to compare them
(Martin, 05.11.2026; QUESTIONS D1, M3f)."""

from datetime import datetime

import pytest

from mart.repository.db import connection
from mart.services import client_service as cs
from mart.services import proposals as pr
from mart.services import renewal_service as rs
from mart.services import upload_service as us
from tests.conftest import get, post
from tests.fixtures import R, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")
POLAND = "Poland|2027-01-01"
JAN = datetime(2027, 1, 1, 1, 0)


def _book() -> tuple[int, dict[str, int]]:
    uid = us.stage("rt.xlsx", renewal_tracker([R(n=1, policy="Medical", renewal_date=JAN),
                                               R(n=2, policy="Life", renewal_date=JAN)], cross_overview=True))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)
    with connection() as conn:
        ids = {r["policy_name"]: r["id"] for r in conn.execute("SELECT id, policy_name FROM renewals")}
        cid = conn.execute("SELECT id FROM clients").fetchone()["id"]
    return cid, ids


def _q(insurer, rnd="first", premium=None, currency="EUR", rate=None, on="2026-11-01", **kw):
    """A proposal form as the browser sends it (empty fields as "")."""
    form = {"insurer": insurer, "round": rnd, "premium": premium, "currency": currency,
            "rate_change": rate, "received_on": on, **kw}
    return {k: "" if v is None else v for k, v in form.items()}


@pytest.mark.parametrize("text, thousands, value", [
    ("120 000", True, 120000), ("120'000", True, 120000), ("120.000,50", True, 120000.5),
    ("120,000.50", True, 120000.5), ("12,5", True, 12.5), ("12,345", True, 12345),
    ("1.234.567", True, 1234567), ("+8", False, 8), ("-3,5 %", False, -3.5), ("8.5", False, 8.5),
    ("", True, None), ("EUR 50000", True, 50000),
])
def test_numbers_as_typed(text, thousands, value):
    assert pr.parse_number(text, thousands) == value


def test_bad_input_is_refused():
    cid, ids = _book()
    for form, msg in [(_q(""), "Which insurer"), (_q("A", rnd="x"), "first, revised"),
                      (_q("A", premium="lots"), "isn't a number"),
                      (_q("A", premium="5", currency="EURO"), "three"),
                      (_q("A", on="31.12.2026"), "date"), (_q("A", premium="-5"), "negative")]:
        with pytest.raises(pr.Invalid, match=msg):
            pr.add(cid, ids["Medical"], form)
    with pytest.raises(pr.Invalid):
        pr.add(cid + 1, ids["Medical"], _q("A"))


def test_compare_latest_quote_per_insurer_and_lowest():
    cid, ids = _book()
    m = ids["Medical"]
    pr.add(cid, m, _q("Allianz", "first", "130'000", rate="+12"))
    final = pr.add(cid, m, _q("Allianz", "final", "118 000", rate="+2", on="2026-11-10"))
    axa = pr.add(cid, m, _q("AXA", "first", "121.500,00", rate="+4,5"))
    pr.add(cid, m, _q("Generali", "first"))                        # no premium yet
    pr.add(cid, m, _q("Zurich", "final", "90000", currency="USD"))   # another currency
    v = rs.detail(cid, m)["my_proposals"]
    card = next(r for r in cs.explorer(cid, bundle=POLAND)["selected"]["renewals"] if r["id"] == m)
    assert card["proposals"]["count"] == v["count"]                 # the card and the panel agree
    by = {(p["insurer"], p["round"]): p for p in v["items"]}
    assert not by[("Allianz", "first")]["current"] and by[("Allianz", "final")]["current"]
    assert by[("Allianz", "final")]["lowest"] and not by[("AXA", "first")]["lowest"]
    assert by[("Zurich", "final")]["lowest"]                        # lowest of ITS currency
    assert by[("AXA", "first")]["premium"] == 121500 and by[("AXA", "first")]["rate_change"] == 4.5
    assert v["count"] == 5 and v["insurers"] == ["Allianz", "AXA", "Generali", "Zurich"]
    # chosen: one per renewal
    pr.choose(cid, axa, True)
    pr.choose(cid, final, True)
    v = rs.detail(cid, m)["my_proposals"]
    assert v["chosen"]["id"] == final and sum(p["chosen"] for p in v["items"]) == 1
    pr.choose(cid, final, False)
    assert rs.detail(cid, m)["my_proposals"]["chosen"] is None


def test_edit_delete_and_upload_keeps_them():
    cid, ids = _book()
    pid = pr.add(cid, ids["Life"], _q("AXA", "first", "50000"))
    pr.edit(cid, pid, _q("AXA", "revised", "48000", note="incl. dental"))
    _book()                                                         # the same export again
    p = rs.detail(cid, ids["Life"])["my_proposals"]["items"][0]
    assert (p["round"], p["premium"], p["note"]) == ("revised", 48000, "incl. dental")
    pr.delete(cid, pid)
    assert rs.detail(cid, ids["Life"])["my_proposals"]["count"] == 0
    with pytest.raises(pr.Invalid):
        pr.delete(cid, pid)


def test_pages_and_routes(app):
    cid, ids = _book()
    base = f"/clients/{cid}"
    back = f"{base}/renewals/{ids['Medical']}"
    res = post(app, f"{base}/renewals/{ids['Medical']}/proposals",
               {**_q("Allianz", "final", "118000", rate="2"), "back": back})
    assert res.status == 303 and dict(res.headers)["Location"].endswith("#proposals")
    assert post(app, f"{base}/renewals/{ids['Medical']}/proposals", {"insurer": ""}).status == 400
    post(app, f"{base}/renewals/{ids['Medical']}/proposals", {**_q("AXA", "first", "121000"), "back": back})
    panel = get(app, back).body_bytes.decode()
    assert "Proposals received" in panel and "118&#39;000 EUR" in panel and "+2 %" in panel
    assert "Proposals in BM+" in panel
    assert panel.index("Proposals received") < panel.index('id="facts-h"')      # in the "yours" slot
    card = get(app, f"{base}?bundle=Poland%7C2027-01-01").body_bytes.decode()
    assert "2 proposals: Allianz, AXA" in card and "2 from 2 insurers" in card
    pid = rs.detail(cid, ids["Medical"])["my_proposals"]["items"][0]["id"]
    assert post(app, f"{base}/proposals/{pid}/chosen", {"chosen": "1", "back": back}).status == 303
    assert "★ Allianz" in get(app, f"{base}?bundle=Poland%7C2027-01-01").body_bytes.decode()
