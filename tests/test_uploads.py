from pathlib import Path

import pytest

from mart.repository.db import connection
from mart.services import backup_service
from mart.services import upload_service as us
from mart.web.framework import Request
from tests.conftest import get, post
from tests.fixtures import CLIENT, CROSS, R, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")


def _book():
    return [R(n=1, policy="Medical"), R(n=2, policy="Life", country="Spain"),
            R(n=3, client="Globex", country="Brazil", policy="Dental")]


def _db(sql, *args):
    with connection() as conn:
        return [dict(r) for r in conn.execute(sql, args)]


def test_preview_lists_clients_and_nothing_is_stored_yet():
    uid = us.stage("Renewal_Tracker.xlsx", renewal_tracker(_book()))
    view = us.preview(uid)
    names = [c["name"] for c in view["clients"]]
    assert sorted(names) == ["Acme Group", "Globex"]
    assert all(c["is_mine"] is None for c in view["clients"])        # cross-client: you choose
    acme = next(c for c in view["clients"] if c["name"] == "Acme Group")
    assert (acme["items"], acme["new"], acme["changed"]) == (2, 2, 0)
    assert view["filters"]["Completed within Last 6 Months"] == "Excluded"
    assert _db("SELECT COUNT(*) n FROM renewals")[0]["n"] == 0


def test_commit_loads_only_my_clients_and_remembers_the_rest(configured):
    uid = us.stage("rt.xlsx", renewal_tracker(_book()))
    acme_key = next(c["key"] for c in us.preview(uid)["clients"] if c["name"] == "Acme Group")
    summary = us.commit(uid, {acme_key})
    assert summary["new"] == 2 and summary["clients_ignored"] == ["Globex"]
    assert sorted(r["policy_name"] for r in _db("SELECT policy_name FROM renewals")) == ["Life", "Medical"]
    mine = {r["name"]: r["is_mine"] for r in _db("SELECT name, is_mine FROM clients")}
    assert mine == {"Acme Group": 1, "Globex": 0}
    assert backup_service.list_backups(Path(configured.backup_dir))        # backed up after commit
    # the next upload remembers the choice
    view = us.preview(us.stage("rt2.xlsx", renewal_tracker(_book())))
    choice = {c["name"]: c["is_mine"] for c in view["clients"]}
    assert choice == {"Acme Group": 1, "Globex": 0}


def _commit_acme(data: bytes) -> dict:
    uid = us.stage("rt.xlsx", data)
    keys = {c["key"] for c in us.preview(uid)["clients"] if c["name"] == "Acme Group"}
    return us.commit(uid, keys)


def test_same_file_again_changes_nothing():
    data = renewal_tracker(_book())
    _commit_acme(data)
    uid = us.stage("rt.xlsx", data)
    view = us.preview(uid)
    assert view["same_file"] is not None
    acme = next(c for c in view["clients"] if c["name"] == "Acme Group")
    assert (acme["new"], acme["changed"], acme["unchanged"]) == (0, 0, 2)
    assert us.commit(uid, {acme["key"]})["unchanged"] == 2


def test_renewals_that_leave_the_export_are_kept_and_can_come_back():
    _commit_acme(renewal_tracker(_book()))
    later = [R(n=1, policy="Medical", status="Completed"), R(n=4, policy="Accident")]
    summary = _commit_acme(renewal_tracker(later, report_date="10 Nov 2026"))
    assert (summary["new"], summary["changed"], summary["left_export"]) == (1, 1, 1)
    rows = {r["policy_name"]: r for r in _db("SELECT * FROM renewals")}
    assert rows["Life"]["in_latest_export"] == 0 and rows["Life"]["left_export_at"]
    assert rows["Medical"]["workflow_status"] == "Completed"
    back = _commit_acme(renewal_tracker(_book(), report_date="17 Nov 2026"))
    assert back["returned"] == 1
    assert _db("SELECT in_latest_export FROM renewals WHERE policy_name='Life'")[0]["in_latest_export"] == 1


def test_a_single_client_export_never_touches_other_clients():
    uid = us.stage("all.xlsx", renewal_tracker(_book()))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]})        # both mine
    globex_only = [R(n=3, client="Globex", country="Brazil", policy="Dental")]
    uid = us.stage("globex.xlsx", renewal_tracker(globex_only, CLIENT, report_date="10 Nov 2026"))
    view = us.preview(uid)
    assert [c["name"] for c in view["clients"]] == ["Globex"] and view["clients"][0]["is_mine"] == 1
    us.commit(uid, {view["clients"][0]["key"]})
    assert _db("SELECT COUNT(*) n FROM renewals WHERE in_latest_export = 1")[0]["n"] == 3


