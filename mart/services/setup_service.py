"""Applying settings: first-time setup and later changes.

Changing the data folder MOVES the database there (unless the new folder
already holds a MART database, which is then used as it is, so pointing
MART at an existing data folder never overwrites it).
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from mart import settings as settings_mod
from mart.repository import schema
from mart.settings import Settings


@dataclass
class ApplyResult:
    settings: Settings
    notes: list[str] = field(default_factory=list)


def apply(new: Settings, old: Settings | None = None) -> ApplyResult:
    notes: list[str] = []
    data_dir = Path(new.data_dir)
    backup_dir = Path(new.backup_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    if old is not None and Path(old.data_dir) != data_dir:
        old_db, new_db = old.db_path, new.db_path
        if old_db.is_file() and new_db.is_file():
            notes.append(
                f"{new_db} already existed and is now used. The previous "
                f"database stays untouched at {old_db}."
            )
        elif old_db.is_file():
            shutil.move(str(old_db), str(new_db))
            notes.append(f"Database moved from {old_db.parent} to {data_dir}.")

    if old is not None:
        new.open_browser = old.open_browser
    version = schema.ensure_schema(new.db_path)
    settings_mod.save(new)
    notes.append(f"Database ready (schema version {version}).")
    return ApplyResult(new, notes)
