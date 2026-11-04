"""The MART web application: routes + the rules every request passes.

Every request goes through `App.handle()`:
1. **Host check**: only requests addressed to this machine's MART
   (127.0.0.1 / localhost on our port) are served. This blocks "DNS
   rebinding", where a web page tricks the browser into talking to a local
   server.
2. **Origin check on POST**: a form may only be posted from MART's own
   pages, so another website open in the browser can't change anything.
3. **Setup gate**: until MART is set up, every page leads to /setup.
4. Routing; any unexpected error becomes a readable error page, and the
   details go to the error log in the data folder.
"""

from __future__ import annotations

import traceback
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from mart import settings as settings_mod
from mart.web import templating
from mart.web.framework import HTTPError, Request, Response, Router

# Paths that work before MART is set up.
_OPEN_PATHS = ("/setup", "/health")


class App:
    def __init__(self, router: Router, allowed_hosts: set[str] | None = None):
        self.router = router
        # None = don't check (tests calling handle() directly).
        self.allowed_hosts = allowed_hosts

    # -- the rules -----------------------------------------------------------
    def _host_ok(self, request: Request) -> bool:
        if self.allowed_hosts is None:
            return True
        return request.headers.get("host", "").lower() in self.allowed_hosts

    def _origin_ok(self, request: Request) -> bool:
        if request.method != "POST" or self.allowed_hosts is None:
            return True
        for header in ("origin", "referer"):
            value = request.headers.get(header)
            if value:
                return urlsplit(value).netloc.lower() in self.allowed_hosts
        return True  # no browser headers at all: a local script, not a web page

    def _back(self, request: Request) -> str | None:
        """The MART page the request came from (to go back and try again)."""
        ref = urlsplit(request.headers.get("referer") or "")
        if not ref.path.startswith("/") or (self.allowed_hosts is not None
                                            and ref.netloc.lower() not in self.allowed_hosts):
            return None
        return ref.path + (f"?{ref.query}" if ref.query else "")

    # -- dispatch ------------------------------------------------------------
    def handle(self, request: Request) -> Response:
        try:
            if not self._host_ok(request):
                raise HTTPError(403, "This address is not served by MART.")
            if not self._origin_ok(request):
                raise HTTPError(403, "Changes can only be made from MART's own pages.")
            if settings_mod.load() is None and not request.path.startswith(_OPEN_PATHS):
                return Response.redirect("/setup")
            handler, params = self.router.match(request.method, request.path)
            return handler(request, **params)
        except HTTPError as exc:
            return templating.render("error.html", status=exc.status, status_code=exc.status,
                                     message=exc.message, back=self._back(request),
                                     configured=settings_mod.load() is not None)
        except Exception:  # noqa: BLE001  (last line of defence: show, log, carry on)
            log_file = log_error(request)
            return templating.render("error.html", status=500, status_code=500,
                                     message="Something went wrong on this page.",
                                     log_file=log_file, back=self._back(request),
                                     configured=settings_mod.load() is not None)


def log_error(request: Request) -> Path:
    s = settings_mod.load()
    log_dir = s.log_dir if s else settings_mod.settings_file().parent
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "mart-error.log"
    with open(log_file, "a", encoding="utf-8") as fh:
        fh.write(f"\n=== {datetime.now().isoformat(timespec='seconds')} "
                 f"{request.method} {request.path}\n")
        fh.write(traceback.format_exc())
    return log_file


def build_router() -> Router:
    from mart.web.routes import clients, home, notes, setup, uploads

    router = Router()
    for module in (home, setup, uploads, clients, notes):
        router.include(module.router)
    return router


def create_app(allowed_hosts: set[str] | None = None) -> App:
    return App(build_router(), allowed_hosts)
