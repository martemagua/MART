"""Page templates (Jinja2, shipped in vendor/).

Templates reload from disk on every render, so a template change shows on
the next page load without restarting MART. Autoescaping is on for every
.html template: values are escaped unless explicitly marked safe.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mart import RELEASE_LABEL, __version__
from mart.services import todo_details
from mart.web import colors, countries
from mart.web.framework import Response

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def dmy(value: Any, with_time: bool = False) -> str:
    """DD.MM.YYYY on screen (ISO everywhere else). Unparseable text passes through.

    Timestamps TEXT from the database are UTC (SQLite's datetime('now')) and are
    shown in this computer's local time; datetime objects are already local."""
    if value in (None, ""):
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M" if with_time else "%d.%m.%Y")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    text = str(value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return text
    if len(text) > 10 and parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc).astimezone()  # noqa: UP017 (3.10 has no datetime.UTC)
    return parsed.strftime("%d.%m.%Y %H:%M" if with_time and len(text) > 10 else "%d.%m.%Y")


def filesize(n: int | None) -> str:
    if not n:
        return "0 KB"
    for unit in ("bytes", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "bytes" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n} GB"


_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
    auto_reload=True,
    trim_blocks=True,
    lstrip_blocks=True,
)
_env.filters["dmy"] = dmy
_env.filters["filesize"] = filesize
_env.filters["strategy_class"] = colors.strategy_class
_env.filters["flag"] = countries.flag
_env.globals["todo_vocab"] = {"urgencies": todo_details.URGENCIES, "statuses": todo_details.STATUSES,
                              "kinds": todo_details.WAITING_KINDS}
_env.globals.update(version=__version__, release=RELEASE_LABEL)


def render_string(name: str, **context: Any) -> str:
    return _env.get_template(name).render(**context)


def render(name: str, status: int = 200, **context: Any) -> Response:
    return Response(render_string(name, **context), status)
