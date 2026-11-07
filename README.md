# MART — Martin's Awesome Renewal Tool

A local web app to run the renewal lifecycle: the real state of every
renewal, broker deadlines, follow-ups, notes and to-dos, built on the BM+
tracker exports. Runs on the work laptop with nothing installed.

**Status:** M3 · day 3 (the Insurer Capability Database; 0.9.7: a proposal holds its negotiation, first to final quote; 0.9.8: strategy, proposals and completed for several renewals at once; day 2: proposals compared; day 1: your strategy, completed) — 0.9.9: day 4, plan design changes; 0.9.10: day 5, regions per client and a region filter; 0.9.11: day 6, the board (0.9.12: a card opens its bundle over the board; 0.9.13: a foldable menu; 0.9.14: the board stage from the bundle header; 0.9.15–0.9.16: what each column means, behind an ⓘ; 0.9.17: why a card was moved; 0.9.18: the renewal overview starts closed; 0.9.19: a leaner renewal page; 0.9.20: one Clients page with a card per client; 0.9.21–0.9.22: QA fixes) — next: day 7, client topics. See `BUILD_PLAN_M3.md`.

## Use it

1. Unzip `MART-<version>.zip` into a local folder, e.g. `C:\Users\<you>\MART`.
2. Double-click `MART.bat`. On first start, choose your data folder (local)
   and backup folder (OneDrive or a network folder).
3. Details: `START-HERE.txt` (in the zip).

## Documents

| File | What |
|---|---|
| `CHANGELOG.md` | what changed in each version, and what to try |
| `CHARTER.md` | vision, goals, scope (agreed 03.11.2026) |
| `PLANNING.md` | design: screens, data model, AI plugin, runtime |
| `TRACKER_MAP.md` | what the BM+ Task and Renewal Tracker exports contain |
| `QUESTIONS.md` | open questions and answers |
| `BUILD_PLAN_M1.md` | the current milestone, day by day |
| `CLAUDE.md` | guide for AI assistants working on the code |

## Make the zip for the work laptop

On the PC with the repo, double-click **`make-zip.bat`**. It fetches the
latest version (`git pull`), builds `dist\MART-<version>.zip`, tests it
(unpacked into a temporary folder, MART's start-up check run from there)
and opens Explorer with the zip selected. `make-zip.bat --no-pull` builds
from the files as they are. The zip's `BUILD-INFO.txt` says which version
and commit it holds.

## How changes are made

Every change comes as a **pull request** into `main` (template in
`.github/pull_request_template.md`), with its documentation updated in the
same PR: `CHANGELOG.md`, this README, `CLAUDE.md`, the build plan. CI runs
the tests on Windows (Python 3.12 and 3.14) for every pull request and
every merge into `main`; a newer push to a PR cancels the run it replaces.

## Develop

```bash
python3.12 -m pytest
ruff check .
python3.12 tools/build_zip.py   # → dist/MART-<version>.zip
```
