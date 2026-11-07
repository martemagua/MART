"""Clients: the list of my clients, one client's explorer, and moving renewals
between its bundles."""

from __future__ import annotations

from urllib.parse import quote

from mart.services import (
    actuals,
    bundle_service,
    client_cards,
    client_service,
    deadlines,
    freshness,
    notes_service,
    proposals,
    renewal_service,
)
from mart.web.framework import HTTPError, Request, Response, Router, local_path
from mart.web.templating import render

router = Router()


@router.route("/clients")
def clients_page(request: Request) -> Response:
    return render("clients.html", active="clients", clients=client_cards.cards(),
                  client_notes=notes_service.client_totals())


def _explorer(request: Request, client_id: int, **kw):
    try:
        return client_service.explorer(client_id,
                                       show_all=request.arg("all") == "1" or kw.pop("show_all", False), **kw)
    except client_service.NotFound as exc:
        raise HTTPError(404, str(exc)) from exc


def _client_counts(client_id: int):
    return notes_service.counts(client_id).get(f"client:{client_id}")


@router.route("/clients/{client_id:int}")
def client_explorer(request: Request, client_id: int) -> Response:
    view = _explorer(request, client_id, bundle=request.arg("bundle"))
    s = view["selected"]
    bundle_mine = notes_service.for_bundle(client_id, s) if s else None
    # opened from the Clients list (no bundle asked for): the side panel starts
    # at the top, without the filters set earlier in this browser tab
    editing = request.arg("edit") == "1" and bool(s)
    bulk_insurers = proposals.insurer_choices(client_id, s["country"]) if editing else None
    return render("client_explorer.html", active="clients", here=request.url, bundle_mine=bundle_mine,
                  client_counts=_client_counts(client_id), mine_counts=notes_service.counts(client_id),
                  fresh=not request.arg("bundle"), editing=editing, notice=request.arg("done"),
                  bulk_insurers=bulk_insurers, **view)


@router.route("/clients/{client_id:int}/renewals/{renewal_id:int}")
def renewal_page(request: Request, client_id: int, renewal_id: int) -> Response:
    """The renewal panel in the middle; the bundle side panel stays."""
    try:
        detail = renewal_service.detail(client_id, renewal_id)
    except renewal_service.NotFound as exc:
        raise HTTPError(404, str(exc)) from exc
    r = detail["renewal"]
    view = _explorer(request, client_id, renewal_id=renewal_id, show_all=not r["in_latest_export"],
                     cards=False)
    if view["selected"]:                    # the bundle's broker deadline pauses the stale clock
        detail["freshness"] = freshness.pause(detail["freshness"], view["selected"]["deadline"])
    mine = notes_service.for_renewal(r, view["selected"])
    return render("client_explorer.html", active="clients", detail=detail, here=request.url,
                  mine=mine, mine_counts={}, client_counts=_client_counts(client_id), **view)


@router.route("/clients/{client_id:int}/notes")
def client_notes(request: Request, client_id: int) -> Response:
    """The client's own notes and to-dos in the middle; the bundles stay."""
    view = _explorer(request, client_id, cards=False)
    try:
        mine = notes_service.for_client(client_id)
    except notes_service.Invalid as exc:
        raise HTTPError(404, str(exc)) from exc
    return render("client_explorer.html", active="clients", here=request.url, client_mine=mine,
                  client_counts=_client_counts(client_id), **view)


# -- moving renewals between bundles ---------------------------------------------------
def _to_bundle(client_id: int, key: str) -> Response:
    return Response.redirect(f"/clients/{client_id}?bundle={quote(key, safe='')}")


@router.route("/clients/{client_id:int}/bundles/move", methods=("POST",))
def bundle_move(request: Request, client_id: int) -> Response:
    ids = [int(x) for x in request.args("renewal") if x.isdigit()]
    try:
        key = bundle_service.move(client_id, ids, request.arg("target") or "", request.arg("name"))
    except bundle_service.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _to_bundle(client_id, key)


@router.route("/clients/{client_id:int}/bundles/rename", methods=("POST",))
def bundle_rename(request: Request, client_id: int) -> Response:
    try:
        key = bundle_service.rename(client_id, request.arg("key") or "", request.arg("name"))
    except bundle_service.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _to_bundle(client_id, key)


# -- broker deadlines on bundles (services/deadlines) ----------------------------------
def _after_deadline(request: Request, client_id: int, key: str, anchor: str = "deadline") -> Response:
    """Back to the page the form was on (a path on MART), else the bundle."""
    back = local_path(request.arg("back"), "")
    if back:
        return Response.redirect(back.split("#", 1)[0] + "#" + anchor)
    return _to_bundle(client_id, key)


@router.route("/clients/{client_id:int}/bundles/deadline", methods=("POST",))
def deadline_set(request: Request, client_id: int) -> Response:
    key = request.arg("key") or ""
    try:
        deadlines.set_deadline(client_id, key, request.arg("date"), request.arg("promised_by"),
                               request.arg("note"))
    except deadlines.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _after_deadline(request, client_id, key)


@router.route("/clients/{client_id:int}/bundles/deadline/close", methods=("POST",))
def deadline_close(request: Request, client_id: int) -> Response:
    key = request.arg("key") or ""
    try:
        deadlines.close(client_id, key, request.arg("outcome") or "", request.arg("date"))
    except deadlines.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _after_deadline(request, client_id, key)


# -- the actual state of renewals (services/actuals) -----------------------------------
@router.route("/clients/{client_id:int}/renewals/{renewal_id:int}/strategy", methods=("POST",))
def actual_strategy(request: Request, client_id: int, renewal_id: int) -> Response:
    try:
        actuals.set_strategy(client_id, renewal_id, request.arg("strategy"), request.arg("reason"))
    except actuals.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _after_deadline(request, client_id, "", "actual")


@router.route("/clients/{client_id:int}/completed", methods=("POST",))
def actual_completed(request: Request, client_id: int) -> Response:
    """Mark one renewal or a whole bundle completed (or take it back)."""
    ids = [int(x) for x in request.args("rid") if x.isdigit()]
    undo = request.arg("undo") == "1"
    try:
        actuals.set_completed(client_id, ids, request.arg("date"), request.arg("reason"), undo=undo)
    except actuals.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _after_deadline(request, client_id, "", "actual" if len(ids) == 1 else "completed")
