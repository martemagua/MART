"""Day 6: moving renewals between bundles (Martin, 04.11.2026), and history:
what each upload changed on a renewal and its tasks.

Bundles: by default country + renewal date. Renewals move, one or several at
once, into a custom bundle of the same country (existing, or new with a
name), and back. A bundle never mixes countries.
"""

from datetime import datetime

import pytest

from mart.repository.db import connection
from mart.services import bundle_service as bs
from mart.services import bundles as bx
from mart.services import client_service as cs
from mart.services import notes_service as ns
from mart.services import renewal_service as rs
from mart.services import upload_service as us
from tests.conftest import get, post
from tests.fixtures import R, T, renewal_tracker, task_tracker

POLAND = "Poland|2027-01-01"


def _load(data: bytes) -> dict:
    uid = us.stage("x.xlsx", data)
    return us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)


def _book(report_date="03 Nov 2026", changes: dict | None = None, overview: bool = False) -> bytes:
    changes = changes or {}
    rows = [R(n=1, policy="Medical", entity="Acme Polska", insurer="PZU"),
            R(n=2, policy="Life", entity="Acme Polska", insurer="Allianz"),
            R(n=3, policy="Dental", entity="Acme Services", insurer="PZU",
              renewal_date=datetime(2027, 3, 1, 1, 0)),
            R(n=4, policy="Medical", country="Spain", entity="Acme Iberia",
              renewal_date=datetime(2027, 2, 1, 1, 0))]
    rows = [R(**{**r.__dict__, **changes.get(r.n, {})}) for r in rows]
    return renewal_tracker(rows, report_date=report_date, cross_overview=overview)


@pytest.fixture
def book(configured):
    _load(_book())
    with connection() as conn:
        cid = conn.execute("SELECT id FROM clients").fetchone()["id"]
        ids = {(r["policy_name"], r["country"]): r["id"] for r in conn.execute("SELECT * FROM renewals")}
    return cid, ids


def _bundles(cid: int) -> dict[str, list[str]]:
    v = cs.explorer(cid)
    return {b["key"]: sorted(r["policy_name"] for r in b["renewals"])
            for g in v["groups"].values() for b in g}


def test_move_into_a_new_bundle_then_more_then_back(book, app):
    cid, ids = book
    med, life, dental = ids[("Medical", "Poland")], ids[("Life", "Poland")], ids[("Dental", "Poland")]
    # one renewal into a new, named bundle (through the page)
    r = post(app, f"/clients/{cid}/bundles/move", {"renewal": str(med), "target": "new",
                                                    "name": "PZU programme"})
    key = dict(r.headers)["Location"].split("bundle=")[1].split("&")[0].replace("%7C", "|")
    custom = bx.custom_id(key)
    assert custom and _bundles(cid)[key] == ["Medical"] and _bundles(cid)[POLAND] == ["Life"]
    # several at once into the existing bundle: different dates are fine, same country
    bs.move(cid, [dental], str(custom))
    assert _bundles(cid)[key] == ["Dental", "Medical"] and "Poland|2027-03-01" not in _bundles(cid)
    page = get(app, f"/clients/{cid}?bundle=custom%7C{custom}").body_bytes.decode()
    assert "PZU programme" in page and "renewals 01.01.2027 – 01.03.2027" in page
    # tick boxes and the move bar only in edit mode (Martin, 04.11.2026)
    assert 'name="renewal"' not in page and "data-move-form" not in page and "Edit renewals…" in page
    page = get(app, f"/clients/{cid}?bundle=custom%7C{custom}&edit=1").body_bytes.decode()
    assert "their own bundle" in page and page.count('name="renewal"') == 2 and "Edit renewals…" not in page
    assert f'class="btn btn-small move-done" href="/clients/{cid}?bundle=custom%7C{custom}"' in page
    # the renewal panel shows its bundle and where it can move
    panel = get(app, f"/clients/{cid}/renewals/{med}").body_bytes.decode()
    assert "Bundle:" in panel and "PZU programme" in panel and "Move to another bundle" in panel
    # back to their own bundles
    bs.move(cid, [med, dental], bs.DEFAULT)
    assert _bundles(cid)[POLAND] == ["Life", "Medical"] and "Poland|2027-03-01" in _bundles(cid)
    # the empty bundle is kept for reuse
    v = cs.explorer(cid, bundle=POLAND)
    assert [(t["name"], t["count"]) for t in v["selected"]["move_targets"]] == [("PZU programme", 0)]
    bs.move(cid, [life], str(custom))
    assert _bundles(cid)[key] == ["Life"]


def test_a_bundle_keeps_to_one_country(book, app):
    cid, ids = book
    med, spain = ids[("Medical", "Poland")], ids[("Medical", "Spain")]
    with pytest.raises(bs.Invalid, match="one country"):
        bs.move(cid, [med, spain], bs.NEW, "Mixed")
    key = bs.move(cid, [med], bs.NEW, "Poland pack")
    with pytest.raises(bs.Invalid, match="Poland bundle"):
        bs.move(cid, [spain], str(bx.custom_id(key)))
    assert "Poland pack" not in [t["name"] for t in cs.explorer(cid, bundle="Spain|2027-02-01")
                                 ["selected"]["move_targets"]]
    for data in ({"renewal": str(med), "target": "new", "name": "  "},       # a new bundle needs a name
                 {"target": "new", "name": "x"},                            # nothing selected
                 {"renewal": "99999", "target": "new", "name": "x"}):       # not this client's
        assert post(app, f"/clients/{cid}/bundles/move", data).status == 400, data


