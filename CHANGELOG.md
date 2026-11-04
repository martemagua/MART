# Changelog

What changed in each MART version, newest first. The version is in
`mart/__init__.py`, shown in MART's sidebar and in the zip's
`BUILD-INFO.txt`. Format: one section per version, grouped into **Added**,
**Changed**, **Fixed**; the "What to try" list is for testing it on the
laptop.

## 0.7.5 — 04.11.2026 · renewal panel: Renewal and Strategy stacked

### Changed (Martin's note on 0.7.4)
- **Renewal and Strategy are stacked** in the renewal panel instead of side
  by side: the strategy section holds much more. The Renewal section's
  short facts (insurer, period, kick-off, benefit owner, …) sit **two per
  row**, one per row in a narrow window.

### Fixed
- The renewal panel's link to its bundle's notes still carried the removed
  "group" setting in its address (harmless, now gone).

### What to try
Open a renewal: Renewal on top in two columns, Strategy below it.

## 0.7.4 — 04.11.2026 · moving renewals in an edit mode

### Changed (Martin's note on 0.7.3)
- **The tick boxes and the move bar only appear while moving.** A bundle
  shows its renewals plainly, with a **Move renewals…** button beside its
  name. That opens the edit mode: a tick box on each card, ticked cards
  outlined, and a bar that stays at the top while you scroll, with
  "N selected", **Select all** / **None**, the bundle to move to, and
  **Done** to leave without moving. **Move** only works once something is
  ticked; after moving you land on the target bundle, out of edit mode.
- Moving a single renewal from its own panel is unchanged.

### What to try
Open a bundle (no tick boxes), click **Move renewals…**, tick two, move
them into a new bundle; click **Done** in another bundle to leave without
moving.

## 0.7.3 — 04.11.2026 · renewal cards: name on top, policy number

### Changed (Martin's note on 0.7.2)
- **The policy name has the whole width of its card**, on top, with the
  tick box and the "⋯" links beside it; it was cut off in its narrow column.
- **The first field is the Entity, with the policy number below it** when
  BM+ has one. The Overview sheet has no policy number: it comes from the
  Renewal Strategy sheet (else Proposals, else Savings), as BM+ writes it
  ("(multiple)" included). The other fields are unchanged.

### What to try
Open a bundle with long policy names: the names are whole, and the policy
number sits under the entity.

## 0.7.2 — 04.11.2026 · date filters, one BM+ link, drag and drop

### Changed (Martin's notes on 0.7.1)
- **No more "By date / By country" toggle**: the country and date filters
  replace it. Bundles are listed by renewal month, each with its flag,
  country and date.
- **From / Until are dates with a calendar** instead of month dropdowns.
  The calendar opens on the client's own renewal dates, and the date shows
  the way Windows is set up (DD.MM.YYYY on a Swiss or German setup).
