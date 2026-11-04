"""Day 6: split and join bundles (user data, per client), and history: what
each upload changed on a renewal and its tasks."""

from datetime import datetime

import pytest

from mart.repository.db import connection
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
            R(n=3, policy="Dental", entity="Acme Services", insurer="PZU"),
            R(n=4, policy="Medical", country="Spain", entity="Acme Iberia",
              renewal_date=datetime(2027, 2, 1, 1, 0))]
    rows = [R(**{**r.__dict__, **changes.get(r.n, {})}) for r in rows]
    return renewal_tracker(rows, report_date=report_date, cross_overview=overview)


@pytest.fixture
def cid(configured):
    _load(_book())
    with connection() as conn:
        return conn.execute("SELECT id FROM clients").fetchone()["id"]


def _bundles(cid: int) -> dict[str, list[str]]:
    v = cs.explorer(cid)
    return {b["key"]: sorted(r["policy_name"] for r in b["renewals"])
            for g in v["groups"].values() for b in g}


def test_split_by_entity_and_insurer_and_undo(cid, app):
    assert _bundles(cid)[POLAND] == ["Dental", "Life", "Medical"]
    r = post(app, f"/clients/{cid}/bundles/split", {"key": POLAND, "by": "entity"})
    assert r.status == 303
    keys = _bundles(cid)
    assert keys[bx.split_key(POLAND, [("entity", "Acme Polska")])] == ["Life", "Medical"]
    assert keys[bx.split_key(POLAND, [("entity", "Acme Services")])] == ["Dental"]
    assert "Spain|2027-02-01" in keys                       # other bundles untouched
    cs.set_split(cid, POLAND, ["entity", "insurer"])
    assert len([k for k in _bundles(cid) if k.startswith("Poland")]) == 3
    page = get(app, f"/clients/{cid}").body_bytes.decode()
    assert "Acme Polska · PZU" in page and "Arrange" in page
    cs.set_split(cid, POLAND, [])                           # undo
    assert _bundles(cid)[POLAND] == ["Dental", "Life", "Medical"]
    with pytest.raises(ValueError):
        cs.set_split(cid, POLAND, ["premium"])


def test_split_by_policy_number_from_the_tasks(cid):
    _load(task_tracker([T(n=1, task_name="Renewal Strategy"), T(n=2, task_name="Renewal Strategy")]))
    cs.set_split(cid, POLAND, ["policy_number"])
    keys = _bundles(cid)
    # the fixture's tasks all carry policy number "PL-001"; Dental has no task
    assert keys[bx.split_key(POLAND, [("policy_number", "PL-001")])] == ["Life", "Medical"]
    assert keys[bx.split_key(POLAND, [("policy_number", None)])] == ["Dental"]


def test_join_and_unjoin(cid, app):
    spain = "Spain|2027-02-01"
    post(app, f"/clients/{cid}/bundles/join", {"key": spain, "into": POLAND})
    keys = _bundles(cid)
    assert spain not in keys and keys[POLAND] == ["Dental", "Life", "Medical", "Medical"]
    page = get(app, f"/clients/{cid}?bundle={POLAND}").body_bytes.decode()
    assert "Joined into this bundle" in page and "+ 1 joined" in page
    # an old link to the joined bundle leads to the bundle that holds it now
    assert cs.explorer(cid, bundle=spain)["selected"]["key"] == POLAND
    with pytest.raises(ValueError):
        cs.join(cid, POLAND, spain)                         # would go round in a circle
    post(app, f"/clients/{cid}/bundles/unjoin", {"member": spain})
    assert spain in _bundles(cid)


def test_bundle_notes_survive_a_split(cid, app):
    ns.add_note("bundle", ns.bundle_ref(cid, POLAND), "One mail for all of Poland")
    cs.set_split(cid, POLAND, ["entity"])
    v = cs.explorer(cid, bundle=POLAND)                     # the old key still leads somewhere
    assert v["selected"]["key"].startswith(POLAND + "|")
    for key in [k for k in v["live_keys"] if k.startswith("Poland")]:
        b = next(b for g in v["groups"].values() for b in g if b["key"] == key)
        notes = ns.for_bundle(cid, b, v["live_keys"])["notes"]
        assert [n["body"] for n in notes] == ["One mail for all of Poland"]
        assert notes[0]["from_bundle"] == "Poland · 2027-01-01"
    # the renewal panel finds its (split) bundle
    with connection() as conn:
        med = conn.execute("SELECT id FROM renewals WHERE policy_name = 'Medical' AND country = 'Poland'"
                           ).fetchone()["id"]
    page = get(app, f"/clients/{cid}/renewals/{med}").body_bytes.decode()
    assert "One mail for all of Poland" in page and "Acme Polska" in page


def test_history_records_what_an_upload_changed(cid, app):
    _load(task_tracker([T(n=1, task_name="Renewal Strategy", status="In Progress")]))
    _load(_book(report_date="10 Nov 2026",
                changes={1: {"status": "Completed", "strategy": "Remarketing",
                             "overview": "08 Nov 2026: Terms received from PZU.\n"},
                         2: {"insurer_upcoming": "Generali"}}, overview=True))
    _load(task_tracker([T(n=1, task_name="Renewal Strategy", status="Completed")], report_date="11 Nov 2026"))
    with connection() as conn:
        rid = {r["policy_name"] + r["country"]: r["id"] for r in conn.execute("SELECT * FROM renewals")}
    d = rs.detail(cid, rid["MedicalPoland"])
    lines = [(g["report_date"], x["task"], x["label"], x["old"], x["new"])
             for g in d["history"] for x in g["lines"]]
    assert ("2026-11-11", "Renewal Strategy", "status", "In Progress", "Completed") in lines
    assert ("2026-11-10", None, "Workflow status", "In Progress", "Completed") in lines
    assert ("2026-11-10", None, "Strategy", "TBC", "Remarketing") in lines
    assert ("2026-11-10", None, "new overview entry", None, "2026-11-08") in lines
    assert ("2026-11-03", None, "first seen in the export", None, None) in lines
    # the stage task was there from the first task upload: no separate "first seen" for it
    assert not [x for x in lines if x[1] and x[2] == "first seen in the export"]
    page = get(app, f"/clients/{cid}/renewals/{rid['MedicalPoland']}").body_bytes.decode()
    assert "History (" in page and "Export of 10.11.2026" in page and "Remarketing" in page
    # an export without Dental: it is kept, and its history says so
    _load(renewal_tracker([R(n=1, policy="Medical", entity="Acme Polska", insurer="PZU")],
                          report_date="12 Nov 2026"))
    labels = [x["label"] for g in rs.detail(cid, rid["DentalPoland"])["history"] for x in g["lines"]]
    assert "no longer in the export" in labels


def test_unchanged_upload_records_nothing(cid):
    _load(_book(report_date="05 Nov 2026"))
    with connection() as conn:
        assert {r["field"] for r in conn.execute("SELECT field FROM changes")} == {"_seen"}
