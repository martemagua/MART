"""Backups of the database.

A backup is a consistent snapshot (SQLite's online backup API, safe while
MART runs), gzipped into the backup folder as

    mart-YYYY-MM-DD_HHMMSS-<hash>.db.gz

`<hash>` identifies the content. If the newest backup already has the same
content, no new file is written, so starting MART ten times without
changing anything leaves one backup, not ten. Only the newest
`backups_keep` files are kept.

The file is first written as `.part` and renamed when complete, so a sync
client (OneDrive) never uploads half a backup.

Backups are made on start (and just before a database upgrade), after every
upload, and every hour while MART runs, so notes and to-dos written during
the day are covered too (unchanged content writes nothing).
"""

from __future__ import annotations

import gzip
import hashlib
import os
import re
import shutil
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

NAME_RE = re.compile(r"^mart-(\d{4}-\d{2}-\d{2}_\d{6})-([0-9a-f]{12})\.db\.gz$")


@dataclass
class BackupFile:
    path: Path
    taken_at: datetime
    content_hash: str
    size: int


@dataclass
class BackupResult:
    status: str            # created | unchanged | skipped
    file: Path | None
    message: str


def list_backups(backup_dir: Path) -> list[BackupFile]:
    """Backups in `backup_dir`, newest first. Other files are ignored."""
    if not backup_dir.is_dir():
        return []
    found = []
    for entry in backup_dir.iterdir():
        m = NAME_RE.match(entry.name)
        if not m or not entry.is_file():
            continue
        taken = datetime.strptime(m.group(1), "%Y-%m-%d_%H%M%S")
        st = entry.stat()
        found.append((BackupFile(entry, taken, m.group(2), st.st_size), st.st_mtime_ns))
    # names are stamped to the second: within one second, the file written
    # last is the newest (never the content hash, which sorts arbitrarily)
    found.sort(key=lambda bm: (bm[0].taken_at, bm[1]), reverse=True)
    return [b for b, _ in found]


def _snapshot(db_path: Path, target: Path) -> None:
    src = sqlite3.connect(str(db_path), timeout=10)
    dst = sqlite3.connect(str(target))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


HOURLY_SECONDS = 3600
_lock = threading.Lock()      # one backup at a time (they share the snapshot file)


def start_hourly(db_path: Path, backup_dir: Path, keep: int,
                 every: float = HOURLY_SECONDS) -> threading.Thread:
    """Back up every `every` seconds while MART runs (a daemon thread: it ends
    with MART). A failed backup is logged to the console and retried later."""
    def loop() -> None:
        while not stop.wait(every):
            try:
                make_backup(db_path, backup_dir, keep)
            except Exception as exc:  # noqa: BLE001  (never take MART down for a backup)
                print(f"  Backup failed, will retry: {exc}")
    stop = threading.Event()
    thread = threading.Thread(target=loop, name="mart-hourly-backup", daemon=True)
    thread.stop = stop  # type: ignore[attr-defined]
    thread.start()
    return thread


def make_backup(db_path: Path, backup_dir: Path, keep: int,
                now: datetime | None = None) -> BackupResult:
    with _lock:
        return _make_backup(db_path, backup_dir, keep, now)


def _make_backup(db_path: Path, backup_dir: Path, keep: int, now: datetime | None) -> BackupResult:
    if not db_path.is_file():
        return BackupResult("skipped", None, "No database yet, nothing to back up.")
    backup_dir.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_name(db_path.name + ".snapshot")
    try:
        _snapshot(db_path, tmp)
        content = _hash_file(tmp)
        existing = list_backups(backup_dir)
        if existing and existing[0].content_hash == content:
            return BackupResult("unchanged", existing[0].path,
                                "Nothing changed since the last backup.")
        stamp = (now or datetime.now()).strftime("%Y-%m-%d_%H%M%S")
        final = backup_dir / f"mart-{stamp}-{content}.db.gz"
        part = final.with_name(final.name + ".part")
        with open(tmp, "rb") as src, gzip.open(part, "wb", compresslevel=6) as dst:
            shutil.copyfileobj(src, dst)
        os.replace(part, final)
    finally:
        tmp.unlink(missing_ok=True)
    prune(backup_dir, keep)
    return BackupResult("created", final, f"Backup written: {final.name}")


def prune(backup_dir: Path, keep: int) -> list[Path]:
    """Delete all but the newest `keep` backups. Returns what was removed."""
    removed = []
    for old in list_backups(backup_dir)[max(1, keep):]:
        old.path.unlink(missing_ok=True)
        removed.append(old.path)
    return removed


def restore(backup_file: Path, db_path: Path, now: datetime | None = None) -> Path | None:
    """Replace the database with a backup. The current database is kept next
    to it as `mart.db.before-restore-<time>`; returns that path (or None if
    there was no database)."""
    if not NAME_RE.match(backup_file.name):
        raise ValueError(f"{backup_file.name} is not a MART backup file.")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    kept = None
    if db_path.exists():
        stamp = (now or datetime.now()).strftime("%Y-%m-%d_%H%M%S")
        kept = db_path.with_name(f"{db_path.name}.before-restore-{stamp}")
        os.replace(db_path, kept)
    part = db_path.with_name(db_path.name + ".restoring")
    with gzip.open(backup_file, "rb") as src, open(part, "wb") as dst:
        shutil.copyfileobj(src, dst)
    os.replace(part, db_path)
    return kept
