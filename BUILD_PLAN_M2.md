# MART — Build plan for M2

**M2 goal:** *start your day in MART.* See which renewals have new overview
entries and which have gone quiet, keep the dates brokers promise, give
to-dos the detail real work needs, and open Home on what is due today.

**Rhythm:** as in M1. One small increment per working day, each ending with
a zip and a short **"what to try"** list. Every change goes through a pull
request with its docs.

Status: **done** (reviewed 05.11.2026, MART 0.8.5). Day 1 done (MART 0.8.0, 04.11.2026). Day 2 done (MART 0.8.1, 04.11.2026). Day 3 done (MART 0.8.2, 04.11.2026). Day 4 done (MART 0.8.3–0.8.4, 05.11.2026). Day 5 done (MART 0.8.5 + the review, 05.11.2026). The foundations of M1
(`BUILD_PLAN_M1.md`) hold unchanged: nothing installed, all SQL in
`repository/`, append-only migrations, uploads never delete what you wrote.

---

## What the M1 review decided (QUESTIONS E1–E4, F2, G1, K4, M2a)

| Topic | Decision |
|---|---|
| Stale overview | amber after **7 days** without a new overview entry, red after **14**; both in Settings → Time limits |
| New overview entry | by the **date written on the entry** (its `DD MMM YYYY:` header); entries dated within the last N days are new (N in Settings, proposed 7) |
| Which entries count | **all** of them; "client ready" is a toggle that is sometimes forgotten |
| Broker deadline vs to-do | **two different things** (Martin, 04.11.2026): a **broker deadline belongs to a bundle**, the date you expect an update on those renewals; a **to-do** is a task of your own, on a renewal, a bundle or the client (no country-wide to-dos, M2c) |
| Broker deadline fulfilled | **you confirm it**; MART only points out a new entry dated on or after the promise |
| Prefill | from the Renewal Strategy sheet's **"Expected date to receive the final renewal terms"** when BM+ has it |
| Reminders | **inside MART** (Home); the AI agent (M4) and an email brief later |
| Richer to-dos | **subtasks**, **description**, **urgency**, **delegated / waiting on** |
| Home | not settled; start with **"Today"** and simple client cards, adjust from use |

---

## Increments

| Day | Increment | What you can try |
|---|---|---|
| 1 ✅ | **Overview freshness.** Each renewal gets the date of its newest overview entry and a state: fresh / amber (≥ 7 days) / red (≥ 14). Entries dated within the last N days are marked **new**. Shown on the renewal cards, rolled up per bundle in the side panel (the worst one wins) and in the renewal panel's overview. The two limits and N in Settings → Time limits | open a client: spot the quiet bundles in the side panel, and the new entries in a renewal's overview |
| 2 ✅ | **Richer to-dos** (your own tasks). A to-do gets a **description**, **subtasks** (tick them one by one; "2 of 3" on the to-do), **urgency** (urgent / normal / low) and **delegated / waiting on** (whom: you, broker, insurer, client, colleague; since when). Status: open → in progress → waiting → done. Existing to-dos keep everything they have | turn one real to-do into a checklist, hand one to a broker, mark one urgent |
| 3 ✅ | **Broker deadlines on bundles.** A bundle gets an **expected update date** ("terms by 15.11", who promised it, an optional note), set from the bundle header with a ✎ like its name. Prefilled from BM+'s expected-terms date of its renewals (see below), shown as "from BM+", yours to keep, change or drop. While the date is ahead, the bundle's renewals are **not stale**; once it has passed, the bundle turns red until you confirm the update arrived (or set a new date). MART points out a new overview entry dated on or after the promise. The date shows in the side panel, on Home and on each renewal of the bundle | set "terms by 15.11" on a bundle from a broker mail; see a prefilled one; confirm one |
| 4 ✅ | **Home: "Today".** One list of what needs you: deadlines due or passed, to-dos due or overdue (urgent first), renewals gone red, new overview entries since yesterday. Below it, a simple card per client (renewals in flight, next renewal date, counts of the above). Adjusted from your use | start a day from Home; tell me what is missing or in the way |
| 5 ✅ | **Hardening + M2 review.** Speed on a full book, upload edge cases found on the way, wording; a day of real work | use M2 for a full day; list what's missing |

---

## Broker deadlines: decided (Martin, 04.11.2026)

The plan first proposed one reminder system (a deadline as a to-do waiting
on someone). Martin decided otherwise, and it fits how the work runs:

- a **broker deadline belongs to a bundle**: when you expect updates for
  those renewals. One open deadline per bundle at a time; confirmed ones
  stay in the bundle's history;
- a **to-do** is something *you* have to get done, about renewals or
  countries. To-dos keep their own list, with the M2 extras (day 2);
- **BM+ prefill**: BM+ writes "Expected date to receive the final renewal
  terms" per renewal. A bundle without a deadline of yours gets the
  **earliest** of its renewals' dates, with each renewal's own date shown
  beside it; if BM+'s date changes later, MART shows the new one next to
  yours instead of moving yours;
- the deadline hangs on the bundle like its notes do: a renewal moved to
  another bundle follows that bundle's deadline.

---

## Still open (not blocking M2)

- **G1** What a client card on Home should show: still not clear after the
  review (Martin goes straight to a client page or to the To-dos). Home stays
  as it is and becomes the place where the AI agent works (M4, QUESTIONS G2).
- **E5** When a deadline passes: flag it only (M2), or also start a chase
  with a draft email (later, with the chaser ladder)?
- **F3** "Waiting on X since Y" comes with the richer to-dos; simple
  dependencies between to-dos stay out unless you miss them.
- ~~**M2c** To-dos on a client's country as a whole?~~ No (Martin,
  04.11.2026): keep them with the bundle. To-dos stay on a renewal, a
  bundle or the client.

## M2 review (after a full day of real work)

**M2's promise:** *start your day in MART.* What 0.8.5 gives you:

| Goal | In M2 | Not yet (planned) |
|---|---|---|
| G1 Orient in minutes | Home "Today" (passed / near expected updates, due or urgent to-dos, new overview entries, quiet bundles) and a card per client | what a client card should show (G1, from your use) |
| G4 What moved / what's quiet | amber after 7 days, red after 14, by the date on the newest entry; "new" marks; a bundle shows its quietest renewal | — |
| G3 Never miss a promise | broker deadlines on bundles, prefilled from BM+, pausing the stale clock, red until you confirm | a chase with a draft mail when one passes (E5, later) |
| To-dos | urgency, status, waiting on whom since when, description, subtasks | client topics, pinned notes, repeating to-dos, a to-do board (M3) |
| Speed | Home under half a second on 4,500 renewals | — |

**Questions for the review:**
- Did Home show what you needed first thing, in the right order?
- Were the amber / red limits right, or too noisy / too quiet?
- Did the BM+ prefill create deadlines you wanted, or noise?
- Which to-do extras did you actually use?

**Answers (Martin, 05.11.2026):**

| Question | Answer | What follows |
|---|---|---|
| Home | not sure what belongs there; Martin goes **straight to a client page or to the To-dos**. Home is likely where the **AI agent** will work later | Home stays as it is for now; it is reshaped with the AI plugin (M4, QUESTIONS G2) |
| Amber / red limits | **the colours are right** (7 / 14 days) | kept |
| BM+ prefill | **works well** | kept |
| To-do extras | **all of them** used: description, subtasks, urgency (and status / waiting on) | kept; the to-do board (M3) builds on them |
| Client card (G1) | not sure, as for Home | left open, revisited in M4 |

**M2 is done.** Next: M3, see `BUILD_PLAN_M3.md`.
