"""Uploading a tracker: stage → preview → commit (or discard).

* **Stage** reads the file once, stores its parsed rows and the upload's
  facts, and keeps NOTHING else: the .xlsx itself is not saved.
* **Preview** is computed live against the database, so it is always right
  even if another upload was committed in between. It is per client, because
  the commit is: only the clients ticked as "mine" are loaded.
* **Commit** runs in one transaction. Items (renewals, tasks) of "my" clients
  are added or updated; an item of such a client that is NOT in the file is
  marked "no longer in the export" and kept, never deleted. Only clients
  present in the file are affected, so a single-client export never touches
  the others. Then a backup is made.

The tracker-specific parts (how to read the file, compare and save its
items) live in `services/trackers.py`, one adapter per tracker.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from mart import settings as settings_mod
from mart.ingestion import renewal_tracker as rt
from mart.ingestion import task_tracker as tt
from mart.repository import clients_repo, renewals_repo, uploads_repo
from mart.repository.db import connection
from mart.services import backup_service, trackers


class UploadError(ValueError):
    """Shown to the user as is."""


def stage(filename: str, data: bytes) -> int:
    if not data:
        raise UploadError("The file is empty.")
    try:
        adapter = trackers.detect(data)
        parsed = adapter.parse(data)
    except (trackers.UnknownFile, rt.NotThisTracker, tt.NotThisTracker) as exc:
        raise UploadError(str(exc)) from exc
    if not parsed.items:
        raise UploadError(f"No {adapter.nouns} found in this export.")
    clients: dict[str, str] = {}
    for item in parsed.items:
        clients.setdefault(item["client_key"], item["client_name"])
    preview = {"clients": clients, "items": len(parsed.items), "title": parsed.title, **parsed.extra}
    rows = [(item["key"], item["client_key"], item) for item in parsed.items]
    with connection() as conn:
        return uploads_repo.create_staged(
            conn, filename=Path(filename).name or "upload.xlsx",
            sha256=hashlib.sha256(data).hexdigest(), size=len(data), tracker=adapter.tracker,
            flavour=parsed.flavour, report_date=parsed.report_date,
            report_time=parsed.report_time, info=parsed.info, preview=preview, rows=rows)


def _report_stamp(u: dict[str, Any]) -> str:
    return f"{u.get('report_date') or ''} {u.get('report_time') or ''}"


def _key(row: dict[str, Any]) -> str:
    return row.get("key") or row["cycle_key"]       # rows staged before 0.4.0 have no "key"


def preview(upload_id: int) -> dict[str, Any]:
    with connection() as conn:
        upload = uploads_repo.get(conn, upload_id)
        if upload is None:
            raise UploadError("This upload doesn't exist.")
        adapter = trackers.BY_TRACKER[upload["tracker"]]
        rows = uploads_repo.staged_rows(conn, upload_id) if upload["status"] == "staged" else []
        p = upload["preview"]
        p.setdefault("items", p.get("renewals", 0))
        known = clients_repo.by_keys(conn, list(p["clients"]))
        existing = adapter.stored(conn, [_key(r) for r in rows])
        in_export = adapter.in_export(conn, [c["id"] for c in known.values()])
        same_file = uploads_repo.committed_same_file(conn, upload["file_sha256"], upload_id)
        newer = [u for u in uploads_repo.committed_of_tracker(conn, upload["tracker"])
                 if _report_stamp(u) > _report_stamp(upload)
                 and set(u["preview"].get("clients", {})) & set(p["clients"])]
        waiting = [u for u in uploads_repo.staged(conn) if u["id"] != upload_id]
        by_client = _by_client(rows)
        kept = {key: adapter.keep(conn, known[key]["id"] if key in known else None,
                                  by_client.get(key, []))
                for key in p["clients"]}
        leaving = {}
        for key, c in known.items():
            gone = in_export.get(c["id"], set()) - {_key(r) for r in by_client.get(key, [])}
            leaving[key] = len(gone - adapter.not_news(conn, upload, gone))

    per_client: dict[str, dict[str, Any]] = {}
    for key, name in p["clients"].items():
        c = known.get(key)
        per_client[key] = {"key": key, "name": name, "known": c is not None,
                           "is_mine": None if c is None else c["is_mine"],
                           "items": 0, "new": 0, "changed": 0, "unchanged": 0, "flagged": 0,
                           "leaving": leaving.get(key, 0),
                           "skipped": len(by_client.get(key, [])) - len(kept[key])}
    ctx = adapter.context(rows)
    for key, client_rows in kept.items():
        pc = per_client[key]
        for r in client_rows:
            pc["items"] += 1
            pc["flagged"] += int(bool(r.get("flagged") or r.get("id_missing")))
            outcome = adapter.outcome(r, existing.get(_key(r)), ctx)
            pc["changed" if outcome == "returned" else outcome] += 1

    if upload["flavour"] == "client":      # a single-client export: surely theirs
        for pc in per_client.values():
            if pc["is_mine"] is None:
                pc["is_mine"] = 1
    ordered = sorted(per_client.values(), key=lambda c: (-(c["is_mine"] or 0), c["name"].casefold()))
    return {
        "upload": upload, "adapter": adapter, "clients": ordered,
        "filters": {k: upload["info"].get(k) for k in adapter.export_filters if k in upload["info"]},
        "same_file": same_file, "newer": newer[0] if newer else None,
        "mine_count": sum(1 for c in ordered if c["is_mine"] == 1),
        "carries_overview": bool({"overview_all", "overview_client_ready"} & set(ctx)),
        "waiting": waiting,
        "skipped": sum(c["skipped"] for c in ordered if c["is_mine"] != 0),
        "renewals_waiting": any(u["tracker"] == "renewal_tracker" for u in waiting),
    }


def _by_client(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        out.setdefault(r["client_key"], []).append(r)
    return out


def commit(upload_id: int, mine_keys: set[str], allow_older: bool = False) -> dict[str, Any]:
    view = preview(upload_id)
    upload, adapter = view["upload"], view["adapter"]
    if upload["status"] != "staged":
        raise UploadError("This upload was already committed or discarded.")
    if view["newer"] and not allow_older:
        raise UploadError("A newer export of these clients is already loaded. Tick "
                          "“load it anyway” if you really want this older one.")
    with connection() as conn:
        rows = uploads_repo.staged_rows(conn, upload_id)
        stored = adapter.stored(conn, [_key(r) for r in rows])
        ctx = adapter.context(rows)
        by_client = _by_client(rows)
        summary = {"new": 0, "changed": 0, "unchanged": 0, "returned": 0, "left_export": 0,
                   "skipped": 0, "clients_loaded": [], "clients_ignored": [], "tracker": adapter.tracker}
        for c in view["clients"]:
            key, mine = c["key"], c["key"] in mine_keys
            client_rows = by_client.get(key, [])
            bm_client_id = next(((r.get("ids") or {}).get("bm_client_id") for r in client_rows
                                 if (r.get("ids") or {}).get("bm_client_id")), None)
            client_id = clients_repo.upsert(conn, key, c["name"], bm_client_id, mine)
            if not mine:
                summary["clients_ignored"].append(c["name"])
                continue
            summary["clients_loaded"].append(c["name"])
            kept = adapter.keep(conn, client_id, client_rows)
            summary["skipped"] += len(client_rows) - len(kept)
            for r in kept:
                e = stored.get(_key(r))
                outcome = adapter.outcome(r, e, ctx)
                adapter.save(conn, r, e, client_id, upload_id, ctx, outcome)
                summary[outcome] += 1
            gone = adapter.in_export(conn, [client_id])[client_id] - {_key(r) for r in client_rows}
            gone -= adapter.not_news(conn, upload, gone)
            adapter.mark_left(conn, sorted(gone), upload_id)
            summary["left_export"] += len(gone)
            adapter.after_client(conn, client_id, kept, ctx, upload)
        uploads_repo.mark_committed(conn, upload_id, summary)

    s = settings_mod.load()
    if s is not None:
        backup_service.make_backup(s.db_path, Path(s.backup_dir), s.backups_keep)
    return summary


def discard(upload_id: int) -> None:
    with connection() as conn:
        upload = uploads_repo.get(conn, upload_id)
        if upload is None or upload["status"] != "staged":
            raise UploadError("Only a staged upload can be discarded.")
        uploads_repo.mark_discarded(conn, upload_id)


def recent_uploads(limit: int = 50) -> list[dict[str, Any]]:
    with connection() as conn:
        return uploads_repo.recent(conn, limit)


def waiting_uploads() -> list[dict[str, Any]]:
    """Staged uploads still waiting for commit or discard, oldest first."""
    with connection() as conn:
        return uploads_repo.staged(conn)


def overview() -> dict[str, Any]:
    """What Home and the Uploads page show about the loaded data."""
    with connection() as conn:
        totals = renewals_repo.totals(conn)
        mine = clients_repo.mine_summary(conn)
        last = uploads_repo.last_committed(conn)
    return {"totals": totals, "mine": mine, "last_upload": last}
