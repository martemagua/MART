"""Client topics (M3 day 7; Martin 05.11.2026, PLANNING §5b, QUESTIONS
M3a/M3c): the client's OWN notes and to-dos (not those on a renewal or a
bundle) organised in named, coloured topics, shown as a board on the client
notes page.

* A topic: a name, a colour (`COLORS`), an optional country (a flag, only a
  label: renewal and bundle notes stay where they are, M2c) and a status
  (active / on hold / done; done ones are archived out of sight).
* Every client note and to-do sits in exactly one topic; "General" is the
  topic without a row (topic_id NULL), so the existing ones start there and
  it can never be deleted. No suggested topics (M3c): Martin makes them.
* A pinned note is a key fact: at the top of its topic, before the dated log.
* Deleting a topic moves its notes and to-dos to General; nothing is lost.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from mart.repository import clients_repo, notes_repo, renewals_repo, topics_repo
from mart.repository.db import connection
from mart.services import notes_service
from mart.services.notes_service import Invalid

COLORS = ("blue", "green", "amber", "red", "purple", "teal", "pink", "grey")
STATUSES = {"active": "Active", "on_hold": "On hold", "done": "Done"}
NAME_MAX = 60
NOTES_SHOWN = 4         # per column; the older notes fold away
GENERAL = {"id": None, "name": "General", "color": "grey", "country": None, "status": "active"}


# -- the board ------------------------------------------------------------------------
def _column(topic: dict[str, Any], notes: list[dict[str, Any]],
            todos: list[dict[str, Any]]) -> dict[str, Any]:
    open_ = [t for t in todos if not t["done_at"]]
    dated = sorted(t["due_date"] for t in open_ if t.get("due_date"))
    pinned = sorted((n for n in notes if n.get("pinned_at")), key=lambda n: n["pinned_at"], reverse=True)
    log = [n for n in notes if not n.get("pinned_at")]           # newest first already
    return {**topic, "open": open_, "done": [t for t in todos if t["done_at"]], "pinned": pinned,
            "notes": log[:NOTES_SHOWN], "older": log[NOTES_SHOWN:],
            "next_due": dated[0] if dated else None,
            "overdue": sum(1 for t in open_ if t.get("overdue")),
            "urgent": sum(1 for t in open_ if t.get("urgency") == "urgent")}


def board(client_id: int, today: date | None = None) -> dict[str, Any]:
    """General first, then the client's topics (active, then on hold) in their
    order; done topics apart (archived). Each with its open to-dos (urgent /
    overdue first, as everywhere), pinned notes, then the newest notes."""
    mine = notes_service.for_client(client_id, today)
    with connection() as conn:
        topics = topics_repo.for_client(conn, client_id)
        countries = sorted({r["country"] for r in renewals_repo.for_client(conn, client_id) if r["country"]})
    by_topic: dict[int | None, tuple[list, list]] = {None: ([], [])}
    for t in topics:
        by_topic[t["id"]] = ([], [])
    for n in mine["notes"]:
        by_topic.get(n.get("topic_id"), by_topic[None])[0].append(n)
    for t in mine["todos"]:
        by_topic.get(t.get("topic_id"), by_topic[None])[1].append(t)
    cols = [_column(GENERAL, *by_topic[None])]
    live = sorted((t for t in topics if t["status"] != "done"), key=lambda t: (t["status"] == "on_hold",
                                                                              t["position"], t["id"]))
    cols += [_column(t, *by_topic[t["id"]]) for t in live]
    return {"target": mine["target"], "columns": cols,
            "done": [_column(t, *by_topic[t["id"]]) for t in topics if t["status"] == "done"],
            "topics": topics, "countries": countries}


# -- writing --------------------------------------------------------------------------
def _clean(client_id: int, name: str | None, color: str | None, country: str | None,
           status: str | None, countries: list[str]) -> dict[str, Any]:
    name = (name or "").strip()
    if not name:
        raise Invalid("Give the topic a name.")
    if len(name) > NAME_MAX:
        raise Invalid(f"The name is too long (at most {NAME_MAX} characters).")
    if name.casefold() == GENERAL["name"].casefold():
        raise Invalid('"General" is there already: pick another name.')
    color = (color or "").strip() or COLORS[0]
    if color not in COLORS:
        raise Invalid("Pick one of the colours.")
    country = (country or "").strip() or None
    if country is not None and country not in countries:
        raise Invalid("Pick one of the client's countries (or none).")
    status = (status or "").strip() or "active"
    if status not in STATUSES:
        raise Invalid("A topic is active, on hold or done.")
    return {"name": name, "color": color, "country": country, "status": status}


def _mine(conn, client_id: int) -> list[str]:
    client = clients_repo.get(conn, client_id)
    if client is None or client["is_mine"] != 1:
        raise Invalid("This client is not one of yours (or doesn't exist).")
    return sorted({r["country"] for r in renewals_repo.for_client(conn, client_id) if r["country"]})


def _topic(conn, client_id: int, topic_id: int) -> dict[str, Any]:
    t = topics_repo.get(conn, topic_id)
    if t is None or t["client_id"] != client_id:
        raise Invalid("That topic doesn't exist.")
    return t


def _no_twin(conn, client_id: int, name: str, topic_id: int | None = None) -> None:
    for t in topics_repo.for_client(conn, client_id):
        if t["name"].casefold() == name.casefold() and t["id"] != topic_id:
            raise Invalid(f'There is a topic "{t["name"]}" already.')


def create(client_id: int, name: str | None, color: str | None = None, country: str | None = None,
           status: str | None = None) -> int:
    with connection() as conn:
        values = _clean(client_id, name, color, country, status, _mine(conn, client_id))
        _no_twin(conn, client_id, values["name"])
        return topics_repo.add(conn, client_id, values)


def edit(client_id: int, topic_id: int, name: str | None, color: str | None, country: str | None,
         status: str | None) -> None:
    with connection() as conn:
        countries = _mine(conn, client_id)
        _topic(conn, client_id, topic_id)
        values = _clean(client_id, name, color, country, status, countries)
        _no_twin(conn, client_id, values["name"], topic_id)
        topics_repo.update(conn, topic_id, values)


def delete(client_id: int, topic_id: int) -> None:
    """Its notes and to-dos stay, in General."""
    with connection() as conn:
        _mine(conn, client_id)
        _topic(conn, client_id, topic_id)
        topics_repo.delete(conn, topic_id)


def move(kind: str, item_id: int, topic_id: Any) -> int:
    """Put a client note (`kind` "note") or to-do ("todo") in another topic
    (empty = General). Returns the client id."""
    getter = {"note": notes_repo.get_note, "todo": notes_repo.get_todo}.get(kind)
    if getter is None:
        raise Invalid("Only notes and to-dos sit in topics.")
    with connection() as conn:
        item = getter(conn, item_id)
        if item is None:
            raise Invalid("This was already deleted.")
        if item["scope"] != "client":
            raise Invalid("Only the client's own notes and to-dos sit in topics.")
        _mine(conn, item["client_id"])
        tid = notes_service.topic_of(conn, item["client_id"], "client", topic_id)
        topics_repo.set_topic(conn, "notes" if kind == "note" else "todos", item_id, tid)
        return item["client_id"]


def pin(note_id: int, pinned: bool) -> None:
    """A key fact stays at the top of its topic."""
    with connection() as conn:
        note = notes_repo.get_note(conn, note_id)
        if note is None:
            raise Invalid("This note was already deleted.")
        _mine(conn, note["client_id"])
        topics_repo.set_pinned(conn, note_id, pinned)
