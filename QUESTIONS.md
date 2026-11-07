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
→i will be the one using MART. when collaborating, I'l share my screen.

**A4** What is your role in a renewal? Which steps do *you* do, and which do COE, the local broker, the insurer and the client do?
→ i am a global account specialist, also refered to as internationaö consultong administrator. i am responsible for the project management and timely deliverable of the renewals. i am also responsible for peer reviewing the data 
that my Data Analyst (COE) gahters from the brokers and following up if i identify issues or need clarification. i also present the data to the client together with the account manager.

**A5** Where does it run? Same as MAPT (local Windows, OneDrive folder, `.bat` launcher)? Any corporate restrictions (installs, cloud, Outlook automation)?
→I can only run it locally currently. I want to have it running on a local folder and back up to onedrive or one of our compamy network folder. I also cannot install anything that requires admin authorization.

**A6** ~~Same stack as MAPT, or something else?~~
→ **Answered:** "whatever works best". **Decided 03.11.2026:** Python 3.12 (already on the laptop) + standard library + preinstalled `openpyxl`, no installs; shipped as a portable zip. See PLANNING §7.

---

## B. The renewal lifecycle

**B1 ⭐** Walk me through one real renewal end to end, with typical timings (T-minus days). Is there an internal playbook or SLA document?
→a renewal is kicked-off automatically in the system, creating a new entry in the renewals. usually, this happens 4 months before renewal, however different clients and individual countries can have their own tomelines.
we follow up with the clients requesting information on the strategy. The broker needs to take care contacting the local client and insurers themself, and will either give us expectations, dates or a strategy, that can be a straight renewal with the incumbent or a remarketing.
policies can also be under rate guarantee for multiple years or be non-expiring. 
there is also the question of plan design changes, so wether coverages stay the same or have cost containment or enhancements proposed as well. These need to be saved and quantified.
Then we require proposals from the insurer or insurers. There might also be multiple rounds if negotiations involved until the final quotes are agreed on. We require the first and the last quote from each insurer involved in the renewal. we also hold on to different proposals (with or without pdc) if offered.
finally, we need to know when and what proposal the client accepted.
after finalizing the renewal, it's nexessary thst all data in the system (BM+) is updated and properly reviewed. this includes document data, claims, headcount, financial and design information for instance.

**B2** Does the process differ by strategy (remarketing / incumbent / rate guarantee / non-expiring / multi-year), product group or country?
→a a remarketing involves reaching out to multiple providers and involving pooling partners. each client has different partners for pooling and their local partners need to be invited in the remarketing. we also need to inform pooling partners regularly about ongoing remarketings.

**B3** When does a renewal *start* for you, and when is it really *done*?
→it starts when the system kicks off the renewal and ends when all the information has been reviewed in the system.

**B4 ⭐** Is BM+'s "Annual Renewal/Review Date" the date the renewal takes effect, or a review date before it? Which date should deadlines count back from?
→the newal date is the date it takes effect. there are also different timelines where we expext tasks to be completed as well, but this depends on the individual client.

**B5** Roughly how many renewals are live at once (≈50? 300?)
→ this depends on the time of year, but it can be about 300 per client on high season

---

## C. Bundles & the Kanban board

