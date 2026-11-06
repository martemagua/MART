"""Insurer Capability Database spec ("All Networks" export, Martin
06.11.2026): every column name MART reads from it.

One sheet matters, "Database": one row per multinational NETWORK × country
× local partner INSURER × line of risk, with what that partner can do there
(fully insured, multinational pool, global insurance program, captive, and
the quota shares). Other sheets a version may carry are ignored. The
network column has no proper header in the export (a stray number sits in
it): it is the column just before "Insurer name". "None" as the insurer =
the network has no partner in that country.
"""

from __future__ import annotations

TRACKER = "insurer_capability"
LABEL = "Insurer Capability Database"
DETECT_SHEET = "Database"

# header text (as BM+ writes it, compared ignoring case and spacing) -> field
COLUMNS = {
    "Region": "region",
    "Country of cover issuance": "country",
    "Insurer name": "insurer",
    "Line of risk": "line",
    "Is cover offered locally on a fully insured basis?": "fully_insured",
    "Can cover be included within a multinational pool?": "pool",
    "What share of the cover can be included within a multinational pool (quota share)?": "pool_share",
    "Can cover be included within a global insurance program (global underwriting approach)?": "gip",
    "What share of the cover can be included within a global insurance program (quota share)?": "gip_share",
    "Can cover be ceded to a captive?": "captive",
    "What is the maximum quota share that the captive can hold?": "captive_share",
    "Comments": "comments",
}
REQUIRED = ("country", "insurer", "line")
# a header that names the network column, in versions that give it one
NETWORK_HEADERS = ("Network", "Multinational Network", "International Network", "Network name")
YES_NO = ("fully_insured", "pool", "gip", "captive")
SHARES = ("pool_share", "gip_share", "captive_share")
NO_PARTNER = ("none", "n/a", "-", "")
