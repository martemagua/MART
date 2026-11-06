"""The bundle view's edit mode (partials/bulk.html, Martin 06.11.2026):
actions on the ticked renewals at once — your strategy, a proposal / quote,
completed. (Moving them is `clients.bundle_move`.) Each returns to the
bundle, still in edit mode, saying what was done."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit

from mart.services import actuals, proposals
from mart.web.framework import HTTPError, Request, Response, Router

router = Router()
_PROPOSAL = ("insurer", "plan_design", "label", "round", "received_on", "currency", "rate_change", "note")


def _ids(request: Request) -> list[int]:
    ids = [int(x) for x in request.args("renewal") if x.isdigit()]
    if not ids:
        raise HTTPError(400, "Tick at least one renewal first.")
    return ids


def _done(request: Request, client_id: int, message: str) -> Response:
    """Back to the page the form was on (a path on MART), with `done=`."""
    back = request.arg("back") or ""
    if not back.startswith("/") or back.startswith("//") or "\\" in back:
        back = f"/clients/{client_id}"
    parts = urlsplit(back.split("#", 1)[0])
    query = [(k, v) for k, v in parse_qsl(parts.query) if k != "done"] + [("done", message)]
    return Response.redirect(f"{parts.path}?{urlencode(query)}")


def _n(count: int) -> str:
    return f"{count} renewal{'s' if count != 1 else ''}"


@router.route("/clients/{client_id:int}/bulk/strategy", methods=("POST",))
def bulk_strategy(request: Request, client_id: int) -> Response:
    ids, value = _ids(request), request.arg("strategy")
    try:
        changed = actuals.set_strategy_many(client_id, ids, value, request.arg("reason"))
    except actuals.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    what = f"set to {value}" if value else "back to BM+'s"
    return _done(request, client_id, f"Strategy {what} for {_n(changed)}"
                 + (f" ({len(ids) - changed} already were)." if changed < len(ids) else "."))


@router.route("/clients/{client_id:int}/bulk/proposals", methods=("POST",))
def bulk_proposals(request: Request, client_id: int) -> Response:
    ids = _ids(request)
    form = {k: request.arg(k) for k in _PROPOSAL}
    premiums = {i: request.arg(f"premium_{i}") for i in ids}
    try:
        n = proposals.add_many(client_id, ids, form, premiums)
    except proposals.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _done(request, client_id, f"Proposal from {form['insurer'].strip()} added to {_n(n)}.")


@router.route("/clients/{client_id:int}/bulk/completed", methods=("POST",))
def bulk_completed(request: Request, client_id: int) -> Response:
    ids = _ids(request)
    try:
        n = actuals.set_completed(client_id, ids, request.arg("date"), request.arg("completed_note"))
    except actuals.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _done(request, client_id, f"{_n(n)} marked completed"
                 + (f" ({len(ids) - n} already were)." if n < len(ids) else "."))
