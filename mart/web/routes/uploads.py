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
                  waiting=upload_service.waiting_uploads(),
                  data=upload_service.overview())


@router.route("/uploads")
def uploads_page(request: Request) -> Response:
    return _page(request)


@router.route("/uploads", methods=("POST",))
def upload_file(request: Request) -> Response:
    """One or several files. Each is staged on its own; one bad file never
    stops the others."""
    files = [f for f in request.files.get("file") or [] if f.data]
    if not files:
        return _page(request, "Choose one or more tracker files first.", 400)
    staged, errors = [], []
    for f in files:
        try:
            staged.append(upload_service.stage(f.filename, f.data))
        except UploadError as exc:
            errors.append(f"{f.filename}: {exc}")
    if not staged:
        return _page(request, " · ".join(errors), 400)
    # Straight to the first preview; the others follow one by one.
    query = []
    if len(staged) > 1:
        query.append("done=" + quote(f"{len(staged)} files uploaded. Here is the first; after you "
                                     "commit or discard it, MART opens the next."))
    if errors:
        query.append("failed=" + quote("Not uploaded: " + " · ".join(errors)))
    first = next((w["id"] for w in upload_service.waiting_uploads() if w["id"] in staged), staged[0])
    return Response.redirect(f"/uploads/{first}" + ("?" + "&".join(query) if query else ""))


def _preview_page(upload_id: int, error: str | None = None, status: int = 200,
                  notice: str | None = None) -> Response:
    try:
        view = upload_service.preview(upload_id)
    except UploadError as exc:
        raise HTTPError(404, str(exc)) from exc
    page = "upload_reference.html" if view.get("reference") else "upload_preview.html"
    return render(page, status=status, active="uploads", error=error, notice=notice, **view)


@router.route("/uploads/{upload_id:int}")
def upload_detail(request: Request, upload_id: int) -> Response:
    return _preview_page(upload_id, error=request.arg("failed"), notice=request.arg("done"))


@router.route("/uploads/{upload_id:int}/commit", methods=("POST",))
def upload_commit(request: Request, upload_id: int) -> Response:
    mine = set(request.args("mine"))
    try:
        summary = upload_service.commit(upload_id, mine, allow_older=bool(request.arg("allow_older")))
    except UploadError as exc:
        return _preview_page(upload_id, str(exc), 400)
    if "rows" in summary:                    # a reference list (Insurer Capability Database)
        msg = (f"Insurer Capability Database loaded: {summary['rows']} partner rows ({summary['new']} new, "
               f"{summary['changed']} changed, {summary['removed']} no longer in the list).")
        return _after_commit(msg)
    loaded = len(summary["clients_loaded"])
    nouns = "tasks" if summary.get("tracker") == "task_tracker" else "renewals"
    msg = (f"Loaded {loaded} client{'s' if loaded != 1 else ''} ({nouns}): {summary['new']} new, "
           f"{summary['changed'] + summary['returned']} changed, {summary['unchanged']} unchanged, "
           f"{summary['left_export']} no longer in the export.")
    if summary.get("skipped"):
        msg += (f" {summary['skipped']} not loaded (implementation / contract tasks, "
                "or no renewal in MART).")
    return _after_commit(msg)


def _after_commit(msg: str) -> Response:
    waiting = upload_service.waiting_uploads()
    if waiting:     # several files uploaded at once: straight on to the next one
        return Response.redirect(f"/uploads/{waiting[0]['id']}?done=" + quote(msg))
    return Response.redirect("/uploads?done=" + quote(msg))


@router.route("/uploads/{upload_id:int}/discard", methods=("POST",))
def upload_discard(request: Request, upload_id: int) -> Response:
    try:
        upload_service.discard(upload_id)
    except UploadError as exc:
        return _preview_page(upload_id, str(exc), 400)
    msg = "Upload discarded. Nothing was changed."
    waiting = upload_service.waiting_uploads()
    if waiting:
        return Response.redirect(f"/uploads/{waiting[0]['id']}?done=" + quote(msg))
    return Response.redirect("/uploads?done=" + quote(msg))
