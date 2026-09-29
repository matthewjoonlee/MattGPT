"""Tier 3 — observational N-of-1 causal inference, gated by data sufficiency.

Scope: observational counterfactual estimation only (a simplified g-formula,
reimplemented from the N1RT methodology as reference — see
`spec/stats-core.md`). Real controlled experiments (randomization/scheduling,
a QuantifyMe fork) are a separate, deferred ticket.

`estimate_n_of_1_effect` always runs `check_data_sufficiency` itself before
producing a causal estimate — the gate can't be bypassed by a caller skipping
a step, per `review.md`'s "data-sufficiency check before any causal claim".
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.power import TTestIndPower

from .results import StatResult


@dataclass(frozen=True)
class SufficiencyResult:
    sufficient: bool
    n_total: int
    n_exposed: int
    n_unexposed: int
    achieved_power: float
    required_power: float
    reasons: tuple[str, ...]


def check_data_sufficiency(
    outcome: pd.Series,
    exposure: pd.Series,
    min_total_days: int = 60,
    min_exposed_days: int = 10,
    min_unexposed_days: int = 10,
    min_power: float = 0.8,
    assumed_effect_size: float | None = None,
) -> SufficiencyResult:
    aligned = pd.concat([outcome.rename("outcome"), exposure.rename("exposure")], axis=1).dropna()
    n_total = len(aligned)
    n_exposed = int((aligned["exposure"] > 0).sum())
    n_unexposed = n_total - n_exposed

    reasons: list[str] = []
    if n_total < min_total_days:
        reasons.append(f"only {n_total} total days of data, need >= {min_total_days}")
    if n_exposed < min_exposed_days:
        reasons.append(f"only {n_exposed} exposed days, need >= {min_exposed_days}")
    if n_unexposed < min_unexposed_days:
        reasons.append(f"only {n_unexposed} unexposed days, need >= {min_unexposed_days}")

    effect_size = assumed_effect_size
    achieved_power = 0.0
    if effect_size is None and n_exposed > 1 and n_unexposed > 1:
        g_exposed = aligned.loc[aligned["exposure"] > 0, "outcome"]
        g_unexposed = aligned.loc[aligned["exposure"] <= 0, "outcome"]
        pooled_std = float(np.sqrt((g_exposed.std() ** 2 + g_unexposed.std() ** 2) / 2))
        effect_size = float(abs(g_exposed.mean() - g_unexposed.mean()) / pooled_std) if pooled_std > 0 else 0.0
    elif effect_size is None:
        effect_size = 0.0

    if n_exposed > 1 and n_unexposed > 1 and effect_size > 0:
        ratio = n_unexposed / n_exposed
        achieved_power = float(
            TTestIndPower().power(effect_size=effect_size, nobs1=n_exposed, ratio=ratio, alpha=0.05)
        )
    if achieved_power < min_power:
        reasons.append(
            f"achieved power {achieved_power:.2f} below required {min_power:.2f} (effect size used: {effect_size:.2f})"
        )

    return SufficiencyResult(
        sufficient=len(reasons) == 0,
        n_total=n_total,
        n_exposed=n_exposed,
        n_unexposed=n_unexposed,
        achieved_power=achieved_power,
        required_power=min_power,
        reasons=tuple(reasons),
    )


@dataclass(frozen=True)
class Tier3Result(StatResult):
    sufficiency: SufficiencyResult | None = None


def estimate_n_of_1_effect(
    outcome: pd.Series,
    exposure: pd.Series,
    confounders: pd.DataFrame | None = None,
    lag_days: int = 1,
    min_total_days: int = 60,
    min_exposed_days: int = 10,
    min_unexposed_days: int = 10,
    min_power: float = 0.8,
    assumed_effect_size: float | None = None,
) -> Tier3Result:
    exposure_lagged = exposure.shift(lag_days).rename("exposure_lag")

    sufficiency = check_data_sufficiency(
        outcome,
        exposure_lagged,
        min_total_days=min_total_days,
        min_exposed_days=min_exposed_days,
        min_unexposed_days=min_unexposed_days,
        min_power=min_power,
        assumed_effect_size=assumed_effect_size,
    )

    if not sufficiency.sufficient:
        return Tier3Result(
            tier=3,
            claim_type="descriptive",
            point_estimate=None,
            confidence_interval=None,
            p_value=None,
            confidence_note="not enough data to claim a causal effect yet",
            n_obs=sufficiency.n_total,
            diagnostics={"gated": False},
            caveats=sufficiency.reasons,
            sufficiency=sufficiency,
        )

    frame_parts = [outcome.rename("outcome"), exposure_lagged]
    if confounders is not None:
        frame_parts.append(confounders)
    aligned = pd.concat(frame_parts, axis=1).dropna()

    y = aligned["outcome"]
    X = sm.add_constant(aligned.drop(columns="outcome"))
    maxlags = max(1, int(4 * (len(y) / 100) ** (2 / 9)))
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})

    # Simplified g-formula: predict each day's outcome under both exposure
    # states with everything else held fixed, then average the difference.
    x_exposed = X.copy()
    x_exposed["exposure_lag"] = 1.0
    x_unexposed = X.copy()
    x_unexposed["exposure_lag"] = 0.0
    ate = float((fit.predict(x_exposed) - fit.predict(x_unexposed)).mean())

    ci_low, ci_high = (float(v) for v in fit.conf_int().loc["exposure_lag"])
    p_value = float(fit.pvalues["exposure_lag"])
    se = float(fit.bse["exposure_lag"])
    converged = np.isfinite(se) and se > 0
    plausible_range = abs(ate) < 10 * float(y.std())

    caveats = () if plausible_range else ("counterfactual estimate outside a plausible range — treat with suspicion",)

    return Tier3Result(
        tier=3,
        claim_type="causal",
        point_estimate=ate,
        confidence_interval=(ci_low, ci_high),
        p_value=p_value,
        confidence_note="observational N-of-1 estimate, gated by a data-sufficiency check — not a randomized experiment",
        n_obs=len(aligned),
        diagnostics={"gated": True, "converged": converged, "plausible_range": plausible_range},
        caveats=caveats,
        sufficiency=sufficiency,
    )
