from datetime import date

from mart.ingestion import overview as ov

ALL = """Standing note: client prefers email.
14 Oct 2026:
Broker confirmed quotes are expected by 15 Nov 2026: three insurers invited.
Internal: budget is tight.

02 Sep 2026: (not client ready)
Discussions ongoing, strategy may change.

20 Aug 2026:
Kick-off held with local HR."""

CLIENT_READY = """14 Oct 2026:
Broker confirmed quotes are expected by 15 Nov 2026: three insurers invited.

20 Aug 2026:
kick-off held   with local HR."""


def test_entries_are_split_on_dated_headers_only():
    es = ov.entries(ALL)
    assert [e["date"] for e in es] == ["2026-10-14", "2026-09-02", "2026-08-20"]  # "15 Nov 2026:" in a body?
    assert ov.preamble(ALL) == "Standing note: client prefers email."
    assert ov.latest_date(ALL) == "2026-10-14"


def test_timeline_marks_what_client_ready_is_missing():
    t = ov.timeline(ALL, CLIENT_READY, today=date(2026, 11, 4))
    assert [e["date"] for e in t["entries"]] == ["2026-10-14", "2026-09-02", "2026-08-20"]
    oct_, sep, aug = t["entries"]
    assert oct_["internal_only"] and [b["internal"] for b in oct_["body"]] == [False, True]
    assert sep["internal_only"] and sep["marked_not_ready"]       # BM+'s own marker
    assert sep["body"][0]["text"] == "Discussions ongoing, strategy may change."
    assert not aug["internal_only"]                             # spacing and capitals ignored
    assert t["age_days"] == 21 and t["internal_entries"] == 2


def test_flags_for_lists():
    assert ov.flag(None, None)["state"] == "empty"
    assert ov.flag(ALL, None)["state"] == "no_cr"
    assert ov.flag(ALL, CLIENT_READY)["state"] == "gaps"
    assert ov.flag(CLIENT_READY, CLIENT_READY)["state"] == "ok"
    only_cr = ov.timeline(None, CLIENT_READY)
    assert only_cr["entries"] and not any(e["internal_only"] for e in only_cr["entries"])
