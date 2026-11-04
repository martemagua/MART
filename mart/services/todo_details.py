"""The M2 extras of a to-do (Martin, 04.11.2026; QUESTIONS M2a): pure
vocabulary and validation, used by notes_service.

* **urgency** — urgent / normal / low (open to-dos sort urgent first)
* **status** while open — open / in progress / waiting (done stays `done_at`)
* **waiting on** — who has it (broker, insurer, client, colleague, other),
  their name, and since when; only kept while the status is "waiting"
* **description** — longer text than the title
* **subtasks** — a checklist inside the to-do (`todo_steps`)
"""

from __future__ import annotations

from datetime import date
from typing import Any

URGENCIES = {"urgent": "Urgent", "normal": "Normal", "low": "Low"}
STATUSES = {"open": "Open", "in_progress": "In progress", "waiting": "Waiting"}
WAITING_KINDS = {"broker": "broker", "insurer": "insurer", "client": "client",
                 "colleague": "colleague", "other": "someone else"}
DESCRIPTION_MAX = 5_000
NAME_MAX = 120
STEP_MAX = 300


class Invalid(ValueError):
    """Shown to the user as is."""


def _choice(value: str | None, allowed: dict[str, str], default: str, what: str) -> str:
    value = (value or "").strip() or default
    if value not in allowed:
        raise Invalid(f"Unknown {what}: {value}.")
    return value


def urgency(value: str | None) -> str:
    return _choice(value, URGENCIES, "normal", "urgency")


def step_title(value: str | None) -> str:
    text = " ".join((value or "").split())
    if not text:
        raise Invalid("A subtask needs a title.")
    if len(text) > STEP_MAX:
        raise Invalid(f"A subtask can have at most {STEP_MAX} characters.")
    return text


def clean(form: dict[str, str | None], today: date | None = None) -> dict[str, Any]:
    """The extras from an edit form -> what update_details stores."""
    description = (form.get("description") or "").replace("\r\n", "\n").strip() or None
    if description and len(description) > DESCRIPTION_MAX:
        raise Invalid(f"A description can have at most {DESCRIPTION_MAX:,} characters.")
    status = _choice(form.get("status"), STATUSES, "open", "status")
    out = {"description": description, "urgency": urgency(form.get("urgency")), "status": status,
           "waiting_kind": None, "waiting_on": None, "waiting_since": None}
    if status == "waiting":
        name = " ".join((form.get("waiting_on") or "").split()) or None
        if name and len(name) > NAME_MAX:
            raise Invalid(f"A name can have at most {NAME_MAX} characters.")
        since = (form.get("waiting_since") or "").strip()
        try:
            since = date.fromisoformat(since).isoformat() if since else (today or date.today()).isoformat()
        except ValueError as exc:
            raise Invalid("'Waiting since' isn't a date.") from exc
        out.update(waiting_kind=_choice(form.get("waiting_kind"), WAITING_KINDS, "other", "kind of person"),
                   waiting_on=name, waiting_since=since)
    return out


def with_steps(todo: dict[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:
    """A to-do with its subtasks and how many are done."""
    return {**todo, "steps": steps, "steps_done": sum(1 for s in steps if s["done_at"])}
