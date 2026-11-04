"""Every test gets its own settings file, home folder and data/backup folders,
so nothing a test does can touch a real MART installation."""

from __future__ import annotations

from pathlib import Path

import pytest

from mart import settings as settings_mod
from mart.repository import schema
from mart.web.app import create_app
from mart.web.framework import Request


@pytest.fixture(autouse=True)
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("MART_SETTINGS_FILE", str(tmp_path / "config" / "settings.json"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    for var in ("OneDrive", "OneDriveCommercial", "OneDriveConsumer"):
        monkeypatch.delenv(var, raising=False)
    (tmp_path / "home").mkdir()
    return tmp_path


@pytest.fixture
def configured(tmp_path: Path) -> settings_mod.Settings:
    """MART set up with data + backup folders inside the test's temp dir."""
    s = settings_mod.Settings(data_dir=str(tmp_path / "data"),
                              backup_dir=str(tmp_path / "backups"), backups_keep=3)
    Path(s.data_dir).mkdir()
    Path(s.backup_dir).mkdir()
    schema.ensure_schema(s.db_path)
    settings_mod.save(s)
    return s


@pytest.fixture
def app():
    return create_app()


def get(app, path: str, headers: dict[str, str] | None = None):
    path, _, query = path.partition("?")
    return app.handle(Request("GET", path, query, headers or {}))


def post(app, path: str, data: dict[str, str] | None = None,
         headers: dict[str, str] | None = None):
    from urllib.parse import urlencode
    h = {"content-type": "application/x-www-form-urlencoded", **(headers or {})}
    return app.handle(Request("POST", path, "", h, urlencode(data or {}).encode()))
