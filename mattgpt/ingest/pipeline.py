"""Orchestrates one ingestion run: authenticate -> fetch each Health bundle
and Calendar -> normalize -> upsert -> log. See spec/data-ingestion.md for
the manual OAuth setup this depends on, and google_health_client.extract_records
for the one piece intentionally left unimplemented pending real API
verification.
"""

import sqlite3
from datetime import date, datetime

from mattgpt.db.queries import log_ingest_run, upsert_calendar_events, upsert_metric_rows
from mattgpt.ingest.bundles import BUNDLES
from mattgpt.ingest.calendar_client import fetch_events
from mattgpt.ingest.calendar_normalize import derive_daily_metrics, normalize_calendar_events
from mattgpt.ingest.google_health_client import extract_records, fetch_bundle
from mattgpt.ingest.normalize import normalize_records
from mattgpt.ingest.oauth import load_credentials


def run_ingestion(conn: sqlite3.Connection, start: date | datetime, end: date | datetime) -> dict[str, int]:
    """Pull every in-scope Health bundle plus Calendar over [start, end],
    logging each source's outcome to `ingest_log`. Returns records-written
    per source."""
    creds = load_credentials()
    written: dict[str, int] = {}

    for bundle in BUNDLES:
        try:
            raw_response = fetch_bundle(creds, bundle, start, end)
            raw_records = extract_records(bundle, raw_response)
            rows = normalize_records(bundle, raw_records)
            count = upsert_metric_rows(conn, rows)
            log_ingest_run(conn, bundle, status="ok", records_written=count)
            written[bundle] = count
        except Exception as exc:
            log_ingest_run(conn, bundle, status="error", error_message=str(exc))
            written[bundle] = 0

    try:
        raw_events = fetch_events(creds, start, end)
        event_rows = normalize_calendar_events(raw_events)
        metric_rows = derive_daily_metrics(event_rows)
        event_count = upsert_calendar_events(conn, event_rows)
        upsert_metric_rows(conn, metric_rows)
        log_ingest_run(conn, "calendar", status="ok", records_written=event_count)
        written["calendar"] = event_count
    except Exception as exc:
        log_ingest_run(conn, "calendar", status="error", error_message=str(exc))
        written["calendar"] = 0

    return written
