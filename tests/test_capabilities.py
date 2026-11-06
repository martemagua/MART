"""The Insurer Capability Database ("All Networks", Martin 06.11.2026): a
reference list for all clients, uploaded like a tracker and replaced whole,
used to choose insurers for a remarketing and to see the networks behind
an insurer. Synthetic data only."""

from datetime import datetime

import pytest

from mart.ingestion import insurer_capability as ic
from mart.repository.db import connection
from mart.services import capabilities as caps
from mart.services import proposals as pr
from mart.services import renewal_service as rs
from mart.services import upload_service as us
from tests.conftest import get
from tests.fixtures import R, capability_db, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")
LIFE, MED = "Life/Survivor's", "Medical/Healthcare"

ROWS = [
    ("Europe", "Poland", "Generali", "Generali Zycie TU SA", LIFE, "Yes", "Yes", 0.9, "No", 0, "yes", 1,
     None),
    ("Europe", "Poland", "Generali", "Generali Zycie TU SA", MED, "Yes ", "no", 0, "No", 0, "No", 0, "Rider"),
    ("Europe", "Poland", "MAXIS", "PZU Zycie SA", LIFE, "Yes", "Yes", 1, "Yes", "80% to 99%", "No", 0, None),
    ("Europe", "Poland", "Maxis", "PZU Zycie SA", MED, "N0", "No", 0, "No", 0, "No", 0, None),
    ("Europe", "Poland", "Allianz", "None", LIFE, "No", "No", 0, "No", 0, "No", 0, "No presence"),
    ("Europe", "Germany", "Allianz", "Allianz Lebensversicherungs-Ag", LIFE, "Yes", "Yes", 0.9, "Yes", 0.9,
     "Yes", 0.9, None),
    ("Europe", "Germany", "Allianz", "Allianz Lebensversicherungs-Ag", "Workers Compensation", "No (CI:Yes)",
     "No", 0, "No", 0, "No", 0, None),
    ("Europe", "Germany", "Zurich", "Zurich Deutscher Herold", "Worker's Compensation", "Yes", "Yes", 1,
     "No", 0, "No", 0, None),
    ("Europe", "Poland", "Generali", "Generali Zycie TU SA", "Worker's Compensation", "No", "No", 0, "No", 0,
     "No", 0, None),
]


def _load(data: bytes, name: str = "2025 Insurer Capability Database - All Networks.xlsx") -> dict:
    uid = us.stage(name, data)
    return {"id": uid, "preview": us.preview(uid), "summary": us.commit(uid, set())}


def test_reading_the_export():
    p = ic.parse(capability_db(ROWS))
    assert p.sheet == "Database"
    assert p.networks == ["Allianz", "Generali", "MAXIS", "Zurich"]          # Maxis -> MAXIS
    by = {(r["country"], r["insurer"], r["line"]): r for r in p.rows}
    g = by[("Poland", "Generali Zycie TU SA", LIFE)]
    assert (g["fully_insured"], g["pool"], g["pool_share"]) == (1, 1, 0.9)
    assert (g["captive"], g["captive_share"]) == (1, 1)
    assert by[("Poland", "Generali Zycie TU SA", MED)]["fully_insured"] == 1                    # "Yes "
    assert by[("Poland", "PZU Zycie SA", MED)]["fully_insured"] == 0                            # "N0"
    assert by[("Poland", "PZU Zycie SA", LIFE)]["gip_share_text"] == "80% to 99%"
    odd = by[("Germany", "Allianz Lebensversicherungs-Ag", "Worker's Compensation")]          # one spelling
    assert odd["fully_insured"] == 0 and odd["fully_insured_text"] == "No (CI:Yes)"
    assert by[("Poland", None, LIFE)]["network"] == "Allianz"                # "None" = no partner
    assert {r["country_key"] for r in p.rows} == {"pl", "de"}
    # a version that names the network column works too; a wrong file is refused
    assert ic.parse(capability_db(ROWS, network_header="Network")).networks[0] == "Allianz"
    with pytest.raises(ic.NotThisTracker):
        ic.parse(capability_db([], network_header="Insurer name"))