- **One BM+ link for the renewal.** The links to the individual tasks all
  opened the same page in BM+ (the renewal's workspace), so the "⋯" menu
  now offers the policy and one **Renewal in BM+** link, and the stage strip
  no longer repeats "Task in BM+" under each stage.

### Added
- **Drag and drop on the Uploads page**: drop one or several tracker files
  on the upload card and they go straight to the preview, as if chosen and
  sent. Only `.xlsx` files are taken (anything else is left out, and said
  so if nothing is left); a file dropped beside the card is ignored instead
  of the browser opening it. Choosing files still works.

### What to try
Open a client: no toggle; set From / Until with the calendar. Open a
renewal's "⋯": Policy and Renewal in BM+. Drag two trackers from Explorer
onto the upload card.

## 0.7.1 — 04.11.2026 · lighter pages, strategy colours, flags, filters

### Changed (Martin's notes on 0.7.0)
- **"Insurer Not Found" gives way to the Provider.** BM+ writes it when an
  insurer isn't in its list; the Provider column beside it then names who
  it is, and MART shows that (expiring, upcoming and in the proposals).
  Without a Provider, BM+'s words stay. Takes effect with the next upload.
- **To-dos and notes take less space**: **+ To-do** and **+ Note** buttons
  open the fields in a small box (the cursor is already in it); the lists
  only show when there is something in them.
- **The move bar's footnote is an ⓘ** that shows the hint on hover or tap.
- **Naming a bundle**: a ✎ pencil right beside the bundle's name replaces
  the "Name this bundle" button.

### Added
- **Strategy colours**: every strategy has its own colour, on the strategy
  pills (renewal cards, bundle header, renewal panel), as the left edge of
  each renewal card, and as small squares in the side panel showing which
  strategies a bundle holds (round dots stay status). Remarketing purple,
  Incumbent without RG blue, Incumbent with RG green, Non-expiring teal,
  Unknown / New Policy rose, TBC amber, none grey. Dark mode has its own
  shades.
- **Country flags** beside every country name: the bundle list (and its
  country headings), the bundle and renewal titles, To-dos and Home. They
  are images shipped with MART (the flag-icons set, MIT): Windows shows flag
  emoji as two letters. BM+'s long names ("Korea, Republic Of") are known;
  a name MART doesn't know shows without a flag.
- **Filters in the bundle list**: a country dropdown and **From / Until**
  month dropdowns (the months the client's renewals renew in), on top of the
  text filter. "4 of 35 bundles · Clear filters" says when one is on. They
  stay while you click through the client's bundles.

### Fixed
- **A client opened somewhere down the bundle list.** MART selected the
  next bundle to renew and scrolled the list to it, so every bundle renewing
  earlier (still in progress) sat above, out of sight. Opening a client now
  starts at the top of the list, with the top bundle selected, and without
  the filters used earlier. Clicking a bundle keeps the list where it was,
  and only the list ever scrolls to the selected bundle, never the page.

### Development
- **CI uses less than half the runner time**: Windows only (3.12 and
  3.14; the Linux job is dropped, MART runs on Windows), one run per change
  (pull requests and merges into `main`, not every branch push a second
  time), and a newer push to a PR cancels the run it replaces. It can also
  be started by hand from the Actions tab.

### What to try
Open a bundle: spot the strategies by colour; add a to-do with **+ To-do**;
hover the ⓘ; rename the bundle with ✎. Pick a country, then From / Until
months, click a few bundles (the filters stay), go back to Clients and open
the client again (top of the list, no filters). After the next upload,
check a renewal that showed "Insurer Not Found".

## 0.7.0 — 04.11.2026 · M1 day 7 · hardening

### Fixed
- **The database no longer grows with every upload.** The rows an upload
  was read into were kept after the commit although nothing needs them;
  they are now removed at commit, old ones are cleared (schema 6), and MART
  compacts the file at start when a quarter of it is free space. On the
  demo data: 7.5 MB → 1.1 MB, backups 405 KB → 73 KB.
- **What you write during the day is backed up**: every hour while MART
  runs (only when something changed; "Backups to keep" in Settings sets how
  many), besides the start and every upload.
- **A backup just before a database upgrade**, so an upgrade can always be
  undone with `MART.bat restore`.
- Two backups in the same second (an upload's and the hourly one) were
  ordered by their content hash, so MART could take the older one for the
  newest and write a duplicate; they are now ordered by when they were
  written.
- **A refused action explains itself and leads back**: "That didn't work",
  the reason, "Nothing was changed.", and a button back to the page you were
  on (the menu stays). Unexpected errors still name the log file.

### Checked (no change needed)
- A single-client upload only ever touches that client (test since 0.2.0).
- Renewals without BM+ ids ("Transitioned") are recognised by client,
  country, entity, policy and date, and marked "no BM+ id".

### What to try
Use MART for a full day of real work, then go through the **M1 review**
list in `BUILD_PLAN_M1.md`.

## 0.6.0 — 04.11.2026 · M1 day 6 · move renewals between bundles, history

### Added
- **Move renewals into your own bundles** (Martin, 04.11.2026: a policy BM+
  split into several renewals, product groups handled by different brokers,
  entities with their own policies). Bundles are still country + renewal
  date by default. On a bundle, tick one or several renewals and **Move the
  selected renewals to** an existing custom bundle of the same country, or
  to **a new bundle…** you name. On a renewal panel, **Move to another
  bundle** does the same for that one renewal. A custom bundle's renewals
  may have different dates (its header shows the range); **Rename** it from
  its header; "their own bundle (country + date)" moves renewals back. A
  bundle never mixes countries. An emptied custom bundle is kept and offered
  again. Placements are yours and survive every upload.
- **Name any bundle**: Rename / "Name this bundle" on the bundle header. A
  default bundle then reads "Poland · 01.01.2027 · *your name*"; clear the
  name to go back to country + date.
- **A bundle whose renewals all moved away stays** while it carries notes or
  open to-dos (0 renewals, "No renewals left in this bundle…"), so nothing
  you wrote is lost; without any, it simply goes.
- Custom bundles work like the others: notes and to-dos on them, on the To-dos
  page as "bundle “name”", counted on the Clients list.
- **History** on the renewal panel (folded, after the overview): every
  upload records what it changed: workflow status, strategy, insurer,
  upcoming insurer, renewal / kick-off / local meeting / client approval
  dates, expected rate change, benefit owner, local analyst, a new overview
  entry, and for its BM+ stage tasks status, due date, assignee, delegate,
  completion and peer-review approval; plus first seen / no longer in the
  export / back in the export. Each is dated by the export it came from
  ("Export of 10.11.2026"): BM+ does not say when something changed.

### What to try
1. In a bundle, tick two renewals and move them to a new bundle with a name;
   from another renewal's panel, move it into that bundle; rename it; move
   one back. Write a note on the custom bundle.
2. Upload a newer Renewal Tracker and Task Tracker, then open a renewal's
   **History**. (History starts with this version: earlier uploads were not
   recorded.)

## 0.5.1 — 04.11.2026 · client notes; notes from earlier renewals

### Added
- **Client notes and to-dos** (Martin, 04.11.2026): a space for things about
  the client as a whole. "Client notes & to-dos" at the top of the
  explorer's side panel opens it in the middle; the Clients list shows its
  counts next to the client. Client to-dos are on the To-dos page and Home
  like the others.
- **Notes from earlier renewals of the policy** on a renewal panel
  (Martin: "see legacy notes from past renewals"): folded under "Notes from
  earlier renewals of this policy", read-only, each with its renewal date
  and a link to that renewal. Cycles are matched by BM+'s stable policy id,
  so the history grows with every renewal MART keeps.

### What to try
Write a client note; open a renewal whose policy MART had last year (from
next year on, as MART keeps the renewals) to see last year's notes.

## 0.5.0 — 04.11.2026 · M1 day 5 · notes and to-dos

### Added
- **To-dos and notes on a renewal**: a "Your to-dos and notes" section on
  the renewal panel, right under the BM+ stages, marked *written in MART*
  (blue rail) so it is never mistaken for BM+ data. Add a to-do (title,
  optional due date) or a note in one line; tick a to-do off; edit or
  delete either under "Edit". The newest three notes show, older ones fold
  away; done to-dos fold away too.
- **To-dos and notes on a bundle** (all its renewals, like one mail
  covering several policies): the same section on the bundle view. A
  renewal's panel also shows its bundle's open to-dos and latest notes,
  with a link to the bundle.
- **Counts on the renewal cards** in a bundle: ☐ open to-dos, ✎ notes.
- **To-dos page** (new menu entry): every open to-do, overdue first, then by
  due date, undated last, each with its client, country, date and renewal
  (or "whole bundle") linking to it; done ones of the last 30 days below
  (or all of them).
- **Home**: a To-dos card with the open count, overdue, due in the next 7
  days, and the next five.
- Uploads never touch any of it: notes and to-dos stay on a renewal that
  changes or leaves the export.

### Fixed
- MART could not show a page with a timestamp on **Python 3.10** (it uses
  `datetime.UTC`, which only exists from 3.11). MART.bat accepts 3.10, so
  this now works there too.

### What to try
Work a real client for a while: add to-dos with due dates on a renewal and
on a bundle, write notes from a call, tick to-dos off on the To-dos page,
and look at Home. Tell me what is missing or in the way (more fields? a
note type? reminders?).

## 0.4.6 — 04.11.2026 · no Proposals stage for fixed-terms strategies

### Changed
- **Proposals reads "not needed"** when the renewal's upcoming strategy is
  *Incumbent with Rate Guarantee* or *Non-expiring* (Martin, 04.11.2026:
  those strategies have no Proposals stage in BM+). Before, it read "not in
  BM+ yet" as if something were missing. Shown on the stage strip and as a
  faint dotted stage dot. If BM+ does create a Proposals task anyway, MART
  shows that task.

### Fixed
- **The left menu stays put** while a page scrolls (Martin, 04.11.2026):
  it is as tall as the window, with the MART version at its bottom, instead
  of growing with the page and scrolling away.

### What to try
Open a renewal with *Incumbent with Rate Guarantee*: the Proposals stage
says "not needed". Scroll down a long renewal: the menu on the left stays.

## 0.4.5 — 04.11.2026 · renewal tasks only; every period type

### Changed
- **Only renewal tasks (Task Category "Renewal Workspace") are loaded**
  (Martin, 04.11.2026). Implementation and contract tasks are not, even
  when they name a policy; ones loaded before are removed at the next Task
  Tracker commit. The preview's column is now **Not loaded**.
- **The export's period works for every Date Type BM+ offers**: Renewal
  Date, Task Start Date, Task Due Date and Task Complete Date. "Not
  Specified" means no period.

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
