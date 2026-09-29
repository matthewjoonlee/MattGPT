import sqlite3
from datetime import date, datetime, timezone

import pytest

from mattgpt.db.queries import (
    MetricPoint,
    get_metric,
    list_available_metrics,
    log_ingest_run,
    upsert_calendar_events,
    upsert_metric_rows,
)
from mattgpt.db.schema import init_db


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    init_db(connection)
    yield connection
    connection.close()


def _row(metric_name: str, ts_start: str, value: float, source: str = "google_health_api") -> dict:
    return {
        "metric_name": metric_name,
        "bundle": "vitals",
        "ts_start": ts_start,
        "ts_end": None,
        "value": value,
        "unit": "bpm",
        "granularity": "daily",
        "source": source,
        "raw_payload": "{}",
        "inserted_at": datetime.now(timezone.utc).isoformat(),
    }


def test_upsert_and_get_metric_filters_by_name_and_range(conn):
    rows = [
        _row("resting_heart_rate", "2026-01-01T00:00:00+00:00", 58.0),
        _row("resting_heart_rate", "2026-01-15T00:00:00+00:00", 60.0),
        _row("resting_heart_rate", "2026-02-01T00:00:00+00:00", 62.0),
        _row("steps", "2026-01-15T00:00:00+00:00", 8000.0),
    ]
    upsert_metric_rows(conn, rows)

    points = get_metric(conn, "resting_heart_rate", date(2026, 1, 1), date(2026, 1, 31))

    assert [p.value for p in points] == [58.0, 60.0]
    assert all(isinstance(p, MetricPoint) for p in points)
    assert points[0].ts_end is None


def test_upsert_is_idempotent_on_conflict(conn):
    rows = [_row("resting_heart_rate", "2026-01-01T00:00:00+00:00", 58.0)]
    upsert_metric_rows(conn, rows)

    updated_rows = [_row("resting_heart_rate", "2026-01-01T00:00:00+00:00", 59.0)]
    upsert_metric_rows(conn, updated_rows)

    points = get_metric(conn, "resting_heart_rate", date(2026, 1, 1), date(2026, 1, 1))
    assert len(points) == 1
    assert points[0].value == 59.0


def test_list_available_metrics(conn):
    upsert_metric_rows(
        conn,
        [
            _row("resting_heart_rate", "2026-01-01T00:00:00+00:00", 58.0),
            _row("steps", "2026-01-01T00:00:00+00:00", 8000.0),
        ],
    )
    assert list_available_metrics(conn) == ["resting_heart_rate", "steps"]


def test_upsert_calendar_events_is_idempotent_on_conflict(conn):
    event = {
        "event_id": "evt1",
        "title": "1:1",
        "ts_start": "2026-01-15T14:00:00+00:00",
        "ts_end": "2026-01-15T14:30:00+00:00",
        "is_all_day": False,
        "attendee_count": 2,
        "raw_payload": "{}",
        "inserted_at": datetime.now(timezone.utc).isoformat(),
    }
    upsert_calendar_events(conn, [event])

    renamed = {**event, "title": "1:1 (rescheduled)"}
    upsert_calendar_events(conn, [renamed])

    rows = conn.execute("SELECT title FROM calendar_events WHERE event_id = 'evt1'").fetchall()
    assert len(rows) == 1
    assert rows[0]["title"] == "1:1 (rescheduled)"


def test_log_ingest_run_records_status(conn):
    log_ingest_run(conn, "vitals", status="ok", records_written=3)
    log_ingest_run(conn, "sleep", status="error", error_message="boom")

    rows = conn.execute("SELECT bundle, status, records_written, error_message FROM ingest_log").fetchall()
    assert rows[0]["bundle"] == "vitals"
    assert rows[0]["status"] == "ok"
    assert rows[0]["records_written"] == 3
    assert rows[1]["error_message"] == "boom"
