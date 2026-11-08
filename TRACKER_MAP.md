# BM+ tracker map for MART

What the BM+ exports contain, where it sits, and how it compares with what
MAPT NEO knew. Built from four exports Martin shared on 03.11.2026. Their
**content is demo data, but the structure is real**:

| File | Tracker | Flavour | Sheets |
|---|---|---|---|
| Tasks Tracker for <client> | Task | client-specific | General Information · Task Summary |
| Tasks Tracker Cross Client | Task | cross-client | General Information · Task Summary |
| Renewal Tracker for <client> | Renewal | client-specific | helper (hidden) · General Information · FX Rates · **Renewal Overview** · **Renewal Strategy** · **Proposals** · **Savings** |
| Renewal Tracker Cross Client | Renewal | cross-client | General Information · FX Rates · **Renewal Overview** · **Renewal Strategy** · **Proposals** · **Savings** |

Not in this batch: the Benefit Tracker and the Insurer Capability DB (known
from MAPT, see its `BENEFIT_TRACKER_MAP.md`). Personal names and e-mails from
the files are deliberately not copied here.

---

## 1. The short version

- **MAPT used a fraction of what is there.** It read only the *Renewal
  Overview* sheet (about 25 of its ~90 columns) and about 28 of the Task
  Tracker's 45–52 columns. The **Renewal Strategy, Proposals and Savings**
  sheets were never read, and they hold almost exactly what MART's
  lifecycle needs: strategy confirmation, the broker's expected date for the
  final terms, pooling partners, first and final quotes per insurer,
  accepted proposal, and a structured savings model.
- **The Task Tracker carries real event dates** (opened, assigned,
  completed, last updated, due date changes) and **the Global Peer Review**
  (approval date, rejections, pending days). That is your peer-review step
  (A4), already in BM+.
- **History is available.** The client-specific Task Tracker holds every
  task back to 2021, completed ones included. The Renewal Tracker export can
  *include* "Completed within last 6 months" and "Upcoming within next 6
  months" (these were *excluded* in the files sent, see §2).
- **Some of MAPT's assumptions are wrong for the cross-client files** (§7).
  The most important: MAPT would read the wrong policy id from the
  cross-client Renewal Tracker.

---

## 2. Layout: header rows, flavours, metadata

| Sheet | Client-specific header row | Cross-client header row | Above the header |
|---|---|---|---|
| Task Summary | 5 | 4 | title rows only |
| Renewal Overview | 5 | 5 | row 4 = section labels |
| Renewal Strategy | 6 | 6 | row 5 = sections, row 4 = super-section |
| Proposals | **5** | **6** | sections + super-section |
| Savings | **5** | **6** | sections + super-section |

**Lines of Coverage** is one cell per renewal, the lines joined by ", "
("Healthcare - Inpatient (Hospital and Surgical), Healthcare - Maternity");
each line is "<product group> - <line>". No comma inside brackets in the
demo exports, but MART doesn't split there anyway.

**Expected date to receive the final renewal terms** (Renewal Strategy
sheet) is an ISO date when filled; 11 of the 47 demo renewals with a
strategy row have one. MART prefills a bundle's broker deadline from the
earliest of its renewals' dates (M2 day 3).

**Policy Number** is on the three detail sheets (Policy Information section)
and on the Task Tracker, NOT on the Overview sheet. BM+ writes it as the
insurer's number, or "(multiple)"; 40 of the 49 demo renewals have one.

→ **Header rows differ per sheet *and* per flavour.** MART must find the
header row by scanning, never from a fixed number.

**Links to BM+** (checked 04.11.2026): the cross-client Renewal Tracker
writes the renewal (`…/client/<c>/renewals/<renewal>/<cycle>`) and the
expiring policy (`…/policies/<cycle>;<stable>`) as full links; the
single-client one only bare ids. Every Task Tracker row links to its task
(`…/renewals/v2/<renewal>/<workspace>?taskId=…`, same `<renewal>` id;
implementation tasks `…/implementation/<id>?taskId=<uuid>`). All of a renewal's
task links open the SAME page in BM+, the renewal's workspace (Martin,
04.11.2026), so MART offers one of them as "Renewal in BM+". MART shows
these links as they are and never builds one. **The renewal link does not
open in BM+** (Martin, 04.11.2026); the policy link does. MART stores the
renewal link but doesn't offer it.

