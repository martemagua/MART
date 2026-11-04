# MART — Project charter

> **Status: agreed v1.0 · 03.11.2026.** This says *why* MART exists, *what*
> it must achieve and *what it will not do*. Everything else (PLANNING.md,
> QUESTIONS.md, the mockup, the build) has to serve it. Changes go into the
> decision log (§11), together with what they displace.

---

## 1. Vision

**MART is my command center for every renewal I manage, so that each one
is delivered on time and closed properly, and nothing I've been promised or
asked for gets lost.**

What that means (Martin's words):

> MART is the center of operations for all the renewals I manage. It allows
> me to set the real state that the renewals are in, and keep track of
> deadlines, follow-ups, tasks, notes and promises. From upcoming renewals
> to post-renewal to-dos, over requests from the client and network
> partners. Everything is connected and reachable via AI.

---

## 2. The problem (why now)

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
7. **Peer review has no trail.** Issues found in the data the data analyst
   gathers from brokers, and the clarifications that follow, aren't tracked
   in one place.
8. **Requests from clients and network partners**, and the updates owed to
   them (e.g. on remarketings or plan design changes), aren't tracked.

---

## 3. Goals and how we'll know

| # | Goal | We'll know it works when… |
|---|---|---|
| G1 | **Orient in minutes** | Opening MART (or asking the agent) tells me what needs attention today in **under 5 minutes**, without opening BM+ or the trackers |
| G2 | **Show the real state** | Every renewal where BM+ lags shows as such; the board is used on a shared screen **without verbal corrections** |
| G3 | **Never miss a promise** | Every deadline a broker gives is recorded in **under 30 seconds**, and **none passes silently**: it is met, or flagged the day it passes |
| G4 | **See what moved and what's quiet** | New and stale overviews are visible per client and per renewal; with no promise open, no renewal goes **more than 14 days** without me noticing |
| G5 | **Close renewals properly** | Every completed renewal gets a post-renewal review; savings and plan design changes are recorded for **100% of closed renewals** |
| G6 | **Work with my AI agent** | The agent can plan my day and capture notes, to-dos, deadlines and actual state through MCP, and its answers match what MART shows |
| G7 | **One place per renewal** | Everything about a renewal (state, notes, to-dos, deadlines, overview, history) is on one screen |
| G8 | **Peer review with a trail** | Every issue I find in the analyst's data is logged as a clarification, and none is closed without an answer |
| G9 | **Proposal register** | First and final quote per insurer, the accepted proposal and its date are recorded for every renewal |
| G10 | **Requests answered on time** | Every request from a client or network partner, and every update owed to them, is logged with a due date and done on time |

**Overall success test:** after 4 weeks of real use, MART is the first
thing I open every morning, and I've stopped keeping renewal follow-ups
anywhere else (Excel, sticky notes, mail flags).

---

## 4. Users and the moments MART serves

Martin is the only user. Colleagues see MART on his shared screen.

| Who | Moment | What MART must do then |
|---|---|---|
| Martin | **Morning**: "where am I?" | Home + the agent's day plan |
| Martin | **Working a client** | Client page: renewals by bundle → renewal detail |
| Martin + colleagues (shared screen) | **Status session** | Kanban with actual vs BM+ state |
| Martin | **Broker call or mail** | Capture a deadline, note or to-do in seconds (UI or agent) |
| Martin | **Peer review** | Log issues and clarifications on the analyst's data |
| Martin | **After a renewal** | Post-renewal review + knowledge capture |
| AI agent | **Any time** | Read everything, write everything except BM+ data, through MCP |

---

## 5. Scope

### v1: must (MART is useful from day one)
- Upload the BM+ **Task and Renewal Trackers** (cross-client and per
  client), only for "my clients", keeping history: completed renewals stay
- Clients → renewals bundled by country + date (split and join) → renewal detail
- Notes and to-dos on renewals and bundles
- Overview freshness: new / stale
- Broker deadlines, met automatically or by hand, flagged when overdue
- Actual state vs BM+ + discrepancy flags
- Kanban board by actual state, cards that change by column
- Home with client cards + Today
- AI plugin v1: MCP server + navigation skill

### v2: should
- Benefit Tracker upload (feeds the post-renewal checks)
- Post-renewal review checks + waivers
- Knowledge base: savings, plan design changes, lessons, client facts
- Proposal register (from the Proposals sheet, plus by hand)
- Peer review log
- Requests and partner communications
- Reminders to Outlook (.ics) and chaser ladder with email drafts
- AI plugin: daily-plan and capture skills, report templates

### Later: could
- Playbook: back-scheduled milestones from the renewal date, health (RAG)
- Reporting: cycle times, savings totals, audit pass rate
- Meeting prep / agenda

### Won't (non-goals)
- ❌ **Replace BM+** or write anything back into BM+. BM+ stays the system of record
- ❌ **Analytics / book exploration** (premium development, peer comparisons, maps)
- ❌ **Reading mailboxes** from MART itself. Capture is by you or your agent
- ❌ **Multi-user with logins**
- ❌ **Cloud hosting.** Runs locally on your machine

---

## 6. Principles: how we decide when in doubt

1. **BM+ is the record, MART is the reality.** Both are shown, and neither
   overwrites the other.
2. **Nothing is lost.** Uploads never delete your data or a renewal's
   history; a completed renewal stays.
3. **Capture must be faster than forgetting.** Adding a deadline, note or
   to-do takes seconds, from wherever you are.
4. **One renewal, one screen.**
5. **The AI writes only your data** (never BM+ data), is always marked as
   AI with its source, and every AI change can be seen and undone.
6. **Show, don't nag.** Signals are visible and ranked; reminders are
   deliberate, not noise.
7. **Simple beats clever.** A feature that isn't used in the first month
   gets cut or reworked.

---

## 7. Constraints

- Single user, local work laptop, confidential client data: no cloud services.
- Data comes from BM+ Excel exports uploaded by hand; MART only knows what has been uploaded.
- **Nothing can be installed**: Python 3.12 + the standard library +
  preinstalled `openpyxl`, plus pure-Python code shipped inside MART.
  Delivered as an unzip-and-run folder (PLANNING §7).
- **The data and backup folders are chosen in MART's settings** (first start
  asks; sensible defaults offered). The live database never runs from a
  synced folder.
