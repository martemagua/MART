"""M3 day 2: the proposals Martin receives, recorded by him to compare them
(Martin, 05.11.2026; QUESTIONS D1, M3f). A proposal = one insurer + variant
holding its quotes, first to final (Martin, 06.11.2026)."""

from datetime import datetime

import pytest

from mart.repository import schema
from mart.repository.db import connect, connection
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
                      (_q("A", on="31.12.2026"), "date"), (_q("A", premium="-5"), "negative"),
                      (_q("A", plan_design="x"), "plan design"), (_q("A", label="x" * 81), "label")]:
        with pytest.raises(pr.Invalid, match=msg):
            pr.add(cid, ids["Medical"], form)
    with pytest.raises(pr.Invalid):
        pr.add(cid + 1, ids["Medical"], _q("A"))


def test_one_proposal_holds_its_negotiation():
    cid, ids = _book()
    m = ids["Medical"]
    allianz = pr.add(cid, m, _q("Allianz", "first", "130'000", rate="+12"))
    # a quote for the same insurer + variant joins the proposal (case and spacing ignored)
    assert pr.add(cid, m, _q(" allianz ", "revised", "124 000", rate="+7", on="2026-11-05")) == allianz
    pr.add_quote(cid, allianz, _q("", "final", "117.000", rate="+1,5", on="2026-11-10"))
    # another variant of the same insurer is a proposal of its own
    pdc = pr.add(cid, m, _q("Allianz", "first", "110000", plan_design="changed", label="without dental"))
    axa = pr.add(cid, m, _q("AXA", "first", "121.500,00", rate="+4,5"))
    pr.add(cid, m, _q("Generali", "first"))                          # no premium yet
    pr.add(cid, m, _q("Zurich", "final", "90000", currency="USD"))     # another currency
    v = rs.detail(cid, m)["my_proposals"]
    assert v["count"] == 5 and v["quotes"] == 7
    assert v["insurers"] == ["Allianz", "AXA", "Generali", "Zurich"]
    by = {(i["insurer"], i["plan_design"]): i for i in v["items"]}
    a = by[("Allianz", "as_expiring")]
    assert [q["round"] for q in a["quotes"]] == ["first", "revised", "final"]
    assert a["latest"]["premium"] == 117000 and a["moved"] == -10.0 and a["next_round"] == "final"
    assert by[("Allianz", "changed")]["lowest"] and by[("Allianz", "changed")]["label"] == "without dental"
    assert not a["lowest"] and by[("Zurich", "as_expiring")]["lowest"]       # lowest of ITS currency
    assert by[("AXA", "as_expiring")]["latest"]["rate_change"] == 4.5
    assert by[("Generali", "as_expiring")]["next_round"] == "revised"
    assert [i["insurer"] for i in v["items"]][:2] == ["Zurich", "Allianz"]   # by latest premium
    # the card and the panel agree
    card = next(r for r in cs.explorer(cid, bundle=POLAND)["selected"]["renewals"] if r["id"] == m)
    assert card["proposals"]["count"] == 5
    # chosen: one per renewal
    pr.choose(cid, axa, True)
    pr.choose(cid, pdc, True)
    v = rs.detail(cid, m)["my_proposals"]
    assert v["chosen"]["id"] == pdc and sum(i["chosen"] for i in v["items"]) == 1
    pr.choose(cid, pdc, False)
    assert rs.detail(cid, m)["my_proposals"]["chosen"] is None


def test_edit_quotes_and_proposals_and_uploads_keep_them():
    cid, ids = _book()
    pid = pr.add(cid, ids["Life"], _q("AXA", "first", "50000"))
    qid = pr.add_quote(cid, pid, _q("", "revised", "49000"))
    pr.edit_quote(cid, qid, _q("", "final", "48000", note="incl. dental"))
    pr.edit(cid, pid, {"insurer": "AXA Life", "plan_design": "changed", "label": "Option B"})
    _book()                                                           # the same export again
    p = rs.detail(cid, ids["Life"])["my_proposals"]["items"][0]
    assert (p["insurer"], p["plan_design"], p["label"]) == ("AXA Life", "changed", "Option B")
    q = p["latest"]
    assert (q["round"], q["premium"], q["note"]) == ("final", 48000, "incl. dental")
    pr.delete_quote(cid, qid)
    p = rs.detail(cid, ids["Life"])["my_proposals"]["items"][0]
    assert len(p["quotes"]) == 1 and p["moved"] is None
    pr.delete(cid, pid)
    assert rs.detail(cid, ids["Life"])["my_proposals"]["count"] == 0
    for call in (lambda: pr.delete(cid, pid), lambda: pr.add_quote(cid, pid, _q("")),
                 lambda: pr.edit_quote(cid, qid, _q(""))):
        with pytest.raises(pr.Invalid):
            call()


