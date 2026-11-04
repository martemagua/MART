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
| `mart/ingestion/` | reading BM+ exports: `sheet.py` (header row found by scanning, section labels, `section`/`after` to tell repeated headers apart, full row copy), `values.py` (dates rounded to the NEAREST midnight, names, keys), `ids.py` (BM+ ids from bare cells and URLs), `renewal_tracker.py` (one Overview row = one renewal; key = per-cycle id → `policy:<stable>:<date>` → `name:…`; distinct rows are NEVER merged, exact duplicates are) |
| `mart/ingestion/specs/` | **every Excel column name**, one module per tracker; also which text stream each export flavour carries |
| `mart/repository/` | **all SQL**: `db.py` connections, `schema.py` append-only migrations, `uploads_repo`, `clients_repo` (`is_mine`: NULL undecided / 1 / 0), `renewals_repo` |
| `mart/services/` | orchestration: `upload_service` (stage → live preview per client → commit in one transaction → backup; renewals are never deleted, only marked "no longer in the export"; content compared flavour-neutrally), backups, setup, status |
| `mart/web/framework.py`, `multipart.py` | the small stdlib web layer: Request (form, files), Response, Router; file uploads via the e-mail parser (no `cgi`) |
| `mart/web/app.py` | request rules (host, origin, setup gate, error page + log), router assembly |
| `mart/web/routes/` | thin handlers, one module per page. **Routes never write SQL.** |
| `mart/web/templates/`, `static/` | Jinja2 pages (autoescaped, reload per request), CSS |
| `vendor/` | Jinja2 + MarkupSafe (pure Python) |
| `tools/build_zip.py` | builds `dist/MART-<version>.zip` (+ `BUILD-INFO.txt`); `--verify` unpacks and runs `mart check` from the zip |
| `tests/` | pytest; every test gets its own settings file and folders (`conftest.py`) |

## Rules

- Migrations are append-only (`MIGRATIONS` in `schema.py`); never edit an applied one.
- Dates: `DD.MM.YYYY` on screen (`| dmy`), ISO everywhere else.
- `NULL` means "to be confirmed", not zero.
- Uploads never delete user-written data, and never delete a renewal.
- Compare BM+ content, not spelling: ids, the Client Name column and header
  spelling differ between export flavours (`content_hash`).
- Test data: `tests/fixtures.py` builds exports to the real layout. Real
  exports can be checked with `MART_REAL_EXPORTS=<folder>` (never committed).
- Timestamps in the DB are UTC; `| dmy(True)` shows them in local time.
- Keep files under ~400 lines; one shared helper over duplicated logic.

## Verify

```bash
python3.12 -m pytest          # needs pytest + openpyxl in a dev environment
ruff check .
python3.12 tools/build_zip.py # then unzip into an empty folder and run it with a bare python3.12
```
