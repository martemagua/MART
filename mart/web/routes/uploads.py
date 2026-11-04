"""Uploads: choose a file → preview (pick my clients) → commit or discard."""

from __future__ import annotations

from urllib.parse import quote

from mart.services import upload_service
from mart.services.upload_service import UploadError
from mart.web.framework import HTTPError, Request, Response, Router
from mart.web.templating import render

router = Router()


def _page(request: Request, error: str | None = None, status: int = 200) -> Response:
    return render("uploads.html", status=status, active="uploads", error=error,
                  notice=request.arg("done"),
                  uploads=upload_service.recent_uploads(),
                  data=upload_service.overview())


@router.route("/uploads")
def uploads_page(request: Request) -> Response:
    return _page(request)


@router.route("/uploads", methods=("POST",))
def upload_file(request: Request) -> Response:
    files = request.files.get("file") or []
    if not files or not files[0].data:
        return _page(request, "Choose a tracker file first.", 400)
    f = files[0]
    try:
        upload_id = upload_service.stage(f.filename, f.data)
    except UploadError as exc:
        return _page(request, f"{f.filename}: {exc}", 400)
    return Response.redirect(f"/uploads/{upload_id}")


def _preview_page(upload_id: int, error: str | None = None, status: int = 200) -> Response:
    try:
        view = upload_service.preview(upload_id)
    except UploadError as exc:
        raise HTTPError(404, str(exc)) from exc
    return render("upload_preview.html", status=status, active="uploads", error=error, **view)


@router.route("/uploads/{upload_id:int}")
def upload_detail(request: Request, upload_id: int) -> Response:
    return _preview_page(upload_id)


@router.route("/uploads/{upload_id:int}/commit", methods=("POST",))
def upload_commit(request: Request, upload_id: int) -> Response:
    mine = set(request.args("mine"))
    try:
        summary = upload_service.commit(upload_id, mine, allow_older=bool(request.arg("allow_older")))
    except UploadError as exc:
        return _preview_page(upload_id, str(exc), 400)
    loaded = len(summary["clients_loaded"])
    msg = (f"Loaded {loaded} client{'s' if loaded != 1 else ''}: {summary['new']} new, "
           f"{summary['changed'] + summary['returned']} changed, {summary['unchanged']} unchanged, "
           f"{summary['left_export']} no longer in the export.")
    return Response.redirect("/uploads?done=" + quote(msg))


@router.route("/uploads/{upload_id:int}/discard", methods=("POST",))
def upload_discard(request: Request, upload_id: int) -> Response:
    try:
        upload_service.discard(upload_id)
    except UploadError as exc:
        return _preview_page(upload_id, str(exc), 400)
    return Response.redirect("/uploads?done=" + quote("Upload discarded. Nothing was changed."))
