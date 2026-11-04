# MART — guide for AI assistants

MART (Martin's Awesome Renewal Tool) is a local, single-user web app that
tracks renewals from BM+ tracker exports and lets Martin record the real
state, deadlines, notes and to-dos. Read `CHARTER.md` (why/what, agreed),
`PLANNING.md` (design), `TRACKER_MAP.md` (what the BM+ exports contain) and
the current `BUILD_PLAN_*.md` before changing anything.

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
| `mart/__main__.py` | CLI: run (check → schema → backup → serve) · check · backup · restore |
| `mart/settings.py` | settings file (`%APPDATA%\MART\settings.json`, override `MART_SETTINGS_FILE`), validation; the live DB must never sit in a synced folder |
| `mart/startup.py` | start-up checks with plain-language messages |
| `mart/repository/` | **all SQL**: `db.py` connections, `schema.py` append-only migrations |
| `mart/services/` | orchestration (backups, setup, status) |
| `mart/web/framework.py` | the small stdlib web layer: Request, Response, Router |
| `mart/web/app.py` | request rules (host, origin, setup gate, error page + log), router assembly |
| `mart/web/routes/` | thin handlers, one module per page. **Routes never write SQL.** |
| `mart/web/templates/`, `static/` | Jinja2 pages (autoescaped, reload per request), CSS |
| `vendor/` | Jinja2 + MarkupSafe (pure Python) |
| `tools/build_zip.py` | builds `dist/MART-<version>.zip` |
| `tests/` | pytest; every test gets its own settings file and folders (`conftest.py`) |

## Rules

- Migrations are append-only (`MIGRATIONS` in `schema.py`); never edit an applied one.
- Dates: `DD.MM.YYYY` on screen (`| dmy`), ISO everywhere else.
- `NULL` means "to be confirmed", not zero.
- Uploads never delete user-written data.
- Keep files under ~400 lines; one shared helper over duplicated logic.

## Verify

```bash
python3.12 -m pytest          # needs pytest + openpyxl in a dev environment
ruff check .
python3.12 tools/build_zip.py # then unzip into an empty folder and run it with a bare python3.12
```
