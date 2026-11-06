"""Plan design changes (services/plan_changes): on a renewal (add, change,
move to another state, delete, take over / dismiss BM+'s suggestion) and the
client-wide overview. Write forms return to the page they came from."""

from __future__ import annotations

from mart.services import client_service, notes_service, plan_changes
from mart.web.framework import HTTPError, Request, Response, Router
from mart.web.routes.notes import _back
from mart.web.templating import render

router = Router()


def _do(request: Request, action) -> Response:
    try:
        action()
    except plan_changes.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _back(request, "plan-changes")


@router.route("/clients/{client_id:int}/renewals/{renewal_id:int}/plan-changes", methods=("POST",))
def change_add(request: Request, client_id: int, renewal_id: int) -> Response:
    args = [request.arg(k) for k in ("title", "detail", "status", "on")]
    return _do(request, lambda: plan_changes.add(client_id, renewal_id, *args))


@router.route("/clients/{client_id:int}/renewals/{renewal_id:int}/plan-changes/bm", methods=("POST",))
def change_from_bm(request: Request, client_id: int, renewal_id: int) -> Response:
    return _do(request, lambda: plan_changes.take_bm(client_id, renewal_id, keep=request.arg("keep") != "0"))


@router.route("/clients/{client_id:int}/plan-changes/{change_id:int}/save", methods=("POST",))
def change_save(request: Request, client_id: int, change_id: int) -> Response:
    return _do(request, lambda: plan_changes.edit(client_id, change_id, request.arg("title"),
                                                  request.arg("detail")))


@router.route("/clients/{client_id:int}/plan-changes/{change_id:int}/status", methods=("POST",))
def change_status(request: Request, client_id: int, change_id: int) -> Response:
    return _do(request, lambda: plan_changes.set_status(client_id, change_id, request.arg("status"),
                                                        request.arg("on")))


@router.route("/clients/{client_id:int}/plan-changes/{change_id:int}/delete", methods=("POST",))
def change_delete(request: Request, client_id: int, change_id: int) -> Response:
    return _do(request, lambda: plan_changes.delete(client_id, change_id))


@router.route("/clients/{client_id:int}/plan-changes")
def client_plan_changes(request: Request, client_id: int) -> Response:
    """Every plan design change of the client in the middle; the bundles stay."""
    try:
        view = client_service.explorer(client_id, show_all=request.arg("all") == "1")
        overview = plan_changes.client_overview(client_id, request.arg("status"))
    except (client_service.NotFound, plan_changes.Invalid) as exc:
        raise HTTPError(404, str(exc)) from exc
    return render("client_explorer.html", active="clients", here=request.url, plan_overview=overview,
                  client_counts=notes_service.counts(client_id).get(f"client:{client_id}"), **view)
