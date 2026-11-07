"""Notes and to-dos: the write endpoints (each returns to the page it came
from) and the To-dos page."""

from __future__ import annotations

from mart.services import notes_service
from mart.services.notes_service import Invalid
from mart.web.framework import HTTPError, Request, Response, Router, local_path
from mart.web.templating import render

router = Router()


def _back(request: Request, anchor: str = "mine") -> Response:
    """Back to the page the form was on. Only a path on this site counts."""
    back = local_path(request.arg("back"), "/todos")
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
        request.arg("scope") or "", request.arg("ref") or "", request.arg("body"), request.arg("topic")))


@router.route("/notes/{note_id:int}/save", methods=("POST",))
def note_save(request: Request, note_id: int) -> Response:
    return _do(request, lambda: notes_service.edit_note(note_id, request.arg("body")))


@router.route("/notes/{note_id:int}/delete", methods=("POST",))
def note_delete(request: Request, note_id: int) -> Response:
    return _do(request, lambda: notes_service.delete_note(note_id))


@router.route("/todos/add", methods=("POST",))
def todo_add(request: Request) -> Response:
    return _do(request, lambda: notes_service.add_todo(
        request.arg("scope") or "", request.arg("ref") or "", request.arg("title"), request.arg("due"),
        request.arg("urgency"), request.arg("topic"), _repeat(request)))


def _repeat(request: Request) -> dict | None:
    """The repeat fields (partials/mine.html `repeat_fields`), when the form has them."""
    if "repeat_unit" not in request.form:
        return None
    return {"unit": request.arg("repeat_unit"), "every": request.arg("repeat_every"),
            "weekdays": request.args("repeat_weekdays")}


DETAIL_FIELDS = ("description", "urgency", "status", "waiting_kind", "waiting_on", "waiting_since")


@router.route("/todos/{todo_id:int}/save", methods=("POST",))
def todo_save(request: Request, todo_id: int) -> Response:
    # the full edit form carries the M2 extras (it always sends "status")
    details = {k: request.arg(k) for k in DETAIL_FIELDS} if "status" in request.form else None
    return _do(request, lambda: notes_service.edit_todo(todo_id, request.arg("title"), request.arg("due"),
                                                         details, _repeat(request)), anchor=f"todo-{todo_id}")


@router.route("/todos/{todo_id:int}/steps/add", methods=("POST",))
def step_add(request: Request, todo_id: int) -> Response:
    return _do(request, lambda: notes_service.add_step(todo_id, request.arg("title")),
               anchor=f"todo-{todo_id}")


def _step(request: Request, action) -> Response:
    try:
        todo_id = action()
    except Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _back(request, f"todo-{todo_id}")


@router.route("/todos/steps/{step_id:int}/done", methods=("POST",))
def step_done(request: Request, step_id: int) -> Response:
    return _step(request, lambda: notes_service.set_step_done(step_id, request.arg("done") == "1"))


@router.route("/todos/steps/{step_id:int}/delete", methods=("POST",))
def step_delete(request: Request, step_id: int) -> Response:
    return _step(request, lambda: notes_service.delete_step(step_id))


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
