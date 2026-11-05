# MART — guide for AI assistants

MART (Martin's Awesome Renewal Tool) is a local, single-user web app that
tracks renewals from BM+ tracker exports and lets Martin record the real
state, deadlines, notes and to-dos. Read `CHARTER.md` (why/what, agreed),
`PLANNING.md` (design), `TRACKER_MAP.md` (what the BM+ exports contain),
`CHANGELOG.md` (what each version did) and the current `BUILD_PLAN_*.md`
before changing anything.

## Working agreement (Martin, 04.11.2026)

- **Every change goes through a pull request** into `main`, never a direct
  push to `main`. Open the PR as soon as the work is pushed, describe it with
  `.github/pull_request_template.md` (what, why, how tested, docs, what to
  try), and keep it updated until it is merged. After a merge, start the next
  work from the new `main`.
- **Documentation is part of every change**, not a later task: update
  `CHANGELOG.md` (+ version in `mart/__init__.py` when MART changes), the
  README status line, this file's layout table/rules, the build-plan progress,
  `TRACKER_MAP.md` for anything new about the BM+ exports, and
  `QUESTIONS.md` for open questions. The PR template's checklist is the list.
- Commit messages say what changed and why, in plain words.

## Hard constraints (from the work laptop)

- **Python versions:** 3.12 on the work laptop, 3.14 on Martin's personal PC;
  CI runs both on Windows. `MART.bat` finds any real Python 3.10+ (test-runs
  each candidate, so the Microsoft Store placeholder is skipped).
- **Nothing can be installed there.** Runtime = Python 3.12 + standard
  library + preinstalled `openpyxl` + pure-Python code in `vendor/`.
  Never add a dependency that needs `pip install` or has compiled parts.
  New vendored code: pure Python only, licence in `vendor/LICENSES/`,
  listed in `vendor/README.md`.
- **No network** at runtime: no CDNs, no web fonts; every JS/CSS file ships
  in `mart/web/static/`.
- **Never commit tracker exports or client data.** `.gitignore` blocks all
  spreadsheets; tests build synthetic workbooks in code.
- The server binds to `127.0.0.1` only; `App.handle()` checks Host and
  Origin. Keep both.

## Layout (strict layers)

| Path | Holds |
|---|---|
| `MART.bat` | Windows launcher (CRLF line endings, see `.gitattributes`) |
| `mart/find-python.cmd` | the ONE Python search, shared by `MART.bat` and `make-zip.bat` |
| `make-zip.bat` | on the PC with the repo: git pull → build → verify → show in Explorer (not shipped) |
| `mart/__main__.py` | CLI: run (check → backup if an upgrade is due → schema → compact if ≥25 % free → backup → hourly backups → serve) · check · backup · restore |
| `mart/settings.py` | settings file (`%APPDATA%\MART\settings.json`, override `MART_SETTINGS_FILE`), validation; the live DB must never sit in a synced folder |
| `mart/startup.py` | start-up checks with plain-language messages |
| `mart/ingestion/` | reading BM+ exports: `sheet.py` (header row found by scanning, section labels, `section`/`after` to tell repeated headers apart, `Col.aliases` for names that differ by flavour, full row copy, `lookup`/`section_items` to read that copy back), `values.py` (`coverage_lines` = BM+'s comma-joined Lines of Coverage split outside brackets, which `product_groups` builds on; a time exactly on the hour/half hour with no seconds is BM+'s midnight-UTC artefact and rounds to the NEAREST midnight; a real timestamp keeps its own date; names, keys, leading numbers like "12 day(s)"), `ids.py` (BM+ ids from bare cells and URLs; `bm_link` = the plain https link BM+ wrote in a cell — MART never builds one), `renewal_tracker.py` (one Overview row = one renewal; key = per-cycle id → `policy:<stable>:<date>` → `name:…`; distinct rows are NEVER merged, exact duplicates are; the detail sheets are OPTIONAL in BM+ — `merge_details` keeps the stored rows of a sheet the export lacks, `details["_from"]` records which upload each sheet was last read from; the BM+ links (`fields.bm_url` / `bm_policy_url`) come only from cross-client exports, so `keep_links` carries them over a single-client one), `task_tracker.py` (one row = one task, key = the `taskId` — 24-hex or UUID; content compared on `specs.task_tracker.COMPARED` only, because the flavours differ in columns and in how they name people; `stage_state` trusts BM+'s status, incl. "Past Due") |
| `mart/ingestion/overview.py` | the renewal overview: dated entries (header `DD MMM YYYY:` at a LINE START), newest-first timeline, line-by-line comparison with the client-ready version (spacing/case ignored; BM+'s own "(not client ready)" marker counts), list flag `empty` / `no_cr` / `gaps` / `ok`; `flag` and `latest_date` are cached by the texts themselves (`lru_cache`, without today's date inside), so pages over a big book stay fast |
| `mart/ingestion/specs/` | **every Excel column name**, one module per tracker; the three text streams (overview all / client ready / feed) |
| `mart/repository/` | **all SQL**: `db.py` connections, `schema.py` append-only migrations, `uploads_repo`, `clients_repo` (`is_mine`: NULL undecided / 1 / 0; `overview_as_of`), `renewals_repo` (`for_client` leaves the detail sheets out; `details_of` fetches them in one query for the bundle shown), `tasks_repo` (an update keeps the stored value of every field the export has no column for), `state_repo` (the `user_state` key/value table), `notes_repo` (notes + to-dos: USER data on a target `(scope, ref)`; to-dos sort open → urgency → due date; `todo_steps` = subtasks, loaded for a whole list with `steps_for`), `bundles_repo` (custom bundles + which renewal sits in which: USER data), `deadlines_repo` (broker deadlines on bundles: USER data; one `open` row per bundle, `confirmed` / `dropped` / `replaced` = its history), `history_repo` (`changes`: append-only, one row per changed field or event per upload) |
| `mart/services/` | orchestration: `trackers` (one ADAPTER per tracker — recognise, parse, `keep` (which rows to load: tasks only when they are Renewal Workspace tasks AND link to a renewal MART has), stored/in-export lookups, `not_news` (stored items the export doesn't cover: tasks outside its own period), outcome, save, after-client hook (tasks: drop stored ones that link to no renewal); a new tracker is one adapter, the upload pipeline never learns what is inside), `upload_service` (stage → live preview per client → commit in one transaction → backup; several files = several staged uploads, Renewal Trackers first, the next opens after a commit/discard; items are never deleted, only marked "no longer in the export"; content compared flavour-neutrally; a text stream is taken from an export only if it fills it somewhere; `overview_as_of` is set only by an export that carries the overview), `client_service` (bundles: a renewal is in its default bundle (country + renewal date) unless moved into a custom bundle; the explorer's groups and selected bundle (`renewal_id` selects the bundle holding it); each renewal in a bundle carries its `freshness` (paused by the bundle's deadline); overview freshness), `bundles` (pure: keys `<country>|<date>` and `custom|<id>`), `bundle_service` (`move` one or several renewals into an existing custom bundle of the SAME country, a new named one, or back to `default`; `rename` any bundle — a default bundle's name lives in `bundle_names` and can be cleared; a bundle never mixes countries), `history` (pure: what changed between two versions of a renewal / task — `RENEWAL_FIELDS`, `TASK_FIELDS`, events `_seen` / `_left` / `_back` / `_overview`; `describe` groups by upload), `renewal_service` (the renewal panel; `policy_number` = the first "Policy Number" on the detail sheets, the Overview sheet has none; `bm_sections` = the stored Overview row bundled under BM+'s own section headings for "Everything BM+ exported"; tasks linked to THIS cycle by `Policy ID` = per-cycle id, else stable id + review date; the three BM+ stages — Proposals is "skipped" for the strategies in `specs.task_tracker.NO_PROPOSALS_STRATEGIES`; `bm_links` = the ONE list behind every "⋯" links menu: the policy link, then ONE "Renewal in BM+" link — the Task Tracker's task links all open the renewal's workspace, so only the first is offered; BM+'s own renewal link (Renewal Tracker) doesn't open, so it is stored but never offered), `deadlines` (broker deadlines on BUNDLES, apart from to-dos: the current one = your open row, else BM+'s earliest expected-terms date of the bundle's renewals (`bm_date`) unless a closed one was as late; a BM+ suggestion is stored only when acted on; `ahead` / `passed`; only Martin closes one), `freshness` (pure + the three limits: a renewal's newest overview entry by its own date, full AND client-ready text, → `fresh` / `amber` / `red` / `none`; a bundle shows its quietest renewal (`worst`); entries dated since `new_since` are new; `pause` = a bundle deadline still ahead turns amber / red into `paused`), `preferences` (Settings → Time limits: each one declared once in `PREFS`, stored as `pref:<name>` in `user_state`), `today` (Home's "Today": passed / near deadlines, due or urgent to-dos, quiet bundles, new overview entries, and a card per client, built from `client_service.explorer` per client so it never disagrees with the client pages; 10 per list), `backup_service` (gzipped snapshots, deduplicated by content: on start — and just BEFORE an upgrade, `__main__.prepare_database` — after every upload, and hourly while running; one at a time), `todo_details` (pure: the to-do extras — urgency, status open / in progress / waiting, waiting on whom + since, description, subtask titles — and their validation; its `Invalid` IS `notes_service.Invalid`), `notes_service` (notes + to-dos; targets `renewal` (ref = renewals.id), `bundle` (ref = `<client id>|<bundle key>`, see `bundles`) and `client` (ref = clients.id); only targets of MY clients can be written on; a renewal also shows its policy's notes from OTHER cycles (same stable policy id, `renewals_repo.cycles_of`), read-only; the To-dos page and Home card), setup, status |
| `mart/web/framework.py`, `multipart.py` | the small stdlib web layer: Request (form, files), Response, Router; file uploads via the e-mail parser (no `cgi`) |
| `mart/web/app.py` | request rules (host, origin, setup gate, error page + log), router assembly |
| `mart/web/countries.py` | country flags: `flag` (a Jinja filter) turns a BM+ country name into an `<img>` of `static/flags/<iso>.svg` (flag-icons, MIT; images because Windows draws flag emoji as letters); `NAMES` + `ALIASES` (BM+ writes ISO 3166's long forms), matched ignoring case, accents and punctuation; unknown → no flag |
| `mart/web/colors.py` | colour coding: `strategy_class` (a Jinja filter) maps each BM+ strategy to a `st-*` class; the colours are `--st-*` tokens in `mart.css` (light + dark). New colour codes go here, never as ad-hoc template logic |
| `mart/web/routes/` | thin handlers, one module per page. **Routes never write SQL.** |
| `mart/web/templates/`, `static/` | Jinja2 pages (autoescaped, reload per request), CSS; the Uploads card takes dropped files (`form[data-dropzone]` in `mart.js` puts the `.xlsx` files into the same file input and sends the form); `partials/` holds the shared pieces: `overview.html` (timeline + pill), `stages.html` (`stage_dots` on cards, `stage_strip` in the panel), `renewal_detail.html` (the renewal panel, shown in the explorer's middle at `/clients/<id>/renewals/<id>`), `links.html` (`links_menu`: the "⋯" menu, a plain `<details>`; `mart.js` closes it on an outside click / Esc), `mine.html` (`mine_section`: to-dos + notes on a target; "+ To-do" / "+ Note" open the add forms in a `details.arrange` popover; plain forms that post and return to `back` = `request.url`; `mine_badges`), `deadline.html` (`deadline_line`: the bundle's expected update in the bundle header and the renewal panel, with set / ✓ arrived / ✎ / × and the history; `deadline_badge` for the side panel), `move.html` (`move_form`: the bundle view's EDIT MODE bar, shown only with `?edit=1` together with the cards' tick boxes — `done` = the link out of it; the card checkboxes join it with `form="…"`, so nothing is nested; with `one` it moves a single renewal from its panel) |
| `vendor/` | Jinja2 + MarkupSafe (pure Python); `LICENSES/` also holds flag-icons' (the flags in `static/flags/`) |
| `tools/build_zip.py` | builds `dist/MART-<version>.zip` (+ `BUILD-INFO.txt`); `--verify` unpacks and runs `mart check` from the zip |
| `tests/` | pytest; every test gets its own settings file and folders (`conftest.py`) |

## Rules

- Migrations are append-only (`MIGRATIONS` in `schema.py`); never edit an applied one.
- Dates: `DD.MM.YYYY` on screen (`| dmy`), ISO everywhere else.
- Jinja: never `x.items` / `x.keys` / `x.values` on a dict — that is the
  dict METHOD; write `x["items"]`.
- The renewal panel keeps a FIXED section order (glance → stages → YOUR
  to-dos and notes → facts (two pairs per row) → strategy, stacked → proposals → savings → overview → the
  rest), so each section is always in the same place. Everything except
  "yours" is BM+ data, read-only; what Martin writes carries the
  `.sec-mine` rail ("written in MART") and is never mixed into BM+ sections.
- **History is recorded, never rebuilt**: `trackers._record` writes what an
  upload changed at commit time; changing what counts as a change only
  affects later uploads. Entries are dated by the export's report date.
- A bundle never mixes countries; a renewal's placement in a custom bundle
  hangs on its MART id (`renewal_bundles`), so uploads never undo it. An
  emptied custom bundle is kept (offered again as a move target); ANY
  emptied bundle stays visible while it carries notes, open to-dos or an
  open broker deadline.
- Write forms post and redirect back; `back` must be a path on MART
  (`routes/notes._back`), never another site.
- Python 3.10 still starts MART: no `datetime.UTC` (3.11+), use
  `timezone.utc`.
- An upload's `staging_rows` live only while it is staged: commit and
  discard delete them (the stored renewals/tasks hold what is needed).
- `NULL` means "to be confirmed", not zero.
- Uploads never delete user-written data, and never delete a renewal.
- **The renewals are the backbone** (Martin, 04.11.2026): a task is stored
  only while it is a renewal task (`RENEWAL_CATEGORY`) and links to a renewal MART has (`renewal_service.links_to_renewal`,
  the same two rules as `link_tasks`); history grows from the renewals kept.
- What an export doesn't carry is not news: a text stream it leaves empty
  everywhere, a sheet it doesn't include, a column its flavour lacks — all
  keep the stored value and are left out of the comparison.
- Compare BM+ content, not spelling: ids, the Client Name column and header
  spelling differ between export flavours (`content_hash`).
- Test data: `tests/fixtures.py` builds exports to the real layout. Real
  exports can be checked with `MART_REAL_EXPORTS=<folder>` (never committed).
- Timestamps in the DB are UTC; `| dmy(True)` shows them in local time.
- **Desktop only** (landscape and portrait windows). The main menu (`.sidebar`) is pinned to the window; explorer pages: side panel scrolls on its own (`.bundle-nav`), content in the middle.
- The explorer opens at the TOP (Martin, 04.11.2026): no bundle asked for → the top bundle of the
  panel is selected, and `data-fresh` resets the panel's remembered scroll and filters. Its
  bundles are always grouped by renewal month (no other grouping); the filters (text, country,
  from / until DATE with the browser's calendar) run in `mart.js` on the items' `data-country` /
  `data-first` / `data-last` (ISO dates), remembered per client per tab. Only the panel scrolls itself into
  view (`scrollTop`), never `scrollIntoView` (that scrolls the page too).
- Keep pages light (Martin, 04.11.2026): input fields hide behind a button
  (`details.arrange` + `.arrange-box`), footnotes behind an ⓘ (`.info` +
  `.tip`), edit actions are icons beside what they edit (`.icon-btn`). A
  popover opened from a button at the RIGHT end of a line gets `.arrange-right`,
  so it opens leftwards and never runs off the window.
- CSS: `[hidden]` always wins (`display: none !important`), so filters work on flex/grid items.
- Keep files under ~400 lines; one shared helper over duplicated logic.

## Verify

```bash
python3.12 -m pytest          # needs pytest + openpyxl in a dev environment
ruff check .
python3.12 tools/build_zip.py # then unzip into an empty folder and run it with a bare python3.12
```
