import sqlite3

from mattgpt.db.schema import init_db


def test_init_db_creates_expected_tables():
    conn = sqlite3.connect(":memory:")
    init_db(conn)

    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert {"metrics", "ingest_log", "calendar_events"} <= tables


def test_init_db_creates_expected_index():
    conn = sqlite3.connect(":memory:")
    init_db(conn)

    indexes = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
    }
    assert "idx_metrics_name_ts" in indexes
    assert "idx_calendar_events_ts" in indexes


def test_init_db_is_idempotent():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    init_db(conn)  # should not raise
