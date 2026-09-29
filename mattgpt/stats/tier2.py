"""Tier 2 — confounder-controlled association on autocorrelated time series.

Never a causal claim (see `review.md`). `fit_controlled_regression` refuses
to run when confounders are supplied without proof that `check_confounders`
was run first — the confounder-check-before-association gate is enforced in
code, not left to caller discipline.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .results import StatResult


@dataclass(frozen=True)
class ConfounderCheckResult:
    flagged: tuple[str, ...]
    correlations: dict[str, tuple[float, float]]
    threshold: float
    n_obs: int


def check_confounders(
    outcome: pd.Series, predictor: pd.Series, candidates: pd.DataFrame, corr_thresh: float = 0.3
) -> ConfounderCheckResult:
    """Flag candidate confounders correlated with both the predictor and the outcome."""
    aligned = pd.concat(
        [outcome.rename("__outcome__"), predictor.rename("__predictor__"), candidates], axis=1
    ).dropna()

    flagged: list[str] = []
    correlations: dict[str, tuple[float, float]] = {}
    for col in candidates.columns:
        if aligned[col].nunique() < 2:
            continue
        corr_pred = float(aligned[col].corr(aligned["__predictor__"]))
        corr_out = float(aligned[col].corr(aligned["__outcome__"]))
        correlations[col] = (corr_pred, corr_out)
        if abs(corr_pred) >= corr_thresh and abs(corr_out) >= corr_thresh:
            flagged.append(col)

    return ConfounderCheckResult(
        flagged=tuple(flagged), correlations=correlations, threshold=corr_thresh, n_obs=len(aligned)
    )


@dataclass(frozen=True)
class Tier2Result(StatResult):
    confounder_check: ConfounderCheckResult | None = None
    r_squared: float | None = None


def _default_hac_maxlags(n_obs: int) -> int:
    # Newey-West rule of thumb.
    return max(1, int(4 * (n_obs / 100) ** (2 / 9)))


def fit_controlled_regression(
    outcome: pd.Series,
    predictor: pd.Series,
    confounder_check: ConfounderCheckResult,
    confounders: pd.DataFrame | None = None,
    *,
    autocorr: Literal["hac", "none"] = "hac",
    hac_maxlags: int | None = None,
) -> Tier2Result:
    """Fit an association, controlled for the given confounders.

    `confounder_check` is required (not optional) — even a bare bivariate
    association must be preceded by `check_confounders(...)`, run against an
    empty candidate pool if there's genuinely nothing else to check, so a
    Tier 2 result can never be produced without that check having happened
    (see review.md: "confounder check before an association is presented as
    meaningful").
    """
    if confounder_check is None:
        raise ValueError(
            "check_confounders(...) must be run first; pass its ConfounderCheckResult as confounder_check"
        )

    frame_parts = [outcome.rename("outcome"), predictor.rename("predictor")]
    if confounders is not None:
        frame_parts.append(confounders)
    aligned = pd.concat(frame_parts, axis=1).dropna()

    y = aligned["outcome"]
    X = sm.add_constant(aligned.drop(columns="outcome"))
    model = sm.OLS(y, X)

    if autocorr == "hac":
        maxlags = hac_maxlags if hac_maxlags is not None else _default_hac_maxlags(len(y))
        fit = model.fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    else:
        fit = model.fit()

    coef = float(fit.params["predictor"])
    se = float(fit.bse["predictor"])
    ci_low, ci_high = (float(v) for v in fit.conf_int().loc["predictor"])
    p_value = float(fit.pvalues["predictor"])

    caveats: list[str] = []
    if confounders is None:
        if confounder_check.flagged:
            caveats.append(
                f"confounder check flagged {list(confounder_check.flagged)} but none were included in this regression"
            )
        else:
            caveats.append(
                "no confounders controlled for — none were flagged as candidates, "
                "but treat as a weaker association than a fully controlled estimate"
            )
    else:
        missing = set(confounder_check.flagged) - set(confounders.columns)
        if missing:
            caveats.append(f"confounder check flagged {sorted(missing)} but they were not included in this regression")

    converged = np.isfinite(se) and se > 0
    diagnostics = {"converged": converged, "hac": autocorr == "hac"}

    return Tier2Result(
        tier=2,
        claim_type="associative",
        point_estimate=coef,
        confidence_interval=(ci_low, ci_high),
        p_value=p_value,
        confidence_note="associative only — confounder-controlled, not a causal estimate (see review.md)",
        n_obs=len(aligned),
        diagnostics=diagnostics,
        caveats=tuple(caveats),
        confounder_check=confounder_check,
        r_squared=float(fit.rsquared),
    )


def forward_chaining_splits(n: int, min_train: int, step: int = 1) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Expanding-window (forward-chaining) train/test index splits.

    Never a random shuffle-split — each test fold is strictly after its
    training fold, so no future observation leaks into training.
    """
    for train_end in range(min_train, n, step):
        test_end = min(train_end + step, n)
        if test_end <= train_end:
            continue
        yield np.arange(0, train_end), np.arange(train_end, test_end)
