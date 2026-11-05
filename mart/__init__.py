"""MART — Martin's Awesome Renewal Tool.

Importing the package puts the shipped `vendor/` folder first on sys.path,
so the pure-Python libraries MART carries (Jinja2, MarkupSafe) are found
without anything being installed. See vendor/README.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

__version__ = "0.8.2"
RELEASE_LABEL = "M2 · day 3 · broker deadlines"

APP_ROOT = Path(__file__).resolve().parent.parent
VENDOR_DIR = APP_ROOT / "vendor"

if VENDOR_DIR.is_dir() and str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))
