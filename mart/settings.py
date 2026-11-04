"""Where MART keeps its data: the settings file.

The settings themselves (data folder, backup folder, …) live in a small JSON
file OUTSIDE the app folder, so unzipping a new MART version never touches
them:

    Windows   %APPDATA%\\MART\\settings.json
    elsewhere $XDG_CONFIG_HOME/mart/settings.json  (~/.config/mart/…)

`MART_SETTINGS_FILE` overrides the location (used by the tests).

No settings file = MART has not been set up yet; every page then sends the
user to /setup first.

Rule (charter §7): the LIVE database never sits in a synced folder
(OneDrive, Dropbox, …). A sync client copying an open SQLite file is a known
way to corrupt it. Backups, on the other hand, belong in one.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

DB_FILENAME = "mart.db"
DEFAULT_PORT = 8070
DEFAULT_BACKUPS_KEEP = 20

# Environment variables Windows sets for synced folders.
_SYNC_ENV_VARS = ("OneDrive", "OneDriveCommercial", "OneDriveConsumer")
# How sync clients name their folders ("OneDrive", "OneDrive - Contoso",
# "Dropbox", …): a folder whose name STARTS like this gives a synced folder
# away even without an env var. (A plain substring match flagged folders
# that merely mention the word.)
_SYNC_NAME_PREFIXES = ("onedrive", "dropbox", "google drive", "icloud drive", "iclouddrive", "box")


@dataclass
class Settings:
    data_dir: str
    backup_dir: str
    backups_keep: int = DEFAULT_BACKUPS_KEEP
    port: int = DEFAULT_PORT
    open_browser: bool = True

    @property
    def db_path(self) -> Path:
        return Path(self.data_dir) / DB_FILENAME

    @property
    def log_dir(self) -> Path:
        return Path(self.data_dir) / "logs"


# ---------------------------------------------------------------------------
# Location of the settings file
# ---------------------------------------------------------------------------
def settings_file() -> Path:
    override = os.environ.get("MART_SETTINGS_FILE")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "MART" / "settings.json"
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "mart" / "settings.json"


def load() -> Settings | None:
    """The saved settings, or None when MART has not been set up yet."""
    path = settings_file()
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return Settings(
            data_dir=str(raw["data_dir"]),
            backup_dir=str(raw["backup_dir"]),
            backups_keep=int(raw.get("backups_keep", DEFAULT_BACKUPS_KEEP)),
            port=int(raw.get("port", DEFAULT_PORT)),
            open_browser=bool(raw.get("open_browser", True)),
        )
    except (ValueError, KeyError, TypeError):
        # A damaged settings file is treated like none: the user sets up again.
        return None


def save(settings: Settings) -> Path:
    path = settings_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return path


# ---------------------------------------------------------------------------
# Defaults offered on first start
# ---------------------------------------------------------------------------
def sync_roots() -> list[Path]:
    roots = []
    for var in _SYNC_ENV_VARS:
        value = os.environ.get(var)
        if value:
            roots.append(Path(value))
    return roots


def defaults() -> Settings:
    home = Path.home()
    roots = sync_roots()
    backup = (roots[0] / "MART-backups") if roots else (home / "MART-backups")
    return Settings(data_dir=str(home / "MART-data"), backup_dir=str(backup))


def synced_folder(path: str | Path) -> str | None:
    """A short reason when `path` looks like a synced folder, else None."""
    p = Path(path).expanduser()
    try:
        resolved = p.resolve()
    except OSError:
        resolved = p
    for root in sync_roots():
        try:
            resolved.relative_to(root.resolve())
            return f"it is inside your synced folder {root}"
        except (ValueError, OSError):
            continue
    for part in resolved.parts:
        low = part.lower()
        for prefix in _SYNC_NAME_PREFIXES:
            if low == prefix or low.startswith((prefix + " ", prefix + "-")):
                return f"its path contains “{part}”, which looks like a synced folder"
    return None


# ---------------------------------------------------------------------------
# Validation of what the user typed
# ---------------------------------------------------------------------------
def validate(data_dir: str, backup_dir: str, backups_keep: str | int,
             port: str | int) -> tuple[Settings | None, list[str]]:
    """Check the form values. Returns (settings, []) or (None, errors)."""
    errors: list[str] = []
    data_dir = (data_dir or "").strip().strip('"')
    backup_dir = (backup_dir or "").strip().strip('"')

    if not data_dir:
        errors.append("Choose a data folder.")
    if not backup_dir:
        errors.append("Choose a backup folder.")
    if data_dir and not Path(data_dir).expanduser().is_absolute():
        errors.append("The data folder must be a full path, e.g. C:\\Users\\you\\MART-data.")
    if backup_dir and not Path(backup_dir).expanduser().is_absolute():
        errors.append("The backup folder must be a full path.")
    if data_dir and Path(data_dir).expanduser().is_absolute():
        reason = synced_folder(data_dir)
        if reason:
            errors.append(
                f"The data folder can't be used because {reason}. The live "
                "database must not sit in a synced folder (syncing an open "
                "database can corrupt it). Put it in a local folder; the "
                "backups can go to OneDrive."
            )
    if data_dir and backup_dir:
        d = Path(data_dir).expanduser()
        b = Path(backup_dir).expanduser()
        if d == b:
            errors.append("The backup folder must be different from the data folder.")
        else:
            try:
                b.relative_to(d)
                errors.append("The backup folder must not be inside the data folder.")
            except ValueError:
                pass

    try:
        keep = int(backups_keep)
        if not 1 <= keep <= 500:
            raise ValueError
    except (TypeError, ValueError):
        errors.append("Backups to keep must be a whole number between 1 and 500.")
        keep = DEFAULT_BACKUPS_KEEP
    try:
        port_n = int(port)
        if not 1024 <= port_n <= 65535:
            raise ValueError
    except (TypeError, ValueError):
        errors.append("The port must be a number between 1024 and 65535.")
        port_n = DEFAULT_PORT

    if errors:
        return None, errors
    return Settings(
        data_dir=str(Path(data_dir).expanduser()),
        backup_dir=str(Path(backup_dir).expanduser()),
        backups_keep=keep,
        port=port_n,
    ), []
