"""Start-up check: does this machine have what MART needs?

Runs before anything else (and on its own via `MART.bat check`). Each check
says in plain words what is missing instead of letting MART crash later.
A `fatal` check stops the start; the others are shown as warnings.
"""

from __future__ import annotations

import sqlite3
import sys
from dataclasses import dataclass


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    fatal: bool = False


def run_checks() -> list[Check]:
    checks: list[Check] = []

    v = sys.version_info
    version = f"{v.major}.{v.minor}.{v.micro}"
    if v < (3, 10):
        checks.append(Check("Python", False, f"{version} is too old; MART needs Python 3.12.", fatal=True))
    elif v < (3, 12):
        checks.append(Check("Python", False, f"{version} may work; MART is tested on 3.12 and newer."))
    else:
        checks.append(Check("Python", True, version))

    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("SELECT json('{}')").fetchone()
        conn.close()
        checks.append(Check("SQLite", True, sqlite3.sqlite_version))
    except sqlite3.Error as exc:
        checks.append(Check("SQLite", False, f"JSON support missing ({exc}).", fatal=True))

    try:
        import jinja2  # noqa: F401  (shipped in vendor/)
        import markupsafe  # noqa: F401
        checks.append(Check("Page templates (shipped)", True, f"Jinja2 {jinja2.__version__}"))
    except ImportError as exc:
        checks.append(Check("Page templates (shipped)", False,
                            f"The vendor/ folder is incomplete ({exc}). Unzip MART again.",
                            fatal=True))

    try:
        import openpyxl
        checks.append(Check("Excel reader (openpyxl)", True, openpyxl.__version__))
    except ImportError:
        checks.append(Check("Excel reader (openpyxl)", False,
                            "Not found. Needed for tracker uploads; everything else works."))
    return checks


def format_checks(checks: list[Check]) -> str:
    lines = []
    for c in checks:
        mark = "OK " if c.ok else ("!! " if c.fatal else "?  ")
        lines.append(f"  {mark} {c.name:<26} {c.detail}")
    return "\n".join(lines)


def has_fatal(checks: list[Check]) -> bool:
    return any(c.fatal and not c.ok for c in checks)
