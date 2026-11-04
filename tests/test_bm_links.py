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


def test_the_policy_link_survives_a_single_client_export(configured, app):
    policy = f"https://bm.example/client/{CLIENT_ID}/policies/{hexid(1, '8')};{hexid(1, '7')}"
    renewal = f"https://bm.example/client/{CLIENT_ID}/renewals/{hexid(1, '9')}/{hexid(1, '8')}"
    _load(renewal_tracker([R(n=1, policy="Medical")], CROSS, report_date="03 Nov 2026"))
    cid, rid = _medical()
    _load(renewal_tracker([R(n=1, policy="Medical")], CLIENT, report_date="04 Nov 2026"))
    d = rs.detail(cid, rid)
    assert d["links"] == [{"label": "Policy in BM+", "url": policy, "title": "The expiring policy in BM+"}]
    assert d["renewal"]["fields"]["bm_url"] == renewal  # kept, but BM+'s renewal link doesn't open
    page = get(app, f"/clients/{cid}/renewals/{rid}").body_bytes.decode()
    assert f'href="{policy}" target="_blank" rel="noopener noreferrer"' in page
    assert renewal not in page.split("Everything BM+ exported")[0]   # not offered as a link
    assert 'class="menu"' in page


def test_the_task_links_give_one_renewal_link(configured, app):
    """Every task link opens the same BM+ page (the renewal's workspace), so
    only one is offered, as the renewal's link (Martin, 04.11.2026)."""
    _load(renewal_tracker([R(n=1, policy="Medical")], CLIENT))
    cid, rid = _medical()
    assert rs.detail(cid, rid)["links"] == []
    assert "No BM+ links yet" in get(app, f"/clients/{cid}/renewals/{rid}").body_bytes.decode()
    _load(task_tracker([T(n=1, task_name="Renewal Strategy"), T(n=1, task_name="Proposals")]))
    links = rs.detail(cid, rid)["links"]
    assert [lk["label"] for lk in links] == ["Renewal in BM+"]
    assert links[0]["url"].startswith("https://bm.example/") and "taskId=" in links[0]["url"]
    page = get(app, f"/clients/{cid}/renewals/{rid}").body_bytes.decode()
    assert "Task in BM+" not in page and page.count("Renewal in BM+ ↗") == 2   # header button + menu


def test_bundle_cards_carry_the_links_menu(configured, app):
    _load(renewal_tracker([R(n=1, policy="Medical"), R(n=2, policy="Life")], CROSS))
    cid, _ = _medical()
    page = get(app, f"/clients/{cid}").body_bytes.decode()
    assert page.count('<details class="menu">') == 2 and page.count("Policy in BM+ ↗") == 2
