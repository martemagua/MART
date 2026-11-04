# Changelog

What changed in each MART version, newest first. The version is in
`mart/__init__.py`, shown in MART's sidebar and in the zip's
`BUILD-INFO.txt`. Format: one section per version, grouped into **Added**,
**Changed**, **Fixed**; the "What to try" list is for testing it on the
laptop.

## 0.4.4 — 04.11.2026 · tasks attach only to renewals MART has

### Changed
- **A task that belongs to no renewal in MART is not loaded** (Martin,
  04.11.2026: the renewals are the backbone, and the history grows from the
  renewals MART keeps). The preview shows them per client in a **No renewal**
  column, and the commit message counts them. Tasks loaded by 0.4.0–0.4.3
  that belong to no renewal are removed at the next Task Tracker commit for
  that client. Implementation tasks (Appointment, Upload Local Documents, …)
  carry no policy id in BM+, so they never attach.
- **Upload the Renewal Tracker first.** Uploaded together, Renewal Trackers
  now open before Task Trackers; a Task Tracker preview says so when a
  Renewal Tracker is still waiting.

### Fixed
- **A Task Tracker for a shorter period no longer reports older tasks as
  "no longer in the export".** BM+ records the export's period on General
  Information ("Date Type: Renewal Date, From … To …"); a task MART has
  whose renewal date lies outside it is not news.

### What to try
Upload a Renewal Tracker and a Task Tracker covering several years in one
go. The Renewal Tracker opens first; the Task Tracker preview shows how many
tasks have no renewal in MART. Then upload a Task Tracker for this year
only: nothing should read "no longer in the export".

## 0.4.3 — 04.11.2026 · a links menu on every renewal

### Changed
- **BM+'s renewal link is no longer offered:** the link the cross-client
  Renewal Tracker writes for the renewal doesn't open in BM+ (Martin,
  04.11.2026; the policy link does). MART keeps it, but doesn't show it.
- The renewal panel's main button is now **Policy in BM+**.

### Added
- A **"⋯" menu** on every renewal card in the bundle view and next to the
  renewal panel's title, with all the renewal's links: the policy in BM+ and
  each stage task in BM+. One open at a time; an outside click or Esc closes
  it. More kinds of links can join the same menu later.

### What to try
In a bundle, click "⋯" on a renewal card and open the policy and a task.
Tell me which task links work, and what other links you want in the menu.

## 0.4.2 — 04.11.2026 · straight to the preview, links to BM+

### Changed
- **Uploading several files opens the first preview straight away** (Martin,
  04.11.2026). It says how many files came and which could not be read;
  after you commit or discard it, MART opens the next one, as before.

### Added
- **Open in BM+** on the renewal panel, to make changes in BM+ directly.
  It is the link BM+ itself writes in the cross-client Renewal Tracker;
  MART keeps it when a single-client export (which has only bare ids)
  comes later. Without it, the button opens one of the renewal's tasks in
  BM+ and says so. Also a link to the expiring **policy** in BM+, and
  **Task in BM+** on each stage card. Links open in a new tab; MART never
  builds a link itself, it only uses `https://` links from the exports.

### What to try
1. Upload several files at once: you land on the first preview.
2. Open a renewal, click **Open in BM+**: it should open that renewal.
   Click **Task in BM+** on a stage. Tell me if any link lands on the wrong
   page.

## 0.4.1 — 04.11.2026 · trackers without some sheets

### Fixed
- **A Renewal Tracker created without some sheets no longer wipes them.**
  BM+ lets you leave out Renewal Strategy, Proposals or Savings. Before, an
  export without one of them showed every renewal as "changed" and, on
  commit, deleted what MART had from that sheet. Now a sheet that isn't in
  the export is not news: MART keeps what it has, compares only the sheets
  that are there, and the preview says so. A sheet that *is* there is the
  truth: a renewal with no rows in it really has none any more.
- The renewal panel marks a section kept from an earlier export: "from the
  export of 28.10.2026".

### What to try
Upload a full Renewal Tracker, then a slim one (e.g. without Proposals):
the preview says which sheets it lacks and shows no changes, and the
renewal panel still has the proposals, marked with the date of the export
they came from.

## 0.4.0 — 04.11.2026 · M1 day 4 · tasks and the renewal panel

