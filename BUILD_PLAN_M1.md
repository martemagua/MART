# MART — Build plan for M1

**M1 goal:** *find any renewal and write on it.* Upload the Task and
Renewal Trackers, see your clients, their renewals bundled by country +
date, open a renewal, and add notes and to-dos.

**Rhythm:** one small increment per working day. Each one ends with a zip
you unzip over the previous version (your data folder is never touched),
plus a short **"what to try"** list. Your feedback steers the next day.

Status: **in progress.** Day 1 done and verified on both machines (04.11.2026). Day 2 done (MART 0.2.0) and verified on the laptop with real exports of both flavours (04.11.2026). Day 3 done (MART 0.3.0) and verified on the laptop (04.11.2026). Day 4 done (MART 0.4.0–0.4.6) and verified on the laptop (04.11.2026). Day 5 done (MART 0.5.0–0.5.1, 04.11.2026). Day 6 done (MART 0.6.0, 04.11.2026). Day 7 done (MART 0.7.0, 04.11.2026), Martin's notes on it in 0.7.1 (lighter pages, strategy colours, flags, panel filters, opening at the top) 0.7.2 (date filters, one BM+ renewal link, drag and drop) 0.7.3 (cards: name on top, policy number) 0.7.4 (moving renewals in an edit mode) and 0.7.5 (Renewal and Strategy stacked); the M1 review is next.

---

## Foundations (true for every increment)

| Topic | Decision |
|---|---|
| Runtime | Python 3.12 + standard library + preinstalled `openpyxl`; pure-Python code only, shipped in the folder (PLANNING §7) |
| Start | `MART.bat`: start-up check → backup → server on `127.0.0.1` → opens the browser |
| Data | SQLite file in the data folder chosen in Settings; schema changes as numbered migrations, applied on start |
| BM+ columns | every Excel column name lives in one spec file per tracker; header rows detected, never fixed |
| Layers | ingestion → repository (all SQL) → services → web (pages) — the same strict layering that kept MAPT maintainable |
| Tests | automated tests run here before every zip, on **synthetic** workbooks built to the real structure (no client data, nothing in git) |
| Your data | uploads never delete your notes, to-dos or a renewal's history |

---

## Increments

| Day | Increment | What you can try |
|---|---|---|
| 1 ✅ | **Skeleton**: `MART.bat`, start-up check, first-run **Settings** (data folder, backup folder), empty Home, database created, automatic backup on start | unzip, double-click, choose your folders, see MART open in the browser; restart and see the backup appear |
| 2 ✅ | **Renewal Tracker upload**: detect tracker + flavour (cross-client / per client), **preview before commit** (clients found, renewals, warnings), **"My clients"** picker so demo clients are ignored, commit | upload a cross-client Renewal Tracker, tick your clients, commit; upload it again and see "no changes" |
| 3 ✅ | **Clients and bundles**: client list; the client **explorer** (Martin, 04.11.2026): bundles (country + renewal date) in a side panel, grouped by month or by country, with a filter; the selected bundle's renewals in the middle, each with its **renewal overview** compared against the client-ready one (MAPT's approach) | open each client, walk its bundles, check the overview marks |
| 4 ✅ | **Task Tracker upload + renewal detail**: tasks linked to *this* cycle (stable id + per-cycle id), renewal panel with BM+ facts, the stage strip (Renewal Strategy → Proposals → Update Policy + peer review state), the dated overview timeline, the Renewal Strategy sheet's fields, proposals and savings. Also: **several files in one upload**, **"overview as of"** per client and **Settings → Time limits** (Martin, 04.11.2026) | open a renewal and compare it with BM+; upload several single-client exports at once |
| 5 ✅ | **Notes and to-dos** on renewals and on bundles; a simple To-dos page (open / done, due date) | write notes and to-dos while working a real client |
| 6 ✅ | **Move renewals between bundles** (Martin chose this over split/join: renewals move, one or several, into a named custom bundle of the same country; any bundle can be named) + **history**: re-uploads keep completed renewals and record what changed | move renewals into a custom bundle, re-upload a newer export, check nothing you wrote was lost |
| 7 ✅ | **Hardening**: per-client uploads that replace only that client, renewals without ids ("Transitioned") identified and flagged, clear error messages, first M1 review | use M1 for a full day of real work; list what's missing |

After day 7 we review M1 together, adjust the plan, and move to **M2**
(freshness, broker deadlines, Home, and richer to-dos: QUESTIONS M2a). The
to-do board comes in M3 with the Kanban (Martin, 04.11.2026).

---

## M1 review (after a full day of real work)

**M1's promise:** *find any renewal and write on it.* What 0.7.0 gives you,
against the charter goals it touches:

| Goal | In M1 | Not yet (planned) |
|---|---|---|
| G7 One place per renewal | renewal panel: BM+ stages + peer review, facts, strategy, proposals, savings, overview (client-ready gaps marked), your to-dos and notes, notes of earlier cycles, history, links to BM+ | deadlines (M2), actual state (M3) |
| G4 What moved / what's quiet | overview timeline per renewal, "overview as of" per client with a time limit | new / stale per renewal, "seen" marks (M2) |
| G9 Proposal register | first and final quote per insurer (from BM+) | the accepted proposal as your own record (M5) |
| G1 Orient in minutes | Home: renewals + to-dos card; To-dos page | the "Today" strip and client cards (M2) |
| G3 Never miss a promise | to-dos with due dates | broker deadlines that defer the stale clock (M2) |
| G2 Show the real state | — | actual state + Kanban (M3) |
| G6 Work with my AI agent | — | MCP + skills + templates (M4) |

**Try during the day, and note what gets in the way:**
1. Upload the morning's exports (Renewal + Task Tracker, cross-client and
   your main single-client ones) in one go.
2. Find three renewals you are working on: how many clicks, and was the
   information right and complete compared with BM+?
3. Arrange one client's bundles the way you actually work them.
4. Capture everything from one call or mail as notes / to-dos in MART.
5. End of the day: is what you wrote all there (and in the backup folder)?

**Questions for the review (they shape M2):**
- What did you still have to open BM+ or a tracker for?
- Which to-dos were really *deadlines a broker gave you*? (M2 turns those
  into deadlines that defer the stale clock.)
- What should Home show first thing in the morning?
- Anything that felt slow, cluttered or in the wrong place?

---

## What I need from you along the way

- **Day 2:** a current cross-client **Renewal Tracker** export (demo data is fine), as before. Real data stays on your laptop.
- **Day 3:** what you didn't like about the mockup (look, layout, density). It decides the visual style before the pages multiply.
- **Day 4:** a current **Task Tracker** export.
- Every day: 10 minutes of feedback on the "what to try" list.
