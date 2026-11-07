"""Notes and to-dos: what Martin writes, on a renewal or a bundle.

USER data: uploads never touch it. Everything hangs on a target (scope, ref):

* ``renewal`` - ref = the renewal's MART id (renewals are never deleted)
* ``bundle``  - ref = "<client id>|<bundle key>": a default bundle
  ("<country>|<renewal date>") or a custom one ("custom|<id>"), see
  services/bundles.py. A note on a bundle is about all its renewals, like one
  mail covering several policies.
* ``client``  - ref = the client's MART id: about the client as a whole.

A renewal also shows the notes of the policy's EARLIER cycles (same stable
policy id), read-only: the history is built from the renewals MART keeps.

Only targets of "my" clients can be written on.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote

from mart.repository import bundles_repo, clients_repo, notes_repo, renewals_repo, topics_repo
from mart.repository.db import connection
from mart.services import bundles as bx
from mart.services import repeats
from mart.services import todo_details as td

SCOPES = ("renewal", "bundle", "client")
NOTE_MAX = 20_000
TITLE_MAX = 300
DONE_SHOWN_DAYS = 30


# one error type for notes and to-dos, shown to the user as is
Invalid = td.Invalid


# -- targets ----------------------------------------------------------------------------
def bundle_ref(client_id: int, key: str) -> str:
    """A bundle target's ref: the client and the bundle key (services/bundles)."""
    return f"{client_id}|{key}"


def _split_bundle(ref: str) -> tuple[int, str]:
    """(client id, bundle key) of a bundle ref."""
    try:
        cid, key = ref.split("|", 1)
        if "|" not in key:
            raise ValueError(ref)
        return int(cid), key
    except ValueError as exc:
        raise Invalid("This bundle doesn't exist.") from exc


def _target(conn, scope: str, ref: str) -> dict[str, Any]:
    """The target's client and how to name and reach it; Invalid if it isn't
    one of my renewals / bundles."""
    if scope == "renewal":
        r = renewals_repo.get(conn, int(ref)) if ref.isdigit() else None
        client = clients_repo.get(conn, r["client_id"]) if r else None
        if not r or not client or client["is_mine"] != 1:
            raise Invalid("This renewal doesn't exist (or isn't one of your clients').")
        return {"scope": scope, "ref": ref, "client_id": r["client_id"]}
    if scope == "client":
        client = clients_repo.get(conn, int(ref)) if ref.isdigit() else None
        if not client or client["is_mine"] != 1:
            raise Invalid("This client doesn't exist (or isn't one of yours).")
        return {"scope": scope, "ref": ref, "client_id": int(ref)}
    if scope == "bundle":
        cid, _ = _split_bundle(ref)
        client = clients_repo.get(conn, cid)
        if not client or client["is_mine"] != 1:
            raise Invalid("This bundle doesn't exist (or isn't one of your clients').")
        return {"scope": scope, "ref": ref, "client_id": cid}
    raise Invalid("Notes and to-dos go on a renewal, a bundle or a client.")


def _describe(t: dict[str, Any], renewal_labels: dict[int, dict[str, Any]],
              customs: dict[int, dict[str, Any]]) -> dict[str, Any]:
    """Label + link for a note's / to-do's target (for lists across targets)."""
    if t["scope"] == "renewal":
        r = renewal_labels.get(int(t["ref"])) or {}
        return {"kind": "renewal", "country": r.get("country"), "renewal_date": r.get("renewal_date"),
                "name": r.get("policy_name") or "—",
                "url": f"/clients/{t['client_id']}/renewals/{t['ref']}"}
    if t["scope"] == "client":
        return {"kind": "client", "country": None, "renewal_date": None, "name": "client notes",
                "url": f"/clients/{t['client_id']}/notes"}
    cid, key = _split_bundle(t["ref"])
    url = f"/clients/{cid}?bundle={quote(key, safe='')}"
    custom_id = bx.custom_id(key)
    if custom_id is not None:
        c = customs.get(custom_id) or {}
        return {"kind": "bundle", "country": c.get("country"), "renewal_date": None,
                "name": f"bundle “{c.get('name', '?')}”", "url": url}
    country, rdate = key.split("|", 1)
    return {"kind": "bundle", "country": country, "renewal_date": rdate if rdate[:4].isdigit() else None,
            "name": "whole bundle", "url": url}


# -- reading ----------------------------------------------------------------------------
def _todos(conn, rows: list[dict[str, Any]], today: date) -> list[dict[str, Any]]:
    """To-dos with their due state and subtasks (one query for all of them)."""
    steps = notes_repo.steps_for(conn, [x["id"] for x in rows])
    return [td.with_steps({**x, **_due(x, today)}, steps[x["id"]]) for x in rows]


def _on(conn, scope: str, ref: str, today: date) -> dict[str, Any]:
    t = [(scope, ref)]
    return {"target": {"scope": scope, "ref": ref}, "notes": notes_repo.notes_for(conn, t),
            "todos": _todos(conn, notes_repo.todos_for(conn, t), today)}


