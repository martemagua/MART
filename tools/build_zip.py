"""Build the zip Martin unzips on his laptop: `dist/MART-<version>.zip`.

    python tools/build_zip.py            build
    python tools/build_zip.py --verify   build, then unpack it into a temporary
                                         folder and run MART's start-up check there
    python tools/build_zip.py --open     afterwards, show the zip in Explorer
    python tools/build_zip.py --pull     git pull first, then build in a fresh
                                         process (so the pulled code is used)

`make-zip.bat` runs `--pull --verify --open --pause`.

The zip holds one top folder `MART/` with exactly what runs: MART.bat, the
`mart/` package, `vendor/`, START-HERE.txt, BUILD-INFO.txt and the licences.
No tests, no caches, no repo files. `.bat`/`.cmd`/`.txt` files are written
with Windows line endings (CRLF): cmd.exe misreads some LF-only batch files.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mart import RELEASE_LABEL, __version__  # noqa: E402

INCLUDE = ["MART.bat", "START-HERE.txt", "mart", "vendor"]
SKIP_DIRS = {"__pycache__", ".pytest_cache"}
SKIP_SUFFIXES = {".pyc", ".pyo"}
CRLF_SUFFIXES = {".bat", ".cmd", ".txt"}


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


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                             timeout=10, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def build_info(now: datetime | None = None) -> str:
    commit = _git("rev-parse", "--short", "HEAD") or "unknown"
    branch = _git("rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    dirty = _git("status", "--porcelain")
    lines = [
        f"MART {__version__} ({RELEASE_LABEL})",
        f"Built     {(now or datetime.now()).strftime('%d.%m.%Y %H:%M')}",
        f"Commit    {commit} on {branch}" + (" (with local changes)" if dirty else ""),
        f"Built by  Python {sys.version.split()[0]}",
    ]
    return "\n".join(lines) + "\n"


def _crlf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


def build(dest_dir: Path | None = None) -> Path:
    dest_dir = dest_dir or ROOT / "dist"
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / f"MART-{__version__}.zip"
    part = target.with_name(target.name + ".part")
    with zipfile.ZipFile(part, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in _files():
            data = f.read_bytes()
            if f.suffix.lower() in CRLF_SUFFIXES:
                data = _crlf(data)
            zf.writestr("MART/" + f.relative_to(ROOT).as_posix(), data)
        zf.writestr("MART/BUILD-INFO.txt", _crlf(build_info().encode("utf-8")))
    os.replace(part, target)
    return target


def verify(zip_path: Path) -> tuple[bool, str]:
    """Unpack into a temporary folder and run MART's start-up check FROM there,
    with a throw-away settings file, so the zip is tested exactly as the work
    laptop will run it and nothing on this PC is touched."""
    with tempfile.TemporaryDirectory(prefix="mart-verify-", ignore_cleanup_errors=True) as tmp:
        with zipfile.ZipFile(zip_path) as zf:
            bad = zf.testzip()
            if bad:
                return False, f"damaged file in the zip: {bad}"
            zf.extractall(tmp)
        app = Path(tmp) / "MART"
        env = {**os.environ, "MART_SETTINGS_FILE": str(Path(tmp) / "settings.json"),
               "PYTHONDONTWRITEBYTECODE": "1"}
        env.pop("PYTHONPATH", None)
        result = subprocess.run([sys.executable, "-X", "utf8", "-m", "mart", "check"],
                                cwd=app, env=env, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=120)
        output = (result.stdout + result.stderr).strip("\n").rstrip()
        return result.returncode == 0, output


def show_in_explorer(path: Path) -> None:
    if sys.platform == "win32":
        subprocess.Popen(f'explorer /select,"{path}"')


def _build_and_report(verify_it: bool, open_it: bool) -> int:
    path = build()
    print(f"  Built     {path}  ({path.stat().st_size // 1024} KB)")
    for line in build_info().splitlines()[2:3]:
        print(f"  {line}")
    if verify_it:
        ok, output = verify(path)
        print("\n  Testing the zip (unpacked into a temporary folder):")
        print(output)
        if not ok:
            print("\n  !! The zip did NOT pass its start-up check. Don't copy it to the laptop.")
            path.unlink(missing_ok=True)
            return 1
        print("\n  The zip passed its start-up check.")
    if open_it:
        show_in_explorer(path)
    return 0


def pull() -> None:
    """git pull --ff-only, explained in plain words; never fatal."""
    if not (ROOT / ".git").exists():
        print("  Not a git checkout: building from the files as they are.")
        return
    try:
        result = subprocess.run(["git", "pull", "--ff-only"], cwd=ROOT, timeout=120)
    except (OSError, subprocess.SubprocessError):
        print("  git not found: building from the files as they are.")
        return
    if result.returncode != 0:
        print("\n  !! Could not update (see the message above). Building from the files as they are.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the MART zip.")
    parser.add_argument("--verify", action="store_true", help="test the zip after building it")
    parser.add_argument("--open", action="store_true", help="show the zip in Explorer")
    parser.add_argument("--pull", action="store_true", help="git pull first (what make-zip.bat does)")
    parser.add_argument("--no-pull", action="store_true", help="override --pull")
    parser.add_argument("--pause", action="store_true", help="wait for Enter at the end")
    args = parser.parse_args(argv)
    unattended = bool(os.environ.get("MART_NO_PAUSE"))  # CI: no Explorer, no waiting
    open_it = args.open and not unattended

    if not args.pull or args.no_pull:
        rc = _build_and_report(args.verify, open_it)
    else:
        print("\n  MART - build the zip for the work laptop")
        print("  " + "-" * 50)
        print("  Fetching the latest version ...")
        pull()
        print()
        # A FRESH process, so the build runs the code that was just pulled.
        cmd = [sys.executable, "-X", "utf8", str(Path(__file__).resolve())]
        cmd += ["--verify"] if args.verify else []
        cmd += ["--open"] if open_it else []
        rc = subprocess.call(cmd, cwd=ROOT)
    if args.pull and not args.no_pull or args.pause:
        if rc == 0:
            print("\n  Done. Copy the zip to the work laptop, unzip it there and start MART.bat.")
        else:
            print("\n  The zip was NOT built. Nothing was changed on the work laptop.")
    if args.pause and not unattended:
        try:
            input("\n  Press Enter to close this window.")
        except EOFError:
            pass
    return rc


if __name__ == "__main__":
    sys.exit(main())