def test_upload_replaces_the_whole_list(app):
    first = _load(capability_db(ROWS))
    assert first["preview"]["reference"] and first["preview"]["clients"] == []
    assert first["summary"]["rows"] == len(ROWS) and first["summary"]["new"] == len(ROWS)
    with connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0] == 0          # no pseudo-client
    changed = [r for r in ROWS if r[1] != "Germany"]
    changed[0] = (*changed[0][:5], "No", *changed[0][6:])
    japan = ("APAC", "Japan", "AIA", "AIA Japan", LIFE, "Yes", "Yes", 1, "No", 0, "No", 0, None)
    second = _load(capability_db(changed + [japan]), "2026 Insurer Capability Database.xlsx")
    s = second["summary"]
    assert (s["new"], s["changed"], s["removed"]) == (1, 1, 3)
    assert caps.loaded()["countries"] == 2                                   # Germany gone, Japan in
    page = get(app, "/uploads").body_bytes.decode()
    assert "Insurer Capability Database" in page and "All clients" in page and "partner rows" in page
    detail = get(app, f"/uploads/{second['id']}").body_bytes.decode()
    assert "Loaded" in detail and "no longer in the list" in detail


def test_insurer_names_match_within_a_country():
    assert caps.same_insurer("Allianz", "Allianz Lebensversicherungs-Ag")
    assert caps.same_insurer("Generali", "Assicurazioni Generali S.p.A.")
    assert caps.same_insurer("AXA", "AXA Seguros S.A. de C.V.")
    assert not caps.same_insurer("Sun Life", "Manulife") and not caps.same_insurer("Allianz", None)
    _load(capability_db(ROWS))
    assert caps.networks_of("Poland", ["PZU", "Generali", "Allianz"]) == {
        "PZU": ["MAXIS"], "Generali": ["Generali"], "Allianz": []}          # no Allianz partner in Poland
    assert caps.networks_of("Germany", ["Allianz"]) == {"Allianz": ["Allianz"]}


def test_insurers_page(app):
    assert "No Insurer Capability Database loaded yet" in get(app, "/insurers").body_bytes.decode()
    _load(capability_db(ROWS))
    start = get(app, "/insurers").body_bytes.decode()
    assert "Countries" in start and "/insurers?country=Poland" in start
    page = get(app, "/insurers?country=Poland").body_bytes.decode()
    assert "Generali Zycie TU SA" in page and "PZU Zycie SA" in page and "2 local partners" in page
    assert "No partner here: Allianz" in page and "✓ 90 %" in page and "80% to 99%" in page
    only = get(app, "/insurers?country=Poland&network=MAXIS").body_bytes.decode()
    assert "PZU Zycie SA" in only and "Generali Zycie TU SA" not in only


def test_proposals_show_the_networks_behind_an_insurer(app):
    _load(capability_db(ROWS))
    jan = datetime(2027, 1, 1, 1, 0)
    export = renewal_tracker([R(n=1, policy="Medical", renewal_date=jan)], cross_overview=True)
    uid = us.stage("rt.xlsx", export)
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)
    with connection() as conn:
        rid, cid = conn.execute("SELECT id, client_id FROM renewals").fetchone()
    pr.add(cid, rid, {"insurer": "PZU", "round": "first", "premium": "100000", "currency": "PLN"})
    d = rs.detail(cid, rid)
    assert [p["insurer"] for p in d["partners"]] == ["Generali Zycie TU SA", "PZU Zycie SA"]
    assert d["networks_of"]["PZU"] == ["MAXIS"]
    panel = get(app, f"/clients/{cid}/renewals/{rid}").body_bytes.decode()
    assert '<option value="PZU Zycie SA">MAXIS network</option>' in panel
    assert "2 network partners in Poland" in panel and 'title="Local partner of the MAXIS network' in panel
