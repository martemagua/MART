"""The facts behind the "System" card: versions, folders, backups."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Any

from mart import RELEASE_LABEL, __version__
from mart.repository import schema
from mart.services import backup_service
from mart.settings import Settings


def system_status(s: Settings) -> dict[str, Any]:
    db = s.db_path
    backups = backup_service.list_backups(Path(s.backup_dir))
    try:
        import openpyxl
        excel = f"openpyxl {openpyxl.__version__}"
    except ImportError:
        excel = None
    return {
        "version": __version__,
        "release": RELEASE_LABEL,
        "python": sys.version.split()[0],
        "sqlite": sqlite3.sqlite_version,
        "excel": excel,
        "data_dir": s.data_dir,
        "db_path": str(db),
        "db_size": db.stat().st_size if db.is_file() else 0,
        "schema_version": schema.current_version(db) if db.is_file() else 0,
        "schema_latest": schema.LATEST_VERSION,
        "backup_dir": s.backup_dir,
        "backups": backups,
        "last_backup": backups[0] if backups else None,
        "backups_keep": s.backups_keep,
    }
