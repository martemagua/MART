"""M2 day 4: Home "Today" (Martin, 04.11.2026). One list of what needs him
(passed / near deadlines, due or urgent to-dos, quiet bundles, new overview
entries), then a card per client. Built from the explorer's own data."""

from datetime import date, datetime, timedelta

import pytest

from mart.repository.db import connection
from mart.services import deadlines as dl
from mart.services import notes_service as ns
from mart.services import today as td
from mart.services import upload_service as us
from tests.conftest import get
from tests.fixtures import R, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")
TODAY = date.today()


def _hdr(days_ago: int) -> str:
    return (TODAY - timedelta(days=days_ago)).strftime("%d %b %Y")


@pytest.fixture
def book():
    jan, feb, mar = (datetime(2027, m, 1, 1, 0) for m in (1, 2, 3))
    rows = [R(n=1, policy="Medical", renewal_date=jan, overview=f"{_hdr(0)}:\nTerms in."),       # new
            R(n=2, policy="Life", country="Spain", renewal_date=feb, overview=f"{_hdr(30)}:\nOld."),  # quiet
            R(n=3, policy="Dental", country="Italy", renewal_date=mar, overview=f"{_hdr(40)}:\nOld.",
              final_terms_date=datetime.combine(TODAY - timedelta(days=2), datetime.min.time())),   # passed
            R(n=4, policy="Vision", country="France", renewal_date=mar, overview=f"{_hdr(3)}:\nOk.")]
    uid = us.stage("rt.xlsx", renewal_tracker(rows, cross_overview=True))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)
    with connection() as conn:
        cid = conn.execute("SELECT id FROM clients").fetchone()["id"]
        ids = {r["policy_name"]: r["id"] for r in conn.execute("SELECT id, policy_name FROM renewals")}
    return cid, ids


def test_the_lists(book):
    cid, ids = book
    dl.set_deadline(cid, "France|2027-03-01", (TODAY + timedelta(days=3)).isoformat(), "Broker F")
    ns.add_todo("renewal", str(ids["Medical"]), "Urgent but undated", None, "urgent")
    ns.add_todo("renewal", str(ids["Life"]), "Overdue", (TODAY - timedelta(days=1)).isoformat())
    ns.add_todo("renewal", str(ids["Life"]), "Later", (TODAY + timedelta(days=9)).isoformat())
    v = td.view()
    assert [x["country"] for x in v["deadlines_passed"]["items"]] == ["Italy"]
    assert [(x["country"], x["deadline"]["promised_by"]) for x in v["deadlines_soon"]["items"]] == \
        [("France", "Broker F")]
    assert [x["title"] for x in v["todos"]["items"]] == ["Urgent but undated", "Overdue"]
    # Italy is quiet too, but already listed for its passed deadline
    assert [x["country"] for x in v["stale"]["items"]] == ["Spain"]
    assert [x["policy"] for x in v["new"]["items"]] == ["Medical"]
    card = v["clients"][0]
    assert card["counts"] == {"passed": 1, "soon": 1, "stale": 1, "new": 1, "todos": 3}
    assert not v["nothing"]


def test_completed_bundles_stop_asking(book):
    """QA 07.11.2026: a bundle whose renewals are all marked completed is no
    longer "gone quiet" and its BM+-suggested date no longer "passed"; a date
    Martin set himself still is."""
    cid, ids = book
    from mart.services import actuals
    actuals.set_completed(cid, [ids["Life"], ids["Dental"]], None)   # Spain quiet, Italy BM+ date passed
    v = td.view()
    assert v["stale"]["items"] == [] and v["deadlines_passed"]["items"] == []
    dl.set_deadline(cid, "Italy|2027-03-01", (TODAY - timedelta(days=1)).isoformat(), "Broker I")
    assert [x["country"] for x in td.view()["deadlines_passed"]["items"]] == ["Italy"]


def test_the_page(book, app):
    page = get(app, "/").body_bytes.decode()
    assert "What needs you today" in page and "Expected updates passed" in page
    assert "New overview entries since yesterday" in page and "Gone quiet" in page
    assert "Your data" in page
    # Your clients, at the top: straight to each one's explorer or board (Martin, 07.11.2026)
    assert page.index('id="go-h"') < page.index('id="today-h"') and 'class="go-list"' in page
    cid = td.view()["clients"][0]["id"]
    assert f'href="/clients/{cid}/board"' in page and f'href="/clients/{cid}"' in page


def test_todos_of_a_client_no_longer_mine_are_hidden_not_lost(book):
    """QA 07.11.2026: unticking a client hid its pages but kept listing its
    to-dos, which then could be neither ticked nor opened."""
    cid, ids = book
    ns.add_todo("renewal", str(ids["Life"]), "Chase the broker", None, "urgent")
    assert [t["title"] for t in ns.todo_list()["open"]] == ["Chase the broker"]
    with connection() as conn:
        conn.execute("UPDATE clients SET is_mine = 0 WHERE id = ?", (cid,))
    assert ns.todo_list()["open"] == []
    with connection() as conn:
        conn.execute("UPDATE clients SET is_mine = 1 WHERE id = ?", (cid,))
    assert [t["title"] for t in ns.todo_list()["open"]] == ["Chase the broker"]
