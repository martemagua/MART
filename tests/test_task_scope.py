"""Tasks attach only to renewals MART has (Martin, 04.11.2026): the renewals
are the backbone and the history grows from them; a task that can't be
linked is discarded. A Task Tracker can cover years (its own period is on
General Information); a task outside that period missing from the export is
not news."""

from datetime import datetime

from mart.repository import tasks_repo
from mart.repository.db import connection
from mart.services import upload_service as us
from tests.conftest import get
from tests.fixtures import R, T, hexid, renewal_tracker, task_tracker


def _load(data: bytes) -> dict:
    uid = us.stage("x.xlsx", data)
    view = us.preview(uid)
    summary = us.commit(uid, {c["key"] for c in view["clients"]}, allow_older=True)
    return {"view": view["clients"][0], "summary": summary}


def _task_keys() -> set[str]:
    with connection() as conn:
        return {r["task_key"] for r in conn.execute("SELECT task_key FROM tasks")}


THIS = T(n=1, task_name="Renewal Strategy")                                   # 2027 renewal
LAST = T(n=3, task_name="Renewal Strategy", status="Completed",               # 2026 renewal
         review_date=datetime(2026, 1, 1, 1, 0))
NONE = T(n=4, task_name="Proposals", review_date=datetime(2024, 1, 1, 1, 0))  # no renewal in MART


def test_tasks_without_a_renewal_in_mart_are_not_loaded(configured, app):
    _load(renewal_tracker([R(n=1, policy="Medical")]))
    uid = us.stage("tasks.xlsx", task_tracker([THIS, NONE]))
    c = us.preview(uid)["clients"][0]
    assert (c["new"], c["skipped"]) == (1, 1)
    page = get(app, f"/uploads/{uid}").body_bytes.decode()
    assert "No renewal" in page and "Tasks only attach to renewals MART has" in page
    summary = us.commit(uid, {c["key"]})
    assert summary["skipped"] == 1 and _task_keys() == {THIS.ids()[0]}


def test_tasks_of_an_older_renewal_mart_kept_attach_to_it(configured):
    # MART kept last year's renewal (same policy, earlier cycle): its tasks attach
    _load(renewal_tracker([R(n=3, policy="Medical", stable=hexid(1, "7"),
                             renewal_date=datetime(2026, 1, 1, 1, 0))], report_date="01 Oct 2025"))
    _load(renewal_tracker([R(n=1, policy="Medical")]))
    r = _load(task_tracker([THIS, LAST, NONE]))
    assert r["summary"]["new"] == 2 and r["summary"]["skipped"] == 1


def test_tasks_loaded_before_that_belong_to_no_renewal_are_removed(configured):
    _load(renewal_tracker([R(n=1, policy="Medical")]))
    _load(task_tracker([THIS]))
    with connection() as conn:       # as 0.4.x stored it: a task with no renewal
        cid = conn.execute("SELECT id FROM clients").fetchone()["id"]
        row = {"key": "orphan-1", "fields": {"task_name": "Proposals", "policy_id": hexid(77, "8")},
               "bm": {}, "content_hash": "x"}
        tasks_repo.save(conn, row, cid, 1, existing=None, touched=True)
    assert "orphan-1" in _task_keys()
    _load(task_tracker([THIS], report_date="05 Nov 2026"))
    assert _task_keys() == {THIS.ids()[0]}


def test_a_task_outside_the_export_period_is_not_news(configured):
    _load(renewal_tracker([R(n=3, policy="Medical", stable=hexid(1, "7"),
                             renewal_date=datetime(2026, 1, 1, 1, 0))], report_date="01 Oct 2025"))
    _load(renewal_tracker([R(n=1, policy="Medical")]))
    _load(task_tracker([THIS, LAST], period=("01 Jan 2024", "31 Dec 2027")))
    # a narrower export: only this year's renewals
    r = _load(task_tracker([THIS], report_date="05 Nov 2026", period=("31 Dec 2026", "30 Dec 2027")))
    assert r["view"]["leaving"] == 0 and r["summary"]["left_export"] == 0
    # one that covers last year's renewal too, without its task: that is news
    r = _load(task_tracker([THIS], report_date="06 Nov 2026", period=("01 Jan 2025", "30 Dec 2027")))
    assert r["view"]["leaving"] == 1 and r["summary"]["left_export"] == 1


def test_renewal_trackers_come_first_when_uploaded_together(configured):
    first = us.stage("tasks.xlsx", task_tracker([THIS]))
    second = us.stage("renewals.xlsx", renewal_tracker([R(n=1)]))
    assert [w["id"] for w in us.waiting_uploads()] == [second, first]
