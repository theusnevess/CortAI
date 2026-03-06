from __future__ import annotations

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS events_hot (
    event_id TEXT NOT NULL PRIMARY KEY,
    ts TEXT NOT NULL,
    event_type TEXT NOT NULL,
    writer_id TEXT,
    severity TEXT,
    action_taken TEXT,
    account_id TEXT,
    window_id TEXT,
    job_id TEXT,
    publish_id TEXT,
    op_key TEXT,
    details_json TEXT
);

CREATE INDEX IF NOT EXISTS ix_events_hot_ts_event_id
ON events_hot (ts DESC, event_id DESC);

CREATE INDEX IF NOT EXISTS ix_events_hot_account_ts
ON events_hot (account_id, ts DESC, event_id DESC);

CREATE INDEX IF NOT EXISTS ix_events_hot_window_ts
ON events_hot (window_id, ts DESC, event_id DESC);

CREATE INDEX IF NOT EXISTS ix_events_hot_job_ts
ON events_hot (job_id, ts DESC, event_id DESC);

CREATE INDEX IF NOT EXISTS ix_events_hot_publish_ts
ON events_hot (publish_id, ts DESC, event_id DESC);

CREATE INDEX IF NOT EXISTS ix_events_hot_op_key_ts
ON events_hot (op_key, ts DESC, event_id DESC);

CREATE INDEX IF NOT EXISTS ix_events_hot_event_type_ts
ON events_hot (event_type, ts DESC, event_id DESC);
"""
