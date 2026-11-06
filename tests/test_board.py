"""M3 day 6: the board (Martin, 05.11.2026; QUESTIONS C2–C4, M3d): one per
client, a card per bundle at its least advanced renewal's stage until Martin
moves it, his stage kept beside BM+'s."""

from datetime import datetime
from pathlib import Path

import pytest

import mart
from mart.repository.db import connection
from mart.services import board, board_service
from mart.services import client_service as cs
from mart.services import upload_service as us
from tests.conftest import get, post
from tests.fixtures import R, T, renewal_tracker, task_tracker

pytestmark = pytest.mark.usefixtures("configured")
POLAND = "Poland|2027-01-01"
CANADA = "Canada|2027-01-01"
JAN = datetime(2027, 1, 1, 1, 0)


def _commit(data: bytes, name: str) -> None:
    uid = us.stage(name, data)
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)


def _book() -> tuple[int, dict[str, int]]:
    """Poland: Medical with its strategy done and proposals running, Life with
    its strategy in progress. Canada: nothing in BM+ yet."""
    _commit(renewal_tracker([R(n=1, policy="Medical", renewal_date=JAN),
                             R(n=2, policy="Life", renewal_date=JAN),
                             R(n=3, policy="Dental", country="Canada", renewal_date=JAN)],
                            cross_overview=True), "rt.xlsx")
    _commit(task_tracker([T(n=1, task_name="Renewal Strategy", status="Completed"),
                          T(n=1, task_name="Proposals", status="In Progress"),
                          T(n=2, task_name="Renewal Strategy", status="In Progress")]), "tt.xlsx")
    with connection() as conn:
        rows = {r["policy_name"]: r["id"] for r in conn.execute("SELECT id, policy_name FROM renewals")}
        cid = conn.execute("SELECT id FROM clients").fetchone()["id"]
    return cid, rows


def _st(*states: str) -> list[dict]:
    return [{"name": n, "state": s, "label": s} for n, s in
            zip(("Renewal Strategy", "Proposals", "Update Policy"), states, strict=True)]


def test_a_renewals_column_from_bms_stages():
    col = board.renewal_column
    assert col(_st("missing", "missing", "missing")) == "not_started"
    assert col(_st("todo", "missing", "missing")) == "not_started"
    assert col(_st("doing", "missing", "missing")) == "strategy"
    assert col(_st("review", "todo", "todo")) == "strategy"
    assert col(_st("done", "todo", "todo")) == "proposals"
    assert col(_st("done", "doing", "todo")) == "proposals"
    assert col(_st("done", "done", "todo")) == "decision"
    assert col(_st("done", "skipped", "todo")) == "update_policy"       # no proposals needed
    assert col(_st("done", "done", "doing")) == "update_policy"
    assert col(_st("done", "done", "done")) == "review"
    assert col(_st("done", "done", "done"), completed=True) == "done"
    assert col([], completed=False) == "not_started"


def test_bundle_sits_at_its_least_advanced_renewal():
    b = board.bundle_column(["decision", "proposals", "proposals"])
    assert (b["column"], b["at"], b["total"], b["mixed"]) == ("proposals", 2, 3, True)
    assert b["spread"] == [("Proposals / Marketing", 2), ("Decision", 1)]
    assert not board.bundle_column(["strategy"])["mixed"]
    assert board.bundle_column([])["column"] == "not_started"
    dots = board.aggregate_stages([_st("done", "doing", "todo"), _st("done", "done", "todo")])
    assert [d["state"] for d in dots] == ["done", "doing", "todo"]
    assert dots[1]["label"] == "In progress (1 of 2 completed)"


def test_place_keeps_martins_stage_until_bm_catches_up():
    def at(bm, stage, then):
        p = board.place(bm, {"stage": stage, "bm_stage": then})
        return p["column"], p["state"], bool(p["mine"])
    assert board.place("strategy", None)["column"] == "strategy"
    # moved ahead: stays while BM+ is behind, follows BM+ once it gets there
    assert at("strategy", "decision", "strategy") == ("decision", "behind", True)
    assert at("proposals", "decision", "strategy") == ("decision", "behind", True)
    assert at("decision", "decision", "strategy") == ("decision", "caught_up", False)
    assert at("update_policy", "decision", "strategy") == ("update_policy", None, False)
    # moved back: held while BM+ stands still, a conflict once BM+ moves on
    assert at("update_policy", "proposals", "update_policy") == ("proposals", "held", True)
    assert at("review", "proposals", "update_policy") == ("proposals", "conflict", True)
    assert at("strategy", "proposals", "update_policy") == ("strategy", None, False)


