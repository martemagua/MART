"""M3 day 8: repeating to-dos (Martin 05.11.2026, QUESTIONS M3b): every N
days / N weeks (on chosen weekdays) / N months; ticking one creates the next."""

from datetime import date, datetime
from urllib.parse import urlencode

import pytest

from mart.repository.db import connection
from mart.services import notes_service as ns
from mart.services import repeats, topics
from mart.services import upload_service as us
from mart.web.framework import Request
from tests.conftest import get, post
from tests.fixtures import R, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")
TODAY = date(2026, 11, 7)                      # a Saturday


def _spec(unit, every=1, weekdays=None, due=None):
    return repeats.clean(unit, every, weekdays, due, TODAY)


def test_the_next_date():
    nxt = repeats.next_due
    assert nxt(_spec("day", 3), "2026-11-10", TODAY) == date(2026, 11, 13)
    assert nxt(_spec("week", 2), "2026-11-10", TODAY) == date(2026, 11, 24)
    # every week on Mon + Thu: from a Monday the Thursday, from the Thursday next Monday
    mon_thu = _spec("week", 1, ["0", "3"])
    assert nxt(mon_thu, "2026-11-09", TODAY) == date(2026, 11, 12)
    assert nxt(mon_thu, "2026-11-12", TODAY) == date(2026, 11, 16)
    assert nxt(_spec("week", 2, ["0"]), "2026-11-09", TODAY) == date(2026, 11, 23)
    # months keep their day; the 31st becomes the month's last day, and comes back
    eom = _spec("month", 1, due="2027-01-31")
    assert nxt(eom, "2027-01-31", TODAY) == date(2027, 2, 28)
    assert nxt(eom, "2027-02-28", TODAY) == date(2027, 3, 31)
    assert nxt(_spec("month", 3, due="2026-11-15"), "2026-11-15", TODAY) == date(2027, 2, 15)
    # no due date: from today; ticked very late: never born overdue
    assert nxt(_spec("day", 7), None, TODAY) == date(2026, 11, 14)
    assert nxt(_spec("month", 1, due="2026-08-05"), "2026-08-05", TODAY) == date(2026, 12, 5)
    assert nxt(_spec("week", 1, ["2"]), "2026-01-07", TODAY) == date(2026, 11, 11)


def test_the_rules_and_the_words():
    assert _spec("") is None and _spec(None) is None
    assert repeats.describe(_spec("month")) == "every month"
    assert repeats.describe(_spec("week", 2, ["3", "0"])) == "every 2 weeks on Mon, Thu"
    assert repeats.describe(_spec("day", 3)) == "every 3 days"
    assert _spec("day", 1, ["0"])["repeat_weekdays"] is None          # weekdays only for weeks
    for bad in (lambda: _spec("year"), lambda: _spec("day", 0), lambda: _spec("day", "x"),
                lambda: _spec("week", 53), lambda: _spec("month", 25), lambda: _spec("week", 1, ["8"])):
        with pytest.raises(ns.Invalid):
            bad()


def _client() -> int:
    rows = [R(n=1, policy="Medical", renewal_date=datetime(2027, 1, 1, 1))]
    uid = us.stage("rt.xlsx", renewal_tracker(rows, cross_overview=True))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)
    with connection() as conn:
        return conn.execute("SELECT id FROM clients").fetchone()["id"]


def test_ticking_creates_the_next_once():
    cid = _client()
    tid = topics.create(cid, "Partner tracker", "teal")
    todo = ns.add_todo("client", str(cid), "Release the partner tracker", "2026-11-30", "urgent", tid,
                       {"unit": "month", "every": "1"})
    ns.edit_todo(todo, "Release the partner tracker", "2026-11-30",
                 {"description": "to all partners", "urgency": "urgent", "status": "open"},
                 {"unit": "month", "every": "1"})
    ns.add_step(todo, "Update the list")
    nxt = ns.set_done(todo, True, TODAY)
    assert nxt is not None
    open_ = {t["id"]: t for t in ns.todo_list(today=TODAY)["open"]}
    n = open_[nxt]
    assert (n["title"], n["due_date"], n["urgency"], n["description"], n["topic_id"]) == (
        "Release the partner tracker", "2026-12-30", "urgent", "to all partners", tid)
    assert [s["title"] for s in n["steps"]] == ["Update the list"] and not n["steps"][0]["done_at"]
    assert repeats.describe(n) == "every month"
    # untick and tick again: no second one; the next one repeats in its turn
    ns.set_done(todo, False)
    assert ns.set_done(todo, True, TODAY) is None
    same = [t for t in ns.todo_list(today=TODAY)["open"] if t["title"] == "Release the partner tracker"]
    assert len(same) == 1
    assert ns.set_done(nxt, True, TODAY) is not None
    # stop repeating: an empty unit
    last = next(t for t in ns.todo_list(today=TODAY)["open"] if t["title"] == "Release the partner tracker")
    ns.edit_todo(last["id"], last["title"], last["due_date"], None, {"unit": ""})
    assert ns.set_done(last["id"], True, TODAY) is None


def test_the_forms(app):
    cid = _client()
    url = f"/clients/{cid}/notes"
    body = [("scope", "client"), ("ref", str(cid)), ("title", "Team call"), ("due", "2026-11-09"),
            ("urgency", "normal"), ("repeat_every", "1"), ("repeat_unit", "week"),
            ("repeat_weekdays", "0"), ("repeat_weekdays", "3"), ("back", url)]
    res = app.handle(Request("POST", "/todos/add", "", {"content-type": "application/x-www-form-urlencoded"},
                             urlencode(body).encode()))
    assert res.status == 303
    page = get(app, url).body_bytes.decode()
    assert "↻ every week on Mon, Thu" in page and 'name="repeat_unit"' in page and "rep-wd-" in page
    t = next(t for t in ns.todo_list()["open"] if t["title"] == "Team call")
    assert post(app, f"/todos/{t['id']}/done", {"done": "1", "back": url}).status == 303
    expected = repeats.next_due(repeats.clean("week", 1, ["0", "3"], "2026-11-09"), "2026-11-09").isoformat()
    assert [x["due_date"] for x in ns.todo_list()["open"] if x["title"] == "Team call"] == [expected]
    bad = post(app, "/todos/add", {"scope": "client", "ref": str(cid), "title": "x", "repeat_unit": "year"})
    assert bad.status == 400
