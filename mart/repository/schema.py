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
]

LATEST_VERSION = MIGRATIONS[-1][0]


def current_version(path: Path | None = None) -> int:
    conn = connect(path)
    try:
        return conn.execute("PRAGMA user_version").fetchone()[0]
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
