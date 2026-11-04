"""Build the zip Martin unzips on his laptop: `dist/MART-<version>.zip`.

    python tools/build_zip.py

The zip holds one top folder `MART/` with exactly what runs: MART.bat, the
`mart/` package, `vendor/`, START-HERE.txt and the licences. No tests, no
caches, no repo files. `.bat` files are written with Windows line endings
(CRLF): cmd.exe misreads some LF-only batch files.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mart import __version__  # noqa: E402

INCLUDE = ["MART.bat", "START-HERE.txt", "mart", "vendor"]
SKIP_DIRS = {"__pycache__", ".pytest_cache"}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def _files() -> list[Path]:
    out: list[Path] = []
    for item in INCLUDE:
        path = ROOT / item
        if path.is_file():
            out.append(path)
            continue
        for f in sorted(path.rglob("*")):
            if f.is_file() and not (set(f.relative_to(ROOT).parts) & SKIP_DIRS) \
                    and f.suffix not in SKIP_SUFFIXES:
                out.append(f)
    return out


def build(dest_dir: Path | None = None) -> Path:
    dest_dir = dest_dir or ROOT / "dist"
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / f"MART-{__version__}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in _files():
            arcname = "MART/" + f.relative_to(ROOT).as_posix()
            data = f.read_bytes()
            if f.suffix.lower() in (".bat", ".cmd", ".txt"):
                data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            zf.writestr(arcname, data)
    return target


if __name__ == "__main__":
    path = build()
    print(f"Built {path} ({path.stat().st_size // 1024} KB)")
