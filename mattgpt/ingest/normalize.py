"""Pure functions: raw Google Health API records -> DB-ready metric rows.

The expected shape of `raw_records` below (metric_name/start/end/value/unit
keys) is this module's own normalized intermediate form, not necessarily
Google's actual API response shape -- mapping the real API JSON into this
shape belongs in google_health_client.py and needs verification against real
API responses (flagged in the approved plan). Keeping that mapping out of
this module is what makes it testable with plain fixtures and no network.
"""

import json
from datetime import datetime, timezone
from typing import TypedDict

from mattgpt.ingest.bundles import BUNDLES


class RawRecord(TypedDict):
    metric_name: str
    ts_start: str  # ISO 8601
    ts_end: str | None
    value: float


class MetricRow(TypedDict):
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


def normalize_records(bundle: str, raw_records: list[RawRecord]) -> list[MetricRow]:
    if bundle not in BUNDLES:
        raise ValueError(f"unknown bundle: {bundle!r}")

    metric_defs = {m.name: m for m in BUNDLES[bundle]["metrics"]}  # type: ignore[union-attr]
    now = datetime.now(timezone.utc).isoformat()
    rows: list[MetricRow] = []

    for record in raw_records:
        metric_def = metric_defs.get(record["metric_name"])
        if metric_def is None:
            raise ValueError(f"metric {record['metric_name']!r} is not defined for bundle {bundle!r}")

        rows.append(
            MetricRow(
                metric_name=record["metric_name"],
                bundle=bundle,
                ts_start=record["ts_start"],
                ts_end=record.get("ts_end"),
                value=record["value"],
                unit=metric_def.unit,
                granularity=metric_def.granularity,
                source="google_health_api",
                raw_payload=json.dumps(record),
                inserted_at=now,
            )
        )

    return rows
