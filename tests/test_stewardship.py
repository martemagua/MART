"""M3 day 9, the stewardship (Martin, 08.11.2026): the reporting period and
which renewals it holds, the savings MART suggests from the quotes (hard =
expiring − final, cost avoidance = first quote − final, unrealized = final −
cheapest option not taken) until Martin confirms them, the key learning, the
page, and the client's reporting currency read from a single-client export."""

from datetime import date, datetime
from urllib.parse import urlencode

import pytest

from mart.repository.db import connection
from mart.services import proposals as pr
from mart.services import stewardship as st
from mart.services import upload_service as us
from mart.web.framework import Request
from tests.conftest import get, post
from tests.fixtures import CLIENT, R, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")
FORM = {"content-type": "application/x-www-form-urlencoded"}


def _book(flavour: str = CLIENT) -> tuple[int, dict[str, int]]:
    rows = [
        R(n=1, policy="Medical", renewal_date=datetime(2026, 1, 1, 1), premium=120_000),
        R(n=2, policy="Life", renewal_date=datetime(2026, 7, 1, 1), premium=10_000),
        R(n=3, policy="Dental", country="Spain", entity="Acme Iberia", renewal_date=datetime(2027, 1, 1, 1)),
    ]
    uid = us.stage("rt.xlsx", renewal_tracker(rows, flavour, reporting_currency="US Dollar (USD)"))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)
    with connection() as conn:
        ids = {r["policy_name"]: r["id"] for r in conn.execute("SELECT id, policy_name FROM renewals")}
        cid = conn.execute("SELECT id FROM clients").fetchone()["id"]
        conn.execute("UPDATE clients SET is_mine = 1")
    return cid, ids


def _quote(cid, rid, insurer, premium, rnd="first", currency="USD") -> int:
    return pr.add(
        cid,
        rid,
        {
            "insurer": insurer,
            "round": rnd,
            "premium": premium,
            "currency": currency,
            "received_on": "2025-11-01",
        },
    )


def test_the_reporting_period():
    today = date(2026, 11, 8)
    p = st.period(1, today=today)
    assert (p["from"], p["until"], p["label"], p["running"]) == ("2026-01-01", "2026-12-31", "2026", True)
    p = st.period(4, today=today)
    assert (p["from"], p["until"], p["label"]) == ("2026-04-01", "2027-03-31", "2026/27")
    assert st.period(4, today=date(2026, 2, 1))["from"] == "2025-04-01"  # not yet April: last year's
    assert st.period(1, 2025)["until"] == "2025-12-31"
    p = st.period(frm="2025-07-01", until="2026-06-30")
    assert p["custom"] and p["label"] == "01.07.2025 – 30.06.2026"
    for bad in (lambda: st.period(frm="2026-02-30"), lambda: st.period(frm="2026-07-01", until="2026-01-01")):
        with pytest.raises(st.Invalid):
            bad()


def test_savings_suggested_from_the_quotes():
    pv = {
        "chosen": {
            "id": 1,
            "insurer": "A",
            "first": {"premium": 115_000, "currency": "USD"},
            "latest": {"premium": 105_000, "currency": "USD"},
        },
        "items": [
            {"id": 1, "latest": {"premium": 105_000, "currency": "USD"}},
            {"id": 2, "latest": {"premium": 98_000, "currency": "USD"}},
            {"id": 3, "latest": {"premium": 90_000, "currency": "EUR"}},
        ],
    }  # another currency: ignored
    s = st.suggest(pv, 120_000, "USD")
    assert (s["hard"]["amount"], s["avoidance"]["amount"], s["unrealized"]["amount"]) == (
        15_000,
        10_000,
        7_000,
    )
    assert s["hard"]["basis"] == [("expiring (BM+)", 120_000), ("final", 105_000)]
    # the final quote in another currency than BM+'s reporting one: no hard savings, and why
    s = st.suggest(pv, 120_000, "EUR")
    assert (
        s["hard"] is None
        and "reporting currency (EUR)" in s["hard_why"]
        and s["avoidance"]["amount"] == 10_000
    )
    assert "upload one" in st.suggest(pv, 120_000, None)["hard_why"]  # the reporting currency unknown yet
    # more than half the expiring premium: flagged (quotes for another cover?)
    assert st.suggest(pv, 400_000, "USD")["hard"]["check"] and not s["avoidance"].get("check")
    # a premium increase is no saving; nothing chosen: nothing suggested, and why
    assert st.suggest(pv, 100_000, "USD")["hard"]["amount"] == 0
    s = st.suggest({"chosen": None, "items": []}, 120_000, "USD")
    assert s["why"] and all(s[k] is None for k in st.KINDS)


