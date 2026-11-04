"""Notes and to-dos: the write endpoints (each returns to the page it came
from) and the To-dos page."""

from __future__ import annotations

from mart.services import notes_service
from mart.services.notes_service import Invalid
from mart.web.framework import HTTPError, Request, Response, Router
from mart.web.templating import render

router = Router()


def _back(request: Request, anchor: str = "mine") -> Response:
    """Back to the page the form was on. Only a path on this site counts."""
    back = request.arg("back") or "/todos"
    if not back.startswith("/") or back.startswith("//") or "\\" in back:
        back = "/todos"
    return Response.redirect(back.split("#", 1)[0] + "#" + anchor)


def _do(request: Request, action, anchor: str = "mine") -> Response:
    try:
        action()
    except Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _back(request, anchor)


@router.route("/notes/add", methods=("POST",))
def note_add(request: Request) -> Response:
    return _do(request, lambda: notes_service.add_note(
        request.arg("scope") or "", request.arg("ref") or "", request.arg("body")))


@router.route("/notes/{note_id:int}/save", methods=("POST",))
def note_save(request: Request, note_id: int) -> Response:
    return _do(request, lambda: notes_service.edit_note(note_id, request.arg("body")))


@router.route("/notes/{note_id:int}/delete", methods=("POST",))
def note_delete(request: Request, note_id: int) -> Response:
    return _do(request, lambda: notes_service.delete_note(note_id))


@router.route("/todos/add", methods=("POST",))
def todo_add(request: Request) -> Response:
    return _do(request, lambda: notes_service.add_todo(
        request.arg("scope") or "", request.arg("ref") or "", request.arg("title"), request.arg("due")))


@router.route("/todos/{todo_id:int}/save", methods=("POST",))
def todo_save(request: Request, todo_id: int) -> Response:
    return _do(request, lambda: notes_service.edit_todo(todo_id, request.arg("title"), request.arg("due")))


@router.route("/todos/{todo_id:int}/done", methods=("POST",))
def todo_done(request: Request, todo_id: int) -> Response:
    return _do(request, lambda: notes_service.set_done(todo_id, request.arg("done") == "1"),
               anchor=f"todo-{todo_id}")


@router.route("/todos/{todo_id:int}/delete", methods=("POST",))
def todo_delete(request: Request, todo_id: int) -> Response:
    return _do(request, lambda: notes_service.delete_todo(todo_id))


@router.route("/todos")
def todos_page(request: Request) -> Response:
    return render("todos.html", active="todos",
                  **notes_service.todo_list(show_done=request.arg("done") == "all"))
