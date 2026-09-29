from mattgpt.stats.schema import records_to_wide
from mattgpt.stats.synthetic import generate_synthetic_dataset


def test_generator_produces_expected_columns():
    records, truth = generate_synthetic_dataset(n_days=200, seed=42)
    wide = records_to_wide(records)
    expected = {
        truth.outcome_metric_tier2,
        truth.outcome_metric_tier3,
        truth.predictor_metric,
        truth.confounder_metric,
        truth.exposure_metric,
        "sleep_duration_min",
    }
    assert expected.issubset(set(wide.columns))
    assert len(wide) == 200


def test_gap_days_are_missing_for_fitbit_metrics_only():
    records, truth = generate_synthetic_dataset(n_days=200, seed=42, gap_start_day=90, gap_length_days=5)
    wide = records_to_wide(records)
    gap_slice = wide.iloc[90:95]
    assert gap_slice[truth.outcome_metric_tier2].isna().all()
    assert gap_slice[truth.predictor_metric].isna().all()
    # self_log/calendar sources aren't gapped
    assert gap_slice[truth.confounder_metric].notna().all()
    assert gap_slice[truth.exposure_metric].notna().all()


def test_confounder_correlates_with_predictor_and_outcome_as_designed():
    records, truth = generate_synthetic_dataset(n_days=200, seed=42, gap_start_day=None)
    wide = records_to_wide(records)
    corr_predictor = wide[truth.confounder_metric].corr(wide[truth.predictor_metric])
    corr_outcome = wide[truth.confounder_metric].corr(wide[truth.outcome_metric_tier2])
    assert corr_predictor < -0.3  # meeting_load -> active_minutes is negative
    assert corr_outcome > 0.3  # meeting_load -> resting_heart_rate is positive
