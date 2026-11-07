"""QA 07.11.2026: a default bundle's key holds its renewal date, so when BM+
moves the date, what Martin put on the bundle has to follow it."""

from datetime import datetime

import pytest

from mart.repository.db import connection
from mart.services import board_service, bundle_service, deadlines
from mart.services import client_service as cs
from mart.services import notes_service as ns
from mart.services import upload_service as us
from tests.fixtures import R, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")
JAN, FEB, MAR = (datetime(2027, m, 1, 1, 0) for m in (1, 2, 3))
OLD, NEW = "Poland|2027-01-01", "Poland|2027-02-01"


def _load(dates, report) -> int:
    rows = [R(n=n, policy=p, renewal_date=d)
            for n, p, d in zip((1, 2), ("Medical", "Life"), dates, strict=True)]
    uid = us.stage(f"rt-{report}.xlsx", renewal_tracker(rows, cross_overview=True, report_date=report))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)
    with connection() as conn:
        return conn.execute("SELECT id FROM clients").fetchone()["id"]


def _mark(cid: int, key: str) -> None:
    deadlines.set_deadline(cid, key, "2026-12-01", "Broker A")
    board_service.set_stage(cid, key, "proposals", "tender out")
    bundle_service.rename(cid, key, "Poland main")
    ns.add_note("bundle", ns.bundle_ref(cid, key), "Broker promised the terms")
    ns.add_todo("bundle", ns.bundle_ref(cid, key), "Chase the broker", None)


def test_everything_follows_when_the_whole_bundle_moves():
    cid = _load((JAN, JAN), "03 Nov 2026")
    _mark(cid, OLD)
    _load((FEB, FEB), "10 Nov 2026")
    b = cs.explorer(cid, bundle=NEW)["selected"]
    assert b["key"] == NEW and b["extra"] == "Poland main"
    assert b["deadline"]["promised_by"] == "Broker A"
    assert (b["stage"]["mine"], b["stage"]["row"]["reason"]) == ("proposals", "tender out")
    mine = ns.for_bundle(cid, b)
    assert [n["body"] for n in mine["notes"]] == ["Broker promised the terms"]
    assert [t["title"] for t in mine["todos"]] == ["Chase the broker"]
    assert OLD not in {x["key"] for items in cs.explorer(cid)["groups"].values() for x in items}


def test_nothing_moves_when_the_bundle_splits():
    cid = _load((JAN, JAN), "03 Nov 2026")
    _mark(cid, OLD)
    _load((FEB, MAR), "10 Nov 2026")                      # one to February, one to March
    old = cs.explorer(cid, bundle=OLD)["selected"]
    assert old["key"] == OLD and old["extra"] == "Poland main" and not old["renewals"]   # kept, visible
    assert cs.explorer(cid, bundle=NEW)["selected"]["extra"] == ""


def test_nothing_moves_when_part_of_the_bundle_stays():
    cid = _load((JAN, JAN), "03 Nov 2026")
    _mark(cid, OLD)
    _load((FEB, JAN), "10 Nov 2026")                      # Life stays in January
    assert cs.explorer(cid, bundle=OLD)["selected"]["extra"] == "Poland main"


def test_the_new_bundles_own_data_is_never_overwritten():
    cid = _load((JAN, FEB), "03 Nov 2026")
    _mark(cid, OLD)
    bundle_service.rename(cid, NEW, "Poland February")
    _load((FEB, FEB), "10 Nov 2026")                      # Medical joins February
    assert cs.explorer(cid, bundle=NEW)["selected"]["extra"] == "Poland February"
    assert cs.explorer(cid, bundle=OLD)["selected"]["extra"] == "Poland main"      # both stay


def test_a_client_spelled_differently_keeps_its_renewals(app):
    """QA 07.11.2026: an export naming the client "Acme Group AG" instead of
    "Acme Group" moved its renewals (same BM+ ids) to a new client, leaving
    their custom bundle, to-dos and links behind."""
    from tests.conftest import post
    cid = _load((JAN, JAN), "03 Nov 2026")
    with connection() as conn:
        medical = conn.execute("SELECT id FROM renewals WHERE policy_name = 'Medical'").fetchone()["id"]
    bundle_service.move(cid, [medical], "new", "Poland – Broker B")
    ns.add_todo("renewal", str(medical), "Ask for the claims data", None)
    rows = [R(n=n, policy=p, renewal_date=JAN, client="Acme Group AG")
            for n, p in ((1, "Medical"), (2, "Life"))]
    uid = us.stage("rt-renamed.xlsx", renewal_tracker(rows, cross_overview=True, report_date="10 Nov 2026"))
    key = us.preview(uid)["clients"][0]["key"]
    r = post(app, f"/uploads/{uid}/commit", {"mine": key, "allow_older": "1"})
    assert "2 stayed with the client" in dict(r.headers)["Location"].replace("%20", " ")
    with connection() as conn:
        owners = {r["client_id"] for r in conn.execute("SELECT client_id FROM renewals")}
    assert owners == {cid}
    b = cs.explorer(cid, renewal_id=medical)["selected"]
    assert b["extra"] == "Poland – Broker B" and [r["id"] for r in b["renewals"]] == [medical]
    assert [t["title"] for t in ns.todo_list()["open"]] == ["Ask for the claims data"]