### Added
- **Task Tracker upload**, both flavours, through the same preview →
  commit as the Renewal Tracker (MART recognises the tracker). Tasks are
  linked to *this* renewal cycle: the Task Tracker's `Policy ID` is the
  Renewal Tracker's per-cycle id; failing that, the stable policy id + the
  review date. Last year's tasks of the same policy never show as this
  year's. Like renewals, tasks are never deleted, only marked "no longer in
  the export".
- **Renewal panel**: click a renewal's name. Always in the same order: the
  glance (strategy, workflow, coverage) → the **BM+ stages** (Renewal
  Strategy → Proposals → Update Policy: status, due date, assignee,
  delegate, completed by, **peer review** approved / pending N days /
  rejected N times, due date moved N times) → the renewal facts and the
  **Renewal Strategy** sheet (incl. last renewal, claims, client-specific
  questions) side by side → **Proposals** (first and final quote per
  insurer) → **Savings** → the **renewal overview** → other BM+ tasks
  (implementation etc.) → the renewal feed and every field BM+ exported,
  folded away.
- **Stage dots** on every renewal card in the bundle view (one per stage,
  coloured by state, red ring = past due).
- **Several files in one upload** (e.g. all your single-client exports):
  each gets its own preview; after you commit or discard one, MART opens the
  next. One bad file doesn't stop the others.
- **"Overview as of"** per client: the report date of the last export that
  carried the overview (in practice the single-client export). Shown in the
  explorer's side panel and as a column on Clients, highlighted when out of
  date.
- **Settings → Time limits**: "Overview data out of date after" (7 days by
  default, 1–90). Stored with your data, so it is in the backups.

### Fixed / learned from the real exports
- Real cross-client Renewal Trackers have **no overview** either (0.3.0's
  note said they did): the overview comes from single-client exports.
- The two Task Tracker flavours name people differently (e-mail vs name),
  carry different columns and write dates as timestamps or dates; MART
  compares only the workflow facts both carry, so loading one flavour after
  the other shows "unchanged", and it keeps what the other flavour had for
  columns the current one lacks.
- BM+ task dates are real timestamps: MART now only rounds a time that is
  exactly on the hour or half hour (BM+'s midnight-UTC artefact), so a task
  completed at 14:32 keeps its own date.
- Implementation tasks (Appointment, Upload Local Documents, …) have UUID
  ids; they were skipped as "no id" before.

### What to try
1. Upload, in one go, the cross-client Renewal Tracker, a single-client
   Renewal Tracker and both Task Trackers. Walk through the previews.
2. Open a client: check "Overview as of" in the side panel and the stage
   dots on the cards.
3. Open a renewal you know well and compare the panel with BM+: stages,
   peer review, strategy, proposals, savings. Tell me what is missing, wrong
   or in the wrong place.
4. Settings → Time limits: set the limit to 1 day and watch the overview
   date turn orange on Clients.

## 0.3.0 — 04.11.2026 · M1 day 3 · client explorer

### Added
- **Clients** page: your clients with renewals, bundles, next renewal date,
  and how many renewals have no client-ready overview, gaps, or no overview.
- **Client explorer**: the client's bundles (same country + renewal date) in
  a side panel, grouped **by date** (month) or **by country**, with a filter
  (country, policy, entity, insurer). The selected bundle in the middle:
  renewal date and countdown, entities, insurers, the strategy and BM+
  workflow mix, and every renewal with coverage, insurer (→ upcoming
  insurer), strategy, workflow status and overview state. Opens on the next
  bundle to renew; the side panel keeps its scroll position.
- **Renewal overview** per renewal, like MAPT's renewals page: dated entries,
  newest first, with every line missing from the client-ready version
  marked, entries BM+ marked "(not client ready)" flagged, and older entries
  folded away.
- "Show / hide renewals no longer in the export".

### Fixed
- **Real cross-client exports carry the overview**: MART now takes a text
  stream from any export that fills it (the 0.2.0 rule, built on the demo
  files, would have ignored the overview of every cross-client upload).
- Overview entries only start at a line start: a date with a colon inside a
  sentence no longer splits an entry.
- Filters hide items reliably (`hidden` wins over layout rules).

### What to try
Open **Clients**, then one of your clients. Walk the bundles by date and by
country, filter for a country or an insurer, open a renewal's overview and
check the "not client-ready" marks against BM+.

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
