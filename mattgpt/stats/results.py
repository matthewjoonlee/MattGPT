"""Shared result shape and multiple-comparisons correction.

`StatResult` is the normalized shape used whenever a tier's output is a
testable finding (a point estimate + p-value) that might need correcting
against other findings tested in the same batch. Tier 2/3 result types
subclass it directly so a mixed list of them can be passed straight into
`apply_multiple_comparisons_correction`.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Literal

from statsmodels.stats.multitest import multipletests

Tier = Literal[1, 2, 3]
ClaimType = Literal["descriptive", "associative", "causal"]


@dataclass(frozen=True)
class StatResult:
    tier: Tier
    claim_type: ClaimType
    point_estimate: float | None
    confidence_interval: tuple[float, float] | None
    p_value: float | None
    q_value: float | None = None
    confidence_note: str = ""
    n_obs: int = 0
    diagnostics: dict = field(default_factory=dict)
    caveats: tuple[str, ...] = ()


def apply_multiple_comparisons_correction(
    results: list[StatResult], method: str = "fdr_bh", alpha: float = 0.05
) -> list[StatResult]:
    """Correct p-values across a batch of findings tested against the same data.

    Intended to be called once per investigative "query" — whenever more than
    one Tier 1/2/3 hypothesis was tested against the same dataset — before any
    of the results are treated as significant. Results without a p-value
    (e.g. a Tier 3 estimate refused by the data-sufficiency gate) pass
    through unchanged. Deciding what counts as "one batch" is the caller's
    (eventually, the agent/router's) responsibility — not handled here.
    """
    indices_with_p = [i for i, r in enumerate(results) if r.p_value is not None]
    if not indices_with_p:
        return list(results)

    pvals = [results[i].p_value for i in indices_with_p]
    _, qvals, _, _ = multipletests(pvals, alpha=alpha, method=method)

    out = list(results)
    for idx, q in zip(indices_with_p, qvals):
        out[idx] = dataclasses.replace(out[idx], q_value=float(q))
    return out
