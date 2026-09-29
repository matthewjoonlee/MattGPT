"""Thin wrapper: authenticated fetch of Calendar events in a date range.

Uses the real, documented Google Calendar API v3 `events.list` endpoint
(unlike the Health client, no endpoint/field-name verification is pending
here).
"""

from datetime import date, datetime
from typing import Any

from google.oauth2.credentials import Credentials

from mattgpt.ingest.http import get_json

EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


def fetch_events(creds: Credentials, start: date | datetime, end: date | datetime) -> list[dict[str, Any]]:
    """Fetch every event in [start, end] from the primary calendar, expanding
    recurring events into individual instances (singleEvents=true)."""
    response = get_json(
        creds,
        EVENTS_URL,
        params={
            "timeMin": _to_iso(start),
            "timeMax": _to_iso(end),
            "singleEvents": "true",
            "orderBy": "startTime",
        },
    )
    return response.get("items", [])


def _to_iso(value: date | datetime) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return f"{value.isoformat()}T00:00:00Z"