def test_quotes_recorded_one_by_one_are_merged(tmp_path):
    """Migration 12: the rows 0.9.5 kept per quote become one proposal per
    renewal, insurer and plan design, holding them as its quotes."""
    db = tmp_path / "old.db"
    conn = connect(db)
    for number, sql in schema.MIGRATIONS:
        if number <= 10:
            conn.executescript(f"BEGIN;\n{sql}\nPRAGMA user_version = {number};\nCOMMIT;")
    conn.execute("INSERT INTO clients (id, client_key, name) VALUES (1, 'k', 'Acme')")
    conn.execute("""INSERT INTO renewals (id, cycle_key, client_id, fields_json, bm_json, content_hash)
                    VALUES (1, 'c', 1, '{}', '{}', 'h')""")
    rows = [("Allianz", "first", 130000, 0), ("allianz", "final", 117000, 1), ("AXA", "first", 121000, 0),
            ("Allianz", "first", 110000, 0)]
    for i, (ins, rnd, prem, chosen) in enumerate(rows, start=1):
        design = "changed" if i == 4 else "as_expiring"
        conn.execute("""INSERT INTO proposals (renewal_id, insurer, round, received_on, premium, currency,
                                               plan_design, note, chosen)
                        VALUES (1, ?, ?, '2026-11-0' || ?, ?, 'EUR', ?, ?, ?)""",
                     (ins, rnd, i, prem, design, f"n{i}", chosen))
    conn.commit()
    conn.close()
    assert schema.ensure_schema(db) == schema.LATEST_VERSION
    conn = connect(db)
    from mart.repository import proposals_repo
    got = {(p["insurer"], p["plan_design"]): p for p in proposals_repo.for_renewal(conn, 1)}
    conn.close()
    assert len(got) == 3
    a = got[("Allianz", "as_expiring")]
    assert [(q["round"], q["premium"], q["note"]) for q in a["quotes"]] == [("first", 130000, "n1"),
                                                                            ("final", 117000, "n2")]
    assert a["chosen"] == 1 and len(got[("Allianz", "changed")]["quotes"]) == 1


def test_pages_and_routes(app):
    cid, ids = _book()
    base = f"/clients/{cid}"
    back = f"{base}/renewals/{ids['Medical']}"
    res = post(app, f"{base}/renewals/{ids['Medical']}/proposals",
               {**_q("Allianz", "first", "125000", rate="5"), "back": back})
    assert res.status == 303 and dict(res.headers)["Location"].endswith("#proposals")
    assert post(app, f"{base}/renewals/{ids['Medical']}/proposals", {"insurer": ""}).status == 400
    pid = rs.detail(cid, ids["Medical"])["my_proposals"]["items"][0]["id"]
    res = post(app, f"{base}/proposals/{pid}/quotes", {**_q("", "final", "118000", rate="2"), "back": back})
    assert res.status == 303
    post(app, f"{base}/renewals/{ids['Medical']}/proposals", {**_q("AXA", "first", "121000"), "back": back})
    panel = get(app, back).body_bytes.decode()
    assert 'id="myprop-h"' in panel and "118&#39;000 EUR" in panel and "+2\u00a0%" in panel
    assert "Negotiation: 2 quotes" in panel and "−5.6\u00a0% from 125&#39;000" in panel
    assert ("<h4>In BM+" in panel) == bool(rs.detail(cid, ids["Medical"])["proposals"])  # BM+'s sheet too
    assert panel.index('id="strat-h"') < panel.index('id="myprop-h"') < panel.index('id="facts-h"')
    card = get(app, f"{base}?bundle=Poland%7C2027-01-01").body_bytes.decode()
    assert "2 proposals: Allianz, AXA" in card and "2 from 2 insurers" in card
    assert post(app, f"{base}/proposals/{pid}/chosen", {"chosen": "1", "back": back}).status == 303
    assert "★ Allianz" in get(app, f"{base}?bundle=Poland%7C2027-01-01").body_bytes.decode()
    qid = rs.detail(cid, ids["Medical"])["my_proposals"]["items"][0]["quotes"][0]["id"]
    assert post(app, f"{base}/quotes/{qid}/delete", {"back": back}).status == 303
