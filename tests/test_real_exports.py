"""Checks against REAL-structure BM+ exports, run only where they exist.

Point MART_REAL_EXPORTS at a folder with exports (demo data is fine) to run
these. They are never in the repo: tracker files hold client data.
"""

import os
from pathlib import Path

import pytest

from mart.ingestion import renewal_tracker as rt

FOLDER = os.environ.get("MART_REAL_EXPORTS")
FILES = sorted(Path(FOLDER).glob("*Renewal*Tracker*.xlsx")) if FOLDER else []

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
