from statsmodels.stats.multitest import multipletests

from mattgpt.stats.results import StatResult, apply_multiple_comparisons_correction


def _result(p_value: float | None) -> StatResult:
    return StatResult(
        tier=2,
        claim_type="associative",
        point_estimate=1.0,
        confidence_interval=(0.5, 1.5),
        p_value=p_value,
    )


def test_bh_correction_matches_statsmodels_reference():
    pvals = [0.001, 0.02, 0.03, 0.4, 0.6]
    results = [_result(p) for p in pvals]

    corrected = apply_multiple_comparisons_correction(results, method="fdr_bh", alpha=0.05)

    _, expected_q, _, _ = multipletests(pvals, alpha=0.05, method="fdr_bh")
    for result, expected in zip(corrected, expected_q):
        assert abs(result.q_value - expected) < 1e-9


def test_results_without_a_p_value_pass_through_unchanged():
    with_p = _result(0.01)
    without_p = StatResult(
        tier=3, claim_type="descriptive", point_estimate=None, confidence_interval=None, p_value=None
    )

    corrected = apply_multiple_comparisons_correction([with_p, without_p])

    assert corrected[0].q_value is not None
    assert corrected[1].q_value is None