def test_rename_and_survive_uploads(book):
    cid, ids = book
    key = bs.move(cid, [ids[("Medical", "Poland")], ids[("Life", "Poland")]], bs.NEW, "Acme Polska")
    bs.rename(cid, key, "Acme Polska (one BM+ policy)")
    _load(_book(report_date="10 Nov 2026", changes={1: {"status": "Completed"}}))
    b = next(b for g in cs.explorer(cid)["groups"].values() for b in g if b["key"] == key)
    assert b["extra"] == "Acme Polska (one BM+ policy)" and len(b["renewals"]) == 2
    with pytest.raises(bs.Invalid):
        bs.rename(cid, "custom|999", "x")
    with pytest.raises(bs.Invalid):
        bs.rename(cid, key, "  ")                  # a custom bundle keeps a name


def test_bundle_notes_on_a_custom_bundle(book, app):
    cid, ids = book
    med = ids[("Medical", "Poland")]
    key = bs.move(cid, [med], bs.NEW, "Broker A")
    ns.add_note("bundle", ns.bundle_ref(cid, key), "Broker A handles medical only")
    ns.add_todo("bundle", ns.bundle_ref(cid, key), "Brief broker A", None)
    assert "Broker A handles medical only" in get(app, f"/clients/{cid}?bundle={key}").body_bytes.decode()
    assert "Broker A handles medical only" in get(app, f"/clients/{cid}/renewals/{med}").body_bytes.decode()
    todo = next(t for t in ns.todo_list()["open"] if t["title"] == "Brief broker A")
    assert todo["target"]["name"] == "bundle “Broker A”" and todo["target"]["country"] == "Poland"
    assert cs.clients_overview()[0]["bundles"] == 4      # Poland 01.01, Broker A, Poland 01.03, Spain


def test_history_records_what_an_upload_changed(book, app):
    cid, ids = book
    _load(task_tracker([T(n=1, task_name="Renewal Strategy", status="In Progress")]))
    _load(_book(report_date="10 Nov 2026",
                changes={1: {"status": "Completed", "strategy": "Remarketing",
                             "overview": "08 Nov 2026: Terms received from PZU.\n"},
                         2: {"insurer_upcoming": "Generali"}}, overview=True))
    _load(task_tracker([T(n=1, task_name="Renewal Strategy", status="Completed")], report_date="11 Nov 2026"))
    d = rs.detail(cid, ids[("Medical", "Poland")])
    lines = [(g["report_date"], x["task"], x["label"], x["old"], x["new"])
             for g in d["history"] for x in g["lines"]]
    assert ("2026-11-11", "Renewal Strategy", "status", "In Progress", "Completed") in lines
    assert ("2026-11-10", None, "Workflow status", "In Progress", "Completed") in lines
    assert ("2026-11-10", None, "Strategy", "TBC", "Remarketing") in lines
    assert ("2026-11-10", None, "new overview entry", None, "2026-11-08") in lines
    assert ("2026-11-03", None, "first seen in the export", None, None) in lines
    assert not [x for x in lines if x[1] and x[2] == "first seen in the export"]
    page = get(app, f"/clients/{cid}/renewals/{ids[('Medical', 'Poland')]}").body_bytes.decode()
    assert "History (" in page and "Export of 10.11.2026" in page and "Remarketing" in page
    # an export without Dental: it is kept, and its history says so
    _load(renewal_tracker([R(n=1, policy="Medical", entity="Acme Polska", insurer="PZU")],
                          report_date="12 Nov 2026"))
    labels = [x["label"] for g in rs.detail(cid, ids[("Dental", "Poland")])["history"] for x in g["lines"]]
    assert "no longer in the export" in labels


def test_unchanged_upload_records_nothing(book):
    _load(_book(report_date="05 Nov 2026"))
    with connection() as conn:
        assert {r["field"] for r in conn.execute("SELECT field FROM changes")} == {"_seen"}


def test_name_a_default_bundle(book, app):
    cid, _ = book
    r = post(app, f"/clients/{cid}/bundles/rename", {"key": POLAND, "name": "Acme Polska programme"})
    assert r.status == 303
    page = get(app, f"/clients/{cid}?bundle={POLAND}").body_bytes.decode()
    assert "Poland · 01.01.2027 · <span class=\"title-extra\">Acme Polska programme</span>" in page
    b = next(b for g in cs.explorer(cid)["groups"].values() for b in g if b["key"] == POLAND)
    assert b["extra"] == "Acme Polska programme" and b["custom_id"] is None
    bs.rename(cid, POLAND, "")                      # cleared: country + date again
    b = next(b for g in cs.explorer(cid)["groups"].values() for b in g if b["key"] == POLAND)
    assert b["extra"] == ""
    assert post(app, f"/clients/{cid}/bundles/rename", {"key": "nonsense", "name": "x"}).status == 400


def test_an_emptied_bundle_with_notes_stays(book, app):
    cid, ids = book
    ns.add_todo("bundle", ns.bundle_ref(cid, POLAND), "Chase the Poland broker", None)
    bs.move(cid, [ids[("Medical", "Poland")], ids[("Life", "Poland")]], bs.NEW, "Everything Poland")
    b = next(b for g in cs.explorer(cid)["groups"].values() for b in g if b["key"] == POLAND)
    assert b["renewals"] == []                      # still listed, with its to-do
    page = get(app, f"/clients/{cid}?bundle={POLAND}").body_bytes.decode()
    assert "No renewals left in this bundle" in page and "Chase the Poland broker" in page
    # without notes or to-dos, an emptied default bundle simply goes
    bs.move(cid, [ids[("Dental", "Poland")]], bs.NEW, "Dental")
    assert "Poland|2027-03-01" not in _bundles(cid)
