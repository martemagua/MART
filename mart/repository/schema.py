"""Schema migrations: the single source of truth for the database layout.

`MIGRATIONS` is APPEND-ONLY. Each entry is (version, sql). `ensure_schema()`
applies every entry above the database's `PRAGMA user_version`, each in its
own transaction, and runs on every start. Never edit an applied migration;
add a new one.
"""

from __future__ import annotations

from pathlib import Path

from mart.repository.db import connect

MIGRATIONS: list[tuple[int, str]] = [
    (1, """
        -- Small key/value store for app state (e.g. "last seen" markers).
        CREATE TABLE user_state (
            key         TEXT PRIMARY KEY,
            value       TEXT,
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """),
    (2, """
        -- Clients. is_mine: NULL = not decided yet, 1 = mine, 0 = not mine
        -- (its renewals are ignored on every upload).
        CREATE TABLE clients (
            id            INTEGER PRIMARY KEY,
            name          TEXT NOT NULL,
            client_key    TEXT NOT NULL UNIQUE,
            bm_client_id  TEXT,
            is_mine       INTEGER,
            created_at    TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at    TEXT
        );

        -- The upload log: every file staged, committed or discarded.
        CREATE TABLE uploads (
            id            INTEGER PRIMARY KEY,
            filename      TEXT NOT NULL,
            file_sha256   TEXT NOT NULL,
            file_size     INTEGER,
            tracker       TEXT NOT NULL,
            flavour       TEXT,
            report_date   TEXT,
            report_time   TEXT,
            info_json     TEXT,          -- General Information label/values
            preview_json  TEXT,
            summary_json  TEXT,          -- what the commit did
            status        TEXT NOT NULL DEFAULT 'staged',   -- staged|committed|discarded
            staged_at     TEXT NOT NULL DEFAULT (datetime('now')),
            committed_at  TEXT,
            discarded_at  TEXT
        );

        -- The parsed rows of a staged upload, so a commit never re-reads the file.
        CREATE TABLE staging_rows (
            id          INTEGER PRIMARY KEY,
            upload_id   INTEGER NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
            cycle_key   TEXT NOT NULL,
            client_key  TEXT NOT NULL,
            data_json   TEXT NOT NULL
        );
        CREATE INDEX ix_staging_upload ON staging_rows(upload_id);

        -- One renewal cycle. MART-owned: never deleted by an upload; a renewal
        -- that leaves the export (e.g. completed in BM+) keeps its row.
        CREATE TABLE renewals (
            id                  INTEGER PRIMARY KEY,
            cycle_key           TEXT NOT NULL UNIQUE,
            cycle_id            TEXT,      -- BM+ per-cycle id (= Task Tracker "Policy ID")
            expiring_policy_id  TEXT,      -- stable across cycles
            bm_renewal_id       TEXT,
            client_id           INTEGER NOT NULL REFERENCES clients(id),
            country             TEXT,
            entity              TEXT,
            division            TEXT,
            region              TEXT,
            policy_name         TEXT,
            lines_of_coverage   TEXT,
            product_groups      TEXT,      -- JSON list
            insurer             TEXT,
            start_date          TEXT,
            end_date            TEXT,
            non_expiring        INTEGER NOT NULL DEFAULT 0,
            renewal_date        TEXT,      -- Annual Renewal/Review Date
            kickoff_date        TEXT,
            workflow_status     TEXT,
            upcoming_strategy   TEXT,
            id_missing          INTEGER NOT NULL DEFAULT 0,
            fields_json         TEXT NOT NULL,   -- every cleaned field
            bm_json             TEXT NOT NULL,   -- every Overview cell as exported
            details_json        TEXT NOT NULL DEFAULT '{}',  -- Strategy/Proposals/Savings rows
            content_hash        TEXT NOT NULL,
            first_upload_id     INTEGER REFERENCES uploads(id),
            last_upload_id      INTEGER REFERENCES uploads(id),
            in_latest_export    INTEGER NOT NULL DEFAULT 1,
            left_export_at      TEXT,
            created_at          TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT
        );
        CREATE INDEX ix_renewals_client ON renewals(client_id);
        CREATE INDEX ix_renewals_expiring ON renewals(expiring_policy_id);
    """),
    (3, """
        -- The report date of the last export that brought this client's
        -- renewal overview (in practice a single-client export: the
        -- cross-client one leaves the overview empty).
        ALTER TABLE clients ADD COLUMN overview_as_of TEXT;
        ALTER TABLE clients ADD COLUMN overview_upload_id INTEGER REFERENCES uploads(id);

        -- BM+ tasks (Task Tracker). Like renewals: never deleted by an upload.
        CREATE TABLE tasks (
            id                  INTEGER PRIMARY KEY,
            task_key            TEXT NOT NULL UNIQUE,   -- BM+ task id
            client_id           INTEGER NOT NULL REFERENCES clients(id),
            policy_id           TEXT,      -- per-cycle id = renewals.cycle_id
            expiring_policy_id  TEXT,      -- stable id = renewals.expiring_policy_id
            bm_renewal_id       TEXT,
            task_name           TEXT,
            task_category       TEXT,
            task_status         TEXT,
            country             TEXT,
            policy_name         TEXT,
            review_date         TEXT,      -- Policy Renewal/Review Date
            assignee            TEXT,
            due_date            TEXT,
            completed_date      TEXT,
            fields_json         TEXT NOT NULL,
            bm_json             TEXT NOT NULL,
            content_hash        TEXT NOT NULL,
            first_upload_id     INTEGER REFERENCES uploads(id),
            last_upload_id      INTEGER REFERENCES uploads(id),
            in_latest_export    INTEGER NOT NULL DEFAULT 1,
            left_export_at      TEXT,
            created_at          TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at          TEXT
        );
        CREATE INDEX ix_tasks_client ON tasks(client_id);
        CREATE INDEX ix_tasks_policy ON tasks(policy_id);
        CREATE INDEX ix_tasks_expiring ON tasks(expiring_policy_id, review_date);
    """),
    (4, """
        -- What Martin writes (USER data: uploads never touch it). Both hang on
        -- a target, the (scope, ref) convention:
        --   renewal  ref = renewals.id (MART's own id; renewals are never deleted)
        --   bundle   ref = "<client id>|<country>|<renewal date>"
        -- client_id is the target's client, for per-client lists.
        CREATE TABLE notes (
            id          INTEGER PRIMARY KEY,
            scope       TEXT NOT NULL,
            ref         TEXT NOT NULL,
            client_id   INTEGER NOT NULL REFERENCES clients(id),
            body        TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT
        );
        CREATE INDEX ix_notes_target ON notes(scope, ref);
        CREATE INDEX ix_notes_client ON notes(client_id);

        CREATE TABLE todos (
            id          INTEGER PRIMARY KEY,
            scope       TEXT NOT NULL,
            ref         TEXT NOT NULL,
            client_id   INTEGER NOT NULL REFERENCES clients(id),
            title       TEXT NOT NULL,
            due_date    TEXT,               -- ISO date; NULL = no date
            done_at     TEXT,               -- UTC timestamp; NULL = open
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT
        );
        CREATE INDEX ix_todos_target ON todos(scope, ref);
        CREATE INDEX ix_todos_open ON todos(done_at, due_date);
    """),
    (5, """
        -- Custom bundles (USER data): Martin moves renewals out of their
        -- default bundle (country + renewal date) into a named bundle of the
        -- same country, e.g. a policy BM+ split into several renewals, or
        -- the product groups one broker handles.
        CREATE TABLE custom_bundles (
            id          INTEGER PRIMARY KEY,
            client_id   INTEGER NOT NULL REFERENCES clients(id),
            country     TEXT NOT NULL,
            name        TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT
        );
        CREATE INDEX ix_custom_bundles_client ON custom_bundles(client_id);
        -- A name Martin gives a DEFAULT bundle (custom bundles carry their own).
        CREATE TABLE bundle_names (
            client_id   INTEGER NOT NULL REFERENCES clients(id),
            bundle_key  TEXT NOT NULL,          -- "<country>|<renewal date>"
            name        TEXT NOT NULL,
            PRIMARY KEY (client_id, bundle_key)
        );
        -- Which renewal sits in which custom bundle (none = its default one).
        CREATE TABLE renewal_bundles (
            renewal_id  INTEGER PRIMARY KEY REFERENCES renewals(id),
            bundle_id   INTEGER NOT NULL REFERENCES custom_bundles(id),
            moved_at    TEXT NOT NULL DEFAULT (datetime('now'))
        );

        -- What each upload changed (append-only). BM+ doesn't say WHEN
        -- something changed, so an entry is dated by the upload (its export's
        -- report date): "first seen in the export of …".
        CREATE TABLE changes (
            id          INTEGER PRIMARY KEY,
            item_kind   TEXT NOT NULL,          -- renewal | task
            item_id     INTEGER NOT NULL,       -- renewals.id / tasks.id
            upload_id   INTEGER NOT NULL REFERENCES uploads(id),
            field       TEXT NOT NULL,          -- a field name, or an event: _seen _left _back
            old_value   TEXT,
            new_value   TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX ix_changes_item ON changes(item_kind, item_id);
    """),
    (6, """
        -- An upload's parsed rows are only needed until it is committed or
        -- discarded; committed ones were kept by mistake and made the file
        -- grow with every upload (0.7.0). Clear them; MART compacts the file
        -- at the next start.
        DELETE FROM staging_rows
        WHERE upload_id IN (SELECT id FROM uploads WHERE status <> 'staged');
    """),
    (7, """
        -- Richer to-dos (M2 day 2, Martin 04.11.2026): a description, an
        -- urgency, a status while open (done stays done_at), who it is
        -- waiting on and since when, and subtasks. USER data, like todos.
        ALTER TABLE todos ADD COLUMN description   TEXT;
        ALTER TABLE todos ADD COLUMN urgency       TEXT NOT NULL DEFAULT 'normal';  -- urgent | normal | low
        ALTER TABLE todos ADD COLUMN status        TEXT NOT NULL DEFAULT 'open';  -- open|in_progress|waiting
        ALTER TABLE todos ADD COLUMN waiting_kind  TEXT;   -- broker | insurer | client | colleague | other
        ALTER TABLE todos ADD COLUMN waiting_on    TEXT;   -- a name, e.g. "Broker A"
        ALTER TABLE todos ADD COLUMN waiting_since TEXT;   -- ISO date
        CREATE TABLE todo_steps (
            id         INTEGER PRIMARY KEY,
            todo_id    INTEGER NOT NULL REFERENCES todos(id) ON DELETE CASCADE,
            title      TEXT NOT NULL,
            position   INTEGER NOT NULL,
            done_at    TEXT,               -- UTC timestamp; NULL = open
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX ix_todo_steps_todo ON todo_steps(todo_id, position);
    """),
    (8, """
        -- Broker deadlines (M2 day 3, Martin 04.11.2026): when Martin expects
        -- an update on a BUNDLE's renewals. USER data, apart from to-dos. One
        -- open row per bundle; confirmed / dropped / replaced ones are its
        -- history. A deadline BM+ suggests (expected-terms date) is only
        -- stored once Martin acts on it (source 'bm').
        CREATE TABLE deadlines (
            id            INTEGER PRIMARY KEY,
            client_id     INTEGER NOT NULL REFERENCES clients(id),
            bundle_key    TEXT NOT NULL,      -- services/bundles: <country>|<date> or custom|<id>
            expected_date TEXT NOT NULL,      -- ISO date
            promised_by   TEXT,
            note          TEXT,
            source        TEXT NOT NULL DEFAULT 'you',   -- you | bm
            status        TEXT NOT NULL DEFAULT 'open',  -- open | confirmed | dropped | replaced
            created_at    TEXT NOT NULL DEFAULT (datetime('now')),
            closed_at     TEXT
        );
        CREATE INDEX ix_deadlines_bundle ON deadlines(client_id, bundle_key, status);
    """),
    (9, """
        -- M3 day 1: the ACTUAL state of a renewal beside BM+'s (USER data,
        -- never touched by uploads). Append-only: the newest row per
        -- (renewal, field) is the current value, a NULL value clears it, and
        -- the older rows are its history.
        CREATE TABLE renewal_actuals (
            id          INTEGER PRIMARY KEY,
            renewal_id  INTEGER NOT NULL REFERENCES renewals(id),
            field       TEXT NOT NULL,     -- strategy | completed
            value       TEXT,              -- the strategy / ISO date completed; NULL = cleared
            bm_value    TEXT,              -- BM+'s value when this was set
            reason      TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX ix_actuals_renewal ON renewal_actuals(renewal_id, field, id);
    """),
    (10, """
        -- M3 day 2: the proposals Martin receives, recorded by him to compare
        -- them (USER data; BM+'s Proposals sheet stays apart, for reference).
        CREATE TABLE proposals (
            id           INTEGER PRIMARY KEY,
            renewal_id   INTEGER NOT NULL REFERENCES renewals(id),
            insurer      TEXT NOT NULL,
            round        TEXT NOT NULL DEFAULT 'first',        -- first | revised | final
            received_on  TEXT,                                 -- ISO date
            premium      REAL,                                 -- annual; NULL = not given
            currency     TEXT,                                 -- e.g. EUR
            rate_change  REAL,                                 -- percent, + = increase
            plan_design  TEXT NOT NULL DEFAULT 'as_expiring',  -- as_expiring | changed
            note         TEXT,
            chosen       INTEGER NOT NULL DEFAULT 0,           -- at most one per renewal
            created_at   TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX ix_proposals_renewal ON proposals(renewal_id);
    """),
    (11, """
        -- M3: the Insurer Capability Database ("All Networks"): a GLOBAL
        -- reference list (not per client), replaced as a whole by each upload.
        CREATE TABLE insurer_capabilities (
            id             INTEGER PRIMARY KEY,
            cap_key        TEXT NOT NULL UNIQUE,  -- network|country key|insurer|line
            network        TEXT NOT NULL,
            region         TEXT,
            country        TEXT NOT NULL,
            country_key    TEXT NOT NULL,         -- ISO code, else name:<normalised>
            insurer        TEXT,                  -- NULL = no partner of this network there
            line           TEXT NOT NULL,
            fully_insured  INTEGER, fully_insured_text TEXT,   -- 1 / 0 / NULL + an unusual answer
            pool           INTEGER, pool_text TEXT,
            pool_share     REAL,    pool_share_text TEXT,      -- fraction 0-1, or the text given
            gip            INTEGER, gip_text TEXT,
            gip_share      REAL,    gip_share_text TEXT,
            captive        INTEGER, captive_text TEXT,
            captive_share  REAL,    captive_share_text TEXT,
            comments       TEXT,
            content_hash   TEXT NOT NULL,
            upload_id      INTEGER REFERENCES uploads(id)
        );
        CREATE INDEX ix_capabilities_country ON insurer_capabilities(country_key, insurer);
    """),
    (12, """
        -- M3 (Martin, 06.11.2026): a proposal = ONE insurer + variant (plan
        -- design as expiring / changed, an optional label) holding its quotes
        -- (first, revised…, final), so a negotiation is one entry. The quote
        -- columns of `proposals` (round … note) are no longer used.
        CREATE TABLE proposal_quotes (
            id           INTEGER PRIMARY KEY,
            proposal_id  INTEGER NOT NULL REFERENCES proposals(id),
            round        TEXT NOT NULL DEFAULT 'first',   -- first | revised | final
            received_on  TEXT,                            -- ISO date
            premium      REAL,
            currency     TEXT,
            rate_change  REAL,
            note         TEXT,
            created_at   TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX ix_quotes_proposal ON proposal_quotes(proposal_id);
        ALTER TABLE proposals ADD COLUMN label TEXT;
        -- every quote recorded so far joins the first proposal of the same
        -- renewal, insurer and plan design
        INSERT INTO proposal_quotes (proposal_id, round, received_on, premium, currency, rate_change, note,
                                     created_at, updated_at)
            SELECT (SELECT MIN(p2.id) FROM proposals p2
                     WHERE p2.renewal_id = p.renewal_id AND lower(trim(p2.insurer)) = lower(trim(p.insurer))
                       AND p2.plan_design = p.plan_design),
                   p.round, p.received_on, p.premium, p.currency, p.rate_change, p.note,
                   p.created_at, p.updated_at
              FROM proposals p ORDER BY p.id;
        UPDATE proposals SET chosen = 1 WHERE id IN (
            SELECT MIN(id) FROM proposals GROUP BY renewal_id, lower(trim(insurer)), plan_design
            HAVING MAX(chosen) = 1);
        DELETE FROM proposals WHERE id NOT IN (
            SELECT MIN(id) FROM proposals GROUP BY renewal_id, lower(trim(insurer)), plan_design);
    """),
    (13, """
        -- M3 day 4: plan design changes per renewal (USER data): what changes,
        -- and where it stands: suggested -> agreed -> implemented, or dropped,
        -- with the date it got there. `source` = 'bm' when it was taken over
        -- from BM+'s Renewal Strategy sheet.
        CREATE TABLE plan_changes (
            id              INTEGER PRIMARY KEY,
            renewal_id      INTEGER NOT NULL REFERENCES renewals(id),
            title           TEXT NOT NULL,
            detail          TEXT,
            status          TEXT NOT NULL DEFAULT 'suggested',  -- suggested | agreed | implemented | dropped
            suggested_on    TEXT,
            agreed_on       TEXT,
            implemented_on  TEXT,
            dropped_on      TEXT,
            source          TEXT NOT NULL DEFAULT 'you',        -- you | bm
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX ix_plan_changes_renewal ON plan_changes(renewal_id);
    """),
    (14, """
        -- M3 day 5: each client's own regions (USER data; Martin 05.11.2026):
        -- clients split the world differently, so a country's region is set
        -- per client. Only Martin's overrides are stored; without one, the
        -- country goes by BM+'s Region column.
        CREATE TABLE client_regions (
            client_id   INTEGER NOT NULL REFERENCES clients(id),
            country     TEXT NOT NULL,          -- as BM+ writes it
            region      TEXT NOT NULL,
            updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (client_id, country)
        );
    """),
    (15, """
        -- M3 day 6: the board. Martin's stage of a BUNDLE (a card is a bundle,
        -- QUESTIONS C2), beside the one MART reads from BM+'s tasks. USER data,
        -- append-only: the newest row per (client, bundle) is the stage; a NULL
        -- stage = the card follows BM+ again. `bm_stage` = BM+'s stage when he
        -- moved it (PLANNING §1d), so MART can tell when BM+ catches up.
        CREATE TABLE bundle_stages (
            id          INTEGER PRIMARY KEY,
            client_id   INTEGER NOT NULL REFERENCES clients(id),
            bundle_key  TEXT NOT NULL,          -- services/bundles: <country>|<date> or custom|<id>
            stage       TEXT,                   -- services/board.COLUMNS; NULL = follow BM+
            bm_stage    TEXT,
            reason      TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX ix_bundle_stages_client ON bundle_stages(client_id, bundle_key);
    """),
    (16, """
        -- M3 day 7: client topics (Martin 05.11.2026, PLANNING §5b, QUESTIONS
        -- M3a/M3c): named, coloured streams inside ONE client for its own notes
        -- and to-dos. USER data. A client note / to-do sits in one topic;
        -- topic_id NULL = "General" (every existing one starts there).
        CREATE TABLE client_topics (
            id          INTEGER PRIMARY KEY,
            client_id   INTEGER NOT NULL REFERENCES clients(id),
            name        TEXT NOT NULL,
            color       TEXT NOT NULL,          -- services/topics.COLORS
            country     TEXT,                   -- optional label (a flag), as BM+ writes it
            status      TEXT NOT NULL DEFAULT 'active',   -- active | on_hold | done
            position    INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT
        );
        CREATE INDEX ix_client_topics_client ON client_topics(client_id, position);
        ALTER TABLE notes ADD COLUMN topic_id INTEGER REFERENCES client_topics(id);
        ALTER TABLE todos ADD COLUMN topic_id INTEGER REFERENCES client_topics(id);
        -- a pinned note = a key fact, at the top of its topic (NULL = not pinned)
        ALTER TABLE notes ADD COLUMN pinned_at TEXT;
    """),
    (17, """
        -- M3 day 8: repeating to-dos (Martin 05.11.2026, QUESTIONS M3b): every
        -- N days / N weeks (on chosen weekdays) / N months. USER data. Ticking
        -- one done creates the next (services/repeats); `repeat_next_id` = the
        -- one it created, so ticking it again never makes a second.
        ALTER TABLE todos ADD COLUMN repeat_unit     TEXT;      -- day | week | month; NULL = doesn't repeat
        ALTER TABLE todos ADD COLUMN repeat_every    INTEGER;
        ALTER TABLE todos ADD COLUMN repeat_weekdays TEXT;      -- "0,3" = Mon, Thu (weeks only)
        ALTER TABLE todos ADD COLUMN repeat_day      INTEGER;   -- day of the month (months only)
        ALTER TABLE todos ADD COLUMN repeat_next_id  INTEGER REFERENCES todos(id);
    """),
]

