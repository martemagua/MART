"""M2 day 1: overview freshness (Martin, 04.11.2026; QUESTIONS E1–E3).

Amber after 7 days without a new overview entry, red after 14, by the date
written on the newest entry, across the full AND the client-ready overview;
entries dated within the last N days are new. A bundle shows its quietest
renewal.
"""

from datetime import date, datetime, timedelta

import pytest

from mart.repository.db import connection
from mart.services import client_service as cs
from mart.services import freshness, preferences
from mart.services import upload_service as us
from tests.conftest import get
from tests.fixtures import R, renewal_tracker

pytestmark = pytest.mark.usefixtures("configured")

TODAY = date(2026, 11, 4)


def _ov(*days: str) -> str:
    return "\n\n".join(f"{d}:\nUpdate." for d in days)


def _load(rows) -> int:
    uid = us.stage("rt.xlsx", renewal_tracker(rows, report_date="04 Nov 2026", cross_overview=True))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]}, allow_older=True)
    with connection() as conn:
        return conn.execute("SELECT id FROM clients").fetchone()["id"]


def test_states_by_age_and_limits():
    lim = freshness.limits(TODAY)
    assert (lim["amber"], lim["red"], lim["new_days"], lim["new_since"]) == (7, 14, 7, "2026-10-28")
    assert freshness.of("2026-10-30", lim)["state"] == "fresh"           # 5 days
    assert freshness.of("2026-10-28", lim)["state"] == "amber"           # 7 days
    assert freshness.of("2026-10-21", lim) == {"state": "red", "age_days": 14, "latest": "2026-10-21",
                                               "label": "stale"}
    assert freshness.of(None, lim)["state"] == "none"
    # the worst renewal speaks for its bundle; an empty overview never hides an old one
    items = [freshness.of(d, lim) for d in ("2026-10-30", None, "2026-10-25")]
    assert freshness.worst(items)["state"] == "amber" and freshness.worst([])["state"] == "none"
    # red is never earlier than amber, whatever Settings say
    preferences.save({"overview_amber_days": "20", "overview_red_days": "10"})
    assert freshness.limits(TODAY)["red"] == 20


def test_client_ready_entries_count_too():
    """E3: 'client ready' is a toggle that is sometimes forgotten."""
    f = {"overview_all": _ov("01 Oct 2026"), "overview_client_ready": _ov("30 Oct 2026")}
    assert freshness.latest(f) == "2026-10-30"


def _d(days_ago: int) -> str:
    """An overview header N days before today (the pages use the real date)."""
    return (date.today() - timedelta(days=days_ago)).strftime("%d %b %Y")


def test_bundles_cards_and_panel_show_it(app):
    jan = datetime(2027, 1, 1, 1, 0)
    cid = _load([R(n=1, policy="Medical", renewal_date=jan, overview=_ov(_d(2), _d(60))),
                 R(n=2, policy="Life", renewal_date=jan, overview=_ov(_d(15))),
                 R(n=3, policy="Dental", country="Spain", renewal_date=jan, overview=_ov(_d(6)))])
    v = cs.explorer(cid, bundle=cs.bundle_key("Poland", "2027-01-01"))
    states = {r["policy_name"]: r["freshness"]["state"] for r in v["selected"]["renewals"]}
    assert states == {"Medical": "fresh", "Life": "red"} and v["selected"]["freshness"]["state"] == "red"
    spain = next(b for g in v["groups"].values() for b in g if b["country"] == "Spain")
    assert spain["freshness"]["state"] == "fresh"
    page = get(app, f"/clients/{cid}?bundle=Poland%7C2027-01-01").body_bytes.decode()
    assert ">15 d</span>" in page                                          # side panel: the bundle
    assert ">stale · 15 days</span>" in page                               # Life's card
    with connection() as conn:
        med = conn.execute("SELECT id FROM renewals WHERE policy_name = 'Medical'").fetchone()["id"]
    panel = get(app, f"/clients/{cid}/renewals/{med}").body_bytes.decode()
    assert panel.count('<span class="pill pill-new"') == 1                 # 2 days old: new; 60: not


def test_three_new_time_limits_in_settings(app):
    page = get(app, "/settings").body_bytes.decode()
    for name in ("overview_amber_days", "overview_red_days", "overview_new_days"):
        assert f'name="{name}"' in page
