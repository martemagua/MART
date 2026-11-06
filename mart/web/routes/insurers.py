"""Insurers: the Insurer Capability Database by country (services/capabilities)."""

from __future__ import annotations

from mart.services import capabilities
from mart.web.framework import Request, Response, Router
from mart.web.templating import render

router = Router()


@router.route("/insurers")
def insurers_page(request: Request) -> Response:
    country = (request.arg("country") or "").strip() or None
    network = (request.arg("network") or "").strip() or None
    line = (request.arg("line") or "").strip() or None
    view = capabilities.for_country(country, network, line) if country else None
    return render("insurers.html", active="insurers", browse=capabilities.browse(),
                  options=capabilities.filters(), view=view, country=country, network=network, line=line,
                  caps=capabilities.CAPS)
