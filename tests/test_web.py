from pathlib import Path

import pytest

from mart import settings as settings_mod
from mart.services import backup_service
from mart.web.app import App, create_app
from mart.web.framework import Response, Router
from tests.conftest import get, post


# -- before setup -------------------------------------------------------------
def test_every_page_leads_to_setup_first(app):
    for path in ("/", "/settings", "/anything"):
        r = get(app, path)
        assert r.status == 303 and dict(r.headers)["Location"] == "/setup"


def test_health_answers_before_setup(app):
    r = get(app, "/health")
    assert r.status == 200 and b'"app": "MART"' in r.body_bytes
    assert b'"configured": false' in r.body_bytes


def test_setup_form_offers_local_defaults(app, tmp_path):
    r = get(app, "/setup")
    html = r.body_bytes.decode()
    assert r.status == 200 and "Welcome to MART" in html
    assert str(tmp_path / "home" / "MART-data") in html
    assert 'href="/settings"' not in html  # no navigation before setup


def test_setup_rejects_bad_folders_and_keeps_what_was_typed(app):
    r = post(app, "/setup", {"data_dir": "relative", "backup_dir": "", "backups_keep": "20",
                             "port": "8070"})
    html = r.body_bytes.decode()
    assert r.status == 400 and "Please check" in html and 'value="relative"' in html
    assert settings_mod.load() is None


def test_setup_creates_folders_database_and_settings(app, tmp_path):
    data, backups = tmp_path / "md", tmp_path / "mb"
    r = post(app, "/setup", {"data_dir": str(data), "backup_dir": str(backups),
                             "backups_keep": "10", "port": "8070"})
    assert r.status == 303 and dict(r.headers)["Location"].startswith("/")
    s = settings_mod.load()
    assert s.data_dir == str(data) and s.backups_keep == 10
    assert (data / "mart.db").is_file() and backups.is_dir()
    assert get(app, "/setup").status == 303  # setup can't be redone over existing settings


# -- after setup ----------------------------------------------------------------
def test_home_shows_the_system_card(app, configured):
    html = get(app, "/").body_bytes.decode()
    assert "No trackers uploaded yet" in html and "Last backup" in html


def test_settings_page_lists_backups(app, configured):
    backup_service.make_backup(configured.db_path, Path(configured.backup_dir), 3)
    html = get(app, "/settings").body_bytes.decode()
    assert "mart-" in html and ".db.gz" in html and "Back up now" in html


def test_back_up_now(app, configured):
    r = post(app, "/settings/backup")
    assert r.status == 303
    assert len(backup_service.list_backups(Path(configured.backup_dir))) == 1


def test_changing_the_data_folder_moves_the_database(app, configured, tmp_path):
    new_data = tmp_path / "moved"
    r = post(app, "/settings", {"data_dir": str(new_data), "backup_dir": configured.backup_dir,
                                "backups_keep": "3", "port": "8070"})
    html = r.body_bytes.decode()
    assert r.status == 200 and "Database moved" in html
    assert (new_data / "mart.db").is_file() and not configured.db_path.exists()


def test_pointing_at_an_existing_database_never_overwrites_it(app, configured, tmp_path):
    from mart.repository import schema
    other = tmp_path / "other"
    schema.ensure_schema(other / "mart.db")
    r = post(app, "/settings", {"data_dir": str(other), "backup_dir": configured.backup_dir,
                                "backups_keep": "3", "port": "8070"})
    assert "already existed" in r.body_bytes.decode()
    assert configured.db_path.exists()  # old one left untouched


def test_unknown_page_and_wrong_method(app, configured):
    assert get(app, "/nope").status == 404
    assert post(app, "/health").status == 405


# -- the protections ------------------------------------------------------------------
def test_requests_for_another_host_are_refused(configured):
    app = create_app({"127.0.0.1:8070", "localhost:8070"})
    assert get(app, "/", {"host": "evil.example:8070"}).status == 403
    assert get(app, "/", {"host": "127.0.0.1:8070"}).status == 200


def test_posts_from_other_websites_are_refused(configured):
    app = create_app({"127.0.0.1:8070"})
    h = {"host": "127.0.0.1:8070"}
    assert post(app, "/settings/backup", headers={**h, "origin": "https://evil.example"}).status == 403
    assert post(app, "/settings/backup", headers={**h, "origin": "http://127.0.0.1:8070"}).status == 303


def test_unexpected_errors_show_a_page_and_are_logged(configured):
    router = Router()

    @router.route("/boom")
    def boom(request) -> Response:
        raise RuntimeError("kaboom")

    r = App(router).handle(__import__("mart.web.framework", fromlist=["Request"]).Request("GET", "/boom"))
    assert r.status == 500 and "Something went wrong" in r.body_bytes.decode()
    log = configured.log_dir / "mart-error.log"
    assert "kaboom" in log.read_text(encoding="utf-8")


def test_values_are_escaped_in_pages(app, tmp_path):
    r = post(app, "/setup", {"data_dir": "<script>alert(1)</script>", "backup_dir": "x",
                             "backups_keep": "1", "port": "8070"})
    html = r.body_bytes.decode()
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html


@pytest.mark.skipif(not hasattr(__import__("time"), "tzset"),
                    reason="time zones can't be switched on Windows")
def test_database_timestamps_are_shown_in_local_time(monkeypatch):
    import time

    from mart.web.templating import dmy
    monkeypatch.setenv("TZ", "Europe/Berlin")
    time.tzset()
    try:
        assert dmy("2026-11-04 08:03:00", True) == "04.11.2026 09:03"   # UTC in the DB
        assert dmy("2026-11-04") == "04.11.2026"                      # a plain date stays
    finally:
        monkeypatch.delenv("TZ")
        time.tzset()


def test_a_refused_action_explains_and_leads_back(configured, app):
    from tests.conftest import post
    h = {"host": "127.0.0.1:8070", "referer": "http://127.0.0.1:8070/clients/1?bundle=x"}
    r = post(app, "/todos/add", {"scope": "nonsense", "ref": "1", "title": "x"}, headers=h)
    page = r.body_bytes.decode()
    assert r.status == 400 and "That didn't work" in page and "Nothing was changed." in page
    assert 'href="/clients/1?bundle=x"' in page and 'class="sidebar"' in page
    # a referer from another site is never offered as the way back
    h["referer"] = "https://evil.example/x"
    page = post(app, "/todos/add", {"scope": "nonsense", "ref": "1", "title": "x"},
                headers={**h, "origin": "http://127.0.0.1:8070"}).body_bytes.decode()
    assert "evil.example" not in page
