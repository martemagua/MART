# MART — Project charter (DRAFT for agreement)

> This is the document we both agree on **before** building. It says *why*
> MART exists, *what* it must achieve, and *what it will not do*. Everything
> else (PLANNING.md, QUESTIONS.md, the mockup) has to serve it.
>
> How to use it: every section has a **draft** written by Claude from what
> Martin has said so far. Mark each one ✅ agree, ✏️ change (write the
> change), or ❌ remove. When every section is ✅, the charter is agreed and
> goes into §11 with a date.
>
> Status: **draft v0.1 · 02.11.2026 · not yet agreed**

---

## 1. Vision (one sentence)

> **Draft:** *MART is the one place where I see the real state of every
> renewal I manage, know what needs doing today, and never lose a promise,
> a deadline or a lesson, from the first signal to the post-renewal review.*

Shorter alternative: *"BM+ is the record. MART is the reality, and my plan."*

Decision: ☐ ✅ x ✏️ 
> MART is the center of operations for all the renewals I manage. it allows me to set the real state that
> the renewals are in, and keep track of deadlines, follow-ups, tasks, notes and promises. From upcoming
> renewals to post-renewal to-dos, over requests form the client and network partners. Everything is
> connected and reachable via AI.
______________________________

---

## 2. The problem (why now)

What hurts today. Draft, from your messages:

1. **BM+ lags reality.** Strategies get agreed but aren't submitted, and
   stages move on without BM+ showing it. In colleague meetings the system
   view has to be corrected verbally.
2. **Orientation costs time.** Starting the day means piecing together
   trackers, notes, mails and memory to know what needs attention.
3. **Promises get lost.** A broker says "update by Friday", and that date
   lives in a mailbox or in memory, not in a system that reminds you.
4. **Freshness isn't visible.** Which renewals have new overview comments
   and which have gone quiet is not obvious.
5. **Renewals end without closure.** Nobody checks systematically whether BM+
   was updated correctly afterwards, or whether savings and plan design
   changes were captured as knowledge.
6. **Notes and to-dos are scattered** and not attached to the renewal they
   belong to.

Missing or wrong? ______________________________

---

## 3. Goals and how we'll know (success measures)

A goal is an *outcome*, not a feature. Each has a measure, so we can tell
whether MART works.

| # | Goal | We'll know it works when… | Decision |
|---|---|---|---|
| G1 | **Orient in minutes** | Opening MART (or asking the agent) tells me what needs attention today in **under 5 minutes**, without opening BM+ or the trackers | ☐ |
| G2 | **Show the real state** | Every renewal where BM+ lags shows as such; the board is used in colleague sessions **without verbal corrections** | ☐ |
| G3 | **Never miss a promise** | Every deadline a broker gives is recorded in **under 30 seconds**, and **none passes silently**: it is met, or flagged the day it passes | ☐ |
| G4 | **See what moved and what's quiet** | New and stale overviews are visible per client and per renewal; no renewal goes **more than N days** without me noticing | ☐ |
| G5 | **Close renewals properly** | Every completed renewal gets a post-renewal review; savings and plan design changes are recorded for **100% of closed renewals** | ☐ |
| G6 | **Work with my AI agent** | The agent can plan my day and capture notes, to-dos and deadlines through MCP, and its answers match what MART shows | ☐ |
| G7 | **One place per renewal** | Everything about a renewal (state, notes, to-dos, deadlines, overview, history) is on one screen | ☐ |

Overall success test (proposal): **after 4 weeks of real use, MART is the
first thing I open every morning, and I stopped keeping renewal follow-ups
anywhere else** (Excel, sticky notes, mail flags).

---

## 4. Users and the moments MART serves

| Who | Moment | What MART must do then |
|---|---|---|
| Martin | **Morning**: "where am I?" | Home + the agent's day plan |
| Martin | **Working a client** | Client page: renewals by bundle → renewal detail |
| Martin + colleagues | **Status session** | Kanban with actual vs BM+ state |
| Martin | **Broker call or mail** | Capture a deadline, note or to-do in seconds (UI or agent) |
| Martin | **After a renewal** | Post-renewal review + knowledge capture |
| AI agent | **Any time** | Read everything, write only user data, through MCP |

Colleagues: viewers on a shared screen, or users themselves? (QUESTIONS A3)

---

## 5. Scope: what's in, in which order

Draft, using **must / should / could / won't (for now)**:

