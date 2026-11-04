"""`python -m mart [command]`, which is what MART.bat runs.

    (no command)   check → back up → start MART and open the browser
    check          only the start-up check
    backup         make a backup now
    restore FILE   replace the database with a backup (stop MART first)
    --no-browser   start without opening the browser
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from mart import RELEASE_LABEL, __version__
from mart import settings as settings_mod
from mart.repository import schema
from mart.services import backup_service
from mart.startup import format_checks, has_fatal, run_checks


def _banner() -> None:
    print(f"\n  MART {__version__}  ({RELEASE_LABEL})")
    print("  " + "-" * 50)


def cmd_check() -> int:
    checks = run_checks()
    print(format_checks(checks))
    return 1 if has_fatal(checks) else 0


def cmd_backup() -> int:
    s = settings_mod.load()
    if s is None:
        print("  MART is not set up yet: start it once and choose your folders.")
        return 1
    result = backup_service.make_backup(s.db_path, Path(s.backup_dir), s.backups_keep)
    print(f"  {result.message}")
    return 0


def cmd_restore(file: str) -> int:
    s = settings_mod.load()
    if s is None:
        print("  MART is not set up yet.")
        return 1
    from mart.web.server import running_mart
    if running_mart(s.port):
        print("  MART is running. Close its window first, then restore.")
        return 1
    kept = backup_service.restore(Path(file), s.db_path)
    schema.ensure_schema(s.db_path)
    print(f"  Restored {Path(file).name}.")
    if kept:
        print(f"  The previous database was kept as {kept.name}.")
    return 0


def cmd_run(open_browser: bool) -> int:
    checks = run_checks()
    print(format_checks(checks))
    if has_fatal(checks):
        print("\n  MART can't start. See the lines marked !! above.")
        return 1

    from mart.web.server import running_mart, serve

    s = settings_mod.load()
    port = s.port if s else settings_mod.DEFAULT_PORT
    already = running_mart(port)
    if already:
        print(f"\n  MART is already running at http://127.0.0.1:{port}/ (opening it).")
        if open_browser:
            webbrowser.open(f"http://127.0.0.1:{port}/")
        return 0

    if s is None:
        print("\n  First start: the browser opens on the setup page.")
    else:
        version = schema.ensure_schema(s.db_path)
        print(f"\n  Database: {s.db_path}  (schema {version})")
        result = backup_service.make_backup(s.db_path, Path(s.backup_dir), s.backups_keep)
        print(f"  Backup:   {result.message}")
        open_browser = open_browser and s.open_browser
    serve(port, open_browser=open_browser)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="MART", add_help=True)
    parser.add_argument("command", nargs="?", default="run",
                        choices=["run", "check", "backup", "restore"])
    parser.add_argument("file", nargs="?", help="backup file (for restore)")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args(argv)
    _banner()
    if args.command == "check":
        return cmd_check()
    if args.command == "backup":
        return cmd_backup()
    if args.command == "restore":
        if not args.file:
            print("  Usage: MART.bat restore <backup file>")
            return 2
        return cmd_restore(args.file)
    return cmd_run(open_browser=not args.no_browser)


if __name__ == "__main__":
    sys.exit(main())
