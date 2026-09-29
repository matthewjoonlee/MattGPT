"""Mocked stats layer, standing in for Window B's real Tier 1/2/3 engine.

`MockStatResult` mirrors the field names seen in Window B's in-progress
`mattgpt.stats.results.StatResult` (tier, claim_type, point_estimate,
confidence_interval, p_value, confidence_note, caveats) so that swapping the
mock for the real thing later is close to a drop-in. This module is only
here to prove an `AnalysisSpec` is consumable downstream — it does no real
computation and must not be mistaken for the statistics core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from mattgpt.router.schema import AnalysisSpec

ClaimType = Literal["descriptive", "associative", "causal"]

_TIER_TO_CLAIM_TYPE: dict[int, ClaimType] = {
    1: "descriptive",
    2: "associative",
    3: "causal",
}


@dataclass(frozen=True)
class MockStatResult:
    tier: Literal[1, 2, 3]
    claim_type: ClaimType
    point_estimate: float | None
    confidence_interval: tuple[float, float] | None
    p_value: float | None
    confidence_note: str
    caveats: tuple[str, ...] = field(default_factory=tuple)


def run_tier1(spec: AnalysisSpec) -> MockStatResult:
    return MockStatResult(
        tier=1,
        claim_type="descriptive",
        point_estimate=42.0,
        confidence_interval=None,
        p_value=None,
        confidence_note="Mocked rolling average over a fake 30-day window.",
        caveats=("This is placeholder output — no real data was queried.",),
    )


def run_tier2(spec: AnalysisSpec) -> MockStatResult:
    return MockStatResult(
        tier=2,
        claim_type="associative",
        point_estimate=0.31,
        confidence_interval=(0.05, 0.57),
        p_value=0.02,
        confidence_note="Mocked regression coefficient with confounders nominally controlled.",
        caveats=(
            "This is placeholder output — confounders were not actually checked.",
        ),
    )


def run_tier3(spec: AnalysisSpec) -> MockStatResult:
    return MockStatResult(
        tier=3,
        claim_type="causal",
        point_estimate=None,
        confidence_interval=None,
        p_value=None,
        confidence_note="Mocked data-sufficiency gate: not enough data yet for a causal estimate.",
        caveats=(
            "This is placeholder output — the real data-sufficiency check does not exist yet.",
        ),
    )


_TIER_TO_RUNNER = {1: run_tier1, 2: run_tier2, 3: run_tier3}


def run_mock_stats(spec: AnalysisSpec) -> MockStatResult:
    """Dispatch to the mocked tier runner matching `spec.tier`."""
    return _TIER_TO_RUNNER[spec.tier](spec)
