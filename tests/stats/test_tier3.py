from mattgpt.stats.tier3 import check_data_sufficiency, estimate_n_of_1_effect


def test_check_data_sufficiency_rejects_small_dataset(small_synthetic):
    wide, truth = small_synthetic
    outcome = wide[truth.outcome_metric_tier3]
    exposure = wide[truth.exposure_metric]

    result = check_data_sufficiency(outcome, exposure)

    assert not result.sufficient
    assert result.reasons


def test_check_data_sufficiency_passes_adequate_dataset(synthetic):
    wide, truth = synthetic
    outcome = wide[truth.outcome_metric_tier3]
    exposure = wide[truth.exposure_metric]

    result = check_data_sufficiency(outcome, exposure, assumed_effect_size=0.5)

    assert result.sufficient
    assert not result.reasons


def test_estimate_n_of_1_effect_is_gated_out_on_insufficient_data(small_synthetic):
    wide, truth = small_synthetic
    outcome = wide[truth.outcome_metric_tier3]
    exposure = wide[truth.exposure_metric]

    result = estimate_n_of_1_effect(outcome, exposure)

    assert result.claim_type == "descriptive"
    assert result.point_estimate is None
    assert result.diagnostics["gated"] is False
    assert result.caveats


def test_estimate_n_of_1_effect_recovers_known_effect_within_tolerance(synthetic):
    wide, truth = synthetic
    outcome = wide[truth.outcome_metric_tier3]
    exposure = wide[truth.exposure_metric]

    result = estimate_n_of_1_effect(outcome, exposure, assumed_effect_size=0.5)

    assert result.claim_type == "causal"
    assert result.point_estimate is not None
    assert result.diagnostics["gated"] is True
    assert abs(result.point_estimate - truth.alcohol_to_hrv_effect) < 3.0