def test_the_other_export_flavour_is_not_a_change():
    """Same data from the cross-client and the single-client export: ids are
    URLs in one and bare in the other, and only one has a Client Name column."""
    _commit_acme(renewal_tracker(_book(), CROSS))
    acme = [r for r in _book() if r.client == "Acme Group"]
    view = us.preview(us.stage("acme.xlsx", renewal_tracker(acme, CLIENT, report_date="04 Nov 2026")))
    c = view["clients"][0]
    assert (c["new"], c["changed"], c["unchanged"]) == (0, 0, 2)


def test_an_upload_never_blanks_text_only_the_other_flavour_carries():
    text = "02 Nov 2026: Strategy agreed with HR: remarketing."
    acme = [R(n=1, policy="Medical", overview=text, feed="01 Nov 2026: system message"),
            R(n=2, policy="Life", country="Spain")]
    _commit_acme(renewal_tracker(acme, CLIENT, report_date="03 Nov 2026"))
    summary = _commit_acme(renewal_tracker(acme, CROSS, report_date="04 Nov 2026"))
    assert summary["changed"] == 1       # the feed (only in cross-client) is new for Medical
    import json
    fields = json.loads(_db("SELECT fields_json FROM renewals WHERE policy_name='Medical'")[0]["fields_json"])
    assert fields["overview_all"] == text and fields["overview_client_ready"] == text
    assert fields["renewal_feed"] == "01 Nov 2026: system message"


def test_an_older_export_needs_explicit_confirmation():
    _commit_acme(renewal_tracker(_book(), report_date="10 Nov 2026"))
    uid = us.stage("old.xlsx", renewal_tracker(_book(), report_date="01 Nov 2026"))
    view = us.preview(uid)
    assert view["newer"] is not None
    keys = {c["key"] for c in view["clients"] if c["is_mine"] == 1}
    with pytest.raises(us.UploadError, match="newer export"):
        us.commit(uid, keys)
    assert us.commit(uid, keys, allow_older=True)["unchanged"] == 2


def test_discard_changes_nothing():
    uid = us.stage("rt.xlsx", renewal_tracker(_book()))
    us.discard(uid)
    assert _db("SELECT status FROM uploads")[0]["status"] == "discarded"
    assert _db("SELECT COUNT(*) n FROM staging_rows")[0]["n"] == 0
    with pytest.raises(us.UploadError):
        us.commit(uid, set())


def test_wrong_file_is_refused_with_a_reason():
    with pytest.raises(us.UploadError, match="missing these columns: Task Status, Task ID"):
        us.stage("tasks.xlsx", renewal_tracker([], task_tracker=True))   # an empty Task Summary
    import io

    import openpyxl
    wb = openpyxl.Workbook()
    wb.active.title = "Benefit Details"
    out = io.BytesIO()
    wb.save(out)
    with pytest.raises(us.UploadError, match="Benefit Tracker"):
        us.stage("benefits.xlsx", out.getvalue())


# -- through the web pages ----------------------------------------------------------------
def _multipart(filename: str, data: bytes) -> Request:
    b = "----martboundary"
    body = (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n").encode() + data + f"\r\n--{b}--\r\n".encode()
    return Request("POST", "/uploads", "", {"content-type": f"multipart/form-data; boundary={b}"}, body)


def test_upload_preview_commit_through_the_pages(app):
    r = app.handle(_multipart("Renewal Tracker Cross Client.xlsx", renewal_tracker(_book())))
    assert r.status == 303
    preview_url = dict(r.headers)["Location"]
    html = get(app, preview_url).body_bytes.decode()
    assert "Which clients are yours?" in html and "Acme Group" in html and "Globex" in html
    key = next(c["key"] for c in us.preview(int(preview_url.rsplit("/", 1)[1]))["clients"]
               if c["name"] == "Acme Group")
    r = post(app, preview_url + "/commit", {"mine": key})
    assert r.status == 303 and dict(r.headers)["Location"].startswith("/uploads?done=")
    page = get(app, dict(r.headers)["Location"]).body_bytes.decode()
    assert "Loaded 1 client (renewals): 2 new" in page and "Acme Group" in page
    home = get(app, "/").body_bytes.decode()
    assert "Your data" in home and "renewals in the latest export" in home and "Today" in home


def test_a_wrong_file_shows_the_reason_on_the_page(app):
    r = app.handle(_multipart("notes.xlsx", b"not a workbook"))
    assert r.status == 400 and "be read as an Excel workbook" in r.body_bytes.decode()


def test_client_names_are_escaped_on_the_preview(app):
    r = app.handle(_multipart("x.xlsx", renewal_tracker([R(client="<b>Evil</b> Ltd")])))
    html = get(app, dict(r.headers)["Location"]).body_bytes.decode()
    assert "<b>Evil</b>" not in html and "&lt;b&gt;Evil&lt;/b&gt; Ltd" in html
