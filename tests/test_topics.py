"""M3 day 7: client topics (Martin 05.11.2026, PLANNING §5b, QUESTIONS
M3a/M3c): the client's own notes and to-dos in named, coloured topics, a
board on the client notes page, pinned notes."""

from datetime import date, datetime, timedelta

import pytest

from mart.repository.db import connection
from mart.services import notes_service as ns
from mart.services import topics
from mart.services import upload_service as us
from tests.conftest import get, post
from tests.fixtures import R, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")
JAN = datetime(2027, 1, 1, 1, 0)


def _client() -> int:
    rows = [R(n=1, policy="Medical", renewal_date=JAN),
            R(n=2, policy="Life", country="Brazil", renewal_date=JAN)]
    uid = us.stage("rt.xlsx", renewal_tracker(rows, cross_overview=True))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)
    with connection() as conn:
        return conn.execute("SELECT id FROM clients").fetchone()["id"]


def _col(board, name):
    return next(c for c in board["columns"] + board["done"] if c["name"] == name)


def test_general_holds_everything_until_topics_are_made():
    cid = _client()
    ns.add_note("client", str(cid), "HR contact changes in January")
    ns.add_todo("client", str(cid), "Plan the annual review", None)
    b = topics.board(cid)
    assert [c["name"] for c in b["columns"]] == ["General"] and b["done"] == []
    g = _col(b, "General")
    assert [n["body"] for n in g["notes"]] == ["HR contact changes in January"]
    assert [t["title"] for t in g["open"]] == ["Plan the annual review"]
    assert b["countries"] == ["Brazil", "Poland"]


def test_topics_hold_their_notes_and_todos_pinned_first():
    cid = _client()
    soon = (date.today() + timedelta(days=3)).isoformat()
    tracker = topics.create(cid, "Partner tracker", "teal")
    brazil = topics.create(cid, "Implementation – Brazil", "amber", "Brazil")
    ns.add_todo("client", str(cid), "Release the partner tracker", soon, topic_id=tracker)
    recipients = ns.add_note("client", str(cid), "Send it to A, B and C", topic_id=tracker)
    ns.add_note("client", str(cid), "Sent the October file", topic_id=tracker)
    topics.pin(recipients, True)
    ns.add_note("client", str(cid), "Go-live 01.03.2027", topic_id=brazil)
    b = topics.board(cid)
    assert [c["name"] for c in b["columns"]] == ["General", "Partner tracker", "Implementation – Brazil"]
    col = _col(b, "Partner tracker")
    assert [n["body"] for n in col["pinned"]] == ["Send it to A, B and C"]
    assert [n["body"] for n in col["notes"]] == ["Sent the October file"]
    assert (len(col["open"]), col["next_due"]) == (1, soon)
    assert _col(b, "Implementation – Brazil")["country"] == "Brazil"
    # on hold goes last, done is archived; deleting a topic keeps its items (in General)
    topics.edit(cid, tracker, "Partner tracker", "teal", None, "on_hold")
    topics.edit(cid, brazil, "Implementation – Brazil", "amber", "Brazil", "done")
    b = topics.board(cid)
    assert [c["name"] for c in b["columns"]] == ["General", "Partner tracker"]
    assert [c["name"] for c in b["done"]] == ["Implementation – Brazil"]
    topics.delete(cid, tracker)
    g = _col(topics.board(cid), "General")
    assert {n["body"] for n in g["pinned"] + g["notes"]} == {"Send it to A, B and C", "Sent the October file"}
    assert [t["title"] for t in g["open"]] == ["Release the partner tracker"]


def test_moving_items_and_the_rules():
    cid = _client()
    tid = topics.create(cid, "Client requests", "purple")
    note = ns.add_note("client", str(cid), "Asked for a dental quote")
    todo = ns.add_todo("client", str(cid), "Answer the dental question", None)
    topics.move("note", note, str(tid))
    topics.move("todo", todo, str(tid))
    col = _col(topics.board(cid), "Client requests")
    assert len(col["notes"]) == 1 and len(col["open"]) == 1
    topics.move("todo", todo, "")                                     # back to General
    assert len(_col(topics.board(cid), "General")["open"]) == 1
    with connection() as conn:
        rid = conn.execute("SELECT id FROM renewals").fetchone()["id"]
    on_renewal = ns.add_note("renewal", str(rid), "About the renewal")
    for bad in (lambda: topics.create(cid, ""), lambda: topics.create(cid, "General"),
                lambda: topics.create(cid, "client requests"), lambda: topics.create(cid, "X", "gold"),
                lambda: topics.create(cid, "X", "blue", "Atlantis"),
                lambda: topics.create(cid, "X", status="later"),
                lambda: topics.create(cid, "x" * 61), lambda: topics.create(cid + 1, "X"),
                lambda: topics.move("note", on_renewal, str(tid)),         # renewal notes stay where they are
                lambda: ns.add_note("renewal", str(rid), "x", topic_id=tid),
                lambda: topics.move("note", note, "999")):
        with pytest.raises(ns.Invalid):
            bad()


def test_the_board_page(app):
    cid = _client()
    url = f"/clients/{cid}/notes"
    res = post(app, f"/clients/{cid}/topics", {"name": "Partner tracker", "color": "teal", "country": "",
                                                "status": "active", "back": url})
    assert res.status == 303 and dict(res.headers)["Location"].startswith(url + "#topic-")
    tid = topics.board(cid)["topics"][0]["id"]
    post(app, "/notes/add", {"scope": "client", "ref": str(cid), "body": "Recipients: A, B",
                             "topic": str(tid), "back": url})
    note = _col(topics.board(cid), "Partner tracker")["notes"][0]["id"]
    assert post(app, f"/notes/{note}/pin", {"pinned": "1", "back": url}).status == 303
    page = get(app, url).body_bytes.decode()
    assert "/static/topics.css" in page and 'class="tcol tc-teal"' in page and 'class="tcol tc-grey"' in page
    assert "Recipients: A, B" in page and 'class="note is-pinned"' in page and "📌 1" in page
    assert f'action="/notes/{note}/topic"' in page and "+ Topic" in page
    assert post(app, f"/clients/{cid}/topics", {"name": "", "back": url}).status == 400
    assert post(app, f"/notes/{note}/topic", {"topic": "", "back": url}).status == 303
    assert post(app, f"/clients/{cid}/topics/{tid}/delete", {"back": url}).status == 303
    assert "Recipients: A, B" in get(app, url).body_bytes.decode()           # kept, now in General


def test_the_todos_page_shows_the_topic(app):
    cid = _client()
    tid = topics.create(cid, "Partner tracker", "teal")
    ns.add_todo("client", str(cid), "Release the partner tracker", None, topic_id=tid)
    ns.add_todo("client", str(cid), "A General one", None)
    assert {t["title"]: (t["topic"] or {}).get("name") for t in ns.todo_list()["open"]} == {
        "Release the partner tracker": "Partner tracker", "A General one": None}
    page = get(app, "/todos").body_bytes.decode()
    assert '<span class="tc-chip tc-teal"' in page and "/static/topics.css" in page
