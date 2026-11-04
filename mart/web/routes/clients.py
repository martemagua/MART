"""Clients: the list of my clients, and one client's explorer."""

from __future__ import annotations

from mart.services import client_service
from mart.web.framework import HTTPError, Request, Response, Router
from mart.web.templating import render

router = Router()


@router.route("/clients")
def clients_page(request: Request) -> Response:
    return render("clients.html", active="clients", clients=client_service.clients_overview())


@router.route("/clients/{client_id:int}")
def client_explorer(request: Request, client_id: int) -> Response:
    try:
        view = client_service.explorer(
            client_id, bundle=request.arg("bundle"), group=request.arg("group", "date") or "date",
            show_all=request.arg("all") == "1")
    except client_service.NotFound as exc:
        raise HTTPError(404, str(exc)) from exc
    return render("client_explorer.html", active="clients", **view)
