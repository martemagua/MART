import json
from datetime import date, datetime

import pytest

from mart.repository.db import connection
from mart.services import client_service as cs
from mart.services import upload_service as us
from tests.conftest import get
from tests.fixtures import CLIENT, CROSS, R, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")

TODAY = date(2026, 11, 4)
OV = "14 Oct 2026:\nQuotes expected by 15 Nov.\nInternal: budget tight.\n\n20 Aug 2026:\nKick-off held."
OV_CR = "14 Oct 2026:\nQuotes expected by 15 Nov.\n\n20 Aug 2026:\nKick-off held."


def _book():
    jan = datetime(2027, 1, 1, 1, 0)
    return [
        R(n=1, policy="Medical", country="Poland", entity="Acme PL", renewal_date=jan,
          overview=OV, overview_cr=OV_CR),
        R(n=2, policy="Life", country="Poland", entity="Acme PL", renewal_date=jan, overview=OV,
          overview_cr=None),
        R(n=3, policy="Disability", country="Poland", entity="Acme PL Services", renewal_date=jan),
        R(n=4, policy="Medical", country="Spain", entity="Acme ES", renewal_date=datetime(2027, 2, 1)),
        R(n=5, policy="Life", country="Brazil", entity="Acme BR", renewal_date=datetime(2026, 7, 1)),
    ]


def _load(renewals, flavour=CROSS, **kw) -> int:
    uid = us.stage("rt.xlsx", renewal_tracker(renewals, flavour, **kw))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]})
    with connection() as conn:
        return conn.execute("SELECT id FROM clients WHERE name = 'Acme Group'").fetchone()["id"]


def test_bundles_are_country_plus_renewal_date():
    cid = _load(_book(), cross_overview=True)
    v = cs.explorer(cid, today=TODAY)
    assert v["bundle_count"] == 3 and v["renewal_count"] == 5
    assert list(v["groups"]) == ["July 2026", "January 2027", "February 2027"]
    # nothing asked for: the bundle at the top of the side panel (the page
    # opens at the top, Martin 04.11.2026), here one already past its date
    s = v["selected"]
    assert (s["country"], s["renewal_date"], len(s["renewals"])) == ("Brazil", "2026-07-01", 1)
    s = cs.explorer(cid, bundle=cs.bundle_key("Poland", "2027-01-01"), today=TODAY)["selected"]
    assert s["days_until"] == 58 and s["entities"] == ["Acme PL", "Acme PL Services"]
    assert v["filters"] == {"countries": ["Brazil", "Poland", "Spain"],
                            "first": "2026-07-01", "last": "2027-02-01"}


def test_choosing_a_bundle():
    cid = _load(_book())
    v = cs.explorer(cid, bundle=cs.bundle_key("Spain", "2027-02-01"), today=TODAY)
    assert list(v["groups"]) == ["July 2026", "January 2027", "February 2027"]   # always by month
    assert v["selected"]["country"] == "Spain"


def test_overview_states_in_the_bundle():
    cid = _load(_book(), cross_overview=True)
    s = cs.explorer(cid, bundle=cs.bundle_key("Poland", "2027-01-01"), today=TODAY)["selected"]
    states = {r["policy_name"]: r["overview_state"] for r in s["renewals"]}
    assert states == {"Medical": "gaps", "Life": "no_cr", "Disability": "empty"}
    med = next(r for r in s["renewals"] if r["policy_name"] == "Medical")
    assert med["overview"]["internal_entries"] == 1


def test_real_cross_client_exports_bring_their_overview_in():
    """Martin's real cross-client exports carry a full overview (unlike the demo):
    it must be loaded, not ignored."""
    cid = _load(_book(), cross_overview=True)
    with connection() as conn:
        f = json.loads(conn.execute("SELECT fields_json FROM renewals WHERE client_id = ? AND "
                                    "policy_name = 'Medical' AND country = 'Poland'", (cid,))
                       .fetchone()[0])
    assert f["overview_all"] == OV and f["overview_client_ready"] == OV_CR


def test_renewals_no_longer_in_the_export_are_hidden_unless_asked():
    cid = _load(_book())
    _load([r for r in _book() if r.country != "Brazil"], report_date="10 Nov 2026")
    v = cs.explorer(cid, today=TODAY)
    assert v["left_count"] == 1 and v["bundle_count"] == 2
    assert cs.explorer(cid, show_all=True, today=TODAY)["bundle_count"] == 3


def test_clients_overview_counts():
    _load(_book(), cross_overview=True)
    row = next(c for c in cs.clients_overview(TODAY) if c["name"] == "Acme Group")
    assert row["renewals"] == 5 and row["bundles"] == 3
    assert row["flags"] == {"gaps": 1, "no_cr": 1, "empty": 3}


def test_only_my_clients_can_be_opened():
    uid = us.stage("rt.xlsx", renewal_tracker([R(client="Globex")]))
    us.commit(uid, set())
    with connection() as conn:
        gid = conn.execute("SELECT id FROM clients WHERE name = 'Globex'").fetchone()["id"]
    with pytest.raises(cs.NotFound):
        cs.explorer(gid)


