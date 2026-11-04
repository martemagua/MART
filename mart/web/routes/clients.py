"""Clients: the list of my clients, and one client's explorer."""

from __future__ import annotations

from mart.services import client_service, notes_service, renewal_service
from mart.web.framework import HTTPError, Request, Response, Router
from mart.web.templating import render

router = Router()


@router.route("/clients")
def clients_page(request: Request) -> Response:
    return render("clients.html", active="clients", clients=client_service.clients_overview(),
                  client_notes=notes_service.client_totals())


@router.route("/clients/{client_id:int}")
def client_explorer(request: Request, client_id: int) -> Response:
    try:
        view = client_service.explorer(
            client_id, bundle=request.arg("bundle"), group=request.arg("group", "date") or "date",
            show_all=request.arg("all") == "1")
    except client_service.NotFound as exc:
        raise HTTPError(404, str(exc)) from exc
    s = view["selected"]
    bundle_mine = notes_service.for_bundle(client_id, s["country"], s["renewal_date"]) if s else None
    return render("client_explorer.html", active="clients", here=request.url, bundle_mine=bundle_mine,
                  client_counts=notes_service.counts(client_id).get(f"client:{client_id}"),
                  mine_counts=notes_service.counts(client_id), **view)


@router.route("/clients/{client_id:int}/renewals/{renewal_id:int}")
def renewal_page(request: Request, client_id: int, renewal_id: int) -> Response:
    """The renewal panel in the middle; the bundle side panel stays."""
    try:
        detail = renewal_service.detail(client_id, renewal_id)
        r = detail["renewal"]
        view = client_service.explorer(
            client_id, bundle=client_service.bundle_key(r["country"], r["renewal_date"]),
            group=request.arg("group", "date") or "date",
            show_all=request.arg("all") == "1" or not r["in_latest_export"])
    except (client_service.NotFound, renewal_service.NotFound) as exc:
        raise HTTPError(404, str(exc)) from exc
    return render("client_explorer.html", active="clients", detail=detail, here=request.url,
                  mine=notes_service.for_renewal(r), mine_counts={},
                  client_counts=notes_service.counts(client_id).get(f"client:{client_id}"), **view)


@router.route("/clients/{client_id:int}/notes")
def client_notes(request: Request, client_id: int) -> Response:
    """The client's own notes and to-dos in the middle; the bundles stay."""
    try:
        view = client_service.explorer(client_id, group=request.arg("group", "date") or "date",
                                       show_all=request.arg("all") == "1")
        mine = notes_service.for_client(client_id)
    except (client_service.NotFound, notes_service.Invalid) as exc:
        raise HTTPError(404, str(exc)) from exc
    return render("client_explorer.html", active="clients", here=request.url, client_mine=mine,
                  client_counts=notes_service.counts(client_id).get(f"client:{client_id}"), **view)
