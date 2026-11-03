import gzip
import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from mart.repository import schema
from mart.services import backup_service as bk


def test_migrations_are_numbered_strictly_upwards():
    numbers = [n for n, _ in schema.MIGRATIONS]
    assert numbers == sorted(set(numbers)) and numbers[0] == 1


def test_ensure_schema_creates_and_is_idempotent(tmp_path):
    db = tmp_path / "x" / "mart.db"
    assert schema.ensure_schema(db) == schema.LATEST_VERSION
    assert schema.ensure_schema(db) == schema.LATEST_VERSION
    conn = sqlite3.connect(db)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert "user_state" in tables


def _write(db: Path, value: str) -> None:
    conn = sqlite3.connect(db)
    conn.execute("INSERT OR REPLACE INTO user_state(key, value) VALUES ('k', ?)", (value,))
    conn.commit()
    conn.close()


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "data" / "mart.db"
    schema.ensure_schema(path)
    return path


def test_no_database_means_nothing_to_back_up(tmp_path):
    r = bk.make_backup(tmp_path / "none.db", tmp_path / "b", 5)
    assert r.status == "skipped"


def test_backup_is_written_then_deduplicated(db, tmp_path):
    out = tmp_path / "backups"
    first = bk.make_backup(db, out, 5, now=datetime(2026, 11, 3, 9, 0, 0))
    assert first.status == "created" and first.file.exists()
    again = bk.make_backup(db, out, 5, now=datetime(2026, 11, 3, 9, 5, 0))
    assert again.status == "unchanged"
    assert len(bk.list_backups(out)) == 1
    _write(db, "changed")
    third = bk.make_backup(db, out, 5, now=datetime(2026, 11, 3, 9, 10, 0))
    assert third.status == "created"
    assert [b.path for b in bk.list_backups(out)][0] == third.file
    assert not list(out.glob("*.part")) and not list(db.parent.glob("*.snapshot"))


def test_backup_is_a_valid_gzipped_database(db, tmp_path):
    _write(db, "hello")
    r = bk.make_backup(db, tmp_path / "b", 5)
    raw = tmp_path / "check.db"
    raw.write_bytes(gzip.decompress(r.file.read_bytes()))
    conn = sqlite3.connect(raw)
    assert conn.execute("SELECT value FROM user_state WHERE key='k'").fetchone()[0] == "hello"
    conn.close()


def test_only_the_newest_backups_are_kept(db, tmp_path):
    out = tmp_path / "b"
    for i in range(5):
        _write(db, str(i))
        bk.make_backup(db, out, keep=3, now=datetime(2026, 11, 3, 10, i, 0))
    kept = bk.list_backups(out)
    assert len(kept) == 3
    assert kept[0].taken_at == datetime(2026, 11, 3, 10, 4, 0)


def test_other_files_in_the_backup_folder_are_left_alone(db, tmp_path):
    out = tmp_path / "b"
    out.mkdir()
    (out / "my-notes.txt").write_text("keep me")
    bk.make_backup(db, out, keep=1)
    _write(db, "x")
    bk.make_backup(db, out, keep=1)
    assert (out / "my-notes.txt").exists()


def test_restore_keeps_the_current_database(db, tmp_path):
    _write(db, "old")
    backup = bk.make_backup(db, tmp_path / "b", 5).file
    _write(db, "new")
    kept = bk.restore(backup, db, now=datetime(2026, 11, 3, 12, 0, 0))
    assert kept.name == "mart.db.before-restore-2026-11-03_120000"
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT value FROM user_state WHERE key='k'").fetchone()[0] == "old"
    conn.close()


def test_restore_refuses_files_that_are_not_mart_backups(tmp_path):
    bogus = tmp_path / "something.gz"
    bogus.write_bytes(b"x")
    with pytest.raises(ValueError):
        bk.restore(bogus, tmp_path / "mart.db")