**"Insurer Not Found"**: BM+ writes it in Insurer when the insurer isn't in
its list (158 of the cross-client demo rows). The **Provider** column beside
each Insurer (expiring, upcoming, and in Proposals) then names who it is
(Martin, 04.11.2026; empty in every demo row). MART shows the Provider in
that case (`renewal_tracker.insurer_or_provider`).

**Country names** are English, mostly the common short form ("Poland",
"United Kingdom") but ISO 3166's long form where it has one: "Korea,
Republic Of", "Tanzania, United Republic Of", "Cote D'Ivoire" (no accent),
and "United States". 79 distinct names in the demo exports, all of them
known to `web/countries.py` (flags).

**Sheets are optional, columns are not** (Martin, 04.11.2026): when a
tracker is created in BM+, each report sheet can be left out (General
Information lists which are included); the standard trackers always have the
same columns. Renewal Overview / Task Summary are the item lists themselves,
so a file without them is refused. A missing Renewal Strategy, Proposals or
Savings sheet is **not news**: MART keeps what it has for those sheets and
compares only the sheets the export includes (`renewal_tracker.merge_details`);
the renewal panel says which export a kept section is from.

**Client name:** the cross-client files have a `Client` / `Client Name`
column. The client-specific files have it only in *General Information* A1,
and that extra title row shifts every metadata cell down by one (Report
Date is row 5 in one flavour and row 4 in the other). MAPT read fixed cells,
so it only worked for the client-specific Renewal Tracker.

**General Information records the export's filters.** This is useful, and
MAPT ignored it:

| Renewal Tracker | Task Tracker |
|---|---|
| Client Status (Active) · In Progress & Pending Kickoff (Included) · **Completed within Last 6 Months (Excluded)** · **Upcoming within Next 6 Months (Excluded)** · which report sheets are included · reporting currency (client file only; MART keeps it per client since 0.9.30, `clients.reporting_currency`: BM+'s premiums are in it) · FX month + source | Task Name · Policy Name · Date Type + From/To · Assignee · Client · Category · Location · Type · Task Status |

→ MART can show *what an upload covers* and warn before a narrower export
makes renewals look as if they had disappeared.
→ Exporting with *Completed* and *Upcoming* included would give MART the
history and the pipeline directly.

**FX Rates:** a month label plus rate columns to EUR / USD / CHF (cross-client).

---

## 3. IDs: the glue (checked across the files)

| Meaning | Task Tracker | Renewal Tracker (client-specific) | Renewal Tracker (cross-client) |
|---|---|---|---|
| **Stable policy id** (same in every cycle) | `Expiring Policy Unique ID` | `Policy Unique ID` (bare id) | **second** id in `…/policies/<cycle id>;<stable id>` |
| **Per-cycle id** (one renewal cycle's upcoming policy) | `Policy ID` | `Renewal Unique ID` (bare id) | **first** id in the same URL |
| BM+ renewal object | `Renewal Unique ID` (bare, cross-client; URL, client file) and the `/renewals/v2/<id>/…` part of `Task ID` | — | `…/renewals/<id>/<cycle id>` in `Renewal Unique ID` |
| Task | `Task ID` = deep link `…/renewals/v2/<renewal>/<…>?taskId=<task>` | — | — |

Checked on the demo data:
- Stable id: **45 of 47** client-file renewals found their tasks via `Expiring Policy Unique ID`.
- Per-cycle id: the Renewal Tracker's `Renewal Unique ID` equals the task's `Policy ID` for **41 of 47**.

That per-cycle id is the **cycle key MART needs**. It ties tasks to *this*
renewal cycle directly; MAPT had to approximate this from review dates.

⚠ The same name means different things: the Renewal Tracker's "Renewal
Unique ID" is the Task Tracker's "Policy ID", not the Task Tracker's
"Renewal Unique ID".

**Rows without ids:** in the cross-client Renewal Overview, 297 rows with
workflow status **"Transitioned Inprogress"** have *no* Policy or Renewal
Unique ID. MART needs a fallback identity for them (client + country +
policy name + renewal date) and should flag them. Another 153 rows have ids
but no client or status, which is probably demo-environment noise; the loader
must skip and report rows missing the minimum fields.

---

## 4. Task Tracker (`Task Summary`): one row per task

| Group | Columns |
|---|---|
| Context | Client *(cross only)* · Task Country · Product Group, Lines of Coverage, Insurer Name *(cross only)* · Policy Name / Number · Policy Renewal/Review Date · Current Renewal Strategy · Benefit Owner · Local Analyst |
| Task | Task Category (*Renewal Workspace · Implementation · Contract*) · Task Type · **Task Name** (*Renewal Strategy · Proposals · Update Policy* + *Appointment · Upload Local Documents · Review ROR · Update Policies · Local Contract Review*) · Task Status · Local Task Priority (*High · Medium · Lowest*) |
| Dates | Task Opened · Task Start · **Original** Task Due *(cross only)* · Current Task Due · # of Times Due Date Changed · Due Date Last Changed by · Task Last Updated Date / By · **Local Task Completed Date / By / Email** · +/- Days to Due Date |
| People | Task Assignee + Email + **Office Location** + **Assigned Date** + **Days with Task Assignee** · Task **Delegated** to + location + date + days with delegate · Escalation Manager (+ Email, cross only) · # of Times Renewal Escalated · Last Escalated Date |
| **Global Peer Review** | Last Rejected Date · No. of times rejected · **Approval Date** · **Pending days** · Approved by. Status value `Global Review Pending` |

What this means for MART:
- **Real dates**: completion, assignment and update dates come from BM+, so
  MART's timeline doesn't have to rely on "first seen at upload".
- **Peer review queue**: `Global Review Pending` + pending days + rejections
  = your review work (A4), with a ready KPI.
- **Slipping deadlines**: original vs current due date and the number of
  changes give a "deadline moved N times" signal.
- **Who holds it**: "days with assignee/delegate" and the office location
  show where a task is stuck.
- **Flavour differences**: the client file lacks Client, Product Group,
  Lines of Coverage, Insurer, Escalation Manager Email and Original Due Date,
  and names differ ("Task Due Date" vs "Current Task Due Date", "Global
  Review…" vs "Global Peer Review…").
- **People differ by flavour too** (checked 04.11.2026): "Global Review
  approved by" is an e-mail in the cross-client file and a name in the
  client file; "Local Task Completed By" is `N/A` in the client file;
  "Renewal Unique ID" is a bare id in one and a URL in the other; the
  completion date is a full timestamp in one and a date in the other. MART
  therefore compares only the workflow facts both carry
  (`specs/task_tracker.COMPARED`) and keeps, per task, what the other
  flavour had for columns this one lacks.
- **Dates are real timestamps** (`2026-10-02 14:32:42`), not BM+'s usual
  midnight-UTC-in-local-time; MART only rounds a time that is exactly on the
  hour or half hour with no seconds.
- **Task ids**: renewal tasks carry a 24-hex `taskId=`; implementation tasks
  (Appointment, Upload Local Documents, Review ROR, Update Policies) a dashed
  UUID.
- **No Proposals stage** for the upcoming strategies *Incumbent with Rate
  Guarantee* and *Non-expiring* (Martin, 04.11.2026): BM+ creates only
  Renewal Strategy and Update Policy for them.
- **Period**: a Task Tracker export can cover years. General Information
  records it ("Date Type: Renewal Date · Date: From 31 Dec 2025 · Date: To
  30 Dec 2026"; the client file showed "Not Specified"). Date Types BM+
  offers (Martin, 04.11.2026): Renewal Date · Task Start Date · Task Due
  Date · Task Complete Date · Not Specified. MART applies each to the
  matching task date.
- **Most tasks of a long export belong to older cycles**: of the 490 tasks
  in the Globex client file, 436 belong to no renewal MART has (the
  Renewal Tracker carries in-progress and pending-kickoff renewals only).
  MART discards those (Martin, 04.11.2026). MART loads **Renewal Workspace**
  tasks only; implementation tasks (which carry no Policy ID / Expiring
  Policy Unique ID at all) and contract tasks are not MART's concern.
- **Linking**: `Policy ID` = the Renewal Tracker's per-cycle id (43 of 49
  Globex renewals found their tasks this way); failing that, the stable
  Expiring Policy Unique ID + the review date.

---

## 5. Renewal Tracker

### 5.1 Renewal Overview: one row per renewal (policy), ~90 columns

| Section | Highlights (**bold** = MAPT ignored it) |
|---|---|
| Policy Information (expiring) | Client Name *(cross)* · **Division · Region · Sub Region** · Country · Entity · Policy Unique ID · Policy Name · **Number of LOCs · Policy Description · Bundled Policy?** · Start / End Date · **Rate Guarantee End Date · Multi-year Policy?** · **Next Renewal Kickoff Timing** (e.g. "4 Months Before Renewal") + **Kickoff Date** · Year of Last Remarketing · Benefit Owner · Local Analyst |
| LOC Information expiring / **upcoming** | Line of Coverage · **Headcount** (packed: "Employee: 500, Dependent: 70") |
| Premium Information expiring / **upcoming** | Insurer · Provider · Local Currency · **Premium Rate Type · Annual Premium Rate · Sum Insured · Annual Premium** (local + reporting) |
| Multinational Network expiring / upcoming | Implemented Network (None / Pooled / Captive) · Network Partner |
| **Broking Remuneration** expiring / upcoming | Type · Commission Rate · Coverage fee · Remuneration (local + reporting) |
| Claims | Target / Actual Loss Ratio · Date Range · Comments |
| Renewal Information | Renewal Unique ID · Annual Renewal/Review Date · **Date of Local Meeting** · Upcoming Renewal Strategy · Workflow Status · Plan Design Changes Considered? + Comments · **Expected Change in Premium Rate (+ %) · Recommended Proposal Change · Final Change · General Benchmarking Position + Comments · Insurer (Recommended Proposals) · Recommended Proposals · Client Approval Date · Cost Savings / Cost Avoidance / Unrealized Savings / Other (MMB + Custom)** · Renewal Overview (all) · (client ready) · **Renewal Feed** |

What to watch out for in the cell contents:
- **Overview text** (settled 04.11.2026, after testing 0.3.0 with real
  exports): the overview (all + client ready) is usually full and very
  important, but **only the single-client export carries it**: real
  cross-client exports leave both overview columns empty, just like the
  demo files, and fill only the **Renewal Feed**, a different stream (BM+
  system messages such as "No documents linked to renewal" and other
  comments). Martin uploads single-client exports for the overview; MART
  shows per client how old that overview data is ("Overview as of …", out
  of date after Settings → Time limits). MART decides from the DATA which
  streams an export carries: a stream with text in at least one renewal is
  carried; one the whole export leaves empty keeps the stored text
  (`renewal_tracker.carried_streams`).
- **Overview entries** start with `DD MMM YYYY:` **at the start of a line**;
  a date followed by a colon inside a sentence ("quotes by 15 Nov 2026: three
  insurers") is not a new entry. BM+ marks some entries "(not client
  ready)" in their header. Entries are not in date order.
- **Values for several lines of coverage packed into one cell** as
  `LOC: value` lines (loss ratios, rate changes, benchmarking, commission),
  so they must be parsed per line of coverage.
- `End Date` may say "Non Expiring Policy". Dates carry stray times (01:00,
  05:30) and must be normalised to plain dates.
- Vocabulary variants ("Unknown / New Policy" vs "Unknown/ New Policy").
  `TBC` is the most common strategy value.
- Workflow status: Not Started · In Progress · **Transitioned Inprogress ·
  Transitioned Completed**.

### 5.2 Renewal Strategy (new): one row per renewal
| Section | Columns |
|---|---|
| General renewal info (upcoming) | Renewal Unique ID · Workflow Status · Renewal Date · Kickoff Date |
| Key takeaways from last renewal | Last Renewal Strategy · Last Year of Remarketing · **Next Remarketing as per RoR** · Plan Design Changes · Other Considerations / Complexity · Other Comments |
| Renewal strategy | Renewal Strategy · **Confirmed with the local client? + date + why not** · Plan design changes considered? + **types** + **reasons** · **Will the pooling partners be invited? · Primary Pooling Partners · Other Preferred Global Insurance Partners · Why not invited?** · **Expected renewal rate adjustment** · **Expected date to receive the final renewal terms** |
| Claims | Number of claims · Claims amount (reporting + local) · Actual Loss Ratio · Date range (packed per line of coverage) |
| Client-specific questions | Question 1–4 (client-defined Q&A) |

→ *Strategy confirmed + date* is a real "actual state" signal.
*Expected date to receive the final renewal terms* is BM+'s own version of
a broker deadline (about 25% filled here), so MART can prefill deadlines
from it. The pooling questions cover B2.

### 5.3 Proposals (new): one row per proposal per renewal
| Section | Columns |
|---|---|
| General renewal info | Renewal Type (Full Renewal / Annual Review) · Upcoming Renewal Strategy · Renewal Unique ID · Status · dates |
| Multinational network | Implemented Network + Partner · **Eligible** Multinational Networks / Pooling / Captive / Global Underwriting Partners · Darwin · SME |
| Proposal details | **Proposal name** ("Proposal 1") · **Recommended / Selected / Lowest Cost** flags · **Insurer** · Provider · **Plan Design** (Expiring vs changed) · Currency · Headcount · **Closing (expiring) Premium** local + reporting · Sum Insured · Any change in premium rate? + % |
| **First Quote** | Premium Rate Type · Annual Premium Rate · Annual Premium local + reporting |
| **Final Quote** | the same four |

→ This is almost exactly the **proposal register** from B1: per insurer,
the first and the final quote, variants with or without plan design
changes, and which one was recommended or selected. BM+ doesn't hold the
*intermediate* negotiation rounds; MART would add them if wanted.

### 5.4 Savings (new): one row per renewal
| Section | Columns |
|---|---|
| Key renewal information | **Was Recommended Proposal Accepted by Client?** |
| Value added | Improved Benefit Level · Enhanced Underwriting Terms · Unquantifiable Changes |
| Considerations for next renewal | Planned design changes · Other Considerations / Complexity · Other Comments |
| Savings (local + reporting currency) | **Cost Savings · Cost Avoidance · Unrealized Savings** (each MMB and Custom) · Other |
| **Premium change drivers** | Headcount · Sum Insured · Forecasted Medical Inflation · Loss Ratio · Regulatory / Legislative · Benefit Design Changes · Change in Fees / Commission · Change of Tariff Rates · Demographic profile changes · Rejected Plan Improvement |

→ BM+ already has a **structured savings model, including the drivers that
explain a premium change**. MART's knowledge capture should use these same
categories. Then the post-renewal check can ask "is the Savings section
filled?" and compare it with Proposals (closing premium vs final quote).

---

## 5b. Insurer Capability Database ("All Networks", 06.11.2026)

Not a BM+ tracker: a list of the international networks' local partners,
the same for all clients, updated now and then (the file Martin has is
"2025 Insurer Capability Database - All Networks.xlsx"). MART reads ONE
sheet, **Database**; other sheets a version may carry are ignored.

| What | Found in the 2025 file |
|---|---|
| Layout | header in row 1, autofilter A1:M; 12,281 rows, 13 columns |
| Columns | Region · Country of cover issuance · *(network, header cell holds a stray `6`)* · Insurer name · Line of risk · Is cover offered locally on a fully insured basis? · Can cover be included within a multinational pool? · … pool quota share · Can cover be included within a global insurance program (global underwriting approach)? · … its quota share · Can cover be ceded to a captive? · … maximum captive quota share · Comments |
| Networks | AIA, Allianz, Generali, IGP, Insurope, MAXIS (also written "Maxis"), Swiss Life, Zurich |
| Countries | 243 spellings, 230 countries; 3 places that aren't countries ("Channel Islands", "International", "Offshore Programs (TCN / Expat)") |
| Regions | APAC · Africa · Europe · LATAM · Middle East · North America · EXPAT · Global (the database's own scheme, not a client's) |
| Lines of risk | 7: Accident/AD&D · Disability (long-term annuity / lump sum) · Life/Survivor's · Medical/Healthcare · Retirement/Pension · Worker's Compensation (once "Workers Compensation") |
| Insurer | the local partner's legal name; **"None"** = the network has no partner in that country; one insurer is often written differently per network |
| Yes / no | mostly Yes / No, also "yes", "No ", "N0", "NO", "No (CI:Yes)" |
| Quota shares | fractions 0–1, a few short texts (ranges such as "80% to 99%", or a condition) |
| Repeats | 64 network × country × insurer × line pairs twice, 62 identical; the other 2 are "None" rows (Allianz, Russia) |

## 6. MART features → where BM+ has the data → what MART adds

| MART feature | BM+ source | What MART adds |
|---|---|---|
| Actual state / Kanban | Workflow Status · task statuses · Renewal Strategy + *confirmed with client* date | the real state when BM+ lags, and the discrepancy itself |
| Broker deadlines | *Expected date to receive the final renewal terms* · task due dates (original vs current) | promises BM+ doesn't hold, and checking whether they were kept |
| Overview freshness | Overview (all / client ready) or **Renewal Feed**, dated entries | new / stale / seen |
| Peer review | Task Global Peer Review fields · `Global Review Pending` | your findings and the clarification log with the data analyst |
| Proposal register | **Proposals** (first + final quote, flags, plan design variant) | intermediate rounds, documents, notes, acceptance |
| Plan design changes | Strategy (considered / types / reasons) · Proposals (plan design) · Savings (benefit design changes) | each change as its own record, quantified |
| Savings | **Savings** sheet + Overview savings totals | consistency checks, knowledge across years |
| Remarketing & pooling | Strategy pooling questions · Proposals eligible networks | invitee list per remarketing, partner updates |
| Client-specific timelines | Kickoff Timing + Kickoff Date · task due dates | a client playbook with expected dates per step |
| Post-renewal review | upcoming-period fields · Client Approval Date · Savings · Update Policy task · Benefit Tracker | the checklist and waivers |
| History | full task history (client file) · Renewal export with Completed / Upcoming included | keeping completed renewals after BM+ drops them |

---

## 7. Corrections to MAPT's knowledge

1. **Cross-client Renewal Tracker**: client name is a column, the metadata
   cells shift, there is no reporting currency, and the stable id is the
   **second** id in the policy URL. MAPT's regex takes the first one, which
   is the per-cycle id.
2. **Overview text** is in *Renewal Feed* in the cross-client export.
3. **Header rows** differ per sheet and per flavour (4 / 5 / 6).
4. **Renewal Unique ID** in the Renewal Tracker = the Task Tracker's
   *Policy ID* (the per-cycle key); same name, different meaning.
5. The **Task Tracker** carries full history and real completion dates;
   MAPT treated it as a snapshot of open work.
6. **More task names and categories** than the three stages (Appointment,
   Upload Local Documents, Review ROR, Local Contract Review; Implementation
   and Contract categories).
7. **"Transitioned"** workflow statuses exist, and those rows have no ids.
   Same-named ones can be *different* renewals (other entity, insurer,
   currency): they must never be merged. Only exact duplicate rows are.
7b. **Dates are midnight UTC shown in the country's local time**: 01:00
   (Europe), 05:30 (India), 08:00 (Asia), but 19:00 / 18:30 on the *previous*
   evening for the Americas. Round to the nearest midnight.
8. Exports can **include completed and upcoming renewals**. MAPT assumed
   completed ones were always dropped.

---

## 8. Questions this raises (copied to QUESTIONS.md §K)

- **K1** Which flavour will you upload day to day: cross-client (all clients in one file), per client, or both?
- **K2** Can the Renewal export include *Completed within last 6 months* and *Upcoming within next 6 months*?
- **K3** What are "Transitioned" renewals (migrated from an older system)? Will they get ids?
- **K4** Is *Expected date to receive the final renewal terms* where brokers record the date they give you, or is it usually empty?
- **K5** Is `Global Review Pending` the queue of tasks waiting for *your* peer review?
- **K6** Intermediate quote rounds: needed in MART, or are first + final enough?
- **K7** Should the Benefit Tracker come into MART as well? The post-renewal checks need it (claims, headcount, financials, design).
