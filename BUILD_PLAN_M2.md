# MART — Build plan for M2

**M2 goal:** *start your day in MART.* See which renewals have new overview
entries and which have gone quiet, keep the dates brokers promise, give
to-dos the detail real work needs, and open Home on what is due today.

**Rhythm:** as in M1. One small increment per working day, each ending with
a zip and a short **"what to try"** list. Every change goes through a pull
request with its docs.

Status: **planned** (04.11.2026, after the M1 review). The foundations of M1
(`BUILD_PLAN_M1.md`) hold unchanged: nothing installed, all SQL in
`repository/`, append-only migrations, uploads never delete what you wrote.

---

## What the M1 review decided (QUESTIONS E1–E4, F2, G1, K4, M2a)

| Topic | Decision |
|---|---|
| Stale overview | amber after **7 days** without a new overview entry, red after **14**; both in Settings → Time limits |
| New overview entry | by the **date written on the entry** (its `DD MMM YYYY:` header); entries dated within the last N days are new (N in Settings, proposed 7) |
| Which entries count | **all** of them; "client ready" is a toggle that is sometimes forgotten |
| Broker deadline fulfilled | **you confirm it**; MART only points out a new entry dated on or after the promise |
| Prefill | from the Renewal Strategy sheet's **"Expected date to receive the final renewal terms"** when BM+ has it |
| Reminders | **inside MART** (Home); the AI agent (M4) and an email brief later |
| Richer to-dos | **subtasks**, **description**, **urgency**, **delegated / waiting on** |
| Home | not settled; start with **"Today"** and simple client cards, adjust from use |

---

## Increments

| Day | Increment | What you can try |
|---|---|---|
| 1 | **Overview freshness.** Each renewal gets the date of its newest overview entry and a state: fresh / amber (≥ 7 days) / red (≥ 14). Entries dated within the last N days are marked **new**. Shown on the renewal cards, rolled up per bundle in the side panel (the worst one wins) and in the renewal panel's overview. The two limits and N in Settings → Time limits | open a client: spot the quiet bundles in the side panel, and the new entries in a renewal's overview |
| 2 | **Richer to-dos.** A to-do gets a **description**, **subtasks** (tick them one by one; "2 of 3" on the to-do), **urgency** (urgent / normal / low) and **delegated / waiting on** (whom: you, broker, insurer, client, colleague; since when). Status: open → in progress → waiting → done. Existing to-dos keep everything they have | turn one real to-do into a checklist, hand one to a broker, mark one urgent |
| 3 | **Broker deadlines.** A deadline is a to-do *waiting on* someone with a **promised date** (see the design note below). Prefilled from BM+'s expected-terms date when there is one (shown as "from BM+", yours to keep, change or drop). A future deadline **pauses the stale clock**; a passed one turns red until you confirm it. MART points out a new overview entry dated on or after the promise | record "terms by 15.11" from a broker mail; see a prefilled one from BM+; confirm one |
| 4 | **Home: "Today".** One list of what needs you: deadlines due or passed, to-dos due or overdue (urgent first), renewals gone red, new overview entries since yesterday. Below it, a simple card per client (renewals in flight, next renewal date, counts of the above). Adjusted from your use | start a day from Home; tell me what is missing or in the way |
| 5 | **Hardening + M2 review.** Speed on a full book, upload edge cases found on the way, wording; a day of real work | use M2 for a full day; list what's missing |

---

## Design note to confirm on day 1: one reminder system

PLANNING §2 asks for **one reminder engine**, not to-dos + deadlines +
chasers as separate things. With "delegated / waiting on" and a due date, a
to-do already says *"waiting on Broker A, by 15.11"*. So M2 proposes:

- a **broker deadline is a to-do** that waits on someone and carries a
  promised date. It shows on the to-do lists, on Home, and in the renewal
  or bundle it belongs to, like every other to-do;
- what makes it a deadline: it **pauses the stale clock** of its renewal or
  bundle until the date, and on the date it turns red until you confirm it;
- the BM+ prefill creates such a to-do once per renewal cycle, marked
  "from BM+"; if BM+'s date changes later, MART shows the new date beside it
  instead of moving yours.

The alternative, a separate "deadlines" list next to the to-dos, is closer
to the first PLANNING sketch but means two places to look. Decide before
day 3.

---

## Still open (not blocking M2)

- **G1** What a client card on Home should show: we learn it on day 4.
- **E5** When a deadline passes: flag it only (M2), or also start a chase
  with a draft email (later, with the chaser ladder)?
- **F3** "Waiting on X since Y" comes with the richer to-dos; simple
  dependencies between to-dos stay out unless you miss them.

## M2 review (after a full day of real work)

**M2's promise:** *start your day in MART.* Questions for the review:
- Did Home show what you needed first thing, in the right order?
- Were the amber / red limits right, or too noisy / too quiet?
- Did the BM+ prefill create deadlines you wanted, or noise?
- Which to-do extras did you actually use?
