"""Checks against REAL-structure BM+ exports, run only where they exist.

Point MART_REAL_EXPORTS at a folder with exports (demo data is fine) to run
these. They are never in the repo: tracker files hold client data.
"""

import os
from pathlib import Path

import pytest

from mart.ingestion import renewal_tracker as rt
from mart.ingestion import task_tracker as tt

FOLDER = os.environ.get("MART_REAL_EXPORTS")
FILES = sorted(Path(FOLDER).glob("*Renewal*Tracker*.xlsx")) if FOLDER else []
TASK_FILES = sorted(Path(FOLDER).glob("*Task*Tracker*.xlsx")) if FOLDER else []

pytestmark = pytest.mark.skipif(not FILES, reason="no real exports configured (MART_REAL_EXPORTS)")


@pytest.mark.parametrize("path", FILES, ids=[p.name for p in FILES])
def test_real_renewal_tracker_reads_completely(path):
    p = rt.parse(path.read_bytes())
    assert p.renewals and not p.sheets_missing
    assert set(p.sheets_read) == {"Renewal Overview", "Renewal Strategy", "Proposals", "Savings"}
    assert p.unmatched_detail_rows == 0
    assert all(r.client_name and r.fields.get("policy_name") for r in p.renewals)
    assert len({r.cycle_key for r in p.renewals}) == len(p.renewals)


def test_cross_and_client_exports_agree_on_keys():
    parsed = [rt.parse(f.read_bytes()) for f in FILES]
    cross = [p for p in parsed if p.flavour == rt.CROSS_CLIENT]
    single = [p for p in parsed if p.flavour == rt.CLIENT]
    if not cross or not single:
        pytest.skip("needs one export of each flavour")
    for s in single:
        client = s.renewals[0].client_key
        with_ids = {r.cycle_key for r in s.renewals if not r.id_missing}
        in_cross = {r.cycle_key for p in cross for r in p.renewals if r.client_key == client}
        assert with_ids <= in_cross


@pytest.mark.parametrize("path", TASK_FILES, ids=[p.name for p in TASK_FILES])
def test_real_task_tracker_reads_completely(path):
    p = tt.parse(path.read_bytes())
    assert p.tasks and p.skipped_no_id == 0
    assert all(t.client_name and t.fields.get("task_name") and t.fields.get("task_status") for t in p.tasks)
    assert len({t.key for t in p.tasks}) == len(p.tasks)


def test_real_tasks_find_their_renewal():
    """Task Tracker `Policy ID` = the Renewal Tracker's per-cycle id: most of a
    client's renewals (single-client export) find their tasks."""
    from mart.services.renewal_service import link_tasks
    tasks = [{"task_key": t.key, "client": t.client_key, **t.fields}
             for f in TASK_FILES for t in tt.parse(f.read_bytes()).tasks]
    singles = [p for p in (rt.parse(f.read_bytes()) for f in FILES) if p.flavour == rt.CLIENT]
    singles = [p for p in singles if any(t["client"] == p.renewals[0].client_key for t in tasks)]
    if not singles:
        pytest.skip("needs a single-client Renewal Tracker and Task Tracker of the same client")
    for p in singles:
        renewals = [{"id": i, "cycle_id": r.ids.get("cycle_id"), "renewal_date": r.fields.get("renewal_date"),
                     "expiring_policy_id": r.ids.get("expiring_policy_id")} for i, r in enumerate(p.renewals)]
        linked = link_tasks(renewals, [t for t in tasks if t["client"] == p.renewals[0].client_key])
        assert sum(1 for v in linked.values() if v) > len(renewals) // 2


CAPABILITY_FILES = sorted(Path(FOLDER).glob("*Capability*.xlsx")) if FOLDER else []


@pytest.mark.parametrize("path", CAPABILITY_FILES, ids=[p.name for p in CAPABILITY_FILES])
def test_real_capability_database_reads_completely(path):
    from mart.ingestion import countries
    from mart.ingestion import insurer_capability as ic

    p = ic.parse(path.read_bytes())
    assert p.sheet == "Database" and p.skipped == 0 and len(p.networks) >= 5
    assert all(r["network"] and r["country"] and r["line"] for r in p.rows)
    assert len({r["line"] for r in p.rows}) <= 8                        # one spelling per line of risk
    # every place is a country MART knows, except the few that aren't countries
    unknown = {r["country"] for r in p.rows if not countries.code(r["country"])}
    assert unknown <= {"Channel Islands", "International", "Offshore Programs (TCN / Expat)"}, unknown
