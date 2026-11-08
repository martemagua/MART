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
from mart.services import (
    actuals,
    board,
    plan_changes,
    proposals,
    repeats,
    stewardship,
    todo_details,
    topics,
    trackers,
)
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


def amount(value: Any) -> str:
    """120000 -> 120'000; 1234.5 -> 1'234.50 (the apostrophe BM+'s amounts
    already show in MART). Text passes through; None -> ''."""
    if value is None or value == "":
        return ""
    if not isinstance(value, (int, float)):
        return str(value)
    text = f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"
    return text.replace(",", "'")


def pct(value: Any) -> str:
    """8 -> +8 %, -3.5 -> −3.5 %; None -> ''."""
    if value is None or value == "":
        return ""
    if not isinstance(value, (int, float)):
        return str(value)
    num = f"{abs(value):.1f}".rstrip("0").rstrip(".")
    return ("+" if value > 0 else "−" if value < 0 else "±") + num + "\u00a0%"   # never split from its %


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
_env.filters["amount"] = amount
_env.filters["pct"] = pct
_env.filters["strategy_class"] = colors.strategy_class
_env.filters["flag"] = countries.flag
_env.globals["todo_vocab"] = {"urgencies": todo_details.URGENCIES, "statuses": todo_details.STATUSES,
                              "kinds": todo_details.WAITING_KINDS}
_env.globals["strategies"] = actuals.STRATEGIES
_env.globals["tracker_label"] = lambda t: trackers.BY_TRACKER[t].label if t in trackers.BY_TRACKER else t
_env.globals["plan_change_vocab"] = plan_changes.OUTCOMES
_env.globals["saving_kinds"] = stewardship.KINDS
_env.globals["saving_hints"] = stewardship.HINTS
_env.globals["board_labels"] = board.LABELS
_env.globals["board_hints"] = board.HINTS
_env.globals["topic_colors"] = topics.COLORS
_env.globals["repeat_units"] = repeats.UNITS
_env.globals["repeat_weekdays"] = repeats.WEEKDAYS
_env.filters["repeat_text"] = repeats.describe
_env.globals["topic_statuses"] = topics.STATUSES
_env.globals["proposal_vocab"] = {"rounds": proposals.ROUNDS, "designs": proposals.PLAN_DESIGNS}
_env.globals["today_iso"] = lambda: date.today().isoformat()
_env.globals.update(version=__version__, release=RELEASE_LABEL)


def render_string(name: str, **context: Any) -> str:
    return _env.get_template(name).render(**context)


def render(name: str, status: int = 200, **context: Any) -> Response:
    return Response(render_string(name, **context), status)
