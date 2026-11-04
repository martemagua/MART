"""Day 5: notes and to-dos on renewals and bundles (user data: uploads never
touch it), the To-dos page and the Home card."""

from datetime import date

import pytest

from mart.repository.db import connection
from mart.services import notes_service as ns
from mart.services import upload_service as us
from tests.conftest import get, post
from tests.fixtures import R, renewal_tracker


def _load(data: bytes) -> None:
    uid = us.stage("rt.xlsx", data)
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)


@pytest.fixture
def book(configured):
    _load(renewal_tracker([R(n=1, policy="Medical"), R(n=2, policy="Life")]))
    with connection() as conn:
        rows = {r["policy_name"]: dict(r) for r in conn.execute("SELECT * FROM renewals")}
    med = rows["Medical"]
    return {"cid": med["client_id"], "med": med["id"], "life": rows["Life"]["id"],
            "bundle": ns.bundle_ref(med["client_id"], "Poland|2027-01-01")}


def _page(app, url: str) -> str:
    r = get(app, url)
    assert r.status == 200, r.status
    return r.body_bytes.decode()


def test_write_on_a_renewal_through_the_pages(book, app):
    url = f"/clients/{book['cid']}/renewals/{book['med']}"
    r = post(app, "/todos/add", {"scope": "renewal", "ref": str(book["med"]), "title": "Chase broker",
                                 "due": "2026-11-10", "back": url})
    assert r.status == 303 and dict(r.headers)["Location"] == url + "#mine"
    post(app, "/notes/add", {"scope": "renewal", "ref": str(book["med"]),
                             "body": "Broker: terms\nexpected late November", "back": url})
    page = _page(app, url)
    assert "Your to-dos and notes" in page and "Chase broker" in page and "due 10.11.2026" in page
    assert "Broker: terms\nexpected late November" in page
    # the bundle card shows the counts
    bundle_page = _page(app, f"/clients/{book['cid']}")
    assert "☐ 1" in bundle_page and "✎ 1" in bundle_page


def test_edit_done_and_delete(book, app):
    tid = ns.add_todo("renewal", str(book["med"]), "Ask HR", None)
    nid = ns.add_note("renewal", str(book["med"]), "first")
    post(app, f"/todos/{tid}/save", {"title": "Ask HR about PDC", "due": "2026-12-01", "back": "/todos"})
    post(app, f"/notes/{nid}/save", {"body": "second", "back": "/todos"})
    r = post(app, f"/todos/{tid}/done", {"done": "1", "back": "/todos"})
    assert dict(r.headers)["Location"] == f"/todos#todo-{tid}"
    m = ns.for_renewal({"id": book["med"], "client_id": book["cid"], "country": "Poland",
                        "renewal_date": "2027-01-01"})
    assert m["todos"][0]["title"] == "Ask HR about PDC" and m["todos"][0]["done_at"]
    assert m["notes"][0]["body"] == "second" and m["notes"][0]["updated_at"]
    post(app, f"/todos/{tid}/done", {"done": "0", "back": "/todos"})
    post(app, f"/todos/{tid}/delete", {"back": "/todos"})
    post(app, f"/notes/{nid}/delete", {"back": "/todos"})
    with connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0


def test_bundle_notes_show_on_the_bundle_and_its_renewals(book, app):
    ns.add_note("bundle", book["bundle"], "One mail to the broker covers all of Poland")
    ns.add_todo("bundle", book["bundle"], "Send the Poland pack", "2026-11-20")
    bundle_page = _page(app, f"/clients/{book['cid']}")
    assert "To-dos and notes on this bundle" in bundle_page and "Send the Poland pack" in bundle_page
    life = _page(app, f"/clients/{book['cid']}/renewals/{book['life']}")
    assert "On the whole bundle" in life and "One mail to the broker covers all of Poland" in life


def test_todos_page_and_home(book, app):
    today = date.today()
    ns.add_todo("renewal", str(book["med"]), "Late one", "2020-01-01")
    ns.add_todo("bundle", book["bundle"], "No date", None)
    done = ns.add_todo("renewal", str(book["life"]), "Finished", None)
    ns.set_done(done, True)
    view = ns.todo_list(today=today)
    assert [t["title"] for t in view["open"]] == ["Late one", "No date"] and view["overdue"] == 1
    assert [t["title"] for t in view["done"]] == ["Finished"]
    assert view["open"][0]["target"]["url"] == f"/clients/{book['cid']}/renewals/{book['med']}"
    assert view["open"][1]["target"]["name"] == "whole bundle"
    page = _page(app, "/todos")
    assert "1 overdue" in page and "Late one" in page and "Finished" in page
    assert ('Acme Group · <img class="flag" src="/static/flags/pl.svg" alt="" width="16" height="12" '
            'title="Poland">Poland') in page
    home = _page(app, "/")
    assert "To-dos" in home and "2 open" in home and "Late one" in home


