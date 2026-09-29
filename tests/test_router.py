"""Canned example questions for the router, run against the real local model.

These are integration tests against a live Ollama instance (no mocking of the
model itself — only the downstream stats layer is mocked, per this ticket).
LLM output isn't perfectly deterministic even at temperature=0, so a wrong
tier is recorded and reported rather than failing the test outright; the
final summary makes every mismatch visible.
"""

from __future__ import annotations

import pytest

from mattgpt.router.mock_stats import run_mock_stats
from mattgpt.router.router import route_question

CASES = [
    # -- Tier 1: descriptive --
    ("What was my average resting heart rate last month?", 1),
    ("How many steps have I taken on average this week?", 1),
    ("What's the trend in my sleep duration over the last 30 days?", 1),
    ("How does my HRV today compare to my typical HRV?", 1),
    # -- Tier 2: controlled association --
    (
        "Does sleep duration predict next-day HRV, controlling for how much I worked out?",
        2,
    ),
    (
        "Is there a relationship between my meeting load and my resting heart rate, "
        "after accounting for how much I slept?",
        2,
    ),
    ("Controlling for stress, does step count predict mood?", 2),
    # -- Tier 3: causal intent --
    ("Did cutting caffeine actually improve my sleep?", 3),
    ("If I meditate daily, does my HRV go up?", 3),
    ("Would sleeping more actually cause my grades to improve?", 3),
    # -- Ambiguous / adversarial --
    # Causal wording, but only observational data exists for this -- still
    # causal *intent*, so Tier 3 is the "correct" route (gated downstream by
    # a data-sufficiency check the mock doesn't perform).
    ("Does more sleep cause better grades?", 3),
    # Regime-change question -- arguably tier 2 (before/after comparison with
    # potential confounders) rather than a clean tier 1 average.
    ("Am I sleeping better since I moved apartments in December?", 2),
]


@pytest.mark.parametrize("question,expected_tier", CASES)
def test_router_produces_consumable_spec(question, expected_tier):
    spec = route_question(question)
    assert spec.tier in (1, 2, 3)
    assert spec.variables, "spec must reference at least one variable"

    # Prove the spec is consumable end-to-end by the mocked stats layer.
    result = run_mock_stats(spec)
    assert result.tier == spec.tier


def test_router_tier_accuracy_report():
    """Not a pass/fail gate -- runs every case and prints a mismatch report."""
    mismatches = []
    for question, expected_tier in CASES:
        spec = route_question(question)
        if spec.tier != expected_tier:
            mismatches.append((question, expected_tier, spec.tier, spec.rationale))

    print(f"\n{len(CASES) - len(mismatches)}/{len(CASES)} questions routed to the expected tier.")
    if mismatches:
        print("Mismatches:")
        for question, expected, actual, rationale in mismatches:
            print(f"  - {question!r}: expected tier {expected}, got tier {actual}")
            print(f"    rationale: {rationale}")