**C1 ⭐** Bundle = client × country × **exact** renewal date, or the same month? Does entity matter (two entities in one country, same date)?
→it would be nice to split and join policies. some can be bundled by country and renewal date, others also need to be broken down by entity, policy number, insurer etc)
→ **Built 0.6.0 (Martin's simpler model, 04.11.2026):** bundles stay country + renewal date; renewals move, one or several at once, into a named custom bundle of the same country (new or existing), and back. Kept across uploads.

**C2 ⭐** Is one Kanban card a **bundle** or a **single renewal**? What should happen when one renewal in a bundle diverges (different strategy or stage)?
→it should be a bundle, but by the logic above, sometimes it might be that it's only one policy, others can be dozens. it depends

**C3 ⭐** Which columns? Proposal: *Not started · Strategy · Proposals / Marketing · Decision · Update Policy · Post-renewal review · Done.*
→ **Answered 05.11.2026:** the proposal is fine. See BUILD_PLAN_M3.md.

**C4** Swimlanes (client / renewal month / owner)? WIP limits?
→ **Answered 05.11.2026:** **one board per client**, with filters for **country**, **date** and **region**. Regions are set **per client** and can be changed: clients split the world differently (one has "Americas", another "LatAm" + "North America"). See BUILD_PLAN_M3.md, day 4.

---

## D. Actual state vs BM+ (discrepancies)

**D1 ⭐** Which fields typically lag in BM+ besides the strategy: stage, workflow status, plan design changes, insurer, dates, other?
→ **Answered 05.11.2026:** most important: the **strategy** and **proposals received** (from whom, how many). Also: **mark a renewal completed** (only once all tasks are submitted and approved), and an overview of **suggested plan design changes, implemented or not**. Martin wants this to build up into a **backlog per client** for the yearly **stewardship meeting**. See BUILD_PLAN_M3.md.

**D2** Should a "BM+ behind" discrepancy automatically become a follow-up for the broker ("please submit the strategy in BM+")?
→ **Answered 05.11.2026:** it must be **visible**; no automatic follow-up.

**D3** Do you need a list or export of all discrepancies, e.g. to send to the brokers or COE?
→ **Answered 05.11.2026:** not needed for now. Exporting **to-dos** would be interesting, but is **not a priority**.

---

## E. Overview freshness & broker deadlines

**E1 ⭐** When is an overview *stale*: a fixed number of days, or tighter as the renewal date approaches? What number of days?
→ **Answered 04.11.2026:** two steps: amber after **7 days** without a new overview entry, red ("stale") after **14**. Both in Settings → Time limits. (A future broker deadline pauses the clock, PLANNING §1c.)

**E2** "New" relative to what: since I last *marked it seen*, since the last client meeting, or since the last upload?
→ **Answered 04.11.2026:** by the **date written on the overview entry itself** (the `DD MMM YYYY:` header MART already splits the overview on). No "seen" marks. MART marks entries dated within the last N days as new (N in Settings; proposed default 7, the same as the amber limit).

**E3** Should freshness be measured on *all* overview entries, or on client-ready ones only?
→ **Answered 04.11.2026:** on **all** entries: "client ready" is a toggle that is sometimes forgotten.

**E4** Is a broker deadline fulfilled by any new overview entry, or should you always confirm it yourself?
→ **Answered 04.11.2026:** **Martin confirms it himself.** (MART may point out that a new entry arrived, but never closes a deadline on its own.)

**E5** When a deadline passes: just flag it, or start a chase (with a draft email) automatically?
→ **Answered 05.11.2026:** **keep it flagged** (as in M2).

---

## F. Reminders & chasers

**F1** Is MAPT's chaser ladder (5 COE rungs + 3 AS rungs, working days) still correct? Do you need country holiday calendars?
→

**F2** How should reminders reach you: in-app only, Outlook calendar (.ics), email, Teams, phone? What is technically allowed on your work machine?
→ **Answered 04.11.2026:** **inside MART** for sure (M2: Home's "Today"); over the AI agent some day (M4); and, if possible, an **email brief** (later, most likely through the agent).

**F3** Do you want "waiting on X since Y" and simple dependencies, or is a checklist enough?
→ **Answered 05.11.2026:** "waiting on" (M2) is enough; **linked to-dos are not a priority**: subtasks work similarly.

**F4** Should BM+ tasks only be mirrored, or should MART also hold your own sub-steps inside each BM+ stage (a playbook)?
→

---

## G. Home & daily orientation

**G1** On a client card on Home, which 3–5 things matter most at a glance?
→ 04.11.2026: **not sure yet**, especially for clients. M2 starts Home with the "Today" list (what is due or overdue) and a simple client card, and we adjust it from use.
→ 0.8.3 (05.11.2026): the card shows renewals in the export, the next renewal date, and counts of passed / near expected updates, new overview entries, quiet bundles and open to-dos. To be adjusted from use.
→ **M2 review 05.11.2026:** still **not sure**. Martin goes straight to a client page or to the To-dos rather than Home. Home stays as it is; it is likely where the AI agent will work (G2, M4), so its shape is decided then.

**G2** Should the AI agent's day plan show up *inside* MART (a "Today" list it fills), or live in the agent's chat and only *read* MART?
→ 05.11.2026 (M2 review): Martin sees Home as **a place for the AI to work in** in the future. To settle in M4.

---

## H. The AI plugin (MCP server + skills + templates)

**H1 ⭐** Which local AI agent will connect: Claude Desktop / Cowork, Claude Code, Microsoft Copilot, the company AI, something else? (This decides how the plugin is packaged.)
→

**H2 ⭐** "Templates for extracting the data": which direction do you mean?
- **out of MART:** report/output shapes (daily brief, client status, discrepancy list for brokers, meeting prep, post-renewal review), or
- **into MART:** pulling structure *out of* emails, meeting notes or broker replies (e.g. "broker says update by Friday" → a deadline), or
- both?
→ **Answered 07.11.2026 (at least "into MART"):** Martin's goal: Claude (Sonnet 5 / 4.6) connects over MCP and reads and EDITS MART's data. Example: a scheduled task goes through his emails, finds new proposals from an insurer (one with the expiring conditions, one with cost containment measures), records them as proposals and a plan design change, and writes a note in MART logging the message and its contents.

**H3 ⭐** What may the agent *write*? Proposal: notes, to-dos, deadlines, seen-marks, contact log entries freely. **Actual-state changes only as suggestions you confirm.** Never BM+ data.
→ **Answered 07.11.2026:** the agent **writes directly** (proposals, plan design changes, notes…), no confirm step. Still never BM+ data, and every AI write marked as AI with its source and undoable (CHARTER rule 5).

**H4** ~~Two MCP servers or one?~~
→ **Answered:** MART has its own MCP server; it does not depend on MAPT's.

**H4b** Which tracker data does MART need beyond the renewal workflow, e.g. premiums, headcount, loss ratios (for the post-renewal review and savings), insurer networks?
→

**H5** Should the plugin include **scheduled routines** (e.g. a weekday morning brief, a weekly stale-overview sweep)?
→ **Answered 07.11.2026:** yes, the agent app can run scheduled tasks. The email sweep should run **every few hours**.

**H5b** (07.11.2026) Attachments: when the agent finds an email with relevant information, it must **review the developments in the whole thread and read ALL attachments** (quotes often come as PDF / Excel). MART stores the values and the reference (sender, date, subject, file names), never the files.
→ **Answered 07.11.2026:** yes, very important (Martin).

**H6** Output formats for the templates: markdown in chat, Excel, Word, an email draft (Outlook `mailto:` / .eml), a MART note?
→

**H7** Should the plugin be shareable with colleagues (installable package), or only for your machine?
→

---

## I. Post-renewal

**I1 ⭐** "Updating our internal knowledge on savings / plan design changes": where does that live today (an Excel savings log, SharePoint, a stewardship report, BM+ itself)? What format does it need?
→ **Answered 03.11.2026:** savings must be saved in BM+; the central knowledge lives in MART; no fixed format. Only Martin reads it. Savings entries are updated from the BM+ tracker upload or by hand (MART does not calculate them). What he'll look things up by is still unsure → start simple. See PLANNING §7c.

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

---

## K. From the tracker files (03.11.2026, see TRACKER_MAP.md)

**K1 ⭐** Which export flavour will you upload day to day: **cross-client** (all clients in one file), **per client**, or both?
→

**K2 ⭐** Can the Renewal Tracker export include *Completed within last 6 months* and *Upcoming within next 6 months*? (That would give MART history and the pipeline directly.)
→

**K3** What are "Transitioned Inprogress / Completed" renewals (migrated from an older system)? Will they get Policy/Renewal Unique IDs?
→

**K4** Is *"Expected date to receive the final renewal terms"* (Renewal Strategy sheet) where brokers record the date they give you, or is it usually empty?
→ **Answered 04.11.2026:** usually **filled**. MART prefills a broker deadline from it when it is there (M2).

**K5** Is `Global Review Pending` the queue of tasks waiting for *your* peer review?
→

**K6** Proposals: BM+ keeps the first and the final quote per proposal. Do you need the intermediate negotiation rounds in MART too?
→

**K7** Should the **Benefit Tracker** come into MART as well? The post-renewal checks need it (claims, headcount, financials, design).
→

---

## L. From building the upload (04.11.2026)

**L8 ⭐** The **cross-client** Renewal Tracker contains **no renewal overview text**: its two overview columns are empty (only the "Renewal Feed" with BM+ system messages is filled). The single-client export has it. Overview freshness (new / stale) needs that text. Is this how your real cross-client exports look too, or only the demo environment? If real: would you upload single-client exports for your main clients regularly, or is there an export setting in BM+ that fills them?
→ **Answered 04.11.2026:** in real exports the overview is usually full and very important (the empty columns were the demo environment). MART now takes a text stream from any export that fills it (`renewal_tracker.carried_streams`) and shows it like MAPT's renewals page: dated entries, newest first, with what the client-ready version is missing marked.
→ **Corrected 04.11.2026 (testing 0.3.0):** real cross-client exports are empty there too; the overview comes from single-client exports, which Martin uploads. MART 0.4.0 takes several files in one upload, shows "Overview as of <report date>" per client and flags it as out of date after 7 days (Settings → Time limits). Open for M2: a broker's expected date should defer the stale clock until then (PLANNING §1c).

**L9** Can a tracker be created with only some sheets, or some columns?
→ **Answered 04.11.2026:** sheets yes (each report sheet can be left out), columns no (the standard trackers always have the same columns). MART 0.4.1 keeps what it has for a sheet an export leaves out, and compares only the sheets that are there.

**L10** Tasks of renewals MART doesn't have (older cycles in a long Task Tracker export)?
→ **Answered 04.11.2026:** tasks only attach to renewals MART has; the others are discarded, and the history grows from the renewals MART keeps (0.4.4).
(a) Date Types: Renewal Date, Task Start Date, Task Due Date, Task Complete Date, Not Specified — all applied (0.4.5). (b) Implementation and contract tasks: not important, ignored; only Renewal Workspace tasks are loaded (0.4.5).

**L11** Notes and to-dos (0.5.0) hang on a renewal cycle or a bundle. Should notes about a *policy* also carry over to its next renewal cycle (e.g. "HR always wants the renewal before October")? And should a client have its own notes (Home: "my clients with their notes")?
→ **Answered 04.11.2026:** see the notes of past renewals; yes, a space for client notes. Both in 0.5.1: a renewal shows its policy's notes from earlier cycles (read-only); clients have their own notes and to-dos.

---

## M. For milestone M2 (04.11.2026)

**M2a ⭐** **Richer to-dos** (to discuss when M2 starts). They already hang on a renewal, a bundle or a client and have a due date. Martin's starting points, from Microsoft To Do / Planner and Google Tasks: **subtasks**, **notes** on the to-do, **urgency**, **delegation** (who it was handed to / who we are waiting on). Open: which of these, what a status set looks like (e.g. open / in progress / waiting / done), and how broker deadlines and Home's "Today" use them.
→ Agreed 04.11.2026: designed in M2 together with broker deadlines and Home; a **to-do board** (cards = to-dos, columns = status) comes in M3, built on the same board code as the renewal Kanban.
→ **Answered 04.11.2026 (M1 review):** all four: **subtasks** (a checklist inside a to-do), a **description**, **urgency**, and **delegated / waiting on** (who it is with, since when). See BUILD_PLAN_M2.md.

**M2b ⭐** Is a broker deadline a to-do that waits on someone (one list), or a thing of its own?
→ **Answered 04.11.2026:** its own thing. **Broker deadlines are linked to the bundles**: when Martin expects updates for those renewals. **To-dos are other tasks** he has to get done regarding the renewals or countries. See BUILD_PLAN_M2.md.

**M2c** To-dos "regarding countries": a to-do sits today on a renewal, a bundle (country + date) or the client. Should a to-do also sit on a client's *country* as a whole, across its bundles there?
→ **Answered 04.11.2026:** no, **keep it with the bundle**. No country-wide target; to-dos stay on a renewal, a bundle or the client.

---

## N. For milestone M3 (05.11.2026)

**M3a ⭐** **Client topics** (PLANNING §5b): named, coloured topics for the client's notes and to-dos, a topic board, pinned notes and repeating to-dos.
→ **Agreed 05.11.2026:** in **M3** scope. Topics live **inside each client**: partner trackers are per client (one file per client, different partners and requirements). The existing client notes and to-dos start in a "General" topic.

**M3b** Repeating to-dos: which rhythms are needed? Proposal: every N weeks, monthly on a day or on the Nth working day, quarterly. Does "working day" need a holiday calendar (which country)?
→ **Answered 05.11.2026:** the standard options, nothing more: **every N days**, **every N weeks** (on chosen weekday(s)), **every N months**. No working-day rule, no holiday calendar.

**M3c** Should a set of topics be suggested for every client (e.g. "Client requests", "Partner tracker", "Implementation – <country>"), or does each client start empty except "General"?
→ **Answered 05.11.2026:** no suggestions; Martin sets each topic up himself. A client starts with "General" only.

**M3d** A bundle whose renewals are at different BM+ stages: until Martin drags its card, should it sit at the **least advanced** renewal's stage, with "2 of 3 at Proposals" on it?
→ **Answered 05.11.2026:** yes, the **least advanced** renewal's stage, but Martin can **move the card freely**.

**M3e** Is BM+'s *Region* column usually already in the client's own scheme, so prefilling the client's regions from it is mostly right? Or should regions start empty?
→ **Answered 05.11.2026:** **use the existing regions** (BM+'s Region column) as the prefill; still editable per client (C4).

**M3f** Proposals: do they reach BM+'s Proposals sheet in time, or do you mostly want to record them yourself as the mails arrive?
→ **Answered 05.11.2026:** Martin will **mostly record them himself** and use them **for comparison**.

**M3g** The stewardship meeting: which period does it cover (calendar year, the client's own stewardship year, since the last meeting)? Is it needed on screen only, or also as an Excel / PDF to send?
→ **Answered 05.11.2026:** **it depends on the client**: the period is set **per client**.

**M3h** "Completed": per renewal only, or also a whole bundle at once?
→ **Answered 05.11.2026:** **also for the whole bundle** (built in 0.9.0).

**M3i** The date filters' calendar (from / until in the side panel) is drawn by the browser and can't be rounded with CSS like the dropdown lists (0.9.4). Is it worth replacing with MART's own small calendar (rounded, MART's colours, Monday first, DD.MM.YYYY), or keep the browser's?
→ **Answered 06.11.2026:** keep the browser's calendar: "it is fine".

**M3j** The Insurer Capability Database (0.9.6): MART matches a proposal's insurer to the network partners of the renewal's country by name ("Allianz" = "Allianz Lebensversicherungs-AG"). Does it find the right ones on your real renewals, or do you see wrong / missing matches?
→

**M3k** Is the Insurers page enough to choose whom to invite for a remarketing, or would you like more there, e.g. only partners that can pool the renewal's lines, or the countries of a whole bundle at once?
→

**M3l** The board (0.9.11) places a card from BM+'s three tasks: **Decision** = proposals done, policy update not started; **Post-renewal review** = all three BM+ tasks done but not yet marked completed by you; **Done** = every renewal marked completed by you. Does that match how you read the stages, or should a column mean something else?
→ **Answered 06.11.2026:** the columns are as Martin imagined them. His guideline for the **renewal pipeline** (now under each column, PLANNING §5): Not started = not kicked off · Strategy = kicked off, strategy pending · Proposals / Marketing = strategy decided, terms and proposals being collected · Decision = final proposals in, client decision pending · Update Policy = confirmed with the client, BM+ data to be updated · Post-renewal review = review all data, key learnings, savings, plan design changes, policy documents uploaded to BM+ · Done = all tasks completed.

**M3m** (QA, 07.11.2026) Home still has its "Your clients" cards, and the new Clients page (0.9.20) has larger ones. Should Home keep its small cards, link to the Clients page instead, or show only the clients that need you?
→

**M3n** (QA, 07.11.2026) On the bundle page, an empty "To-dos and notes on this bundle" is still a full card ("Nothing written here yet"). Should it become the slim one-line version the renewal page has (0.9.19)?
→
