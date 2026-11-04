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
| `mart/__main__.py` | CLI: run (check → schema → backup → serve) · check · backup · restore |
| `mart/settings.py` | settings file (`%APPDATA%\MART\settings.json`, override `MART_SETTINGS_FILE`), validation; the live DB must never sit in a synced folder |
| `mart/startup.py` | start-up checks with plain-language messages |
| `mart/ingestion/` | reading BM+ exports: `sheet.py` (header row found by scanning, section labels, `section`/`after` to tell repeated headers apart, `Col.aliases` for names that differ by flavour, full row copy, `lookup`/`section_items` to read that copy back), `values.py` (a time exactly on the hour/half hour with no seconds is BM+'s midnight-UTC artefact and rounds to the NEAREST midnight; a real timestamp keeps its own date; names, keys, leading numbers like "12 day(s)"), `ids.py` (BM+ ids from bare cells and URLs; `bm_link` = the plain https link BM+ wrote in a cell — MART never builds one), `renewal_tracker.py` (one Overview row = one renewal; key = per-cycle id → `policy:<stable>:<date>` → `name:…`; distinct rows are NEVER merged, exact duplicates are; the detail sheets are OPTIONAL in BM+ — `merge_details` keeps the stored rows of a sheet the export lacks, `details["_from"]` records which upload each sheet was last read from; the BM+ links (`fields.bm_url` / `bm_policy_url`) come only from cross-client exports, so `keep_links` carries them over a single-client one), `task_tracker.py` (one row = one task, key = the `taskId` — 24-hex or UUID; content compared on `specs.task_tracker.COMPARED` only, because the flavours differ in columns and in how they name people; `stage_state` trusts BM+'s status, incl. "Past Due") |
| `mart/ingestion/overview.py` | the renewal overview: dated entries (header `DD MMM YYYY:` at a LINE START), newest-first timeline, line-by-line comparison with the client-ready version (spacing/case ignored; BM+'s own "(not client ready)" marker counts), list flag `empty` / `no_cr` / `gaps` / `ok` |
| `mart/ingestion/specs/` | **every Excel column name**, one module per tracker; the three text streams (overview all / client ready / feed) |
| `mart/repository/` | **all SQL**: `db.py` connections, `schema.py` append-only migrations, `uploads_repo`, `clients_repo` (`is_mine`: NULL undecided / 1 / 0; `overview_as_of`), `renewals_repo`, `tasks_repo` (an update keeps the stored value of every field the export has no column for), `state_repo` (the `user_state` key/value table) |
| `mart/services/` | orchestration: `trackers` (one ADAPTER per tracker — recognise, parse, `keep` (which rows to load: tasks only when they link to a renewal MART has), stored/in-export lookups, `not_news` (stored items the export doesn't cover: tasks outside its own period), outcome, save, after-client hook (tasks: drop stored ones that link to no renewal); a new tracker is one adapter, the upload pipeline never learns what is inside), `upload_service` (stage → live preview per client → commit in one transaction → backup; several files = several staged uploads, Renewal Trackers first, the next opens after a commit/discard; items are never deleted, only marked "no longer in the export"; content compared flavour-neutrally; a text stream is taken from an export only if it fills it somewhere; `overview_as_of` is set only by an export that carries the overview), `client_service` (bundles = client + country + renewal date; the explorer's groups and selected bundle; overview freshness), `renewal_service` (the renewal panel; tasks linked to THIS cycle by `Policy ID` = per-cycle id, else stable id + review date; the three BM+ stages; `bm_links` = the ONE list behind every "⋯" links menu — BM+'s own renewal link doesn't open, so it is stored but never offered), `preferences` (Settings → Time limits: each one declared once in `PREFS`, stored as `pref:<name>` in `user_state`), backups, setup, status |
| `mart/web/framework.py`, `multipart.py` | the small stdlib web layer: Request (form, files), Response, Router; file uploads via the e-mail parser (no `cgi`) |
| `mart/web/app.py` | request rules (host, origin, setup gate, error page + log), router assembly |
| `mart/web/routes/` | thin handlers, one module per page. **Routes never write SQL.** |
| `mart/web/templates/`, `static/` | Jinja2 pages (autoescaped, reload per request), CSS; `partials/` holds the shared pieces: `overview.html` (timeline + pill), `stages.html` (`stage_dots` on cards, `stage_strip` in the panel), `renewal_detail.html` (the renewal panel, shown in the explorer's middle at `/clients/<id>/renewals/<id>`), `links.html` (`links_menu`: the "⋯" menu, a plain `<details>`; `mart.js` closes it on an outside click / Esc) |
| `vendor/` | Jinja2 + MarkupSafe (pure Python) |
| `tools/build_zip.py` | builds `dist/MART-<version>.zip` (+ `BUILD-INFO.txt`); `--verify` unpacks and runs `mart check` from the zip |
| `tests/` | pytest; every test gets its own settings file and folders (`conftest.py`) |

## Rules

- Migrations are append-only (`MIGRATIONS` in `schema.py`); never edit an applied one.
- Dates: `DD.MM.YYYY` on screen (`| dmy`), ISO everywhere else.
- Jinja: never `x.items` / `x.keys` / `x.values` on a dict — that is the
  dict METHOD; write `x["items"]`.
- The renewal panel keeps a FIXED section order (glance → stages → facts +
  strategy → proposals → savings → overview → the rest), so each section is
  always in the same place. Everything in it is BM+ data, read-only.
- `NULL` means "to be confirmed", not zero.
- Uploads never delete user-written data, and never delete a renewal.
- **The renewals are the backbone** (Martin, 04.11.2026): a task is stored
  only while it links to a renewal MART has (`renewal_service.links_to_renewal`,
  the same two rules as `link_tasks`); history grows from the renewals kept.
- What an export doesn't carry is not news: a text stream it leaves empty
  everywhere, a sheet it doesn't include, a column its flavour lacks — all
  keep the stored value and are left out of the comparison.
- Compare BM+ content, not spelling: ids, the Client Name column and header
  spelling differ between export flavours (`content_hash`).
- Test data: `tests/fixtures.py` builds exports to the real layout. Real
  exports can be checked with `MART_REAL_EXPORTS=<folder>` (never committed).
- Timestamps in the DB are UTC; `| dmy(True)` shows them in local time.
- **Desktop only** (landscape and portrait windows). Explorer pages: side panel scrolls on its own (`.bundle-nav`), content in the middle.
- CSS: `[hidden]` always wins (`display: none !important`), so filters work on flex/grid items.
- Keep files under ~400 lines; one shared helper over duplicated logic.

## Verify

```bash
python3.12 -m pytest          # needs pytest + openpyxl in a dev environment
ruff check .
python3.12 tools/build_zip.py # then unzip into an empty folder and run it with a bare python3.12
```
