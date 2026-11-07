"""A client's own regions (services/regions): the page in the explorer's
middle and saving it."""

from __future__ import annotations

from urllib.parse import quote

from mart.services import client_service, notes_service, regions
from mart.web.framework import HTTPError, Request, Response, Router
from mart.web.templating import render

router = Router()


@router.route("/clients/{client_id:int}/regions")
def regions_page(request: Request, client_id: int) -> Response:
    try:
        view = client_service.explorer(client_id, show_all=request.arg("all") == "1", cards=False)
        page = regions.for_client(client_id)
    except (client_service.NotFound, regions.Invalid) as exc:
        raise HTTPError(404, str(exc)) from exc
    return render("client_explorer.html", active="clients", here=request.url, region_page=page,
                  notice=request.arg("done"),
                  client_counts=notes_service.counts(client_id).get(f"client:{client_id}"), **view)


@router.route("/clients/{client_id:int}/regions", methods=("POST",))
def regions_save(request: Request, client_id: int) -> Response:
    countries, names = request.args("country"), request.args("region")
    if len(countries) != len(names):
        raise HTTPError(400, "The form came back incomplete; nothing was changed.")
    try:
        n = regions.save(client_id, dict(zip(countries, names, strict=True)))
    except regions.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    msg = f"Regions saved: {n} countr{'y' if n == 1 else 'ies'} set by you, the others go by BM+."
    return Response.redirect(f"/clients/{client_id}/regions?done=" + quote(msg))
