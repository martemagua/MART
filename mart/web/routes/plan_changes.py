"""Plan design changes (services/plan_changes): add one covering several
renewals, track or dismiss one of BM+'s lines, change one (wording, premium
effect, which renewals it covers), record its outcome, delete it; and the
client-wide overview. Write forms return to the page they came from.
The renewals a change covers come as the tick boxes `cover`."""

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


@router.route("/clients/{client_id:int}/plan-changes/add", methods=("POST",))
def change_add(request: Request, client_id: int) -> Response:
    return _do(request, lambda: plan_changes.add(
        client_id, request.args("cover"), request.arg("title"), request.arg("detail"),
        request.arg("outcome"), request.arg("reason"), request.arg("cost")))


@router.route("/clients/{client_id:int}/plan-changes/track", methods=("POST",))
def change_track(request: Request, client_id: int) -> Response:
    return _do(request, lambda: plan_changes.track_bm(client_id, request.arg("line"), request.args("cover")))


@router.route("/clients/{client_id:int}/plan-changes/dismiss", methods=("POST",))
def change_dismiss(request: Request, client_id: int) -> Response:
    return _do(request, lambda: plan_changes.dismiss_bm(client_id, request.arg("line"), request.args("cover"),
                                                        undo=request.arg("undo") == "1"))


@router.route("/clients/{client_id:int}/plan-changes/{change_id:int}/save", methods=("POST",))
def change_save(request: Request, client_id: int, change_id: int) -> Response:
    # the tick boxes are on the form only where it lists the renewals (`covers` = 1)
    covers = request.args("cover") if request.arg("covers") == "1" else None
    return _do(request, lambda: plan_changes.edit(client_id, change_id, request.arg("title"),
                                                  request.arg("detail"), request.arg("cost"), covers))


@router.route("/clients/{client_id:int}/plan-changes/{change_id:int}/outcome", methods=("POST",))
def change_outcome(request: Request, client_id: int, change_id: int) -> Response:
    return _do(request, lambda: plan_changes.set_outcome(client_id, change_id, request.arg("outcome"),
                                                         request.arg("reason")))


@router.route("/clients/{client_id:int}/plan-changes/{change_id:int}/delete", methods=("POST",))
def change_delete(request: Request, client_id: int, change_id: int) -> Response:
    return _do(request, lambda: plan_changes.delete(client_id, change_id))


@router.route("/clients/{client_id:int}/plan-changes")
def client_plan_changes(request: Request, client_id: int) -> Response:
    """Every plan design change of the client in the middle; the bundles stay."""
    try:
        view = client_service.explorer(client_id, show_all=request.arg("all") == "1", cards=False)
        overview = plan_changes.client_overview(client_id, request.arg("outcome"))
    except (client_service.NotFound, plan_changes.Invalid) as exc:
        raise HTTPError(404, str(exc)) from exc
    return render("client_explorer.html", active="clients", here=request.url, plan_overview=overview,
                  client_counts=notes_service.counts(client_id).get(f"client:{client_id}"), **view)
