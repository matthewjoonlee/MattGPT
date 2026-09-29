import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class MetricPoint:
    metric_name: str
    ts_start: datetime
    ts_end: datetime | None
    value: float
    unit: str
    source: str


def _to_iso(value: date | datetime) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    return datetime(value.year, value.month, value.day, tzinfo=timezone.utc).isoformat()


def get_metric(
    conn: sqlite3.Connection,
    name: str,
    start: date | datetime,
    end: date | datetime,
) -> list[MetricPoint]:
    rows = conn.execute(
        """
        SELECT metric_name, ts_start, ts_end, value, unit, source
        FROM metrics
        WHERE metric_name = ? AND ts_start >= ? AND ts_start <= ?
        ORDER BY ts_start ASC
        """,
        (name, _to_iso(start), _to_iso(end)),
    ).fetchall()

    return [
        MetricPoint(
            metric_name=row["metric_name"],
            ts_start=datetime.fromisoformat(row["ts_start"]),
            ts_end=datetime.fromisoformat(row["ts_end"]) if row["ts_end"] else None,
            value=row["value"],
            unit=row["unit"],
            source=row["source"],
        )
        for row in rows
    ]


def list_available_metrics(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT DISTINCT metric_name FROM metrics ORDER BY metric_name").fetchall()
    return [row["metric_name"] for row in rows]


def upsert_metric_rows(conn: sqlite3.Connection, rows: list[Mapping[str, Any]]) -> int:
    """Insert normalized metric rows, updating in place on (metric_name, ts_start, source)
    conflicts so re-running a pull over the same window is idempotent."""
    conn.executemany(
        """
        INSERT INTO metrics
            (metric_name, bundle, ts_start, ts_end, value, unit, granularity, source, raw_payload, inserted_at)
        VALUES
            (:metric_name, :bundle, :ts_start, :ts_end, :value, :unit, :granularity, :source, :raw_payload, :inserted_at)
        ON CONFLICT (metric_name, ts_start, source) DO UPDATE SET
            ts_end = excluded.ts_end,
            value = excluded.value,
            unit = excluded.unit,
            granularity = excluded.granularity,
            raw_payload = excluded.raw_payload,
            inserted_at = excluded.inserted_at
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def upsert_calendar_events(conn: sqlite3.Connection, rows: list[Mapping[str, Any]]) -> int:
    """Insert normalized calendar event rows, updating in place on event_id
    conflicts so re-running a pull over the same window is idempotent."""
    conn.executemany(
        """
        INSERT INTO calendar_events
            (event_id, title, ts_start, ts_end, is_all_day, attendee_count, raw_payload, inserted_at)
        VALUES
            (:event_id, :title, :ts_start, :ts_end, :is_all_day, :attendee_count, :raw_payload, :inserted_at)
        ON CONFLICT (event_id) DO UPDATE SET
            title = excluded.title,
            ts_start = excluded.ts_start,
            ts_end = excluded.ts_end,
            is_all_day = excluded.is_all_day,
            attendee_count = excluded.attendee_count,
            raw_payload = excluded.raw_payload,
            inserted_at = excluded.inserted_at
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def log_ingest_run(
    conn: sqlite3.Connection,
    bundle: str,
    status: str,
    records_written: int = 0,
    error_message: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO ingest_log (bundle, run_at, status, error_message, records_written)
        VALUES (?, ?, ?, ?, ?)
        """,
        (bundle, datetime.now(timezone.utc).isoformat(), status, error_message, records_written),
    )
    conn.commit()
