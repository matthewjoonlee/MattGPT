"""Thin wrapper: one function per bundle, authenticated request -> raw API JSON.

ENDPOINT PATHS BELOW ARE PLACEHOLDERS (see the <TODO> markers). Per the
approved plan, the exact Google Health API request/response shape must be
confirmed against current docs before the first real pull -- this module
intentionally does not guess field names beyond what's needed to compile and
be exercised by tests with mocked responses.
"""

from datetime import date, datetime
from typing import Any

from google.oauth2.credentials import Credentials

from mattgpt.ingest.http import get_json

API_BASE_URL = "<TODO: confirm Google Health API base URL>"


def fetch_bundle(creds: Credentials, bundle: str, start: date | datetime, end: date | datetime) -> dict[str, Any]:
    """Fetch raw API data for one bundle over [start, end]."""
    path = f"<TODO: confirm endpoint path for bundle={bundle!r}>"
    return get_json(
        creds,
        f"{API_BASE_URL}{path}",
        params={"startTime": start.isoformat(), "endTime": end.isoformat()},
    )


def extract_records(bundle: str, api_response: dict[str, Any]) -> list[dict[str, Any]]:
    """Map a raw API response for `bundle` into normalize.RawRecord-shaped dicts
    (metric_name/ts_start/ts_end/value). Left unimplemented: the real Google
    Health API response shape needs to be confirmed against current docs
    before this can be written without guessing field names (flagged as a
    human-review item in the approved plan)."""
    raise NotImplementedError(
        f"extract_records for bundle={bundle!r}: confirm the real API response shape first"
    )
