"""A deliberately small web layer on the standard library.

MART can't install a web framework, and one user on 127.0.0.1 doesn't need
one. This gives the three things the pages need: a Request with parsed
query/form, a Response, and a Router with `{name}` / `{name:int}` path
parameters. Handlers are plain functions `handler(request, **params)`.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any
from urllib.parse import parse_qs

Handler = Callable[..., "Response"]


class HTTPError(Exception):
    def __init__(self, status: int, message: str = ""):
        super().__init__(message or str(status))
        self.status = status
        self.message = message


@dataclass
class Request:
    method: str
    path: str
    query_string: str = ""
    headers: dict[str, str] = field(default_factory=dict)  # lower-case keys
    body: bytes = b""

    @cached_property
    def query(self) -> dict[str, list[str]]:
        return parse_qs(self.query_string, keep_blank_values=True)

    @cached_property
    def form(self) -> dict[str, list[str]]:
        ctype = self.headers.get("content-type", "")
        if ctype.startswith("application/x-www-form-urlencoded"):
            return parse_qs(self.body.decode("utf-8", errors="replace"),
                            keep_blank_values=True)
        return {}

    def arg(self, name: str, default: str | None = None) -> str | None:
        """First value of `name` from the form, else from the query string."""
        for source in (self.form, self.query):
            if name in source and source[name]:
                return source[name][0]
        return default

    @property
    def is_htmx(self) -> bool:
        return self.headers.get("hx-request") == "true"


@dataclass
class Response:
    body: bytes | str = b""
    status: int = 200
    content_type: str = "text/html; charset=utf-8"
    headers: list[tuple[str, str]] = field(default_factory=list)

    @property
    def body_bytes(self) -> bytes:
        return self.body.encode("utf-8") if isinstance(self.body, str) else self.body

    @classmethod
    def redirect(cls, location: str, status: int = 303) -> Response:
        return cls(b"", status, headers=[("Location", location)])

    @classmethod
    def json(cls, data: Any, status: int = 200) -> Response:
        return cls(json.dumps(data, default=str), status, "application/json; charset=utf-8")

    @classmethod
    def text(cls, text: str, status: int = 200) -> Response:
        return cls(text, status, "text/plain; charset=utf-8")


_PARAM_RE = re.compile(r"\{(\w+)(?::(int))?\}")


@dataclass
class _Route:
    methods: tuple[str, ...]
    regex: re.Pattern[str]
    converters: dict[str, Callable[[str], Any]]
    handler: Handler
    pattern: str


class Router:
    def __init__(self) -> None:
        self._routes: list[_Route] = []

    def add(self, pattern: str, handler: Handler, methods: tuple[str, ...] = ("GET",)) -> None:
        converters: dict[str, Callable[[str], Any]] = {}

        def repl(m: re.Match[str]) -> str:
            name, kind = m.group(1), m.group(2)
            if kind == "int":
                converters[name] = int
                return rf"(?P<{name}>\d+)"
            converters[name] = str
            return rf"(?P<{name}>[^/]+)"

        regex = re.compile("^" + _PARAM_RE.sub(repl, pattern) + "$")
        self._routes.append(_Route(tuple(m.upper() for m in methods), regex,
                                   converters, handler, pattern))

    def route(self, pattern: str, methods: tuple[str, ...] = ("GET",)) -> Callable[[Handler], Handler]:
        def deco(fn: Handler) -> Handler:
            self.add(pattern, fn, methods)
            return fn
        return deco

    def include(self, other: Router) -> None:
        self._routes.extend(other._routes)

    def match(self, method: str, path: str) -> tuple[Handler, dict[str, Any]]:
        allowed = False
        for r in self._routes:
            m = r.regex.match(path)
            if not m:
                continue
            allowed = True
            if method.upper() in r.methods:
                params = {k: r.converters[k](v) for k, v in m.groupdict().items()}
                return r.handler, params
        if allowed:
            raise HTTPError(405, "Method not allowed")
        raise HTTPError(404, "Page not found")
