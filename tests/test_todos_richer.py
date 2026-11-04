"""M2 day 2: richer to-dos (Martin, 04.11.2026; QUESTIONS M2a): subtasks, a
description, urgency, and "waiting on" someone since a date. To-dos stay on
a renewal, a bundle or the client (M2c); broker deadlines are separate."""

from datetime import date

import pytest

from mart.repository.db import connection
from mart.services import notes_service as ns
from mart.services import upload_service as us
from tests.conftest import get, post
from tests.fixtures import R, renewal_tracker


@pytest.fixture
def book(configured):
    uid = us.stage("rt.xlsx", renewal_tracker([R(n=1, policy="Medical")]))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]})
    with connection() as conn:
        med = dict(conn.execute("SELECT id, client_id FROM renewals").fetchone())
    return {"cid": med["client_id"], "med": med["id"],
            "bundle": ns.bundle_ref(med["client_id"], "Poland|2027-01-01")}


def _todo(t_id: int) -> dict:
    return next(t for t in ns.todo_list()["open"] + ns.todo_list()["done"] if t["id"] == t_id)


def test_extras_are_stored_and_cleared(book):
    tid = ns.add_todo("renewal", str(book["med"]), "Collect the claims data", None, "urgent")
    t = _todo(tid)
    assert (t["urgency"], t["status"], t["steps"], t["description"]) == ("urgent", "open", [], None)
    ns.edit_todo(tid, "Collect the claims data", "2026-11-20",
                 {"description": "  Ask HR for 2025.\r\nThen the census.\r\n", "urgency": "normal",
                  "status": "waiting", "waiting_kind": "broker", "waiting_on": " Broker   A ",
                  "waiting_since": ""})
    t = _todo(tid)
    assert t["description"] == "Ask HR for 2025.\nThen the census."         # CRLF -> LF, trimmed
    assert (t["status"], t["waiting_kind"], t["waiting_on"]) == ("waiting", "broker", "Broker A")
    assert t["waiting_since"] == date.today().isoformat()                 # defaults to today
    # leaving "waiting" forgets who it was waiting on
    ns.edit_todo(tid, "Collect the claims data", None, {"status": "in_progress", "urgency": "low"})
    t = _todo(tid)
    assert (t["status"], t["urgency"], t["waiting_on"], t["waiting_since"]) == \
        ("in_progress", "low", None, None)
    # the old two-field edit (title + due) leaves the extras alone
    ns.edit_todo(tid, "Collect claims", None)
    assert _todo(tid)["status"] == "in_progress"
    for bad in ({"status": "someday"}, {"urgency": "asap"}, {"status": "waiting", "waiting_since": "soon"},
                {"description": "x" * 5001}):
        with pytest.raises(ns.Invalid):
            ns.edit_todo(tid, "Collect claims", None, bad)


def test_subtasks(book):
    tid = ns.add_todo("bundle", book["bundle"], "Prepare the renewal", None)
    a = ns.add_step(tid, "claims data")
    b = ns.add_step(tid, "census")
    ns.add_step(tid, "broker brief")
    assert ns.set_step_done(a, True) == tid and ns.set_step_done(b, True) == tid
    ns.set_step_done(b, False)
    t = _todo(tid)
    assert [s["title"] for s in t["steps"]] == ["claims data", "census", "broker brief"]
    assert t["steps_done"] == 1
    assert ns.delete_step(a) == tid and len(_todo(tid)["steps"]) == 2
    with pytest.raises(ns.Invalid):
        ns.add_step(tid, "   ")
    with pytest.raises(ns.Invalid):
        ns.set_step_done(99999, True)
    ns.delete_todo(tid)                                                   # its subtasks go with it
    with connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM todo_steps").fetchone()[0] == 0


def test_urgent_first_then_by_due_date(book):
    ref = str(book["med"])
    ns.add_todo("renewal", ref, "Normal, soon", "2026-11-05")
    ns.add_todo("renewal", ref, "Low, sooner", "2026-11-04", "low")
    ns.add_todo("renewal", ref, "Urgent, undated", None, "urgent")
    assert [t["title"] for t in ns.todo_list()["open"]] == ["Urgent, undated", "Normal, soon", "Low, sooner"]


def test_through_the_pages(book, app):
    back = f"/clients/{book['cid']}/renewals/{book['med']}"
    r = post(app, "/todos/add", {"scope": "renewal", "ref": str(book["med"]), "title": "Chase broker",
                                 "urgency": "urgent", "back": back})
    assert r.status == 303
    tid = ns.todo_list()["open"][0]["id"]
    assert post(app, f"/todos/{tid}/steps/add", {"title": "Mail", "back": back}).status == 303
    r = post(app, f"/todos/{tid}/save", {
        "title": "Chase broker", "due": "", "urgency": "urgent", "status": "waiting",
        "waiting_kind": "broker", "waiting_on": "Broker A", "waiting_since": "2026-11-03",
        "description": "Terms promised.", "back": back})
    assert r.status == 303 and dict(r.headers)["Location"].endswith(f"#todo-{tid}")
    page = get(app, back).body_bytes.decode()
    assert '<span class="pill pill-urgent">urgent</span>' in page
    assert "waiting on broker Broker A since 03.11.2026" in page and "Terms promised." in page
    assert "☑ 0/1" in page and 'action="/todos/steps/' in page
    assert ">urgent</span>" in get(app, "/todos").body_bytes.decode()
    assert post(app, f"/todos/{tid}/save", {"title": "x", "status": "nope", "back": back}).status == 400
