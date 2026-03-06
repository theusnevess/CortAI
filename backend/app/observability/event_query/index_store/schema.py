from __future__ import annotations

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS events_index (
    source_file TEXT NOT NULL,
    source_line INTEGER NOT NULL,
    event_id TEXT NOT NULL,
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
    details_json TEXT,
    PRIMARY KEY (source_file, source_line)
);

CREATE INDEX IF NOT EXISTS ix_events_index_ts_event_id
ON events_index (ts DESC, event_id DESC);

CREATE INDEX IF NOT EXISTS ix_events_index_account_ts
ON events_index (account_id, ts DESC, event_id DESC);

CREATE INDEX IF NOT EXISTS ix_events_index_window_ts
ON events_index (window_id, ts DESC, event_id DESC);

CREATE INDEX IF NOT EXISTS ix_events_index_job_ts
ON events_index (job_id, ts DESC, event_id DESC);

CREATE INDEX IF NOT EXISTS ix_events_index_publish_ts
ON events_index (publish_id, ts DESC, event_id DESC);

CREATE INDEX IF NOT EXISTS ix_events_index_op_key_ts
ON events_index (op_key, ts DESC, event_id DESC);

CREATE INDEX IF NOT EXISTS ix_events_index_event_type_ts
ON events_index (event_type, ts DESC, event_id DESC);
"""
