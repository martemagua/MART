"""Task Tracker spec: every column name MART reads from it.

Checked against real exports of both flavours (03.11.2026, TRACKER_MAP.md
§4). The client-specific export has no Client / Product Group / Lines of
Coverage / Insurer / Escalation Manager Email / Original Due Date columns and
names a few differently; `aliases` lists those names. Every other column is
kept in the full JSON copy of the row.
"""

from __future__ import annotations

from mart.ingestion.sheet import Col

TRACKER = "task_tracker"
LABEL = "Task Tracker"
DETECT_SHEET = "Task Summary"
INFO_SHEET = "General Information"

COLUMNS: list[Col] = [
    Col("client_name", "Client"),                                  # cross-client only
    Col("country", "Task Country"),
    Col("product_group", "Product Group"),
    Col("lines_of_coverage", "Lines of Coverage"),
    Col("task_category", "Task Category"),
    Col("task_type", "Task Type"),
    Col("task_status", "Task Status", required=True),
    Col("task_ref", "Task ID", required=True),
    Col("expiring_policy_id", "Expiring Policy Unique ID"),
    Col("renewal_ref", "Renewal Unique ID"),
    Col("strategy", "Current Renewal Strategy"),
    Col("priority", "Local Task Priority"),
    Col("task_name", "Task Name"),
    Col("policy_id", "Policy ID"),                                 # = the Renewal Tracker's per-cycle id
    Col("policy_name", "Policy Name"),
    Col("policy_number", "Policy Number"),
    Col("review_date", "Policy Renewal/Review Date"),
    Col("insurer", "Insurer Name"),
    Col("benefit_owner", "Benefit Owner (expiring period)"),
    Col("local_analyst", "Local Analyst"),
    Col("review_rejected_date", "Global Peer Review Last Rejected Date",
        aliases=("Global Review Last Rejected Date",)),
    Col("review_rejected_count", "Global Peer Review No. of times rejected",
        aliases=("Global Review No. of times rejected",)),
    Col("review_approved_date", "Global Peer Review Approval Date",
        aliases=("Global Review Approval Date",)),
    Col("review_pending_days", "Global Review Pending days"),
    Col("review_approved_by", "Global Review approved by"),
    Col("opened_date", "Task Opened Date"),
    Col("start_date", "Task Start Date"),
    Col("original_due_date", "Original Task Due Date"),            # cross-client only
    Col("due_date", "Current Task Due Date", aliases=("Task Due Date",)),
    Col("due_changed_by", "Task Due Date Last Changed by"),
    Col("due_changed_count", "# of Times Due Date Changed"),
    Col("updated_date", "Task Last Updated Date"),
    Col("updated_by", "Task Last Updated By"),
    Col("completed_date", "Local Task Completed Date"),
    Col("completed_by", "Local Task Completed By"),
    Col("assignee", "Task Assignee"),
    Col("assignee_location", "Task Assignee Office Location"),
    Col("assignee_email", "Task Assignee Email"),
    Col("days_with_assignee", "Days with Task Assignee"),
    Col("assigned_date", "Task Assigned Date"),
    Col("delegated_to", "Task Delegated to"),
    Col("days_with_delegate", "Days with Delegate"),
    Col("escalation_manager", "Escalation Manager"),
    Col("days_to_due", "+/- Days to Current Due Date", aliases=("+/- Days to Due Date",)),
    Col("times_escalated", "# of Times Renewal Escalated"),
    Col("last_escalated_date", "Last Escalated Date"),
]

DATE_FIELDS = {"review_date", "review_rejected_date", "review_approved_date", "opened_date",
               "start_date", "original_due_date", "due_date", "updated_date", "completed_date",
               "assigned_date", "last_escalated_date"}
INT_FIELDS = {"review_rejected_count", "review_pending_days", "due_changed_count",
              "days_with_assignee", "days_with_delegate", "days_to_due", "times_escalated"}
PERSON_FIELDS = {"benefit_owner", "local_analyst", "assignee", "delegated_to",
                 "escalation_manager", "completed_by", "updated_by", "review_approved_by"}

# What counts as a CHANGE to a task: the workflow facts BOTH flavours carry,
# as MART reads them (dates as dates). The rest differs by flavour (columns
# only one has; people as e-mail in one, names in the other; counters that
# tick daily), so comparing it would flag every task when flavours alternate.
COMPARED = ("task_name", "task_category", "task_type", "task_status", "country", "policy_name",
            "policy_id", "expiring_policy_id", "review_date", "opened_date", "start_date",
            "due_date", "updated_date", "completed_date", "review_approved_date",
            "review_rejected_date", "assignee", "delegated_to")

# The only Task Category MART loads (Martin, 04.11.2026): the renewal's own
# tasks. Implementation and Contract tasks are not MART's concern.
RENEWAL_CATEGORY = "Renewal Workspace"

# Every BM+ renewal runs through these stages, in this order (Task Name).
STAGES = ("Renewal Strategy", "Proposals", "Update Policy")

# Upcoming renewal strategies that have no Proposals stage in BM+ (Martin,
# 04.11.2026): the incumbent's terms are fixed, so nothing is quoted.
NO_PROPOSALS_STRATEGIES = ("Incumbent with Rate Guarantee", "Non-expiring")

# Labels on the General Information sheet: the export's own filters. A task
# missing from a filtered export is not necessarily done.
EXPORT_FILTERS = ["Client Status", "Task Name", "Policy Name", "Date Type", "Date: From",
                  "Date: To", "Assignee", "Client", "Category", "Location", "Type", "Task Status"]
