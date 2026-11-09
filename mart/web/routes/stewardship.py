"""The stewardship (services/stewardship, M3 day 9): the client's page for
its reporting period (in the explorer's middle), the client's reporting year,
and a renewal's savings and key learning. Write forms return to the page
they came from, at the renewal's savings."""

from __future__ import annotations

from mart.services import client_service, notes_service, stewardship
from mart.web.framework import HTTPError, Request, Response, Router
from mart.web.routes.notes import _back
from mart.web.templating import render

router = Router()


def _do(request: Request, action, anchor: str) -> Response:
    try:
        action()
    except stewardship.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _back(request, anchor)


@router.route("/clients/{client_id:int}/stewardship")
def page(request: Request, client_id: int) -> Response:
    year = request.arg("year")
    try:
        view = client_service.explorer(client_id, show_all=request.arg("all") == "1", cards=False)
        sv = stewardship.view(
            client_id,
            int(year) if (year or "").isdigit() else None,
            request.arg("from"),
            request.arg("until"),
        )
    except client_service.NotFound as exc:
        raise HTTPError(404, str(exc)) from exc
    except stewardship.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return render(
        "client_explorer.html",
        active="clients",
        here=request.url,
        stewardship=sv,
        client_counts=notes_service.counts(client_id).get(f"client:{client_id}"),
        **view,
    )


@router.route("/clients/{client_id:int}/stewardship/period", methods=("POST",))
def set_period(request: Request, client_id: int) -> Response:
    return _do(request, lambda: stewardship.set_start_month(client_id, request.arg("month")), "top")


@router.route("/clients/{client_id:int}/renewals/{renewal_id:int}/savings", methods=("POST",))
def savings(request: Request, client_id: int, renewal_id: int) -> Response:
    return _do(
        request,
        lambda: stewardship.save_savings(
            client_id,
            renewal_id,
            *(request.arg(k) for k in ("hard", "avoidance", "unrealized", "currency", "note")),
        ),
        f"savings-{renewal_id}",
    )


@router.route("/clients/{client_id:int}/renewals/{renewal_id:int}/savings/reset", methods=("POST",))
def savings_reset(request: Request, client_id: int, renewal_id: int) -> Response:
    return _do(request, lambda: stewardship.reset_savings(client_id, renewal_id), f"savings-{renewal_id}")


@router.route("/clients/{client_id:int}/renewals/{renewal_id:int}/learning", methods=("POST",))
def learning(request: Request, client_id: int, renewal_id: int) -> Response:
    return _do(
        request,
        lambda: stewardship.save_learning(client_id, renewal_id, request.arg("text")),
        f"savings-{renewal_id}",
    )
