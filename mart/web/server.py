"""The HTTP server: standard library only, bound to 127.0.0.1.

Nothing outside this machine can reach MART: the socket listens on the
loopback address only, and App.handle() additionally checks the Host and
Origin headers.
"""

from __future__ import annotations

import json
import mimetypes
import threading
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from mart.web.app import App, create_app
from mart.web.framework import Request, Response

STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_BODY = 200 * 1024 * 1024  # tracker uploads are a few MB; this is a safety cap
HOST = "127.0.0.1"


def allowed_hosts_for(port: int) -> set[str]:
    return {f"127.0.0.1:{port}", f"localhost:{port}"}


def serve_static(path: str) -> Response | None:
    """Files under /static/. Anything resolving outside STATIC_DIR is refused."""
    rel = path[len("/static/"):]
    target = (STATIC_DIR / rel).resolve()
    try:
        target.relative_to(STATIC_DIR)
    except ValueError:
        return Response.text("Not found", 404)
    if not target.is_file():
        return Response.text("Not found", 404)
    ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    if ctype.startswith("text/") or ctype in ("application/javascript",):
        ctype += "; charset=utf-8"
    return Response(target.read_bytes(), 200, ctype,
                    headers=[("Cache-Control", "no-cache")])


def make_handler(app: App) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "MART"
        sys_version = ""

        def _dispatch(self) -> None:
            path, _, query = self.path.partition("?")
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                self._send(Response.text("Upload too large", 413))
                return
            body = self.rfile.read(length) if length else b""
            headers = {k.lower(): v for k, v in self.headers.items()}
            request = Request(self.command, path, query, headers, body)
            if path.startswith("/static/") and self.command == "GET":
                response = serve_static(path) or Response.text("Not found", 404)
            else:
                response = app.handle(request)
            self._send(response)

        def _send(self, response: Response) -> None:
            body = response.body_bytes
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "same-origin")
            for name, value in response.headers:
                self.send_header(name, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        do_GET = do_POST = do_HEAD = _dispatch

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            pass  # quiet console; errors go to the error log

    return Handler


def running_mart(port: int) -> dict | None:
    """The /health answer if a MART is already listening on `port`."""
    try:
        with urllib.request.urlopen(f"http://{HOST}:{port}/health", timeout=1.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data if data.get("app") == "MART" else None
    except (OSError, ValueError):
        return None


def bind(preferred: int, tries: int = 10) -> ThreadingHTTPServer:
    """A server on `preferred`, or the next free port above it."""
    last_error: OSError | None = None
    for port in range(preferred, preferred + tries):
        try:
            return ThreadingHTTPServer((HOST, port), BaseHTTPRequestHandler)
        except OSError as exc:
            last_error = exc
    raise OSError(f"No free port between {preferred} and {preferred + tries - 1}") from last_error


def serve(preferred_port: int, open_browser: bool = True) -> None:
    httpd = bind(preferred_port)
    port = httpd.server_address[1]
    httpd.RequestHandlerClass = make_handler(create_app(allowed_hosts_for(port)))
    httpd.daemon_threads = True
    url = f"http://{HOST}:{port}/"
    print(f"\n  MART is running at {url}")
    print("  Keep this window open while you use MART. Close it (or press Ctrl+C) to stop.\n")
    if open_browser:
        threading.Timer(0.6, webbrowser.open, args=(url,)).start()
    try:
        httpd.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\n  MART stopped.")
    finally:
        httpd.server_close()
