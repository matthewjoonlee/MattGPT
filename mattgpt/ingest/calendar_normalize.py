"""Pure functions: raw Google Calendar API v3 event resources -> DB-ready rows.

Unlike the Health API (still <TODO>-flagged pending verification), the
Calendar API v3 `events.list` response shape used here is real and
documented: each item has `id`, optional `summary`, `start`/`end` objects
with either `dateTime` (timed events) or `date` (all-day events), and an
optional `attendees` list.

All-day events are excluded from the derived `meeting_count`/`meeting_minutes`
metrics (they're typically holidays/reminders, not meetings) but are still
stored in `calendar_events` for full fidelity.
"""

import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, TypedDict


class EventRow(TypedDict):
    event_id: str
    title: str | None
    ts_start: str
    ts_end: str
    is_all_day: bool
    attendee_count: int
    raw_payload: str
    inserted_at: str


class CalendarMetricRow(TypedDict):
    metric_name: str
    bundle: str
    ts_start: str
    ts_end: str | None
    value: float
    unit: str
    granularity: str
    source: str
    raw_payload: str
    inserted_at: str


def _parse_event_time(time_obj: dict[str, Any]) -> tuple[datetime, bool]:
    if "date" in time_obj:
        d = datetime.strptime(time_obj["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return d, True
    return datetime.fromisoformat(time_obj["dateTime"]).astimezone(timezone.utc), False


def normalize_calendar_events(raw_events: list[dict[str, Any]]) -> list[EventRow]:
    now = datetime.now(timezone.utc).isoformat()
    rows: list[EventRow] = []

    for event in raw_events:
        ts_start, all_day_start = _parse_event_time(event["start"])
        ts_end, _ = _parse_event_time(event["end"])

        rows.append(
            EventRow(
                event_id=event["id"],
                title=event.get("summary"),
                ts_start=ts_start.isoformat(),
                ts_end=ts_end.isoformat(),
                is_all_day=all_day_start,
                attendee_count=len(event.get("attendees", [])),
                raw_payload=json.dumps(event),
                inserted_at=now,
            )
        )

    return rows


def derive_daily_metrics(event_rows: list[EventRow]) -> list[CalendarMetricRow]:
    """Aggregate timed (non-all-day) events into per-day meeting_count and
    meeting_minutes rows in the same shape mattgpt/ingest/normalize.py
    produces for Health bundles, so get_metric() serves both uniformly."""
    now = datetime.now(timezone.utc).isoformat()
    counts: dict[str, int] = defaultdict(int)
    minutes: dict[str, float] = defaultdict(float)

    for row in event_rows:
        if row["is_all_day"]:
            continue
        start = datetime.fromisoformat(row["ts_start"])
        end = datetime.fromisoformat(row["ts_end"])
        day_key = start.date().isoformat()
        counts[day_key] += 1
        minutes[day_key] += (end - start).total_seconds() / 60

    metric_rows: list[CalendarMetricRow] = []
    for day_key in counts:
        day_start = datetime.fromisoformat(day_key).replace(tzinfo=timezone.utc).isoformat()
        metric_rows.append(
            CalendarMetricRow(
                metric_name="meeting_count",
                bundle="calendar",
                ts_start=day_start,
                ts_end=None,
                value=float(counts[day_key]),
                unit="count",
                granularity="daily",
                source="google_calendar",
                raw_payload="{}",
                inserted_at=now,
            )
        )
        metric_rows.append(
            CalendarMetricRow(
                metric_name="meeting_minutes",
                bundle="calendar",
                ts_start=day_start,
                ts_end=None,
                value=minutes[day_key],
                unit="minutes",
                granularity="daily",
                source="google_calendar",
                raw_payload="{}",
                inserted_at=now,
            )
        )

    return metric_rows