def test_a_renewal_confirmed_corrected_and_its_learning(app):
    cid, ids = _book()
    m = ids["Medical"]
    with connection() as conn:
        assert conn.execute("SELECT reporting_currency FROM clients").fetchone()[0] == "USD"
    assert not st.for_renewal(cid, m)["any"]
    a = _quote(cid, m, "Allianz", "115'000")
    _quote(cid, m, "Allianz", "105'000", "final")
    _quote(cid, m, "Generali", "98'000")
    pr.choose(cid, a, True)
    rv = st.for_renewal(cid, m)
    assert not rv["confirmed"] and rv["amounts"] == {"hard": 15_000, "avoidance": 10_000, "unrealized": 7_000}
    st.save_savings(cid, m, "15'000", "10'000", "", "usd", "rate guarantee two years")
    rv = st.for_renewal(cid, m)
    assert rv["confirmed"] and rv["amounts"]["unrealized"] == 0 and rv["currency"] == "USD"
    for bad in (
        lambda: st.save_savings(cid, m, "-5", "", "", "USD", None),
        lambda: st.save_savings(cid, m, "1.2m", "", "", "USD", None),
        lambda: st.save_savings(cid, m, "1", "", "", "dollars", None),
        lambda: st.save_savings(cid + 1, m, "1", "", "", "USD", None),
    ):
        with pytest.raises(st.Invalid):
            bad()
    st.reset_savings(cid, m)
    assert (
        not st.for_renewal(cid, m)["confirmed"] and st.for_renewal(cid, m)["amounts"]["unrealized"] == 7_000
    )
    st.save_learning(cid, m, "  Three pooling partners   brought +2 % instead of +9 %  ")
    assert st.for_renewal(cid, m)["key_learning"] == "Three pooling partners brought +2 % instead of +9 %"
    # the routes, back to the renewal's savings
    back = f"/clients/{cid}/renewals/{m}"
    body = urlencode(
        {
            "hard": "15000",
            "avoidance": "10000",
            "unrealized": "0",
            "currency": "USD",
            "note": "",
            "back": back,
        }
    ).encode()
    res = app.handle(Request("POST", f"/clients/{cid}/renewals/{m}/savings", "", FORM, body))
    assert res.status == 303 and dict(res.headers)["Location"].endswith(f"#savings-{m}")
    assert post(app, f"/clients/{cid}/renewals/{m}/savings", {"hard": "x1", "back": back}).status == 400
    panel = get(app, back).body_bytes.decode()
    assert (
        "Savings &amp; key learning" in panel and "✓ confirmed" in panel and "Three pooling partners" in panel
    )
    assert post(app, f"/clients/{cid}/renewals/{m}/savings/reset", {"back": back}).status == 303
    assert "suggested by MART" in get(app, back).body_bytes.decode()
    assert post(app, f"/clients/{cid}/renewals/{m}/learning", {"text": "", "back": back}).status == 303
    assert st.for_renewal(cid, m)["key_learning"] is None


def test_the_page_holds_the_renewals_with_a_renewal_date_in_the_period(app):
    cid, ids = _book()
    a = _quote(cid, ids["Medical"], "Allianz", "115'000")
    _quote(cid, ids["Medical"], "Allianz", "105'000", "final")
    pr.choose(cid, a, True)
    v = st.view(cid, 2026)
    assert v["period"]["label"] == "2026" and list(v["countries"]) == ["Poland"]
    assert [x["policy_name"] for x in v["countries"]["Poland"]] == ["Medical", "Life"]  # Spain renews 2027
    s = v["summary"]
    assert (s["renewals"], s["completed"], s["proposals"], s["suggested"], s["confirmed"]) == (2, 0, 1, 1, 0)
    assert s["savings"] == {"USD": {"hard": 15_000, "avoidance": 10_000}}
    st.save_savings(cid, ids["Life"], "500", "", "", "EUR", None)  # another currency: its own line
    assert st.view(cid, 2026)["summary"]["savings"]["EUR"] == {"hard": 500}
    # April to March: Medical (Jan 2026) falls in 2025/26, Life (Jul 2026) in 2026/27
    st.set_start_month(cid, "4")
    assert [x["policy_name"] for x in st.view(cid, 2025)["countries"]["Poland"]] == ["Medical"]
    assert st.view(cid, frm="2026-01-01", until="2027-12-31")["summary"]["renewals"] == 3
    with pytest.raises(st.Invalid):
        st.set_start_month(cid, "13")
    page = get(app, f"/clients/{cid}/stewardship?year=2026").body_bytes.decode()
    assert "Stewardship · Acme Group" in page and "Reporting period 01.04.2026 – 31.03.2027" in page
    assert "renewal date in this period" in page and "Print / PDF" in page and "Life" in page
    assert (
        post(
            app, f"/clients/{cid}/stewardship/period", {"month": "1", "back": f"/clients/{cid}/stewardship"}
        ).status
        == 303
    )
    assert (
        "Reporting period 01.01.2026 – 31.12.2026"
        in get(app, f"/clients/{cid}/stewardship?year=2026").body_bytes.decode()
    )
    assert get(app, f"/clients/{cid}/stewardship?from=2026-13-01").status == 400
    assert f'href="/clients/{cid}/stewardship"' in get(app, f"/clients/{cid}").body_bytes.decode()
