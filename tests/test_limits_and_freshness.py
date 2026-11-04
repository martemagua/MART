"""Day 4: the Time limits setting, "overview as of" per client, and uploading
several files at once."""

from datetime import date

from mart.repository.db import connection
from mart.services import client_service as cs
from mart.services import preferences
from mart.services import upload_service as us
from mart.web.framework import Request
from tests.conftest import get, post
from tests.fixtures import CLIENT, CROSS, R, T, renewal_tracker, task_tracker

OV = "01 Nov 2026: Terms received.\n"


def _load(data: bytes, name: str = "rt.xlsx") -> dict:
    uid = us.stage(name, data)
    return us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]})


def _acme() -> dict:
    with connection() as conn:
        return dict(conn.execute("SELECT * FROM clients WHERE name = 'Acme Group'").fetchone())


# -- preferences ----------------------------------------------------------------------------
def test_time_limit_defaults_validates_and_saves(configured):
    assert preferences.get("overview_data_stale_days") == 7
    assert preferences.save({"overview_data_stale_days": "0"})          # below the range
    assert preferences.save({"overview_data_stale_days": "seven"})      # not a number
    assert preferences.get("overview_data_stale_days") == 7             # nothing stored
    assert preferences.save({"overview_data_stale_days": " 14 ", "unknown": "x"}) == []
    assert preferences.get("overview_data_stale_days") == 14


def test_time_limits_card_on_the_settings_page(configured, app):
    page = get(app, "/settings").body_bytes.decode()
    assert "Time limits" in page and 'name="overview_data_stale_days"' in page and 'value="7"' in page
    bad = post(app, "/settings/limits", {"overview_data_stale_days": "500"})
    assert bad.status == 400 and "a whole number from 1 to 90 days" in bad.body_bytes.decode()
    ok = post(app, "/settings/limits", {"overview_data_stale_days": "10"})
    assert ok.status == 303 and dict(ok.headers)["Location"] == "/settings?limits=1"
    assert "Time limits saved." in get(app, "/settings?limits=1").body_bytes.decode()
    assert preferences.get("overview_data_stale_days") == 10


# -- overview as of -------------------------------------------------------------------------
def test_only_exports_carrying_the_overview_date_it(configured):
    _load(renewal_tracker([R(n=1, overview=OV)], CROSS, report_date="27 Oct 2026"))
    assert _acme()["overview_as_of"] is None          # cross-client: no overview in it
    _load(renewal_tracker([R(n=1, overview=OV)], CLIENT, report_date="28 Oct 2026"))
    assert _acme()["overview_as_of"] == "2026-10-28"
    _load(renewal_tracker([R(n=1, overview=OV)], CROSS, report_date="04 Nov 2026"))
    assert _acme()["overview_as_of"] == "2026-10-28"  # a later cross-client export leaves it


def test_freshness_goes_stale_after_the_limit(configured, app):
    _load(renewal_tracker([R(n=1, overview=OV)], CLIENT, report_date="28 Oct 2026"))
    fresh = cs.overview_freshness("2026-10-28", date(2026, 11, 4))
    assert (fresh["age_days"], fresh["stale"], fresh["limit"]) == (7, False, 7)
    assert cs.overview_freshness("2026-10-28", date(2026, 11, 5))["stale"] is True
    assert cs.overview_freshness(None, date(2026, 11, 5))["stale"] is True
    preferences.save({"overview_data_stale_days": "30"})
    assert cs.overview_freshness("2026-10-28", date(2026, 11, 20))["stale"] is False
    row = next(c for c in cs.clients_overview(date(2026, 11, 4)) if c["name"] == "Acme Group")
    assert row["freshness"]["as_of"] == "2026-10-28"
    assert "28.10.2026" in get(app, "/clients").body_bytes.decode()
    assert "Overview as of 28.10.2026" in get(app, f"/clients/{_acme()['id']}").body_bytes.decode()


# -- several files at once ------------------------------------------------------------------
def _multipart(*files: tuple[str, bytes]) -> Request:
    b = "----martboundary"
    body = b""
    for name, data in files:
        body += (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
                 f"Content-Type: application/octet-stream\r\n\r\n").encode() + data + b"\r\n"
    body += f"--{b}--\r\n".encode()
    return Request("POST", "/uploads", "", {"content-type": f"multipart/form-data; boundary={b}"}, body)


def test_several_files_wait_and_commit_leads_to_the_next(configured, app):
    tasks = task_tracker([T(n=1, task_name="Proposals", status="Not Started")])
    r = app.handle(_multipart(("renewals.xlsx", renewal_tracker([R(n=1)])), ("tasks.xlsx", tasks),
                              ("notes.xlsx", b"not a workbook")))
    assert r.status == 303 and dict(r.headers)["Location"].startswith("/uploads?done=")
    page = get(app, dict(r.headers)["Location"]).body_bytes.decode()
    assert "2 files ready for preview" in page and "notes.xlsx" in page and "Waiting for you" in page
    waiting = us.waiting_uploads()
    assert [w["filename"] for w in waiting] == ["renewals.xlsx", "tasks.xlsx"]
    first, second = waiting[0]["id"], waiting[1]["id"]
    key = us.preview(first)["clients"][0]["key"]
    r = post(app, f"/uploads/{first}/commit", {"mine": key})
    assert r.status == 303 and dict(r.headers)["Location"].startswith(f"/uploads/{second}?done=")
    html = get(app, dict(r.headers)["Location"]).body_bytes.decode()
    assert "Loaded 1 client (renewals)" in html and "Task Tracker" in html
    assert "1 task for 1 client" in html
    assert "built-in method" not in html
    assert [w["id"] for w in us.waiting_uploads()] == [second]
