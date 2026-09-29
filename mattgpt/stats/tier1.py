"""Tier 1 — descriptive statistics. No causal or associative claim implied."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd
from statsmodels.tsa.seasonal import STL


@dataclass(frozen=True)
class BaselineResult:
    rolling: pd.Series
    rolling_std: pd.Series
    latest: float
    window_days: int
    n_obs: int
    coverage: float


def compute_baseline(
    series: pd.Series, window_days: int = 28, method: Literal["mean", "median"] = "mean"
) -> BaselineResult:
    min_periods = max(3, window_days // 4)
    if method == "mean":
        rolling = series.rolling(window=window_days, min_periods=min_periods).mean()
    else:
        rolling = series.rolling(window=window_days, min_periods=min_periods).median()
    rolling_std = series.rolling(window=window_days, min_periods=min_periods).std()

    n_obs = int(series.notna().sum())
    coverage = float(series.tail(window_days).notna().mean()) if len(series) else 0.0
    latest = float(rolling.iloc[-1]) if len(rolling) and pd.notna(rolling.iloc[-1]) else float("nan")

    return BaselineResult(
        rolling=rolling,
        rolling_std=rolling_std,
        latest=latest,
        window_days=window_days,
        n_obs=n_obs,
        coverage=coverage,
    )


@dataclass(frozen=True)
class DecompositionResult:
    trend: pd.Series
    seasonal: pd.Series
    resid: pd.Series
    period_days: int
    n_obs: int
    coverage: float


def decompose_trend(series: pd.Series, period_days: int = 7) -> DecompositionResult:
    clean = series.dropna()
    if len(clean) < period_days * 2:
        raise ValueError(
            f"need at least {period_days * 2} observations to decompose with period_days={period_days}, "
            f"got {len(clean)}"
        )
    result = STL(clean, period=period_days, robust=True).fit()
    coverage = float(series.notna().mean()) if len(series) else 0.0

    return DecompositionResult(
        trend=result.trend,
        seasonal=result.seasonal,
        resid=result.resid,
        period_days=period_days,
        n_obs=len(clean),
        coverage=coverage,
    )


@dataclass(frozen=True)
class Anomaly:
    date: pd.Timestamp
    value: float
    z_score: float


def detect_anomalies(series: pd.Series, baseline: BaselineResult, z_thresh: float = 2.5) -> list[Anomaly]:
    z_scores = (series - baseline.rolling) / baseline.rolling_std
    anomalies = []
    for date, z in z_scores.items():
        if pd.notna(z) and abs(z) >= z_thresh:
            anomalies.append(Anomaly(date=date, value=float(series.loc[date]), z_score=float(z)))
    return anomalies
