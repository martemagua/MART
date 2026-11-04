from datetime import datetime

import pytest

from mart.ingestion import task_tracker as tt
from mart.repository import tasks_repo
from mart.repository.db import connection
from mart.services import client_service as cs
from mart.services import renewal_service as rs
from mart.services import upload_service as us
from tests.conftest import get
from tests.fixtures import CLIENT, CROSS, R, T, hexid, renewal_tracker, task_tracker

UUID = "642f1b9b-289d-11ef-8147-6e8d75ec91b4"


def _tasks():
    return [
        T(n=1, task_name="Renewal Strategy", status="Completed",
          completed=datetime(2026, 10, 2, 14, 32, 42, 220000), approved=datetime(2026, 10, 3, 9, 15, 7)),
        T(n=1, task_name="Proposals", status="Global Review Pending", pending="12 day(s)", rejected=1),
        T(n=1, task_name="Appointment", category="Implementation", task_id=UUID, status="Not Started"),
        T(n=2, task_name="Renewal Strategy", status="Not Started, Past Due"),
        T(n=2, task_name="Proposals", status="Completed", policy_id=hexid(99, "8"),   # an older cycle
          review_date=datetime(2026, 1, 1, 1, 0)),
    ]


@pytest.mark.parametrize("flavour, header_row", [(CROSS, 4), (CLIENT, 5)])
def test_both_task_tracker_flavours(flavour, header_row):
    p = tt.parse(task_tracker(_tasks(), flavour))
    assert p.flavour == ("cross_client" if flavour == CROSS else "client") and p.header_row == header_row
    assert len(p.tasks) == 5 and p.skipped_no_id == 0
    f = next(t.fields for t in p.tasks
             if t.fields["task_name"] == "Renewal Strategy" and t.fields["task_status"] == "Completed")
    assert f["completed_date"] == "2026-10-02"        # a real timestamp keeps its own date
    assert f["review_date"] == "2027-01-01" and f["review_approved_date"] == "2026-10-03"
    assert f["policy_id"] == hexid(1, "8") and f["expiring_policy_id"] == hexid(1, "7")
    prop = next(t for t in p.tasks
                if t.fields["task_name"] == "Proposals" and t.fields["review_pending_days"])
    assert prop.fields["review_pending_days"] == 12 and prop.fields["review_rejected_count"] == 1
    assert any(t.key == UUID for t in p.tasks)        # implementation task ids are UUIDs


def test_task_status_states():
    assert tt.stage_state("Not Started, Past Due") == ("todo", True)
    assert tt.stage_state("Global Review Pending") == ("review", False)
    assert tt.stage_state("Completed") == ("done", False)


@pytest.fixture
def loaded(configured):
    uid = us.stage("rt.xlsx", renewal_tracker([R(n=1, policy="Medical"), R(n=2, policy="Life")]))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]})
    uid = us.stage("tasks.xlsx", task_tracker(_tasks()))
    view = us.preview(uid)
    assert view["adapter"].tracker == "task_tracker" and view["clients"][0]["is_mine"] == 1
    summary = us.commit(uid, {c["key"] for c in view["clients"]})
    # not loaded: the older cycle (no renewal here) and the implementation task
    assert summary["new"] == 3 and summary["skipped"] == 2
    with connection() as conn:
        cid = conn.execute("SELECT id FROM clients WHERE name = 'Acme Group'").fetchone()["id"]
        rids = {r["policy_name"]: r["id"] for r in conn.execute(
            "SELECT id, policy_name FROM renewals WHERE client_id = ?", (cid,))}
    return cid, rids


def test_tasks_link_to_their_renewal_cycle_only(loaded):
    cid, rids = loaded
    d = rs.detail(cid, rids["Medical"])
    st = {s["name"]: s for s in d["stages"]}
    assert st["Renewal Strategy"]["state"] == "done"
    assert st["Renewal Strategy"]["review_approved_date"] == "2026-10-03"
    assert st["Proposals"]["state"] == "review" and st["Proposals"]["review_pending_days"] == 12
    assert st["Update Policy"]["state"] == "missing"
    assert d["other_tasks"] == []                      # implementation tasks are not MART's
    life = {s["name"]: s for s in rs.detail(cid, rids["Life"])["stages"]}
    assert life["Renewal Strategy"]["past_due"] is True
    assert life["Proposals"]["state"] == "missing"     # the older cycle's task is not this one's


