"""Synthetic BM+ exports, built in code to the REAL layout (TRACKER_MAP.md).

No client data and no .xlsx files in the repo: every test builds the
workbook it needs. The builders copy the quirks that matter: header rows
that move between sheets and flavours, merged section labels, ids bare in
one flavour and inside URLs in the other, repeated column names, dates with
a stray local time.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import openpyxl

CROSS, CLIENT = "cross", "client"


def hexid(n: int, prefix: str = "6") -> str:
    return (prefix + f"{n:023x}")[:24]


@dataclass
class R:
    """One renewal as the test wants it in the export."""
    client: str = "Acme Group"
    country: str = "Poland"
    entity: str = "Acme Polska"
    policy: str = "Medical"
    n: int = 1                       # makes the ids
    stable: str | None = "auto"
    cycle: str | None = "auto"
    renewal_date: datetime = datetime(2027, 1, 1, 1, 0)   # 01:00 like a CET export
    status: str = "In Progress"
    strategy: str = "TBC"
    policy_number: str | None = None      # on the detail sheets only, as in BM+
    insurer: str = "Meridian Health"
    insurer_upcoming: str | None = None
    provider: str | None = None           # "Provider" beside "Insurer" (BM+ fills it rarely)
    provider_upcoming: str | None = None
    loc: str = "Healthcare - Medical"
    owner: str = "Ann Lee Ann Lee"
    owner_email: str = "ann@example.com"
    analyst: str | None = "Bo Chen"
    analyst_email: str | None = "bo@example.com"
    end_date: object = datetime(2026, 12, 31)
    proposals: list[tuple[str, float, float]] = field(default_factory=list)
    final_terms_date: datetime | None = None
    pdc_types: str | None = None     # Strategy sheet: types of plan design changes
    pdc_reasons: str | None = None
    overview: str | None = None      # "Renewal Overview (all)"
    overview_cr: str | None = "same"  # "(client ready)"; "same" = as overview
    feed: str | None = None          # "Renewal Feed"

    def ids(self) -> tuple[str | None, str | None, str]:
        stable = hexid(self.n, "7") if self.stable == "auto" else self.stable
        cycle = hexid(self.n, "8") if self.cycle == "auto" else self.cycle
        return stable, cycle, hexid(self.n, "9")


CLIENT_ID = hexid(1, "5")

# (section, header) of the Overview sheet: a subset of the real ~90 columns,
# including the repeats MART must tell apart.
OVERVIEW = [
    ("Policy Information (Expiring Policy Period)", h) for h in (
        "Division", "Region", "Country", "Entity", "Policy Unique ID*", "Policy Name",
        "Number of Lines of Coverage", "Start Date", "End Date", "Year of Last Remarketing",
        "Benefit Owner", "Email", "Local Analyst", "Email")
] + [
    ("LOC Information (expiring Policy)", "Line of Coverage"),
    ("LOC Information (upcoming Policy)", "Line of Coverage"),
    ("Premium Information (Expiring Policy Period)", "Insurer"),
    ("Premium Information (Expiring Policy Period)", "Provider"),
    ("Premium Information (Expiring Policy Period)", "Annual Premium_x000D_ (reporting currency)"),
    ("Premium Information (Upcoming Policy Period)", "Insurer"),
    ("Premium Information (Upcoming Policy Period)", "Provider"),
    (" Renewal Information", "Renewal Unique ID*"),
    (" Renewal Information", "Annual Renewal/Review Date"),
    (" Renewal Information", "Upcoming Renewal Strategy"),
    (" Renewal Information", "Renewal Workflow Status"),
    (" Renewal Information", "Renewal Overview (all)"),
    (" Renewal Information", "Renewal Overview (client ready)"),
    (" Renewal Information", "Renewal Feed"),
]


def _policy_cell(r: R, flavour: str) -> str | None:
    stable, cycle, _ = r.ids()
    if flavour == CLIENT:
        return stable
    if stable is None and cycle is None:
        return None
    return (f"https://bm.example/client/{CLIENT_ID}/policies/"
            f"{cycle or 'undefined'};{stable or 'undefined'}")


def _renewal_cell(r: R, flavour: str) -> str | None:
    _, cycle, robj = r.ids()
    if cycle is None:
        return None
    if flavour == CLIENT:
        return cycle
    return f"https://bm.example/client/{CLIENT_ID}/renewals/{robj}/{cycle}"


def _overview_values(r: R, flavour: str, cross_overview: bool = False) -> list:
    # The demo environment's cross-client export left the overview empty and
    # filled only the feed; real cross-client exports carry the overview too.
    has_ov = flavour == CLIENT or cross_overview
    cr = r.overview if r.overview_cr == "same" else r.overview_cr
    return [
        "Sales", "EMEA", r.country, r.entity, _policy_cell(r, flavour), r.policy, 1,
        datetime(2026, 1, 1), r.end_date, "Unknown / New Policy", r.owner, r.owner_email,
        r.analyst, r.analyst_email, r.loc, r.loc, r.insurer, r.provider, 1000, r.insurer_upcoming,
        r.provider_upcoming,
        _renewal_cell(r, flavour), r.renewal_date, r.strategy, r.status,
        r.overview if has_ov else None,
        cr if has_ov else None,
        r.feed if flavour == CROSS else None,               # single-client: left empty by BM+
    ]


def _write_table(ws, flavour: str, header_row: int, columns: list[tuple[str, str]],
                 rows: list[list], client: str, title: str, super_label: str | None = None) -> None:
    cols = ([("Policy Information (Expiring Policy Period)", "Client Name")] if flavour == CROSS
            else []) + columns
    if flavour == CLIENT:
        ws.cell(1, 1, client)
        ws.cell(2, 1, title)
    else:
        ws.cell(1, 1, title)
    ws.cell(header_row - 2 if super_label else 2, 1 if not super_label else 1,
            "* Indicates special handling has been applied to the field. ")
    if super_label:
        ws.cell(header_row - 2, len(cols), super_label)
    last = None
    for i, (section, header) in enumerate(cols, start=1):
        if section != last:                      # merged labels: value only in the first cell
            ws.cell(header_row - 1, i, section)
            last = section
        ws.cell(header_row, i, header)
    for j, values in enumerate(rows, start=header_row + 1):
        cells = ([client] if flavour == CROSS else []) + values
        for i, value in enumerate(cells, start=1):
            if value is not None:
                ws.cell(j, i, value)


def renewal_tracker(renewals: list[R], flavour: str = CROSS, report_date: str = "03 Nov 2026",
                    report_time: str = "16:13:55", completed: str = "Excluded",
                    task_tracker: bool = False, missing_rows: list[list] | None = None,
                    cross_overview: bool = False) -> bytes:
    wb = openpyxl.Workbook()
    gi = wb.active
    gi.title = "General Information"
    client = renewals[0].client if renewals else "Acme Group"
    lines = ([] if flavour == CROSS else [(client, None)]) + [
        ("Renewal Tracker", None), (None, None), ("Report Information:", None),
        ("Report Date", report_date), ("Report Time", report_time),
        ("Report Generated By", "Test User"), ("Currency Conversion Timing", "October 2026"),
        (None, None), ("Renewal Status:", None), ("Client Status", "Active"),
        ("In Progress & Pending Kickoff", "Included"),
        ("Completed within Last 6 Months", completed),
        ("Upcoming within Next 6 Months", "Excluded")]
    for i, (a, b) in enumerate(lines, start=1):
        if a is not None:
            gi.cell(i, 1, a)
        if b is not None:
            gi.cell(i, 2, b)
    if task_tracker:
        wb.create_sheet("Task Summary")
        out = io.BytesIO()
        wb.save(out)
        return out.getvalue()

    # --- Renewal Overview: header row 5 in both flavours -----------------------
    ov = wb.create_sheet("Renewal Overview")
    by_client: dict[str, list[R]] = {}
    for r in renewals:
        by_client.setdefault(r.client, []).append(r)
    rows_written = 0
    ov.cell(1, 1, "Renewal Tracker - Renewal Overview")
    last = None
    cols = ([("Policy Information (Expiring Policy Period)", "Client Name")] if flavour == CROSS
            else []) + OVERVIEW
    for i, (section, header) in enumerate(cols, start=1):
        if section != last:
            ov.cell(4, i, section)
            last = section
        ov.cell(5, i, header)
    for r in renewals:
        cells = ([r.client] if flavour == CROSS else []) + _overview_values(r, flavour, cross_overview)
        for i, value in enumerate(cells, start=1):
            if value is not None:
                ov.cell(6 + rows_written, i, value)
        rows_written += 1
    for extra in missing_rows or []:             # rows with no client (BM+ demo noise)
        for i, value in enumerate(extra, start=1):
            if value is not None:
                ov.cell(6 + rows_written, i, value)
        rows_written += 1

    # --- the three detail sheets ---------------------------------------------------
    id_cols = [("Policy Information (Expiring Policy Period)", h)
               for h in ("Country", "Entity", "Policy Unique ID*", "Policy Name", "Policy Number",
                         "Annual Renewal/Review Date")]
    ren_col = [("General Renewal Information (Upcoming Policy Period)", "Renewal Unique ID*")]

    def ids_of(r: R) -> list:
        return [r.country, r.entity, _policy_cell(r, flavour), r.policy, r.policy_number, r.renewal_date]

    strat = wb.create_sheet("Renewal Strategy")
    _write_table(strat, flavour, 6, id_cols + ren_col + [
        ("Renewal Strategy Information", "Renewal Strategy"),
        ("Renewal Strategy Information", "Expected date to receive the final renewal terms"),
        ("Renewal Strategy Information", "Types of Plan Desing changes (e.g adding or removing a coverage, "
                                         "changing benefit levels, etc):"),
        ("Renewal Strategy Information", "Reasons for plan design changes")],
        [ids_of(r) + [_renewal_cell(r, flavour), r.strategy, r.final_terms_date, r.pdc_types, r.pdc_reasons]
         for r in renewals],
        client, "Renewal Tracker - Renewal Strategy", "Renewal Strategy Information")

    prop_header = 5 if flavour == CLIENT else 6   # moves between flavours, as in BM+
    prop_rows = []
    for r in renewals:
        for name, first, final in r.proposals:
            prop_rows.append(ids_of(r) + [_renewal_cell(r, flavour), "Proposal 1", name, first, final])
    _write_table(wb.create_sheet("Proposals"), flavour, prop_header, id_cols + ren_col + [
        ("Proposal Details", "Proposals"), ("Proposal Details", "Insurer"),
        ("First Quote", "Annual Premium (Reporting Currency)"),
        ("Final Quote", "Annual Premium (Reporting Currency)")],
        prop_rows, client, "Renewal Tracker - Proposals", "Proposal Information")

    _write_table(wb.create_sheet("Savings"), flavour, prop_header, id_cols + ren_col + [
        ("Savings (Reporting Currency)", "Cost Savings (MMB)")],
        [ids_of(r) + [_renewal_cell(r, flavour), 0] for r in renewals],
        client, "Renewal Tracker - Savings", "Key Renewal Information")

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def minus_hours(d: datetime, hours: float) -> datetime:
    return d - timedelta(hours=hours)


# ---------------------------------------------------------------------------
# Task Tracker
# ---------------------------------------------------------------------------
@dataclass
class T:
    """One BM+ task. `n` ties it to R(n=…): same per-cycle and stable ids."""
    n: int = 1
    task_name: str = "Renewal Strategy"
    status: str = "In Progress"
    client: str = "Acme Group"
    country: str = "Poland"
    category: str = "Renewal Workspace"
    task_id: str | None = None                      # default: derived from n + task_name
    due: datetime = datetime(2026, 11, 20)
    review_date: datetime = datetime(2027, 1, 1, 1, 0)
    completed: datetime | str | None = "N/A"
    assignee: str = "Ola Nowak"
    approved: datetime | str | None = "N/A"
    pending: str = "N/A"
    rejected: int = 0
    policy_id: str | None = "auto"
    policy_number: str | None = "PL-001"

    def ids(self) -> tuple[str, str | None, str, str]:
        tid = self.task_id or hexid(self.n * 10 + len(self.task_name), "a")
        cycle = hexid(self.n, "8") if self.policy_id == "auto" else self.policy_id
        return tid, cycle, hexid(self.n, "7"), hexid(self.n, "9")


_TASK_COLS = [  # (header in the cross-client export, header in the client-specific one)
    ("Task Country", None), ("Task Category", None), ("Task Type", None), ("Task Status", None),
    ("Task ID", None), ("Expiring Policy Unique ID", None), ("Renewal Unique ID", None),
    ("Current Renewal Strategy", None), ("Local Task Priority", None), ("Task Name", None),
    ("Policy ID", None), ("Policy Name", None),
    ("Policy Renewal/Review Date", "Policy Renewal/_x000d_\nReview Date"),
    ("Global Peer Review_x000d_\nNo. of times rejected", "Global Review No. of times rejected"),
    ("Global Peer Review_x000d_\nApproval Date", "Global Review Approval Date"),
    ("Global Review Pending days", None), ("Current Task Due Date", "Task Due Date"),
    ("Local Task Completed Date", None), ("Task Assignee", None), ("Days with Task Assignee", None),
    ("Global Review approved by", None), ("Original Task Due Date", "-"),   # "-": cross-client only
    ("Policy Number", None),
]


def task_tracker(tasks: list[T], flavour: str = CROSS, report_date: str = "03 Nov 2026",
                 period: tuple[str, str] | None = None) -> bytes:
    """`period` = the export's own filter (Date Type "Renewal Date", From, To),
    e.g. ("31 Dec 2025", "30 Dec 2026"), as BM+ writes it on General Information."""
    wb = openpyxl.Workbook()
    gi = wb.active
    gi.title = "General Information"
    client = tasks[0].client if tasks else "Acme Group"
    lines = ([] if flavour == CROSS else [client]) + ["Task Tracker", None, "Report Information:"]
    for i, a in enumerate(lines, start=1):
        if a:
            gi.cell(i, 1, a)
    base = len(lines)
    for i, (a, b) in enumerate([("Report Date", report_date), ("Report Time", "16:14:52"),
                                ("Report Generated By", "Test User"), ("Assignee", "All")]
                               + ([("Date Type", "Renewal Date"), ("Date: From", period[0]),
                                   ("Date: To", period[1])] if period else []),
                               start=base + 1):
        gi.cell(i, 1, a)
        gi.cell(i, 2, b)
    ws = wb.create_sheet("Task Summary")
    header_row = 4 if flavour == CROSS else 5
    if flavour == CLIENT:
        ws.cell(1, 1, client)
        ws.cell(2, 1, "Task Summary")
    else:
        ws.cell(1, 1, "Task Summary")
    keep = [flavour == CROSS or alt != "-" for _, alt in _TASK_COLS]
    headers = (["Client"] if flavour == CROSS else []) + \
        [c if flavour == CROSS or alt is None else alt
         for (c, alt), k in zip(_TASK_COLS, keep, strict=True) if k]
    for i, h in enumerate(headers, start=1):
        ws.cell(header_row, i, h)
    for j, t in enumerate(tasks, start=header_row + 1):
        tid, cycle, stable, robj = t.ids()
        url = f"https://bm.example/client/{CLIENT_ID}/renewals/v2/{robj}/{cycle}?taskId={tid}"
        cols = [
            t.country, t.category, "Local", t.status, url, stable,
            robj if flavour == CROSS else url.replace("?taskId=", "/"), "TBC", "High",
            t.task_name, cycle, "Medical", t.review_date, t.rejected, t.approved, t.pending,
            t.due, t.completed, t.assignee, "214",
            # BM+ gives the approver as an e-mail in one flavour, a name in the other
            ("ola.nowak@example.com" if flavour == CROSS else "Ola Nowak") if t.approved != "N/A" else "N/A",
            t.due, t.policy_number]
        vals = ([t.client] if flavour == CROSS else []) + [x for x, k in zip(cols, keep, strict=True) if k]
        for i, value in enumerate(vals, start=1):
            if value is not None:
                ws.cell(j, i, value)
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


# -- the Insurer Capability Database ("All Networks") ------------------------------------
CAP_HEADERS = ["Region", "Country of cover issuance", 6, "Insurer name", "Line of risk",
               "Is cover offered locally on a fully insured basis? ",
               "Can cover be included within a multinational pool? ",
               "What share of the cover can be included within a multinational pool (quota share)?",
               "Can cover be included within a global insurance program (global underwriting approach)? ",
               "What share of the cover can be included within a global insurance program (quota share)?",
               "Can cover be ceded to a captive? ",
               "What is the maximum quota share that the captive can hold? ",
               "Comments"]


def capability_db(rows: list[tuple], network_header=6,
                  other_sheets: tuple[str, ...] = ("Read me",)) -> bytes:
    """The real layout: one "Database" sheet, the network column's header a
    stray number (as BM+ exports it). Each row: (region, country, network,
    insurer, line, fully insured, pool, pool share, gip, gip share, captive,
    captive share, comments). Synthetic data only."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Database"
    ws.append([network_header if i == 2 else h for i, h in enumerate(CAP_HEADERS)])
    for r in rows:
        ws.append([r[0], r[1], r[2], r[3], r[4], *r[5:]])
    for name in other_sheets:
        wb.create_sheet(name).append(["Country", "Insurer name", "Line of risk", "Something else"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
