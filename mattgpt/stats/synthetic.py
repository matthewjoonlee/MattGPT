"""Synthetic biometric dataset generator — dev/test only, not shipped as
production code. Stands in for what Window A (the real ingestion pipeline,
not yet built) will eventually produce, so Tiers 1-3 can be built and tested
now per `spec/stats-core.md`.

Ground-truth effects are baked in deliberately so tests can check that each
tier recovers a known answer, not just that it runs without crashing:
- `meeting_load` is a confounder of `active_minutes` (predictor) and
  `resting_heart_rate_bpm` (outcome) — for Tier 2 confounder-check tests.
- `alcohol_flag` has a fixed next-day causal effect on `hrv_rmssd_ms` — for
  Tier 3 effect-recovery tests.
- One contiguous gap of `device_not_worn` records is injected into the
  Fitbit-sourced metrics — for missing-data handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np

from .schema import BiometricRecord

SUBJECT_ID_DEFAULT = "matthew"

ALCOHOL_TO_HRV_EFFECT = -8.0
CONFOUNDER_TO_PREDICTOR_COEF = -1.2
CONFOUNDER_TO_OUTCOME_COEF = 0.8

PREDICTOR_METRIC = "active_minutes"
OUTCOME_METRIC_TIER2 = "resting_heart_rate_bpm"
OUTCOME_METRIC_TIER3 = "hrv_rmssd_ms"
EXPOSURE_METRIC = "alcohol_flag"
CONFOUNDER_METRIC = "meeting_load"


@dataclass(frozen=True)
class SyntheticGroundTruth:
    alcohol_to_hrv_effect: float = ALCOHOL_TO_HRV_EFFECT
    confounder_metric: str = CONFOUNDER_METRIC
    confounder_to_predictor_coef: float = CONFOUNDER_TO_PREDICTOR_COEF
    confounder_to_outcome_coef: float = CONFOUNDER_TO_OUTCOME_COEF
    predictor_metric: str = PREDICTOR_METRIC
    outcome_metric_tier2: str = OUTCOME_METRIC_TIER2
    outcome_metric_tier3: str = OUTCOME_METRIC_TIER3
    exposure_metric: str = EXPOSURE_METRIC


def _ar1_series(n: int, sigma: float, phi: float, rng: np.random.Generator) -> np.ndarray:
    """Mean-zero AR(1) noise, stationary variance ~= sigma**2."""
    innovation_sigma = sigma * np.sqrt(1 - phi**2)
    x = np.empty(n)
    x[0] = rng.normal(0, sigma)
    for t in range(1, n):
        x[t] = phi * x[t - 1] + rng.normal(0, innovation_sigma)
    return x


def generate_synthetic_dataset(
    n_days: int = 180,
    seed: int = 42,
    subject_id: str = SUBJECT_ID_DEFAULT,
    gap_start_day: int | None = 90,
    gap_length_days: int = 5,
) -> tuple[list[BiometricRecord], SyntheticGroundTruth]:
    rng = np.random.default_rng(seed)
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    dates = [start + timedelta(days=i) for i in range(n_days)]
    weekday = np.array([d.weekday() for d in dates])
    is_weekend = weekday >= 5

    meeting_load = np.where(is_weekend, rng.uniform(0, 2, n_days), rng.uniform(3, 9, n_days))
    alcohol_flag = (rng.uniform(0, 1, n_days) < np.where(is_weekend, 0.55, 0.15)).astype(float)

    active_minutes = (
        45
        + CONFOUNDER_TO_PREDICTOR_COEF * meeting_load
        + np.where(is_weekend, 15, 0)
        + _ar1_series(n_days, 8, 0.4, rng)
    )
    resting_hr = (
        60
        + CONFOUNDER_TO_OUTCOME_COEF * meeting_load
        + np.where(is_weekend, -1.5, 1.5)
        + _ar1_series(n_days, 3, 0.6, rng)
    )

    alcohol_lag1 = np.roll(alcohol_flag, 1)
    alcohol_lag1[0] = 0.0
    hrv = (
        65
        + np.where(is_weekend, 3, -1)
        + ALCOHOL_TO_HRV_EFFECT * alcohol_lag1
        + _ar1_series(n_days, 6, 0.5, rng)
    )

    sleep_duration = 420 + np.where(is_weekend, 30, 0) + _ar1_series(n_days, 25, 0.3, rng)

    gap_days: set[int] = set()
    if gap_start_day is not None:
        gap_days = set(range(gap_start_day, min(gap_start_day + gap_length_days, n_days)))

    fitbit_metrics = {
        OUTCOME_METRIC_TIER2: resting_hr,
        OUTCOME_METRIC_TIER3: hrv,
        PREDICTOR_METRIC: active_minutes,
        "sleep_duration_min": sleep_duration,
    }

    records: list[BiometricRecord] = []
    for metric, values in fitbit_metrics.items():
        for i, d in enumerate(dates):
            if i in gap_days:
                records.append(BiometricRecord(subject_id, d, metric, float("nan"), "fitbit", "device_not_worn"))
            else:
                records.append(BiometricRecord(subject_id, d, metric, float(values[i]), "fitbit", "ok"))

    for i, d in enumerate(dates):
        records.append(BiometricRecord(subject_id, d, CONFOUNDER_METRIC, float(meeting_load[i]), "calendar", "ok"))
        records.append(BiometricRecord(subject_id, d, EXPOSURE_METRIC, float(alcohol_flag[i]), "self_log", "ok"))

    return records, SyntheticGroundTruth()
