"""Clients: the list of my clients, one client's explorer, and moving renewals
between its bundles."""

from __future__ import annotations

from urllib.parse import quote

from mart.services import bundle_service, client_service, notes_service, renewal_service
from mart.web.framework import HTTPError, Request, Response, Router
from mart.web.templating import render

router = Router()


@router.route("/clients")
def clients_page(request: Request) -> Response:
    return render("clients.html", active="clients", clients=client_service.clients_overview(),
                  client_notes=notes_service.client_totals())


def _explorer(request: Request, client_id: int, **kw):
    try:
        return client_service.explorer(client_id, group=request.arg("group", "date") or "date",
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
    return render("client_explorer.html", active="clients", here=request.url, bundle_mine=bundle_mine,
                  client_counts=_client_counts(client_id), mine_counts=notes_service.counts(client_id),
                  **view)


@router.route("/clients/{client_id:int}/renewals/{renewal_id:int}")
def renewal_page(request: Request, client_id: int, renewal_id: int) -> Response:
    """The renewal panel in the middle; the bundle side panel stays."""
    try:
        detail = renewal_service.detail(client_id, renewal_id)
    except renewal_service.NotFound as exc:
        raise HTTPError(404, str(exc)) from exc
    r = detail["renewal"]
    view = _explorer(request, client_id, renewal_id=renewal_id, show_all=not r["in_latest_export"])
    mine = notes_service.for_renewal(r, view["selected"])
    return render("client_explorer.html", active="clients", detail=detail, here=request.url,
                  mine=mine, mine_counts={}, client_counts=_client_counts(client_id), **view)


@router.route("/clients/{client_id:int}/notes")
def client_notes(request: Request, client_id: int) -> Response:
    """The client's own notes and to-dos in the middle; the bundles stay."""
    view = _explorer(request, client_id)
    try:
        mine = notes_service.for_client(client_id)
    except notes_service.Invalid as exc:
        raise HTTPError(404, str(exc)) from exc
    return render("client_explorer.html", active="clients", here=request.url, client_mine=mine,
                  client_counts=_client_counts(client_id), **view)


# -- moving renewals between bundles ---------------------------------------------------
def _to_bundle(request: Request, client_id: int, key: str) -> Response:
    group = request.arg("group") or "date"
    return Response.redirect(f"/clients/{client_id}?bundle={quote(key, safe='')}&group={quote(group)}")


@router.route("/clients/{client_id:int}/bundles/move", methods=("POST",))
def bundle_move(request: Request, client_id: int) -> Response:
    ids = [int(x) for x in request.args("renewal") if x.isdigit()]
    try:
        key = bundle_service.move(client_id, ids, request.arg("target") or "", request.arg("name"))
    except bundle_service.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _to_bundle(request, client_id, key)


@router.route("/clients/{client_id:int}/bundles/rename", methods=("POST",))
def bundle_rename(request: Request, client_id: int) -> Response:
    try:
        key = bundle_service.rename(client_id, request.arg("key") or "", request.arg("name"))
    except bundle_service.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    return _to_bundle(request, client_id, key)