LATEST_VERSION = MIGRATIONS[-1][0]


def current_version(path: Path | None = None) -> int:
    conn = connect(path)
    try:
        return conn.execute("PRAGMA user_version").fetchone()[0]
    finally:
        conn.close()


def compact_if_worth_it(path: Path | None = None, min_free_share: float = 0.25) -> bool:
    """SQLite never gives freed space back on its own: VACUUM when at least a
    quarter of the file is free pages (and it is more than a little). Returns
    True if it compacted."""
    conn = connect(path)
    try:
        pages = conn.execute("PRAGMA page_count").fetchone()[0]
        free = conn.execute("PRAGMA freelist_count").fetchone()[0]
        if pages < 256 or free < pages * min_free_share:
            return False
        conn.execute("VACUUM")
        return True
    finally:
        conn.close()


def ensure_schema(path: Path | None = None) -> int:
    """Create or upgrade the database. Returns the schema version."""
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(path)
    try:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        for number, sql in MIGRATIONS:
            if number <= version:
                continue
            # executescript() commits first; wrap explicitly so a failing
            # migration leaves the version untouched.
            conn.executescript(f"BEGIN;\n{sql}\nPRAGMA user_version = {int(number)};\nCOMMIT;")
            version = number
        return version
    finally:
        conn.close()
