# MART — Build plan for M3

**M3 goal:** *run a colleague status session in MART, and keep the record
for the yearly stewardship meeting.* Each client gets a board of its
bundles in their **actual** stage. MART keeps what really happened beside
BM+: the strategy, the proposals received, the plan design changes and
whether a renewal is completed. The client's own notes and to-dos are
organised into topics.

**Rhythm:** as in M1 and M2. One small increment per working day, each
ending with a zip and a short **"what to try"** list. Every change goes
through a pull request with its docs.

Status: **in progress.** Day 1 done (MART 0.9.0, 05.11.2026; 0.9.1 after Martin's notes: his strategy drawn neutral with a ✎, picked from one dropdown with "Canceled"). The foundations of M1
(`BUILD_PLAN_M1.md`) hold unchanged: nothing installed, all SQL in
`repository/`, append-only migrations, uploads never delete what you
wrote. Everything Martin records in M3 is USER data beside BM+'s data:
BM+ stays the record, and MART shows where the two differ.

---

## What Martin decided (05.11.2026, QUESTIONS C3–F3)

| Topic | Decision |
|---|---|
| Board columns (C3) | the proposal: **Not started · Strategy · Proposals / Marketing · Decision · Update Policy · Post-renewal review · Done** |
| Board layout (C4) | **one board per client**, filtered by **country**, **date** (from / until) and **region** |
| Regions | **per client, editable**: clients split the world differently (one has "Americas", another "LatAm" + "North America"), so each client gets its own country → region list |
| Actual state (D1) | the most important: **strategy**, and **proposals received: from whom and how many**. Also **mark a renewal completed** (that only happens once all tasks are submitted and approved), and an overview of **suggested plan design changes, implemented or not** |
| Stewardship | start building a **backlog per client**, so the renewals can be reviewed for the **yearly stewardship meeting** |
| MART ≠ BM+ (D2/D3) | **visible**, no automatic to-dos. Exporting to-dos would be nice; **not a priority** |
| Passed deadline (E5) | **keep it flagged**, no draft emails |
| Linked to-dos (F3) | **not needed**: subtasks do the job |
| A bundle at mixed stages (M3d) | until moved, the card sits at its **least advanced** renewal's stage; Martin can **move it freely** |
| Regions (M3e) | **use the existing regions**: BM+'s *Region* column prefills each client's list, which stays editable |
| Proposals (M3f) | Martin **mostly records them himself**, and uses them **for comparison** |
| Stewardship period (M3g) | **depends on the client**: set per client |
| Completed (M3h) | per renewal **and for the whole bundle** at once |

---

## Increments

| Day | Increment | What you can try |
|---|---|---|
| 1 ✅ | **Actual strategy + completed.** In the renewal panel, set **your** strategy beside BM+'s ("BM+: blank" / "BM+: Remarketing"), with an optional reason. Mark a renewal **completed** (with a date). MART suggests it once BM+'s three stages are done, but only you mark it. The cards show your strategy, a ≠ badge where BM+ differs, and ✓ completed. When an upload brings BM+ in line, the ≠ turns into "✓ BM+ caught up" by itself. A whole bundle can be marked completed from its header (M3h) | set a strategy BM+ doesn't have yet; mark a finished renewal completed |
| 2 | **Proposals received.** Mostly recorded by you as the mails arrive (M3f): per renewal, **insurer**, date received, first / final quote, **premium** (+ currency) and rate change, an optional note. Shown **side by side for comparison** against the expiring premium, with BM+'s Proposals sheet beside them for reference. The card and the bundle show "3 proposals: Allianz, AXA, Generali" | record the quotes you have for one remarketing and compare them |
| 3 | **Plan design changes.** A list per renewal: what changes, and its state: **suggested → agreed → implemented** (or dropped), with dates. Prefilled from BM+'s "types / reasons of plan design changes" as suggestions. A client-wide overview lists every change with its state | log a suggested change; mark one implemented; open the client overview |
| 4 | **Regions per client.** On the client page, a country → region list for THAT client, prefilled from BM+'s *Region* column (M3e: use the existing regions; yours to change). The explorer gets a **region** filter beside country and dates | set "LatAm" vs "North America" for one client and filter by it |
| 5 | **The board.** One per client: the columns above, a card per **bundle** (flag, name, date, renewals, strategy pills, proposals count, ≠ / stale / deadline badges, BM+ stage dots). Until you move it, a card sits at its **least advanced** renewal's stage ("2 of 3 at Proposals", M3d); drag it anywhere to record its **actual stage** (an optional one-line reason). Filters: country, region, from / until date. A card in a different column than BM+ says so ("BM+: Proposals") | run a status call from the board; drag a bundle into Decision |
| 6 | **Client topics.** Named, coloured topics inside a client (optional country, active / on hold / done). Client notes and to-dos sit in one topic each; the existing ones start in **General**. A **topic board** on the client notes page, plus **pinned notes** (key facts) at the top of their topic (PLANNING §5b) | make "Partner tracker" and "Implementation – Brazil" topics; pin the partner-file recipients |
| 7 | **Repeating to-dos.** Every N days / every N weeks on chosen weekday(s) / every N months. Ticking one creates the next with the next date (QUESTIONS M3b) | "release the partner tracker: every month" |
| 8 | **Stewardship view.** Per client, over **that client's own period** (set per client, M3g): each renewal with its strategy, the proposals received, the plan design changes (implemented or not), savings (from BM+) and the completed date, grouped by country. Kept after BM+ drops a completed renewal (MART never deletes one). Printable | open last year's view for one client and check it is what the meeting needs |
| 9 | **Hardening + M3 review.** Speed on a full book, wording, a day of real work | use M3 for a status call; list what's missing |

---

## How the pieces fit

- **Actual state** (days 1–3) is per **renewal**, stored beside BM+'s
  values with who / when / why and **BM+'s value at that moment**
  (PLANNING §1d). Three states: *in sync*, *BM+ behind* (yours is ahead),
  *conflict* (BM+ moved to something else). It is visible only: no
  to-dos are created (D2).
- **The board's stage** (day 5) is per **bundle**, because a card is a
  bundle (C2). Until you drag it, the card sits at its least advanced
  renewal's BM+ stage (M3d).
- **Regions** (day 4) are per **client**: a country → region list. They
  never change BM+'s data. The board and the explorer both filter on them.
- **Stewardship** (day 8) only reads what days 1–3 recorded, so the
  backlog grows on its own as you work.

---

## Open questions

None at the moment: M3d–M3h were answered on 05.11.2026 (see the table
above).

## Not in M3

- To-do export (D3: nice, not a priority), linked to-dos (F3),
  draft chase emails (E5), the post-renewal review checks (M5; the column
  exists on the board, the checks come later), Home's new shape (M4,
  with the AI plugin).
