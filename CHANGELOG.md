# Changelog

What changed in each MART version, newest first. The version is in
`mart/__init__.py`, shown in MART's sidebar and in the zip's
`BUILD-INFO.txt`. Format: one section per version, grouped into **Added**,
**Changed**, **Fixed**; the "What to try" list is for testing it on the
laptop.

## 0.2.0 — 04.11.2026 · M1 day 2 · Renewal Tracker upload

### Added
- **Uploads page**: upload a Renewal Tracker export (cross-client or
  single-client), see a **preview** per client (new / changed / unchanged /
  not in the file), then **commit** or **discard**. The .xlsx itself is not
  kept, only what MART reads from it.
- **My clients**: tick your clients in the preview; MART remembers, and
  ignores the others on every later upload. A single-client export is
  ticked automatically. Filter box and "All visible / None" for long lists.
- Renewals are **never deleted**: one missing from a later export is kept
  and marked "no longer in the export", and comes back if it reappears.
- All four data sheets are kept: Renewal Overview, Renewal Strategy,
  Proposals, Savings.
- Safety: notice for an identical file, a block (with override) for an
  export older than the one loaded, a backup after every commit, a plain
  reason for a wrong file.
- Home shows what is loaded.

### Fixed / learned from the real exports
- Same-named renewals without BM+ ids ("Transitioned") can be different
  policies: distinct rows are never merged, only exact duplicates.
- Dates are rounded to the nearest midnight (BM+ exports midnight UTC in
  local time; the evening before for the Americas).
- The two export flavours spell the same data differently (URL vs bare ids,
  a Client Name column, header spelling): compared by content, not spelling.
- The cross-client export carries no overview text (only the Renewal Feed):
  neither flavour can blank a text stream that only the other carries.
- Upload times shown in local time, not UTC.

### What to try
Upload the real cross-client Renewal Tracker, tick your clients, commit;
upload it again (all "unchanged"); upload a single-client export.

## 0.1.1 — 04.11.2026 · launcher and zip builder

### Fixed
- `MART.bat` finds Python wherever it is installed (py launcher, per-user
  and machine-wide folders, PATH) and skips the Microsoft Store placeholder.
  MART runs on Python 3.12 and 3.14.

### Added
- `make-zip.bat` (on the PC with the repo): pulls the latest version,
  builds the zip, tests it, shows it in Explorer.
- `BUILD-INFO.txt` in the zip: version, commit, build date.

## 0.1.0 — 03.11.2026 · M1 day 1 · skeleton

### Added
- `MART.bat`: start-up check, database, backup on start, server on
  127.0.0.1, browser opens.
- First-start **setup** and **Settings**: data folder (never a synced
  folder), backup folder, backups to keep, port.
- Backups: consistent snapshot, gzipped, deduplicated, newest N kept;
  `MART.bat backup` / `restore`.
- Runs with nothing installed: standard library, preinstalled `openpyxl`,
  Jinja2 + MarkupSafe shipped in `vendor/`.
