from datetime import datetime

import pytest

from mart.ingestion import renewal_tracker as rt
from mart.ingestion import values as v
from mart.ingestion.ids import renewal_tracker_ids
from tests.fixtures import CLIENT, CROSS, R, hexid, renewal_tracker


# -- values ---------------------------------------------------------------------
@pytest.mark.parametrize("stamp, expected", [
    (datetime(2027, 1, 1, 0, 0), "2027-01-01"),
    (datetime(2027, 1, 1, 1, 0), "2027-01-01"),    # Europe
    (datetime(2027, 1, 1, 5, 30), "2027-01-01"),   # India
    (datetime(2026, 12, 31, 19, 0), "2027-01-01"),  # the Americas: the evening before
    (datetime(2026, 12, 31, 18, 30), "2027-01-01"),
])
def test_dates_round_to_the_nearest_midnight(stamp, expected):
    assert v.to_date(stamp) == expected


def test_text_values():
    assert v.to_date("Non Expiring Policy") is None and v.is_non_expiring("Non Expiring Policy")
    assert v.person_name("Ann Lee Ann Lee") == "Ann Lee"
    assert v.person_name("Ann Ann Lee") == "Ann Ann Lee"
    assert v.product_groups("Healthcare - Medical, Life - Basic Term Life\nHealthcare - Dental") \
        == ["Healthcare", "Life"]
    assert v.client_key("SPG GmbH & Co. KG") == v.client_key("spg gmbh and co kg")


def test_ids_from_both_flavours():
    stable, cycle, robj, cid = hexid(1, "7"), hexid(1, "8"), hexid(1, "9"), hexid(1, "5")
    cross = renewal_tracker_ids(f"https://x/client/{cid}/policies/{cycle};{stable}",
                                f"https://x/client/{cid}/renewals/{robj}/{cycle}")
    client = renewal_tracker_ids(stable, cycle)
    assert (cross.cycle_id, cross.expiring_policy_id, cross.bm_renewal_id, cross.bm_client_id) \
        == (cycle, stable, robj, cid)
    assert (client.cycle_id, client.expiring_policy_id) == (cycle, stable)
    broken = renewal_tracker_ids(f"https://x/client/undefined/policies/{cycle};undefined", None)
    assert broken.cycle_id == cycle and broken.expiring_policy_id is None


# -- whole files ------------------------------------------------------------------------
def _three():
    return [
        R(n=1, policy="Medical", proposals=[("Meridian Health", 120.0, 110.0), ("Atlas", 130.0, 115.0)],
          final_terms_date=datetime(2026, 11, 15)),
        R(n=2, policy="Life", country="Spain", entity="Acme Iberia", insurer="Atlas",
          insurer_upcoming="Atlas Re"),
        R(n=3, client="Globex", country="Brazil", entity="Globex BR", policy="Dental"),
    ]


def test_cross_client_export():
    p = rt.parse(renewal_tracker(_three(), CROSS))
    assert p.flavour == rt.CROSS_CLIENT and p.report_date == "2026-11-03"
    assert p.sheets_read == {"Renewal Overview": 5, "Renewal Strategy": 6, "Proposals": 6, "Savings": 6}
    assert len(p.renewals) == 3 and {r.client_name for r in p.renewals} == {"Acme Group", "Globex"}
    med = next(r for r in p.renewals if r.fields["policy_name"] == "Medical")
    assert med.cycle_key == hexid(1, "8") and med.ids["expiring_policy_id"] == hexid(1, "7")
    f = med.fields
    assert f["renewal_date"] == "2027-01-01" and f["benefit_owner"] == "Ann Lee"
    assert f["benefit_owner_email"] == "ann@example.com" and f["local_analyst_email"] == "bo@example.com"
    assert f["product_groups"] == ["Healthcare"]
    assert len(med.details["proposals"]) == 2 and len(med.details["strategy"]) == 1
    life = next(r for r in p.renewals if r.fields["policy_name"] == "Life")
    assert life.fields["insurer"] == "Atlas" and life.fields["insurer_upcoming"] == "Atlas Re"
    # every Overview cell is kept, keyed by section and header
    key = "Premium Information (Expiring Policy Period) › Annual Premium (reporting currency)"
    assert med.bm[key] == 1000


def test_both_flavours_give_the_same_keys():
    acme = [r for r in _three() if r.client == "Acme Group"]
    cross = {r.cycle_key for r in rt.parse(renewal_tracker(_three(), CROSS)).renewals
             if r.client_name == "Acme Group"}
    single = rt.parse(renewal_tracker(acme, CLIENT))
    assert single.flavour == rt.CLIENT
    assert single.sheets_read["Proposals"] == 5          # header row moved, still found
    assert {r.cycle_key for r in single.renewals} == cross
    assert all(r.client_name == "Acme Group" for r in single.renewals)


def test_rows_without_client_are_skipped_and_counted():
    noise = [None, "Sales", "EMEA", "Chile", None, "https://x/client/undefined/policies/"
             + hexid(9, "8") + ";undefined", "Orphan"]
    p = rt.parse(renewal_tracker(_three(), CROSS, missing_rows=[noise]))
    assert p.skipped_no_client == 1 and len(p.renewals) == 3


def test_renewals_without_ids_are_never_merged_by_mistake():
    twins = [R(n=5, stable=None, cycle=None, insurer="A"), R(n=6, stable=None, cycle=None, insurer="B"),
             R(n=7, stable=None, cycle=None, insurer="B")]   # 6 and 7: exact duplicate rows
    p = rt.parse(renewal_tracker(twins, CROSS))
    assert p.duplicates_merged == 1
    keys = sorted(r.cycle_key for r in p.renewals)
    assert len(keys) == 2 and keys[0].startswith("name:") and keys[1] == keys[0] + "#2"
    assert p.no_id_count == 2


def test_non_expiring_policies():
    p = rt.parse(renewal_tracker([R(end_date="Non Expiring Policy")], CROSS))
    f = p.renewals[0].fields
    assert f["end_date"] is None and f["non_expiring"] is True


@pytest.mark.parametrize("data, message", [
    (renewal_tracker([], task_tracker=True), "Task Tracker"),
    (b"this is not a workbook", "can't be read"),
])
def test_wrong_files_get_a_plain_message(data, message):
    with pytest.raises(rt.NotThisTracker, match=message):
        rt.parse(data)


def test_insurer_not_found_gives_way_to_the_provider():
    """Martin, 04.11.2026: when BM+ says "Insurer Not Found", the Provider
    column names who it is; without one, BM+'s words stay."""
    from mart.ingestion import renewal_tracker as rt
    from tests.fixtures import R, renewal_tracker
    p = rt.parse(renewal_tracker([
        R(n=1, policy="A", insurer="Insurer Not Found", provider="Local Mutual Co.",
          insurer_upcoming="Insurer Not Found", provider_upcoming="Local Mutual Co."),
        R(n=2, policy="B", insurer="Insurer Not Found"),
        R(n=3, policy="C", insurer="PZU", provider="ignored when the insurer is known")]))
    got = {r.fields["policy_name"]: (r.fields["insurer"], r.fields["insurer_upcoming"]) for r in p.renewals}
    assert got == {"A": ("Local Mutual Co.", "Local Mutual Co."), "B": ("Insurer Not Found", None),
                   "C": ("PZU", None)}