def test_the_board_and_moving_a_card(app):
    cid, ids = _book()
    v = board_service.board_of(cid)
    where = {b["key"]: col["key"] for col in v["columns"] for b in col["cards"]}
    assert where == {POLAND: "strategy", CANADA: "not_started"}       # Life holds Poland back
    poland = next(b for c in v["columns"] for b in c["cards"] if b["key"] == POLAND)
    assert (poland["bm_stage"]["at"], poland["bm_stage"]["total"]) == (1, 2)
    assert v["card_count"] == 2 and v["moved"] == 0

    board_service.set_stage(cid, POLAND, "decision", "quotes in, HR deciding")
    p = cs.explorer(cid, bundle=POLAND)["selected"]["stage"]
    assert (p["column"], p["state"], p["mine"], p["row"]["reason"]) == ("decision", "behind", "decision",
                                                                        "quotes in, HR deciding")
    assert board_service.board_of(cid)["moved"] == 1
    board_service.set_stage(cid, POLAND, "strategy")                  # BM+'s own column: follow BM+
    assert cs.explorer(cid, bundle=POLAND)["selected"]["stage"]["mine"] is None

    # into Done, marking the open renewals completed at the same time (M3h)
    board_service.set_stage(cid, POLAND, "done", "all approved", complete=True)
    s = cs.explorer(cid, bundle=POLAND)["selected"]
    assert s["completed"] == 2 and s["stage"]["column"] == "done" and s["stage"]["state"] == "caught_up"
    for bad in (lambda: board_service.set_stage(cid, POLAND, "limbo"),
                lambda: board_service.set_stage(cid, "Atlantis|2027-01-01", "done"),
                lambda: board_service.set_stage(cid, CANADA, "done", "x" * 201),
                lambda: board_service.set_stage(cid + 1, CANADA, "done")):
        with pytest.raises(board_service.Invalid):
            bad()


def test_pages(app):
    cid, ids = _book()
    assert dict(get(app, "/board").headers)["Location"] == f"/clients/{cid}/board"   # one client: its board
    page = get(app, f"/clients/{cid}/board").body_bytes.decode()
    assert "Board · Acme Group" in page and "Post-renewal review" in page and "/static/board.js" in page
    assert f'data-key="{POLAND}"' in page and "1 of 2 at Strategy" in page and "<dialog" in page
    assert 'data-bundle-filters' in page and 'data-filter-count' in page
    res = post(app, f"/clients/{cid}/board/stage", {"key": CANADA, "stage": "proposals", "reason": "",
                                                     "back": f"/clients/{cid}/board"})
    assert res.status == 303 and dict(res.headers)["Location"] == f"/clients/{cid}/board"
    page = get(app, f"/clients/{cid}/board").body_bytes.decode()
    assert "BM+: Not started" in page and 'class="board-card is-mine"' in page
    assert post(app, f"/clients/{cid}/board/stage", {"key": CANADA, "stage": "x"}).status == 400
    assert get(app, f"/clients/{cid + 1}/board").status == 404
    explorer = get(app, f"/clients/{cid}?bundle=Canada%7C2027-01-01").body_bytes.decode()
    assert f'href="/clients/{cid}/board"' in explorer and "✎ Proposals / Marketing" in explorer
    assert 'href="/board"' in explorer                                   # in the main menu
    assert "/static/board.css" in get(app, f"/clients/{cid}/board").body_bytes.decode()


def test_a_card_opens_its_bundle_over_the_board(app):
    """Martin, 06.11.2026: click a card → its bundle in a pop-up over the
    board; a click outside shrinks it back (board.js). The page inside is the
    client page itself, without the menus (base.html → .is-embedded)."""
    cid, _ = _book()
    page = get(app, f"/clients/{cid}/board").body_bytes.decode()
    assert 'id="board-pop"' in page and "data-pop-iframe" in page and "data-pop-close" in page
    assert f'href="/clients/{cid}?bundle=Poland%7C2027-01-01"' in page               # what the card opens
    inside = get(app, f"/clients/{cid}?bundle=Poland%7C2027-01-01").body_bytes.decode()
    assert 'classList.add("is-embedded")' in inside
    css = (Path(mart.__file__).parent / "web" / "static" / "mart.css").read_text(encoding="utf-8")
    assert ".is-embedded .sidebar, .is-embedded .bundle-nav { display: none; }" in css


