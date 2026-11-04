"""First-start setup and the Settings page (same form, two entry points)."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from mart import settings as settings_mod
from mart.services import backup_service, preferences, setup_service, status_service
from mart.web.framework import Request, Response, Router
from mart.web.templating import render

router = Router()


def _form_values(request: Request) -> dict[str, str]:
    return {
        "data_dir": request.arg("data_dir", "") or "",
        "backup_dir": request.arg("backup_dir", "") or "",
        "backups_keep": request.arg("backups_keep", "") or "",
        "port": request.arg("port", "") or "",
    }


def _values_of(s: settings_mod.Settings) -> dict[str, str]:
    return {"data_dir": s.data_dir, "backup_dir": s.backup_dir,
            "backups_keep": str(s.backups_keep), "port": str(s.port)}


# ---------------------------------------------------------------------------
# First start
# ---------------------------------------------------------------------------
@router.route("/setup")
def setup_form(request: Request) -> Response:
    if settings_mod.load() is not None:
        return Response.redirect("/settings")
    return render("setup.html", values=_values_of(settings_mod.defaults()), errors=[])


@router.route("/setup", methods=("POST",))
def setup_save(request: Request) -> Response:
    if settings_mod.load() is not None:
        return Response.redirect("/settings")
    values = _form_values(request)
    new, errors = settings_mod.validate(**values)
    if errors:
        return render("setup.html", status=400, values=values, errors=errors)
    setup_service.apply(new)
    return Response.redirect("/?welcome=1")


# ---------------------------------------------------------------------------
# Settings page
# ---------------------------------------------------------------------------
def _settings_page(values: dict[str, str], errors: list[str], notes: list[str],
                   status: int = 200, pref_errors: list[str] | None = None,
                   pref_values: dict[str, str] | None = None) -> Response:
    s = settings_mod.load()
    return render("settings.html", status=status, values=values, errors=errors,
                  notes=notes, status_info=status_service.system_status(s),
                  prefs=preferences.PREFS, pref_values=pref_values or preferences.all_values(),
                  pref_errors=pref_errors or [], active="settings")


@router.route("/settings")
def settings_form(request: Request) -> Response:
    s = settings_mod.load()
    notes = []
    if request.arg("saved"):
        notes.append("Settings saved.")
    msg = request.arg("backup")
    if msg:
        notes.append(msg)
    if request.arg("limits"):
        notes.append("Time limits saved.")
    return _settings_page(_values_of(s), [], notes)


@router.route("/settings", methods=("POST",))
def settings_save(request: Request) -> Response:
    old = settings_mod.load()
    values = _form_values(request)
    new, errors = settings_mod.validate(**values)
    if errors:
        return _settings_page(values, errors, [], status=400)
    result = setup_service.apply(new, old)
    notes = ["Settings saved.", *result.notes]
    if old is not None and old.port != new.port:
        notes.append(f"The new port {new.port} is used from the next start of MART.")
    return _settings_page(_values_of(result.settings), [], notes)


@router.route("/settings/backup", methods=("POST",))
def backup_now(request: Request) -> Response:
    s = settings_mod.load()
    result = backup_service.make_backup(s.db_path, Path(s.backup_dir), s.backups_keep)
    return Response.redirect("/settings?backup=" + quote(result.message))


@router.route("/settings/limits", methods=("POST",))
def limits_save(request: Request) -> Response:
    values = {name: request.arg(name, "") or "" for name in preferences.PREFS}
    errors = preferences.save(values)
    if errors:
        s = settings_mod.load()
        return _settings_page(_values_of(s), [], [], status=400, pref_errors=errors, pref_values=values)
    return Response.redirect("/settings?limits=1")
