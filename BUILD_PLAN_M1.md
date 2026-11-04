# MART — Build plan for M1

**M1 goal:** *find any renewal and write on it.* Upload the Task and
Renewal Trackers, see your clients, their renewals bundled by country +
date, open a renewal, and add notes and to-dos.

**Rhythm:** one small increment per working day. Each one ends with a zip
you unzip over the previous version (your data folder is never touched),
plus a short **"what to try"** list. Your feedback steers the next day.

Status: **in progress.** Day 1 done and verified on both machines (04.11.2026): MART 0.1.1 runs on the personal PC (Python 3.14) and the work laptop (Python 3.12); `make-zip.bat` builds the tested zip.

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
| 2 | **Renewal Tracker upload**: detect tracker + flavour (cross-client / per client), **preview before commit** (clients found, renewals, warnings), **"My clients"** picker so demo clients are ignored, commit | upload a cross-client Renewal Tracker, tick your clients, commit; upload it again and see "no changes" |
| 3 | **Clients and bundles**: client list, client page with renewals **bundled by country + renewal date**, counts and next renewal date | open each client and check the bundles look right |
| 4 | **Task Tracker upload + renewal detail**: tasks linked to *this* cycle (stable id + per-cycle id), renewal panel with BM+ facts, the stage strip (Renewal Strategy → Proposals → Update Policy + peer review state), the dated overview timeline, the Renewal Strategy sheet's fields | open a renewal and compare it with BM+ |
| 5 | **Notes and to-dos** on renewals and on bundles; a simple To-dos page (open / done, due date) | write notes and to-dos while working a real client |
| 6 | **Split and join bundles** (by entity, policy number, insurer; per client) + **history**: re-uploads keep completed renewals and record what changed | split a bundle, re-upload a newer export, check nothing you wrote was lost |
| 7 | **Hardening**: per-client uploads that replace only that client, renewals without ids ("Transitioned") identified and flagged, clear error messages, first M1 review | use M1 for a full day of real work; list what's missing |

After day 7 we review M1 together, adjust the plan, and move to **M2**
(freshness, broker deadlines, Home).

---

## What I need from you along the way

- **Day 2:** a current cross-client **Renewal Tracker** export (demo data is fine), as before. Real data stays on your laptop.
- **Day 3:** what you didn't like about the mockup (look, layout, density). It decides the visual style before the pages multiply.
- **Day 4:** a current **Task Tracker** export.
- Every day: 10 minutes of feedback on the "what to try" list.