def test_menu_folds_and_popovers_keep_in_view(app):
    """Martin, 06.11.2026: a toggle folds the main menu into icons
    (remembered); a pop-over never opens where the board (or the menu) cuts
    it off (mart.js `fit`)."""
    page = get(app, "/clients").body_bytes.decode()
    assert "data-menu-toggle" in page and 'class="nav-icon"' in page and "mart-menu-mini" in page
    assert page.count('class="nav-label"') == 8                          # 7 links + the toggle
    js = (Path(mart.__file__).parent / "web" / "static" / "mart.js").read_text(encoding="utf-8")
    assert "function fit(d)" in js and 'document.addEventListener("toggle"' in js


def test_the_bundle_header_moves_it_on_the_board(app):
    """Martin, 06.11.2026: the open card (the bundle page, also in the
    pop-up) changes the board stage too."""
    cid, _ = _book()
    url = f"/clients/{cid}?bundle=Canada%7C2027-01-01"
    page = get(app, url).body_bytes.decode()
    assert f'action="/clients/{cid}/board/stage"' in page and 'name="key" value="Canada|2027-01-01"' in page
    assert "Not started (BM+)" in page
    res = post(app, f"/clients/{cid}/board/stage", {"key": CANADA, "stage": "decision", "back": url})
    assert dict(res.headers)["Location"] == url
    assert "✎ Decision ▾" in get(app, url).body_bytes.decode()


def test_each_column_says_what_it_means(app):
    """Martin, 06.11.2026: the renewal pipeline's guideline, under each
    column's title and with the stage picked in a stage form."""
    cid, _ = _book()
    assert board.HINTS["decision"].startswith("The final proposals from the insurer(s) are in")
    page = get(app, f"/clients/{cid}/board").body_bytes.decode()
    assert page.count('<span class="info" tabindex="0" role="note"') == 7            # behind an ⓘ, not shown
    assert 'data-col-label="Decision"' in page
    assert "check that the policy documents are uploaded to BM+" in page
    assert 'data-hint="The renewal has not been kicked off."' in page and "data-hint-text" in page


def test_the_reason_shows_and_every_move_is_listed(app):
    """Martin, 06.11.2026: where is the "Why" shown? On the card while your
    stage applies, and behind the ✎ (also after BM+ caught up), and under the
    bundle header's stage form."""
    cid, _ = _book()
    board_service.set_stage(cid, CANADA, "proposals", "broker asked for quotes")
    board_service.set_stage(cid, CANADA, "decision", "quotes in, HR deciding")
    hist = cs.explorer(cid, bundle=CANADA)["selected"]["stage_history"]
    assert [(m["stage"], m["reason"]) for m in hist] == [("decision", "quotes in, HR deciding"),
                                                         ("proposals", "broker asked for quotes")]
    page = get(app, f"/clients/{cid}/board").body_bytes.decode()
    assert 'class="bc-why"' in page and "✎ quotes in, HR deciding" in page
    assert "Your moves on the board" in page and "broker asked for quotes" in page
    board_service.set_stage(cid, CANADA, "not_started", "")          # back to BM+'s: follows BM+
    page = get(app, f"/clients/{cid}/board").body_bytes.decode()
    assert 'class="bc-why"' not in page and "follows BM+ again" in page and "bc-mine is-past" in page
    header = get(app, f"/clients/{cid}?bundle=Canada%7C2027-01-01").body_bytes.decode()
    assert "Your moves on the board" in header and "quotes in, HR deciding" in header


def test_a_lone_renewals_overview_starts_closed(app):
    """Martin, 06.11.2026: a bundle with one renewal opens like any other,
    its renewal overview closed."""
    _commit(renewal_tracker([R(n=1, policy="Medical", renewal_date=JAN,
                               overview="01 Nov 2026: broker asked for claims data")],
                            cross_overview=True), "rt.xlsx")
    with connection() as conn:
        cid = conn.execute("SELECT id FROM clients").fetchone()["id"]
    page = get(app, f"/clients/{cid}?bundle=Poland%7C2027-01-01").body_bytes.decode()
    assert "broker asked for claims data" in page
    assert '<details class="rc-overview">' in page and '<details class="rc-overview" open' not in page