def for_renewal(r: dict[str, Any], bundle: dict[str, Any] | None = None,
                today: date | None = None) -> dict[str, Any]:
    """The renewal's own notes / to-dos, its bundle's (under "bundle"), and the
    notes of the policy's other renewal cycles (under "earlier")."""
    today = today or date.today()
    with connection() as conn:
        out = {**_on(conn, "renewal", str(r["id"]), today), "earlier": _earlier_notes(conn, r)}
        if bundle:
            out["bundle"] = _on(conn, "bundle", bundle_ref(r["client_id"], bundle["key"]), today)
        return out


def _earlier_notes(conn, r: dict[str, Any]) -> list[dict[str, Any]]:
    """Notes on the same policy's other cycles, newest cycle first, each with
    its cycle's renewal date and link. Only renewals with BM+'s stable policy
    id can be matched across cycles."""
    if not r.get("expiring_policy_id"):
        return []
    cycles = {c["id"]: c for c in renewals_repo.cycles_of(conn, r["client_id"], r["expiring_policy_id"])
              if c["id"] != r["id"]}
    notes = notes_repo.notes_for(conn, [("renewal", str(i)) for i in cycles])
    out = [{**n, "cycle": cycles[int(n["ref"])],
            "url": f"/clients/{r['client_id']}/renewals/{n['ref']}"} for n in notes]
    return sorted(out, key=lambda n: (n["cycle"]["renewal_date"] or "", n["created_at"]), reverse=True)


def for_client(client_id: int, today: date | None = None) -> dict[str, Any]:
    with connection() as conn:
        _target(conn, "client", str(client_id))
        return _on(conn, "client", str(client_id), today or date.today())


def client_totals() -> dict[int, dict[str, int]]:
    """client id -> notes / open to-dos on the CLIENT itself (Clients list)."""
    with connection() as conn:
        return notes_repo.client_target_counts(conn)


def for_bundle(client_id: int, bundle: dict[str, Any], today: date | None = None) -> dict[str, Any]:
    with connection() as conn:
        return _on(conn, "bundle", bundle_ref(client_id, bundle["key"]), today or date.today())


def counts(client_id: int) -> dict[str, dict[str, int]]:
    """"<scope>:<ref>" -> {"notes", "todos" (open)} for one client's targets."""
    with connection() as conn:
        return {f"{s}:{r}": c for (s, r), c in notes_repo.counts_by_target(conn, client_id).items()}


