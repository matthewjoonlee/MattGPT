"""Data shapes for time-stamped biometric records.

Long/tidy format (one row per subject/timestamp/metric) matches how
Fitbit/Google Health Takeout data arrives and how self-logged and
calendar-derived confounders get merged in alongside it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

import pandas as pd

Source = Literal["fitbit", "self_log", "calendar"]
Quality = Literal["ok", "imputed", "missing", "device_not_worn"]


@dataclass(frozen=True)
class BiometricRecord:
    subject_id: str
    timestamp: datetime
    metric: str
    value: float
    source: Source
    quality: Quality = "ok"


def records_to_wide(records: list[BiometricRecord]) -> pd.DataFrame:
    """Pivot long-format records into a date-indexed frame, one column per metric.

    Only "ok" and "imputed" rows contribute values; "missing" and
    "device_not_worn" rows are dropped (they'd otherwise silently coerce to
    NaN anyway, but making the exclusion explicit documents the choice).
    """
    if not records:
        return pd.DataFrame()

    frame = pd.DataFrame(
        {
            "date": [r.timestamp.date() for r in records],
            "metric": [r.metric for r in records],
            "value": [r.value for r in records],
            "quality": [r.quality for r in records],
        }
    )
    frame = frame[frame["quality"].isin(["ok", "imputed"])]
    wide = frame.pivot_table(index="date", columns="metric", values="value", aggfunc="mean")
    wide.index = pd.DatetimeIndex(wide.index)
    wide = wide.sort_index()
    wide.columns.name = None
    return wide
