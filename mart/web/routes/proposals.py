"""The proposals Martin records on a renewal (services/proposals): add,
change, delete, mark chosen, and each proposal's quotes (first, revised…,
final). Each returns to the page it came from."""

from __future__ import annotations

from mart.services import proposals
from mart.web.framework import HTTPError, Request, Response, Router
from mart.web.routes.notes import _back

router = Router()
_FORM = ("insurer", "plan_design", "label",                                       # the proposal
         "round", "received_on", "premium", "currency", "rate_change", "note")    # a quote


def _do(request: Request, action) -> Response:
    try:
        action()
    except proposals.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _back(request, "proposals")


def _form(request: Request) -> dict[str, str | None]:
    return {k: request.arg(k) for k in _FORM}


@router.route("/clients/{client_id:int}/renewals/{renewal_id:int}/proposals", methods=("POST",))
def proposal_add(request: Request, client_id: int, renewal_id: int) -> Response:
    return _do(request, lambda: proposals.add(client_id, renewal_id, _form(request)))


@router.route("/clients/{client_id:int}/proposals/{proposal_id:int}/save", methods=("POST",))
def proposal_save(request: Request, client_id: int, proposal_id: int) -> Response:
    return _do(request, lambda: proposals.edit(client_id, proposal_id, _form(request)))


@router.route("/clients/{client_id:int}/proposals/{proposal_id:int}/delete", methods=("POST",))
def proposal_delete(request: Request, client_id: int, proposal_id: int) -> Response:
    return _do(request, lambda: proposals.delete(client_id, proposal_id))


@router.route("/clients/{client_id:int}/proposals/{proposal_id:int}/chosen", methods=("POST",))
def proposal_chosen(request: Request, client_id: int, proposal_id: int) -> Response:
    return _do(request, lambda: proposals.choose(client_id, proposal_id, request.arg("chosen") == "1"))


@router.route("/clients/{client_id:int}/proposals/{proposal_id:int}/quotes", methods=("POST",))
def quote_add(request: Request, client_id: int, proposal_id: int) -> Response:
    return _do(request, lambda: proposals.add_quote(client_id, proposal_id, _form(request)))


@router.route("/clients/{client_id:int}/quotes/{quote_id:int}/save", methods=("POST",))
def quote_save(request: Request, client_id: int, quote_id: int) -> Response:
    return _do(request, lambda: proposals.edit_quote(client_id, quote_id, _form(request)))


@router.route("/clients/{client_id:int}/quotes/{quote_id:int}/delete", methods=("POST",))
def quote_delete(request: Request, client_id: int, quote_id: int) -> Response:
    return _do(request, lambda: proposals.delete_quote(client_id, quote_id))
