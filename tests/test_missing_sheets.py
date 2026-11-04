"""A Renewal Tracker can be created without some of its sheets (Martin,
04.11.2026: the columns are fixed, the sheets are optional). A sheet the
export doesn't have is not news: MART keeps what it had and compares only
the sheets that are there."""

import io

import openpyxl

from mart.repository import renewals_repo
from mart.repository.db import connection
from mart.services import renewal_service as rs
from mart.services import upload_service as us
from tests.conftest import get
from tests.fixtures import R, renewal_tracker

ALL = ("Renewal Strategy", "Proposals", "Savings")


def _book(report_date: str, final: float = 90.0) -> bytes:
    return renewal_tracker([R(n=1, policy="Medical", proposals=[("Allianz", 100.0, final)]),
                            R(n=2, policy="Life")], report_date=report_date)


def _without(data: bytes, *sheets: str) -> bytes:
    wb = openpyxl.load_workbook(io.BytesIO(data))
    for s in sheets:
        del wb[s]
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def _load(data: bytes) -> dict:
    uid = us.stage("rt.xlsx", data)
    view = us.preview(uid)
    us.commit(uid, {c["key"] for c in view["clients"]})
    return view


def _renewals() -> dict[str, dict]:
    with connection() as conn:
        ids = [r["id"] for r in conn.execute("SELECT id FROM renewals ORDER BY id")]
        return {r["policy_name"]: r for r in (renewals_repo.get(conn, i) for i in ids)}


def test_an_export_without_sheets_keeps_them_and_shows_no_changes(configured):
    _load(_book("03 Nov 2026"))
    before = {k: {s: v for s, v in r["details"].items() if s != "_from"} for k, r in _renewals().items()}
    assert before["Medical"].keys() == {"strategy", "proposals", "savings"}
    view = _load(_without(_book("04 Nov 2026"), *ALL))
    c = view["clients"][0]
    assert (c["changed"], c["unchanged"]) == (0, 2)
    after = _renewals()
    for name, r in after.items():
        assert {s: v for s, v in r["details"].items() if s != "_from"} == before[name]
    # and the next full export is still "unchanged": the stored hash stayed right
    c = _load(_book("05 Nov 2026"))["clients"][0]
    assert (c["changed"], c["unchanged"]) == (0, 2)


def test_a_sheet_that_is_there_is_the_truth(configured):
    _load(_book("03 Nov 2026"))
    c = _load(_without(_book("04 Nov 2026", final=80.0), "Savings"))["clients"][0]
    assert c["changed"] == 1                           # Medical's final quote moved
    med = _renewals()["Medical"]
    assert "savings" in med["details"]                 # kept from the first export
    rows = med["details"]["proposals"]
    assert any(80.0 in row.values() or 80 in row.values() for row in rows)


def test_the_panel_says_which_export_a_kept_section_is_from(configured, app):
    _load(_book("03 Nov 2026"))
    _load(_without(_book("04 Nov 2026"), "Proposals"))
    med = _renewals()["Medical"]
    d = rs.detail(med["client_id"], med["id"])
    assert d["older"] == {"proposals": "2026-11-03"}
    page = get(app, f"/clients/{med['client_id']}/renewals/{med['id']}").body_bytes.decode()
    assert "from the export of 03.11.2026" in page and page.count("sec-old") == 1


def test_the_preview_explains_missing_sheets(configured, app):
    _load(_book("03 Nov 2026"))
    uid = us.stage("rt.xlsx", _without(_book("04 Nov 2026"), "Savings"))
    page = get(app, f"/uploads/{uid}").body_bytes.decode()
    assert "Not in this export: Savings. MART keeps what it already has" in page
