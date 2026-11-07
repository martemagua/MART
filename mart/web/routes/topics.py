"""Client topics (services/topics, M3 day 7): making, changing and deleting a
client's topics, putting a note / to-do in a topic, pinning a note. The
board itself is the client notes page (clients.client_notes)."""

from __future__ import annotations

from mart.services import topics
from mart.services.notes_service import Invalid
from mart.web.framework import HTTPError, Request, Response, Router, local_path

router = Router()


def _back(request: Request, client_id: int | None, anchor: str = "") -> Response:
    default = f"/clients/{client_id}/notes" if client_id else "/todos"
    back = local_path(request.arg("back"), default).split("#", 1)[0]
    return Response.redirect(back + (f"#{anchor}" if anchor else ""))


def _fields(request: Request) -> tuple:
    return (request.arg("name"), request.arg("color"), request.arg("country"), request.arg("status"))


@router.route("/clients/{client_id:int}/topics", methods=("POST",))
def topic_add(request: Request, client_id: int) -> Response:
    try:
        tid = topics.create(client_id, *_fields(request))
    except Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _back(request, client_id, f"topic-{tid}")


@router.route("/clients/{client_id:int}/topics/{topic_id:int}/save", methods=("POST",))
def topic_save(request: Request, client_id: int, topic_id: int) -> Response:
    try:
        topics.edit(client_id, topic_id, *_fields(request))
    except Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _back(request, client_id, f"topic-{topic_id}")


@router.route("/clients/{client_id:int}/topics/{topic_id:int}/delete", methods=("POST",))
def topic_delete(request: Request, client_id: int, topic_id: int) -> Response:
    try:
        topics.delete(client_id, topic_id)
    except Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _back(request, client_id)


def _move(request: Request, kind: str, item_id: int) -> Response:
    try:
        client_id = topics.move(kind, item_id, request.arg("topic"))
    except Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _back(request, client_id, f"{kind}-{item_id}")


@router.route("/notes/{item_id:int}/topic", methods=("POST",))
def note_topic(request: Request, item_id: int) -> Response:
    return _move(request, "note", item_id)


@router.route("/todos/{item_id:int}/topic", methods=("POST",))
def todo_topic(request: Request, item_id: int) -> Response:
    return _move(request, "todo", item_id)


@router.route("/notes/{note_id:int}/pin", methods=("POST",))
def note_pin(request: Request, note_id: int) -> Response:
    try:
        topics.pin(note_id, request.arg("pinned") == "1")
    except Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _back(request, None, f"note-{note_id}")