def test_bundle_cards_carry_stage_dots_and_renewal_pages_render(loaded, app):
    cid, rids = loaded
    v = cs.explorer(cid)
    assert v["has_task_data"] and all(len(r["stages"]) == 3 for r in v["selected"]["renewals"])
    page = get(app, f"/clients/{cid}").body_bytes.decode()
    assert f'/clients/{cid}/renewals/{rids["Medical"]}' in page and "sdot-done" in page
    rp = get(app, f"/clients/{cid}/renewals/{rids['Medical']}").body_bytes.decode()
    for text in ("BM+ stages", "Peer review pending", "peer review ✓ 03.10.2026", "Proposals",
                 "Everything BM+ exported"):
        assert text in rp, text
    assert get(app, f"/clients/{cid}/renewals/99999").status == 404


def test_same_task_export_again_is_unchanged(loaded):
    uid = us.stage("tasks.xlsx", task_tracker(_tasks(), report_date="04 Nov 2026"))
    view = us.preview(uid)
    c = view["clients"][0]
    assert (c["new"], c["changed"], c["unchanged"], c["skipped"]) == (0, 0, 3, 2)


def test_flavours_alternating_are_not_changes_and_keep_their_extra_columns(loaded):
    """The client export lacks some columns and names people differently;
    loading it after the cross-client one changes nothing."""
    cid, rids = loaded                                   # the cross-client export is in
    uid = us.stage("tasks-acme.xlsx", task_tracker(_tasks(), CLIENT, report_date="04 Nov 2026"))
    c = us.preview(uid)["clients"][0]
    assert (c["new"], c["changed"], c["unchanged"], c["skipped"]) == (0, 0, 3, 2)
    us.commit(uid, {c["key"]})
    with connection() as conn:
        tasks = {t["task_name"] + str(t["review_date"]): t for t in tasks_repo.for_client(conn, cid)}
    strat = tasks["Renewal Strategy2027-01-01"]
    assert strat["fields"]["original_due_date"] == "2026-11-20"   # only the cross-client one has it


@pytest.mark.parametrize("strategy", ["Incumbent with Rate Guarantee", "Non-expiring"])
def test_strategies_without_a_proposals_stage(configured, app, strategy):
    """Martin, 04.11.2026: these strategies have no Proposals stage in BM+."""
    uid = us.stage("rt.xlsx", renewal_tracker([R(n=1, policy="Medical", strategy=strategy),
                                               R(n=2, policy="Life", strategy="Remarketing")]))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]})
    with connection() as conn:
        rows = {r["policy_name"]: (r["client_id"], r["id"])
                for r in conn.execute("SELECT id, client_id, policy_name FROM renewals")}
    uid = us.stage("t.xlsx", task_tracker([T(n=1, task_name="Renewal Strategy")]))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]})
    med = {s["name"]: s for s in rs.detail(*rows["Medical"])["stages"]}
    assert med["Proposals"]["state"] == "skipped" and strategy in med["Proposals"]["label"]
    assert med["Update Policy"]["state"] == "missing"
    life = {s["name"]: s for s in rs.detail(*rows["Life"])["stages"]}
    assert life["Proposals"]["state"] == "missing"
    page = get(app, "/clients/{}/renewals/{}".format(*rows["Medical"])).body_bytes.decode()
    assert f"not needed ({strategy})" in page and "stage-skipped" in page
    # if BM+ does create one anyway, it is shown as it is
    uid = us.stage("t2.xlsx", task_tracker([T(n=1, task_name="Renewal Strategy"),
                                           T(n=1, task_name="Proposals", status="In Progress")],
                                          report_date="05 Nov 2026"))
    us.commit(uid, {c["key"] for c in us.preview(uid)["clients"]})
    med = {s["name"]: s for s in rs.detail(*rows["Medical"])["stages"]}
    assert med["Proposals"]["state"] == "doing"
