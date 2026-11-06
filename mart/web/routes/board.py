"""The board (services/board_service): one per client, a card per bundle,
and moving a card to another column. `/board` picks the client."""

from __future__ import annotations

from mart.services import board_service, client_service
from mart.web.framework import HTTPError, Request, Response, Router
from mart.web.templating import render

router = Router()


@router.route("/board")
def board_index(request: Request) -> Response:
    clients = client_service.clients_overview()
    if len(clients) == 1:
        return Response.redirect(f"/clients/{clients[0]['id']}/board")
    return render("board_index.html", active="board", clients=clients)


@router.route("/clients/{client_id:int}/board")
def board_page(request: Request, client_id: int) -> Response:
    try:
        view = board_service.board_of(client_id)
    except board_service.Invalid as exc:
        raise HTTPError(404, str(exc)) from exc
    return render("board.html", active="board", here=request.url, **view)


@router.route("/clients/{client_id:int}/board/stage", methods=("POST",))
def board_stage(request: Request, client_id: int) -> Response:
    key = request.arg("key") or ""
    try:
        board_service.set_stage(client_id, key, request.arg("stage"), request.arg("reason"),
                                complete=request.arg("complete") == "1")
    except board_service.Invalid as exc:
        raise HTTPError(400, str(exc)) from exc
    back = request.arg("back") or ""
    if not back.startswith("/") or back.startswith("//") or "\\" in back:
        back = f"/clients/{client_id}/board"
    return Response.redirect(back.split("#", 1)[0])