- **Time for testing: 3–4 hours a day.**
- **Desktop only** (landscape and portrait windows); no phone layouts.

---

## 8. Assumptions and risks

| Assumption / risk | If wrong… | Mitigation |
|---|---|---|
| Trackers are uploaded often enough (daily or weekly) | Freshness and "BM+ caught up" signals lag | Show "as of last upload" everywhere; agree on an upload rhythm |
| BM+ export layouts stay stable | Ingestion breaks | Column names in one spec file; header rows detected, never fixed; warnings on unknown headers |
| You keep recording actual state and deadlines | Board and Home drift from reality | Very fast capture; the agent captures from notes and mails |
| Python 3.12 / `openpyxl` stay on the laptop | MART won't start | Start-up check with a clear message; fallback: ship Python's embeddable zip |
| Scope creep | v1 never ships | This charter: anything not in v1 waits |

---

## 9. How we work together

- **Roles:** Martin = product owner (decides what and why, tests with real
  work). Claude = builds, proposes, and flags trade-offs and risks.
- **Rhythm:** with 3–4 hours of testing a day, **small daily increments**.
  Each ends with a zip you can unzip and try with a real tracker, and a
  short "what to try" list.
- **Changing scope:** allowed, but it goes into the decision log (§11) with
  what it displaces.
- **Definition of done for a feature:** works with a real-structure export,
  has tests, is described for the AI agent (skill / MCP), and you have
  tried it.

---

## 10. Milestones

| Milestone | Contents | You can… |
|---|---|---|
| M0 | Charter agreed ✅, blocking questions answered ✅ | — |
| M1 | Upload + clients + bundles + renewal detail + notes/to-dos | find any renewal and write on it |
| M2 | Freshness + broker deadlines + Home | start your day in MART |
| M3 | Actual state + Kanban | run a colleague status session in MART |
| M4 | AI plugin v1 | ask your agent to plan your day |
| M5 | v2 items, starting with the post-renewal review and knowledge base | close renewals properly |

---

## 11. Decision log

| Date | Decision |
|---|---|
| 02.11.2026 | MART is built new and standalone; MAPT NEO is reference only |
| 02.11.2026 | AI plugin (MCP + skills + templates) is part of MART |
| 03.11.2026 | Single user; colleagues see MART on a shared screen |
| 03.11.2026 | Runtime: Python 3.12, nothing installed, delivered as a portable zip |
| 03.11.2026 | The AI app's plugin format = Claude Code plugin layout; MART generates its own plugin |
| 03.11.2026 | Knowledge base in MART; savings still recorded in BM+ |
| 03.11.2026 | Data and backup folders are set in MART's settings |
| 03.11.2026 | Time for testing: 3–4 hours a day → daily increments |
| 04.11.2026 | Desktop only (landscape and portrait); the client page is an explorer: bundles on the side, the bundle in the middle |
| 03.11.2026 | **Charter agreed (v1.0)**, with goals G8–G10 added and the Benefit Tracker moved to v2 |
