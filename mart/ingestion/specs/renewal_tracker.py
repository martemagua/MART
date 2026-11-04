"""Renewal Tracker spec: every column name MART reads from it.

Checked against real exports of both flavours (03.11.2026, TRACKER_MAP.md
§5). Fields listed here become real columns in MART; every OTHER column is
still kept, in the full JSON copy of the row (see sheet.SheetData.full_row).
"""

from __future__ import annotations

from mart.ingestion.sheet import Col

TRACKER = "renewal_tracker"
LABEL = "Renewal Tracker"
DETECT_SHEET = "Renewal Overview"
INFO_SHEET = "General Information"

# Sheets of OTHER trackers, so a wrong file gets a helpful message.
OTHER_TRACKERS = {
    "Task Summary": "a Task Tracker (its upload comes in M1 · day 4)",
    "Benefit Details": "a Benefit Tracker (its upload comes in v2)",
}

OVERVIEW: list[Col] = [
    Col("client_name", "Client Name"),                       # cross-client flavour only
    Col("division", "Division"),
    Col("region", "Region"),
    Col("sub_region", "Sub Region"),
    Col("country", "Country"),
    Col("entity", "Entity"),
    Col("policy_ref", "Policy Unique ID*", required=True),
    Col("policy_name", "Policy Name", required=True),
    Col("n_locs", "Number of Lines of Coverage"),
    Col("policy_description", "Policy Description"),
    Col("bundled", "Bundled Policy?*"),
    Col("start_date", "Start Date"),
    Col("end_date", "End Date"),
    Col("rate_guarantee_end", "Rate Guarantee End Date"),
    Col("multi_year", "Multi-year Policy?"),
    Col("kickoff_timing", "Next Renewal (Annual Review) Kickoff Timing"),
    Col("kickoff_date", "Next Renewal (Annual Review) Kickoff Date"),
    Col("last_remarketing", "Year of Last Remarketing"),
    Col("benefit_owner", "Benefit Owner"),
    Col("benefit_owner_email", "Email", after="Benefit Owner"),
    Col("local_analyst", "Local Analyst"),
    Col("local_analyst_email", "Email", after="Local Analyst"),
    Col("lines_of_coverage", "Line of Coverage", section="LOC Information (expiring"),
    Col("lines_upcoming", "Line of Coverage", section="LOC Information (upcoming"),
    Col("insurer", "Insurer", section="Premium Information (Expiring"),
    Col("insurer_upcoming", "Insurer", section="Premium Information (Upcoming"),
    Col("renewal_ref", "Renewal Unique ID*", required=True),
    Col("renewal_date", "Annual Renewal/Review Date", required=True),
    Col("local_meeting_date", "Date of Local Meeting"),
    Col("upcoming_strategy", "Upcoming Renewal Strategy"),
    Col("workflow_status", "Renewal Workflow Status"),
    Col("pdc_considered", "Plan Design Changes Considered?"),
    Col("pdc_comments", "Plan Design Comments"),
    Col("expected_rate_change", "Expected Change in Premium Rate"),
    Col("client_approval_date", "Client Approval Date"),
    Col("overview_all", "Renewal Overview (all)"),
    Col("overview_client_ready", "Renewal Overview (client ready)"),
    Col("renewal_feed", "Renewal Feed"),                     # cross-client: the overview text lives here
]

# The three detail sheets are kept whole (full_row); MART only needs to know
# which renewal each row belongs to.
_DETAIL_IDS: list[Col] = [
    Col("client_name", "Client Name"),
    Col("policy_ref", "Policy Unique ID*", required=True),
    Col("renewal_ref", "Renewal Unique ID*", required=True),
    Col("policy_name", "Policy Name"),
]

DETAIL_SHEETS: dict[str, tuple[str, list[Col]]] = {
    # key        sheet name          columns
    "strategy": ("Renewal Strategy", _DETAIL_IDS),
    "proposals": ("Proposals", _DETAIL_IDS),
    "savings": ("Savings", _DETAIL_IDS),
}

# Identity cells: written differently per flavour (URL vs bare id, a Client
# Name column only in the cross-client export). Covered by the renewal key,
# so they never count as a change.
IDENTITY_HEADERS = ("Client Name", "Policy Unique ID*", "Renewal Unique ID*")

# The three text streams. Which ones an export CARRIES is decided from the
# data, not from the flavour: a stream is carried when at least one renewal in
# the export has text in it (renewal_tracker.carried_streams). A stream the
# whole export leaves empty is not carried, and the stored text is kept.
# Why: in the demo environment the cross-client export left both overview
# columns empty (and filled only the Renewal Feed, which holds BM+ system
# messages, not the overview), while Martin's REAL cross-client exports carry
# a full overview. A per-flavour rule would have thrown that away.
TEXT_STREAMS = {
    "overview_all": "Renewal Overview (all)",
    "overview_client_ready": "Renewal Overview (client ready)",
    "renewal_feed": "Renewal Feed",
}

DATE_FIELDS = {"start_date", "end_date", "rate_guarantee_end", "kickoff_date",
               "renewal_date", "local_meeting_date", "client_approval_date"}
PERSON_FIELDS = {"benefit_owner", "local_analyst"}

# Labels on the General Information sheet worth showing in the preview.
EXPORT_FILTERS = ["Client Status", "In Progress & Pending Kickoff",
                  "Completed within Last 6 Months", "Upcoming within Next 6 Months"]