### v1: must (MART is useful from day one)
- Upload the BM+ trackers (Task, Renewal, Benefit), keeping history: completed renewals are kept
- Clients → renewals bundled by country + date → renewal detail
- Notes and to-dos on renewals and bundles
- Overview freshness: new / stale
- Broker deadlines, met automatically or by hand, flagged when overdue
- Actual state vs BM+ + discrepancy flags
- Kanban board by actual state
- Home with client cards + Today
- AI plugin v1: MCP server + navigation skill

### v2: should
- Reminders to Outlook (.ics) and chaser ladder with email drafts
- Post-renewal review checks + waivers
- Knowledge capture: savings + plan design changes
- AI plugin: daily-plan and capture skills, report templates

### Later: could
- Playbook: back-scheduled milestones from the renewal date, health (RAG)
- Reporting: cycle times, savings totals, audit pass rate
- Meeting prep / agenda, extraction templates (mail → deadline)

### Won't (non-goals): just as important
- ❌ **Replace BM+** or write anything back into BM+. BM+ stays the system of record
- ❌ **Analytics / book exploration** (premium development, peer comparisons, maps)
- ❌ **Reading mailboxes automatically** (v1). Capture is by you or your agent
- ❌ **Multi-user with logins** (v1), unless QUESTIONS A3 says otherwise
- ❌ **Cloud hosting.** Runs locally on your machine

Decision on scope tiers: ☐ ✅ ☐ ✏️ ______________________________

---

## 6. Principles: how we decide when in doubt

1. **BM+ is the record, MART is the reality.** Both are shown, and neither
   overwrites the other.
2. **Nothing is lost.** Uploads never delete your data or a renewal's
   history; a completed renewal stays.
3. **Capture must be faster than forgetting.** Adding a deadline, note or
   to-do takes seconds, from wherever you are.
4. **One renewal, one screen.**
5. **The AI writes only your data** (notes, to-dos, deadlines, suggestions),
   is always marked as AI, and never invents tracker facts.
6. **Show, don't nag.** Signals are visible and ranked; reminders are
   deliberate, not noise.
7. **Simple beats clever.** A feature that isn't used in the first month
   gets cut or reworked.

---

## 7. Constraints

- Single user, local machine (work laptop), confidential client data: no cloud services. *(confirm: QUESTIONS A5)*
- Data comes from BM+ Excel exports uploaded by hand; MART only knows what has been uploaded.
- Tech stack: open (QUESTIONS A6).
- Time: [HOW MUCH TIME PER WEEK CAN YOU GIVE TO TESTING AND FEEDBACK?]

---

## 8. Assumptions and risks

| Assumption / risk | If wrong… | Mitigation |
|---|---|---|
| Trackers are uploaded often enough (e.g. daily or weekly) | Freshness and "BM+ caught up" signals lag | Show "as of last upload" everywhere; agree on an upload rhythm |
| BM+ export layouts stay stable | Ingestion breaks | Column names in one spec file; warnings on unknown headers |
| You keep recording actual state and deadlines | Board and Home drift from reality | Make capture very fast; the agent captures from notes and mails |
| Scope creep (MAPT has many features) | v1 never ships | This charter: anything not in v1 waits |

---

## 9. How we'll work together

- **Roles:** Martin = product owner (decides what and why, tests with real
  work). Claude = builds, proposes, and flags trade-offs and risks.
- **Rhythm:** small increments; each one ends with something you can click
  and try with a real tracker.
- **Changing scope:** allowed, but it goes into the decision log (§11) with
  what it displaces.
- **Definition of done for a feature:** works with a real export, has
  tests, is described for the AI agent (skill/MCP), and you have tried it.

---

## 10. Milestones (proposal)

| Milestone | Contents | You can… |
|---|---|---|
| M0 | Charter agreed, questions answered | — |
| M1 | Upload + clients + bundles + renewal detail + notes/to-dos | find any renewal and write on it |
| M2 | Freshness + broker deadlines + Home | start your day in MART |
| M3 | Actual state + Kanban | run a colleague status session in MART |
| M4 | AI plugin v1 | ask your agent to plan your day |
| M5 | Reminders, post-renewal review, knowledge capture | close renewals properly |

---

## 11. Decision log

| Date | Decision |
|---|---|
| 02.11.2026 | MART is built new and standalone; MAPT NEO is reference only |
| 02.11.2026 | AI plugin (MCP + skills + templates) is part of MART |
| | *Charter agreed: ________* |
