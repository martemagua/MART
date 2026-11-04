"""Uploading a tracker: stage → preview → commit (or discard).

* **Stage** reads the file once, stores its parsed rows and the upload's
  facts, and keeps NOTHING else: the .xlsx itself is not saved.
* **Preview** is computed live against the database, so it is always right
  even if another upload was committed in between. It is per client, because
  the commit is: only the clients ticked as "mine" are loaded.
* **Commit** runs in one transaction. Renewals of "my" clients are added or
  updated; a renewal of such a client that is NOT in the file is marked "no
  longer in the export" and kept, never deleted. Only clients present in the
  file are affected, so a single-client export never touches the others.
  Then a backup is made.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from mart import settings as settings_mod
from mart.ingestion import renewal_tracker as rt
from mart.ingestion.specs import renewal_tracker as spec
from mart.repository import clients_repo, renewals_repo, uploads_repo
from mart.repository.db import connection
from mart.services import backup_service


class UploadError(ValueError):
    """Shown to the user as is."""


def stage(filename: str, data: bytes) -> int:
    if not data:
        raise UploadError("The file is empty.")
    try:
        parsed = rt.parse(data)
    except rt.NotThisTracker as exc:
        raise UploadError(str(exc)) from exc
    if not parsed.renewals:
        raise UploadError("No renewals found in this export.")
    clients: dict[str, str] = {}
    for r in parsed.renewals:
        clients.setdefault(r.client_key, r.client_name)
    preview = {
        "clients": clients,
        "sheets_read": parsed.sheets_read,
        "sheets_missing": parsed.sheets_missing,
        "renewals": len(parsed.renewals),
        "skipped_no_client": parsed.skipped_no_client,
        "duplicates_merged": parsed.duplicates_merged,
        "no_id": parsed.no_id_count,
        "unmatched_detail_rows": parsed.unmatched_detail_rows,
        "title": parsed.title,
    }
    rows = []
    for r in parsed.renewals:
        d = asdict(r)
        d["content_hash"] = r.content_hash
        rows.append((r.cycle_key, r.client_key, d))
    with connection() as conn:
        return uploads_repo.create_staged(
            conn, filename=Path(filename).name or "upload.xlsx",
            sha256=hashlib.sha256(data).hexdigest(), size=len(data), tracker=spec.TRACKER,
            flavour=parsed.flavour, report_date=parsed.report_date,
            report_time=parsed.report_time, info=parsed.info, preview=preview, rows=rows)


def _report_stamp(u: dict[str, Any]) -> str:
    return f"{u.get('report_date') or ''} {u.get('report_time') or ''}"


def _outcome(row: dict[str, Any], stored: dict[str, Any] | None, carried: tuple[str, ...]) -> str:
    """new | returned (back in the export) | changed | unchanged."""
    if stored is None:
        return "new"
    if not stored["in_latest_export"]:
        return "returned"
    if stored["content_hash"] != row["content_hash"] or rt.text_changed(row, stored["fields"], carried):
        return "changed"
    return "unchanged"


def preview(upload_id: int) -> dict[str, Any]:
    with connection() as conn:
        upload = uploads_repo.get(conn, upload_id)
        if upload is None:
            raise UploadError("This upload doesn't exist.")
        rows = uploads_repo.staged_rows(conn, upload_id) if upload["status"] == "staged" else []
        p = upload["preview"]
        known = clients_repo.by_keys(conn, list(p["clients"]))
        existing = renewals_repo.stored_by_key(conn, [r["cycle_key"] for r in rows])
        in_export = renewals_repo.in_export_for_clients(conn, [c["id"] for c in known.values()])
        same_file = uploads_repo.committed_same_file(conn, upload["file_sha256"], upload_id)
        newer = [u for u in uploads_repo.committed_of_tracker(conn, upload["tracker"])
                 if _report_stamp(u) > _report_stamp(upload)
                 and set(u["preview"].get("clients", {})) & set(p["clients"])]

    per_client: dict[str, dict[str, Any]] = {}
    for key, name in p["clients"].items():
        c = known.get(key)
        per_client[key] = {
            "key": key, "name": name, "known": c is not None,
            "is_mine": None if c is None else c["is_mine"],
            "renewals": 0, "new": 0, "changed": 0, "unchanged": 0, "no_id": 0,
            "leaving": 0,
        }
    carried = rt.carried_streams(rows)
    seen: dict[str, set[str]] = {k: set() for k in per_client}
    for r in rows:
        pc = per_client[r["client_key"]]
        pc["renewals"] += 1
        pc["no_id"] += int(bool(r.get("id_missing")))
        seen[r["client_key"]].add(r["cycle_key"])
        outcome = _outcome(r, existing.get(r["cycle_key"]), carried)
        pc["changed" if outcome == "returned" else outcome] += 1
    for key, c in known.items():
        per_client[key]["leaving"] = len(in_export.get(c["id"], set()) - seen[key])

    if upload["flavour"] == rt.CLIENT:      # a single-client export: surely theirs
        for pc in per_client.values():
            if pc["is_mine"] is None:
                pc["is_mine"] = 1
    ordered = sorted(per_client.values(),
                     key=lambda c: (-(c["is_mine"] or 0), c["name"].casefold()))
    return {
        "upload": upload,
        "clients": ordered,
        "filters": {k: upload["info"].get(k) for k in spec.EXPORT_FILTERS if k in upload["info"]},
        "same_file": same_file,
        "newer": newer[0] if newer else None,
        "mine_count": sum(1 for c in ordered if c["is_mine"] == 1),
    }


def commit(upload_id: int, mine_keys: set[str], allow_older: bool = False) -> dict[str, Any]:
    view = preview(upload_id)
    upload = view["upload"]
    if upload["status"] != "staged":
        raise UploadError("This upload was already committed or discarded.")
    if view["newer"] and not allow_older:
        raise UploadError("A newer export of these clients is already loaded. Tick "
                          "“load it anyway” if you really want this older one.")
    with connection() as conn:
        rows = uploads_repo.staged_rows(conn, upload_id)
        stored = renewals_repo.stored_by_key(conn, [r["cycle_key"] for r in rows])
        carried = rt.carried_streams(rows)
        by_client: dict[str, list[dict[str, Any]]] = {}
        for r in rows:
            by_client.setdefault(r["client_key"], []).append(r)
        summary = {"new": 0, "changed": 0, "unchanged": 0, "returned": 0, "left_export": 0,
                   "clients_loaded": [], "clients_ignored": []}
        for c in view["clients"]:
            key, mine = c["key"], c["key"] in mine_keys
            client_rows = by_client.get(key, [])
            bm_client_id = next((r["ids"].get("bm_client_id") for r in client_rows
                                 if r["ids"].get("bm_client_id")), None)
            client_id = clients_repo.upsert(conn, key, c["name"], bm_client_id, mine)
            if not mine:
                summary["clients_ignored"].append(c["name"])
                continue
            summary["clients_loaded"].append(c["name"])
            for r in client_rows:
                e = stored.get(r["cycle_key"])
                outcome = _outcome(r, e, carried)
                if e is not None:
                    rt.keep_streams_not_carried(r, e["fields"], e["bm"], carried)
                renewals_repo.save(conn, r, client_id, upload_id,
                                   existing_id=e["id"] if e else None,
                                   touched=outcome != "unchanged")
                summary[outcome] += 1
            gone = renewals_repo.in_export_for_clients(conn, [client_id])[client_id] \
                - {r["cycle_key"] for r in client_rows}
            renewals_repo.mark_left_export(conn, sorted(gone))
            summary["left_export"] += len(gone)
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


def overview() -> dict[str, Any]:
    """What Home and the Uploads page show about the loaded data."""
    with connection() as conn:
        totals = renewals_repo.totals(conn)
        mine = clients_repo.mine_summary(conn)
        last = uploads_repo.last_committed(conn)
    return {"totals": totals, "mine": mine, "last_upload": last}
