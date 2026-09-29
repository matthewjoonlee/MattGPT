import numpy as np
import pandas as pd

from mattgpt.stats.tier1 import compute_baseline, decompose_trend, detect_anomalies


def test_compute_baseline_recovers_known_mean():
    idx = pd.date_range("2025-01-01", periods=60, freq="D")
    rng = np.random.default_rng(0)
    series = pd.Series(50 + rng.normal(0, 1, 60), index=idx)

    baseline = compute_baseline(series, window_days=30)

    assert abs(baseline.latest - 50) < 1.0
    assert baseline.coverage == 1.0


def test_decompose_trend_recovers_weekly_seasonality():
    idx = pd.date_range("2025-01-01", periods=70, freq="D")
    is_weekend = idx.weekday >= 5
    seasonal_true = np.where(is_weekend, 5.0, -2.0)
    rng = np.random.default_rng(1)
    series = pd.Series(100 + seasonal_true + rng.normal(0, 0.5, 70), index=idx)

    decomp = decompose_trend(series, period_days=7)

    weekend_mean = decomp.seasonal[is_weekend].mean()
    weekday_mean = decomp.seasonal[~is_weekend].mean()
    assert weekend_mean > weekday_mean


def test_detect_anomalies_flags_injected_outlier():
    idx = pd.date_range("2025-01-01", periods=60, freq="D")
    rng = np.random.default_rng(2)
    values = 50 + rng.normal(0, 1, 60)
    values[45] += 20
    series = pd.Series(values, index=idx)

    baseline = compute_baseline(series, window_days=30)
    anomalies = detect_anomalies(series, baseline, z_thresh=2.5)

    flagged_dates = {a.date for a in anomalies}
    assert idx[45] in flagged_dates
    # not every day should be flagged
    assert len(anomalies) < 10
