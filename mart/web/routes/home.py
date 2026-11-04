"""Home page and the health endpoint."""

from __future__ import annotations

from mart import RELEASE_LABEL, __version__
from mart import settings as settings_mod
from mart.services import status_service, upload_service
from mart.web.framework import Request, Response, Router
from mart.web.templating import render

router = Router()


@router.route("/")
def home(request: Request) -> Response:
    s = settings_mod.load()
    return render("home.html", status_info=status_service.system_status(s), active="home",
                  welcome=bool(request.arg("welcome")), data=upload_service.overview())


@router.route("/health")
def health(request: Request) -> Response:
    # Also how a second MART.bat start recognises an already-running MART.
    return Response.json({"app": "MART", "version": __version__, "release": RELEASE_LABEL,
                          "configured": settings_mod.load() is not None})