def todo_list(show_done: bool = False, today: date | None = None) -> dict[str, Any]:
    """The To-dos page: every open to-do (urgent first, then by due date,
    undated last) and those done in the last DONE_SHOWN_DAYS (or all)."""
    today = today or date.today()
    # timezone.utc, not datetime.UTC: MART still starts on Python 3.10
    now = datetime.now(timezone.utc)  # noqa: UP017
    since = None if show_done else (now - timedelta(days=DONE_SHOWN_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    with connection() as conn:
        rows = _todos(conn, notes_repo.all_todos(conn, since), today)
        labels = renewals_repo.labels(conn, [int(t["ref"]) for t in rows if t["scope"] == "renewal"])
        customs = bundles_repo.all_custom(conn)
        topic_of_ = topics_repo.by_id(conn, {t["topic_id"] for t in rows if t.get("topic_id")})
    # a client to-do carries its topic (day 7): its name and colour as a chip
    items = [{**t, "target": _describe(t, labels, customs), "topic": topic_of_.get(t.get("topic_id"))}
             for t in rows]
    open_ = [t for t in items if not t["done_at"]]
    return {"open": open_, "done": [t for t in items if t["done_at"]], "show_done": show_done,
            "overdue": sum(1 for t in open_ if t["overdue"]),
            "this_week": sum(1 for t in open_ if t["days"] is not None and 0 <= t["days"] <= 7),
            "done_days": DONE_SHOWN_DAYS}


def _due(t: dict[str, Any], today: date) -> dict[str, Any]:
    if not t.get("due_date") or t.get("done_at"):
        return {"days": None, "overdue": False}
    days = (date.fromisoformat(t["due_date"]) - today).days
    return {"days": days, "overdue": days < 0}


# -- writing ----------------------------------------------------------------------------
def _clean_body(body: str | None) -> str:
    text = (body or "").replace("\r\n", "\n").strip()
    if not text:
        raise Invalid("A note needs some text.")
    if len(text) > NOTE_MAX:
        raise Invalid(f"A note can have at most {NOTE_MAX:,} characters.")
    return text


def _clean_title(title: str | None) -> str:
    text = " ".join((title or "").split())
    if not text:
        raise Invalid("A to-do needs a title.")
    if len(text) > TITLE_MAX:
        raise Invalid(f"A to-do title can have at most {TITLE_MAX} characters.")
    return text


def _clean_due(due: str | None) -> str | None:
    due = (due or "").strip()
    if not due:
        return None
    try:
        return date.fromisoformat(due).isoformat()
    except ValueError as exc:
        raise Invalid("The due date isn't a date.") from exc


def topic_of(conn, client_id: int, scope: str, topic_id: Any) -> int | None:
    """A client topic to put a note / to-do in (services/topics): only on the
    client itself, only one of THIS client's; empty = General."""
    if topic_id in (None, "", "general"):
        return None
    try:
        tid = int(topic_id)
    except (TypeError, ValueError) as exc:
        raise Invalid("That topic doesn't exist.") from exc
    topic = topics_repo.get(conn, tid)
    if scope != "client" or topic is None or topic["client_id"] != client_id:
        raise Invalid("That topic doesn't exist (topics are for the client's own notes and to-dos).")
    return tid


def add_note(scope: str, ref: str, body: str | None, topic_id: Any = None) -> int:
    with connection() as conn:
        t = _target(conn, scope, ref)
        return notes_repo.add_note(conn, t["scope"], t["ref"], t["client_id"], _clean_body(body),
                                   topic_of(conn, t["client_id"], t["scope"], topic_id))


def _own(conn, getter, item_id: int) -> dict[str, Any]:
    item = getter(conn, item_id)
    if item is None:
        raise Invalid("This was already deleted.")
    _target(conn, item["scope"], item["ref"])       # still one of my targets
    return item


def edit_note(note_id: int, body: str | None) -> None:
    with connection() as conn:
        _own(conn, notes_repo.get_note, note_id)
        notes_repo.update_note(conn, note_id, _clean_body(body))


def delete_note(note_id: int) -> None:
    with connection() as conn:
        _own(conn, notes_repo.get_note, note_id)
        notes_repo.delete_note(conn, note_id)


def add_todo(scope: str, ref: str, title: str | None, due: str | None, urgency: str | None = None,
             topic_id: Any = None, repeat: dict[str, Any] | None = None) -> int:
    """`repeat` = the form's repeat fields (unit, every, weekdays), see services/repeats."""
    due = _clean_due(due)
    spec = repeats.clean(*_repeat_args(repeat), due) if repeat else None
    with connection() as conn:
        t = _target(conn, scope, ref)
        tid = notes_repo.add_todo(conn, t["scope"], t["ref"], t["client_id"], _clean_title(title),
                                  due, td.urgency(urgency),
                                  topic_of(conn, t["client_id"], t["scope"], topic_id))
        if spec:
            notes_repo.set_repeat(conn, tid, spec)
        return tid


def _repeat_args(repeat: dict[str, Any]) -> tuple:
    return repeat.get("unit"), repeat.get("every"), repeat.get("weekdays")


def edit_todo(todo_id: int, title: str | None, due: str | None,
              details: dict[str, str | None] | None = None, repeat: dict[str, Any] | None = None) -> None:
    """Title and due date; with `details` (the edit form) also the M2 extras,
    with `repeat` its repeat (an empty unit = doesn't repeat any more)."""
    due = _clean_due(due)
    with connection() as conn:
        _own(conn, notes_repo.get_todo, todo_id)
        extras = td.clean(details) if details is not None else None
        spec = repeats.clean(*_repeat_args(repeat), due) if repeat is not None else None
        notes_repo.update_todo(conn, todo_id, _clean_title(title), due)
        if extras is not None:
            notes_repo.update_details(conn, todo_id, extras)
        if repeat is not None:
            notes_repo.set_repeat(conn, todo_id, spec)


def add_step(todo_id: int, title: str | None) -> int:
    with connection() as conn:
        _own(conn, notes_repo.get_todo, todo_id)
        return notes_repo.add_step(conn, todo_id, td.step_title(title))


def _own_step(conn, step_id: int) -> dict[str, Any]:
    step = notes_repo.get_step(conn, step_id)
    if step is None:
        raise Invalid("This subtask was already deleted.")
    _own(conn, notes_repo.get_todo, step["todo_id"])
    return step


def set_step_done(step_id: int, done: bool) -> int:
    """Returns the step's to-do id (for the page anchor)."""
    with connection() as conn:
        step = _own_step(conn, step_id)
        notes_repo.set_step_done(conn, step_id, done)
        return step["todo_id"]


def delete_step(step_id: int) -> int:
    with connection() as conn:
        step = _own_step(conn, step_id)
        notes_repo.delete_step(conn, step_id)
        return step["todo_id"]


def set_done(todo_id: int, done: bool, today: date | None = None) -> int | None:
    """Tick a to-do (or untick it). A repeating one, ticked for the first
    time, creates the next (services/repeats); returns its id. Unticking
    leaves the next one as it is."""
    with connection() as conn:
        todo = _own(conn, notes_repo.get_todo, todo_id)
        notes_repo.set_done(conn, todo_id, done)
        if done and todo.get("repeat_unit") and not todo.get("repeat_next_id"):
            nxt = repeats.next_due(todo, todo.get("due_date"), today)
            return notes_repo.add_next(conn, todo, nxt.isoformat())
    return None


def delete_todo(todo_id: int) -> None:
    with connection() as conn:
        _own(conn, notes_repo.get_todo, todo_id)
        notes_repo.delete_todo(conn, todo_id)
