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

→ **Header rows differ per sheet *and* per flavour.** MART must find the
header row by scanning, never from a fixed number.

**Client name:** the cross-client files have a `Client` / `Client Name`
column. The client-specific files have it only in *General Information* A1,
and that extra title row shifts every metadata cell down by one (Report
Date is row 5 in one flavour and row 4 in the other). MAPT read fixed cells,
so it only worked for the client-specific Renewal Tracker.

**General Information records the export's filters.** This is useful, and
MAPT ignored it:

| Renewal Tracker | Task Tracker |
|---|---|
| Client Status (Active) · In Progress & Pending Kickoff (Included) · **Completed within Last 6 Months (Excluded)** · **Upcoming within Next 6 Months (Excluded)** · which report sheets are included · reporting currency (client file only) · FX month + source | Task Name · Policy Name · Date Type + From/To · Assignee · Client · Category · Location · Type · Task Status |

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
- **Overview text** (corrected 04.11.2026, checked renewal by renewal): the
  **cross-client export does not carry the renewal overview at all**. Its
  *Renewal Overview (all) / (client ready)* columns are there but empty,
  although its General Information says they are "Included". It carries the
  **Renewal Feed** instead, which is a *different* stream (BM+ system messages
  such as "No documents linked to renewal" and other comments), not the
  overview. The single-client export is the opposite: overview filled, feed
  empty. MART takes each stream only from the flavour that carries it and
  never lets the other flavour blank it (`specs/renewal_tracker.CARRIED_STREAMS`).
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
