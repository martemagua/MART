# MART — open questions

Every open question in one place, so it can be answered in one sitting.
Write the answer under each question (or just reply in chat with the IDs).
⭐ = shapes the design most, so worth answering first.
Background for each group: `PLANNING.md`.

Answered so far: **MART is built new and standalone; MAPT NEO is reference
only** (own database, own notes/to-dos, nothing migrated) · bundles exist (client × country × renewal date) · BM+ state
and actual state are kept side by side · an MCP connection for the local AI
agent is wanted · an AI plugin (MCP + skills + templates) is wanted.

---

## A. Scope & setup

**A1** ~~Alongside / replace / part of MAPT?~~
→ **Answered:** built new in MART, standalone. MAPT NEO is reference only.

**A2** ~~Take over / share / start fresh with MAPT's notes, to-dos, chasers?~~
→ **Answered:** start fresh; MART has its own.

**A3** Who uses MART? Only you, or colleagues too? When "working with colleagues" on the Kanban, do you share your screen in a call, or should they open MART themselves?
→

**A4** What is your role in a renewal? Which steps do *you* do, and which do COE, the local broker, the insurer and the client do?
→

**A5** Where does it run? Same as MAPT (local Windows, OneDrive folder, `.bat` launcher)? Any corporate restrictions (installs, cloud, Outlook automation)?
→

**A6** Since MART is new: same stack as MAPT (Python · FastAPI · SQLite · HTMX, no build step), or something else?
→

---

## B. The renewal lifecycle

**B1 ⭐** Walk me through one real renewal end to end, with typical timings (T-minus days). Is there an internal playbook or SLA document?
→

**B2** Does the process differ by strategy (remarketing / incumbent / rate guarantee / non-expiring / multi-year), product group or country?
→

**B3** When does a renewal *start* for you, and when is it really *done*?
→

**B4 ⭐** Is BM+'s "Annual Renewal/Review Date" the date the renewal takes effect, or a review date before it? Which date should deadlines count back from?
→

**B5** Roughly how many renewals are live at once (≈50? 300?)
→

---

## C. Bundles & the Kanban board

**C1 ⭐** Bundle = client × country × **exact** renewal date, or the same month? Does entity matter (two entities in one country, same date)?
→

**C2 ⭐** Is one Kanban card a **bundle** or a **single renewal**? What should happen when one renewal in a bundle diverges (different strategy or stage)?
→

**C3 ⭐** Which columns? Proposal: *Not started · Strategy · Proposals / Marketing · Decision · Update Policy · Post-renewal review · Done.*
→

**C4** Swimlanes (client / renewal month / owner)? WIP limits?
→

---

## D. Actual state vs BM+ (discrepancies)

**D1 ⭐** Which fields typically lag in BM+ besides the strategy: stage, workflow status, plan design changes, insurer, dates, other?
→

**D2** Should a "BM+ behind" discrepancy automatically become a follow-up for the broker ("please submit the strategy in BM+")?
→

**D3** Do you need a list or export of all discrepancies, e.g. to send to the brokers or COE?
→

---

## E. Overview freshness & broker deadlines

**E1 ⭐** When is an overview *stale*: a fixed number of days, or tighter as the renewal date approaches? What number of days?
→

**E2** "New" relative to what: since I last *marked it seen*, since the last client meeting, or since the last upload?
→

**E3** Should freshness be measured on *all* overview entries, or on client-ready ones only?
→

**E4** Is a broker deadline fulfilled by any new overview entry, or should you always confirm it yourself?
→

**E5** When a deadline passes: just flag it, or start a chase (with a draft email) automatically?
→

---

## F. Reminders & chasers

**F1** Is MAPT's chaser ladder (5 COE rungs + 3 AS rungs, working days) still correct? Do you need country holiday calendars?
→

**F2** How should reminders reach you: in-app only, Outlook calendar (.ics), email, Teams, phone? What is technically allowed on your work machine?
→

**F3** Do you want "waiting on X since Y" and simple dependencies, or is a checklist enough?
→

**F4** Should BM+ tasks only be mirrored, or should MART also hold your own sub-steps inside each BM+ stage (a playbook)?
→

---

## G. Home & daily orientation

**G1** On a client card on Home, which 3–5 things matter most at a glance?
→

**G2** Should the AI agent's day plan show up *inside* MART (a "Today" list it fills), or live in the agent's chat and only *read* MART?
→

---

## H. The AI plugin (MCP server + skills + templates)

**H1 ⭐** Which local AI agent will connect: Claude Desktop / Cowork, Claude Code, Microsoft Copilot, the company AI, something else? (This decides how the plugin is packaged.)
→

**H2 ⭐** "Templates for extracting the data": which direction do you mean?
- **out of MART:** report/output shapes (daily brief, client status, discrepancy list for brokers, meeting prep, post-renewal review), or
- **into MART:** pulling structure *out of* emails, meeting notes or broker replies (e.g. "broker says update by Friday" → a deadline), or
- both?
→

**H3 ⭐** What may the agent *write*? Proposal: notes, to-dos, deadlines, seen-marks, contact log entries freely. **Actual-state changes only as suggestions you confirm.** Never BM+ data.
→

**H4** ~~Two MCP servers or one?~~
→ **Answered:** MART has its own MCP server; it does not depend on MAPT's.

**H4b** Which tracker data does MART need beyond the renewal workflow, e.g. premiums, headcount, loss ratios (for the post-renewal review and savings), insurer networks?
→

**H5** Should the plugin include **scheduled routines** (e.g. a weekday morning brief, a weekly stale-overview sweep)?
→

**H6** Output formats for the templates: markdown in chat, Excel, Word, an email draft (Outlook `mailto:` / .eml), a MART note?
→

**H7** Should the plugin be shareable with colleagues (installable package), or only for your machine?
→

---

## I. Post-renewal

**I1 ⭐** "Updating our internal knowledge on savings / plan design changes": where does that live today (an Excel savings log, SharePoint, a stewardship report, BM+ itself)? What format does it need?
→

**I2** How are savings defined (vs the renewal ask? the expiring premium? the best alternative quote? which currency)? Could you share an anonymised sample of the Renewal Tracker's `Savings`, `Proposals` and `Renewal Strategy` sheets?
→

**I3** Which fields *exactly* must be correct after a renewal? Is the list in PLANNING §4.1 right, and what is missing?
→

**I4** Should the post-renewal review *block* closing a case, or only be a checklist with waivers?
→

---

## J. Data & history

**J1** Which trackers will you upload, and how often? (Upload frequency limits how accurately MART can date events.) Any new sources: Jira, Outlook, meeting notes?
→

**J2** Should MART keep every completed renewal forever, giving each policy a year-over-year renewal history (strategy, outcome, savings, cycle time)?
→
