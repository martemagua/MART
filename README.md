# MART — Martin's Awesome Renewal Tool

A local web app to run the renewal lifecycle: the real state of every
renewal, broker deadlines, follow-ups, notes and to-dos, built on the BM+
tracker exports. Runs on the work laptop with nothing installed.

**Status:** M1 · day 1 (skeleton). See `BUILD_PLAN_M1.md`.

## Use it

1. Unzip `MART-<version>.zip` into a local folder, e.g. `C:\Users\<you>\MART`.
2. Double-click `MART.bat`. On first start, choose your data folder (local)
   and backup folder (OneDrive or a network folder).
3. Details: `START-HERE.txt` (in the zip).

## Documents

| File | What |
|---|---|
| `CHARTER.md` | vision, goals, scope (agreed 03.11.2026) |
| `PLANNING.md` | design: screens, data model, AI plugin, runtime |
| `TRACKER_MAP.md` | what the BM+ Task and Renewal Tracker exports contain |
| `QUESTIONS.md` | open questions and answers |
| `BUILD_PLAN_M1.md` | the current milestone, day by day |
| `CLAUDE.md` | guide for AI assistants working on the code |

## Develop

```bash
python3.12 -m pytest
ruff check .
python3.12 tools/build_zip.py   # → dist/MART-<version>.zip
```