def test_only_my_targets_and_real_text(book, app):
    _load(renewal_tracker([R(n=9, client="Globex", policy="Dental")]))
    with connection() as conn:     # a client you untick later is no longer yours
        other = conn.execute("SELECT id FROM renewals WHERE policy_name = 'Dental'").fetchone()["id"]
        conn.execute("UPDATE clients SET is_mine = 0 WHERE name = 'Globex'")
    for data in ({"scope": "renewal", "ref": str(other), "title": "x"},          # not my client
                 {"scope": "renewal", "ref": "99999", "title": "x"},             # no such renewal
                 {"scope": "policy", "ref": "1", "title": "x"},                  # not a target
                 {"scope": "renewal", "ref": str(book["med"]), "title": "  "},   # empty
                 {"scope": "renewal", "ref": str(book["med"]), "title": "x", "due": "31.12.2026"}):
        assert post(app, "/todos/add", data).status == 400, data
    assert post(app, "/notes/add", {"scope": "bundle", "ref": "nonsense", "body": "x"}).status == 400
    # back only goes to a page of MART
    r = post(app, "/notes/add", {"scope": "renewal", "ref": str(book["med"]), "body": "ok",
                                 "back": "//evil.example/x"})
    assert dict(r.headers)["Location"] == "/todos#mine"


def test_notes_are_escaped(book, app):
    ns.add_note("renewal", str(book["med"]), "<script>alert(1)</script>")
    page = _page(app, f"/clients/{book['cid']}/renewals/{book['med']}")
    assert "<script>alert(1)</script>" not in page and "&lt;script&gt;" in page


def test_uploads_never_touch_notes(book):
    ns.add_note("renewal", str(book["med"]), "keep me")
    ns.add_todo("renewal", str(book["life"]), "keep me too", None)
    # Medical changes, Life leaves the export: both keep what was written on them
    _load(renewal_tracker([R(n=1, policy="Medical", status="Completed")], report_date="05 Nov 2026"))
    with connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0] == 1
    m = ns.for_renewal({"id": book["life"], "client_id": book["cid"], "country": "Poland",
                        "renewal_date": "2027-01-01"})
    assert m["todos"][0]["title"] == "keep me too"


def test_client_notes_space(book, app):
    cid = book["cid"]
    url = f"/clients/{cid}/notes"
    page = _page(app, url)
    assert "Notes and to-dos on Acme Group" in page and "Client notes &amp; to-dos" in page
    r = post(app, "/notes/add", {"scope": "client", "ref": str(cid), "body": "HR contact changes in Jan",
                                 "back": url})
    assert dict(r.headers)["Location"] == url + "#mine"
    ns.add_todo("client", str(cid), "Plan the annual review", "2026-12-01")
    assert "HR contact changes in Jan" in _page(app, url)
    clients = _page(app, "/clients")
    assert f'href="/clients/{cid}/notes"' in clients and "☐ 1" in clients and "✎ 1" in clients
    todo = next(t for t in ns.todo_list()["open"] if t["title"] == "Plan the annual review")
    assert todo["target"] == {"kind": "client", "country": None, "renewal_date": None,
                              "name": "client notes", "url": url}
    assert post(app, "/notes/add", {"scope": "client", "ref": "999", "body": "x"}).status == 400
    assert get(app, "/clients/999/notes").status == 404


def test_notes_of_earlier_cycles_show_on_the_renewal(configured, app):
    from datetime import datetime

    from tests.fixtures import hexid
    stable = hexid(1, "7")
    _load(renewal_tracker([R(n=3, policy="Medical", stable=stable, renewal_date=datetime(2026, 1, 1, 1, 0))],
                          report_date="01 Oct 2025"))
    _load(renewal_tracker([R(n=1, policy="Medical", stable=stable), R(n=2, policy="Life")]))
    with connection() as conn:
        rows = {(r["policy_name"], r["renewal_date"]): dict(r)
                for r in conn.execute("SELECT * FROM renewals")}
    old, new = rows[("Medical", "2026-01-01")], rows[("Medical", "2027-01-01")]
    life = rows[("Life", "2027-01-01")]
    ns.add_note("renewal", str(old["id"]), "Last year HR wanted quotes by October")
    ns.add_note("renewal", str(life["id"]), "a different policy")
    earlier = ns.for_renewal(new)["earlier"]
    assert [n["body"] for n in earlier] == ["Last year HR wanted quotes by October"]
    assert earlier[0]["cycle"]["renewal_date"] == "2026-01-01"
    page = _page(app, f"/clients/{new['client_id']}/renewals/{new['id']}")
    assert "Notes from earlier renewals of this policy (1)" in page and "renewal 01.01.2026" in page
    assert ns.for_renewal(life)["earlier"] == []