# -- the pages ------------------------------------------------------------------------
def test_clients_and_explorer_pages(app):
    cid = _load(_book(), cross_overview=True)
    html = get(app, "/clients").body_bytes.decode()
    assert f'href="/clients/{cid}"' in html and "1 with gaps" in html
    page = get(app, f"/clients/{cid}").body_bytes.decode()
    assert "Brazil · 01.07.2026" in page and 'data-fresh' in page
    assert "By country" not in page and "group=" not in page          # the toggle is gone
    assert '<img class="flag" src="/static/flags/br.svg"' in page
    assert 'type="date" data-f="from" min="2026-07-01" max="2027-02-01"' in page
    spain = get(app, f"/clients/{cid}?bundle=Spain%7C2027-02-01").body_bytes.decode()
    assert "Spain · 01.02.2027" in spain and "data-fresh" not in spain
    assert 'data-country="Spain" data-first="2027-02-01" data-last="2027-02-01"' in spain
    poland = get(app, f"/clients/{cid}?bundle=Poland%7C2027-01-01").body_bytes.decode()
    assert "not in client-ready" in poland and "no client-ready" in poland
    assert "Internal: budget tight." in poland


def test_unknown_client_is_a_404(app):
    assert get(app, "/clients/999").status == 404


def test_single_client_upload_after_cross_keeps_overview_when_cross_has_none():
    """The demo environment's cross-client export has no overview: loading it
    after a single-client one must not blank the overview."""
    cid = _load(_book(), CLIENT)
    _load(_book(), CROSS, report_date="10 Nov 2026")          # no overview in this one
    s = cs.explorer(cid, bundle=cs.bundle_key("Poland", "2027-01-01"), today=TODAY)["selected"]
    assert any(r["overview"]["entries"] for r in s["renewals"])


def test_cards_put_the_name_on_top_and_the_policy_number_under_the_entity(app):
    """Martin, 04.11.2026: the policy name was cut off in its column. It now
    spans the card; the first field is the entity with the policy number,
    which BM+ only gives on the detail sheets."""
    book = _book()
    book[0] = R(**{**book[0].__dict__, "policy_number": "PL-4711"})
    cid = _load(book)
    page = get(app, f"/clients/{cid}?bundle=Poland%7C2027-01-01").body_bytes.decode()
    card = page.split('<article class="renewal-card')[1:]
    assert all(c.index('class="rc-name"') < c.index('class="renewal-row"') for c in card)
    assert page.count("Policy no. PL-4711") == 1 and page.count("Policy no.") == 1
    assert '<div class="rc-label">Entity</div>' in page


def test_renewal_panel_stacks_renewal_and_strategy(app):
    """Martin, 04.11.2026: the strategy holds much more than the renewal's
    facts, so the two sections are stacked; the short facts sit two per row."""
    cid = _load(_book())
    with connection() as conn:
        rid = conn.execute("SELECT id FROM renewals WHERE policy_name = 'Medical'").fetchone()["id"]
    page = get(app, f"/clients/{cid}/renewals/{rid}").body_bytes.decode()
    assert "rd-cols" not in page and '<dl class="facts facts-2col">' in page
    assert page.index('id="facts-h"') < page.index('id="strat-h"')
    assert "group=" not in page


def test_lines_of_coverage_are_a_list_in_the_panel(app):
    """Martin, 04.11.2026: BM+ joins the lines of coverage with commas; the
    panel shows one per bullet."""
    book = _book()
    book[0] = R(**{**book[0].__dict__,
                   "loc": "Healthcare - Inpatient (Hospital and Surgical), Healthcare - Maternity"})
    cid = _load(book)
    with connection() as conn:
        rid = conn.execute("SELECT id FROM renewals WHERE policy_name = 'Medical' AND country = 'Poland'"
                           ).fetchone()["id"]
    page = get(app, f"/clients/{cid}/renewals/{rid}").body_bytes.decode()
    assert ('<ul class="loc-list"><li>Healthcare - Inpatient (Hospital and Surgical)</li>'
            "<li>Healthcare - Maternity</li></ul>") in page


def test_everything_bm_exported_is_bundled_by_section(app):
    """Martin, 04.11.2026: the raw BM+ row is grouped under BM+'s own
    section headings, each one expandable, in the export's order."""
    from mart.services import renewal_service as rs
    secs = rs.bm_sections({"Policy Information (Expiring Policy Period) › Country": "Poland",
                           "Policy Information (Expiring Policy Period) › Start Date": "2026-01-01",
                           "Renewal Information › Renewal Unique ID*": "x", "Loose cell": 1})
    assert [(s["name"], len(s["items"])) for s in secs] == [
        ("Policy Information (Expiring Policy Period)", 2), ("Renewal Information", 1), ("Other", 1)]
    cid = _load(_book())
    with connection() as conn:
        rid = conn.execute("SELECT id FROM renewals WHERE policy_name = 'Medical' AND country = 'Poland'"
                           ).fetchone()["id"]
    page = get(app, f"/clients/{cid}/renewals/{rid}").body_bytes.decode()
    raw = page.split("Everything BM+ exported")[1]
    assert raw.count('<details class="bm-group">') >= 3
    assert "<summary>Policy Information (Expiring Policy Period) <span" in raw
    assert "›" not in raw.split("</details>\n</details>")[0]          # headers shown without the section
