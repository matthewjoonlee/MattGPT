import sqlite3

DDL = """
CREATE TABLE IF NOT EXISTS metrics (
    id            INTEGER PRIMARY KEY,
    metric_name   TEXT NOT NULL,
    bundle        TEXT NOT NULL,
    ts_start      TEXT NOT NULL,
    ts_end        TEXT,
    value         REAL NOT NULL,
    unit          TEXT NOT NULL,
    granularity   TEXT NOT NULL,
    source        TEXT NOT NULL,
    raw_payload   TEXT,
    inserted_at   TEXT NOT NULL,
    UNIQUE (metric_name, ts_start, source)
);

CREATE INDEX IF NOT EXISTS idx_metrics_name_ts ON metrics (metric_name, ts_start);

CREATE TABLE IF NOT EXISTS ingest_log (
    id              INTEGER PRIMARY KEY,
    bundle          TEXT NOT NULL,
    run_at          TEXT NOT NULL,
    status          TEXT NOT NULL,
    error_message   TEXT,
    records_written INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS calendar_events (
    id              INTEGER PRIMARY KEY,
    event_id        TEXT NOT NULL,
    title           TEXT,
    ts_start        TEXT NOT NULL,
    ts_end          TEXT NOT NULL,
    is_all_day      INTEGER NOT NULL DEFAULT 0,
    attendee_count  INTEGER NOT NULL DEFAULT 0,
    raw_payload     TEXT,
    inserted_at     TEXT NOT NULL,
    UNIQUE (event_id)
);

CREATE INDEX IF NOT EXISTS idx_calendar_events_ts ON calendar_events (ts_start);
"""


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL)
    conn.commit()
