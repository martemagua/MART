"""Links back to BM+ (Martin, 04.11.2026: "a link to the renewal in BM+, so
I can reach it directly if I need to make changes"). MART only uses links BM+
itself wrote; it never builds or guesses one."""

from mart.ingestion.ids import bm_link
from mart.repository.db import connection
from mart.services import renewal_service as rs
from mart.services import upload_service as us
from tests.conftest import get
from tests.fixtures import CLIENT, CLIENT_ID, CROSS, R, T, hexid, renewal_tracker, task_tracker


def _load(data: bytes) -> None:
    uid = us.stage("x.xlsx", data)
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)


def _medical() -> tuple[int, int]:
    with connection() as conn:
        r = conn.execute("SELECT id, client_id FROM renewals WHERE policy_name = 'Medical'").fetchone()
    return r["client_id"], r["id"]


def test_only_plain_https_links_count():
    assert bm_link(" https://bm.example/client/1/renewals/2/3 ") == "https://bm.example/client/1/renewals/2/3"
    for bad in (None, "", hexid(1, "8"), "javascript:alert(1)", "http://bm.example/x",
                'https://x" onmouseover="y', "see https://bm.example/x"):
        assert bm_link(bad) is None, bad


def test_the_renewal_link_survives_a_single_client_export(configured, app):
    url = f"https://bm.example/client/{CLIENT_ID}/renewals/{hexid(1, '9')}/{hexid(1, '8')}"
    _load(renewal_tracker([R(n=1, policy="Medical")], CROSS, report_date="03 Nov 2026"))
    cid, rid = _medical()
    assert rs.detail(cid, rid)["bm_link"]["url"] == url
    _load(renewal_tracker([R(n=1, policy="Medical")], CLIENT, report_date="04 Nov 2026"))
    d = rs.detail(cid, rid)
    assert d["bm_link"] == {"url": url, "label": "Open in BM+", "title": "The renewal in BM+"}
    page = get(app, f"/clients/{cid}/renewals/{rid}").body_bytes.decode()
    assert f'href="{url}" target="_blank" rel="noopener noreferrer"' in page and "policy ↗" in page


def test_without_the_renewal_link_a_task_link_stands_in(configured, app):
    _load(renewal_tracker([R(n=1, policy="Medical")], CLIENT))
    cid, rid = _medical()
    assert rs.detail(cid, rid)["bm_link"] is None
    assert "no BM+ link yet" in get(app, f"/clients/{cid}/renewals/{rid}").body_bytes.decode()
    _load(task_tracker([T(n=1, task_name="Renewal Strategy"), T(n=1, task_name="Proposals")]))
    d = rs.detail(cid, rid)
    assert d["bm_link"]["label"] == "Open in BM+ (Renewal Strategy task)"
    assert d["bm_link"]["url"].startswith("https://bm.example/") and "taskId=" in d["bm_link"]["url"]
    page = get(app, f"/clients/{cid}/renewals/{rid}").body_bytes.decode()
    assert page.count("Task in BM+ ↗") == 2              # the two stages that have a task
