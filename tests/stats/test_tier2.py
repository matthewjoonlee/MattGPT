import numpy as np
import pandas as pd
import pytest

from mattgpt.stats.tier2 import check_confounders, fit_controlled_regression, forward_chaining_splits


def test_check_confounders_flags_known_confounder(synthetic):
    wide, truth = synthetic
    outcome = wide[truth.outcome_metric_tier2]
    predictor = wide[truth.predictor_metric]
    candidates = wide[[truth.confounder_metric]]

    result = check_confounders(outcome, predictor, candidates, corr_thresh=0.3)

    assert truth.confounder_metric in result.flagged


def test_check_confounders_does_not_flag_unrelated_noise(synthetic):
    wide, truth = synthetic
    outcome = wide[truth.outcome_metric_tier2]
    predictor = wide[truth.predictor_metric]
    noise = pd.Series(np.random.default_rng(5).normal(0, 1, len(wide)), index=wide.index)
    candidates = pd.DataFrame({"unrelated_noise": noise})

    result = check_confounders(outcome, predictor, candidates)

    assert "unrelated_noise" not in result.flagged


def test_fit_controlled_regression_requires_confounder_check_first(synthetic):
    wide, truth = synthetic
    outcome = wide[truth.outcome_metric_tier2]
    predictor = wide[truth.predictor_metric]
    confounders = wide[[truth.confounder_metric]]

    with pytest.raises(TypeError):
        fit_controlled_regression(outcome, predictor, confounders=confounders)  # missing confounder_check


def test_fit_controlled_regression_rejects_explicit_none_confounder_check(synthetic):
    wide, truth = synthetic
    outcome = wide[truth.outcome_metric_tier2]
    predictor = wide[truth.predictor_metric]

    with pytest.raises(ValueError):
        fit_controlled_regression(outcome, predictor, confounder_check=None)


def test_controlling_for_confounder_shrinks_spurious_association(synthetic):
    wide, truth = synthetic
    outcome = wide[truth.outcome_metric_tier2]
    predictor = wide[truth.predictor_metric]
    confounders = wide[[truth.confounder_metric]]

    empty_check = check_confounders(outcome, predictor, pd.DataFrame(index=wide.index))
    uncontrolled = fit_controlled_regression(outcome, predictor, confounder_check=empty_check)
    check = check_confounders(outcome, predictor, confounders)
    controlled = fit_controlled_regression(outcome, predictor, confounder_check=check, confounders=confounders)

    # active_minutes and resting_heart_rate are only spuriously linked via
    # meeting_load in the synthetic generator — controlling for it should
    # shrink the coefficient toward zero.
    assert abs(controlled.point_estimate) < abs(uncontrolled.point_estimate)
    assert controlled.claim_type == "associative"
    assert controlled.confounder_check is check


def test_forward_chaining_splits_never_leak_future_into_past():
    splits = list(forward_chaining_splits(20, min_train=10, step=5))

    assert len(splits) > 0
    for train_idx, test_idx in splits:
        assert train_idx.max() < test_idx.min()
        assert set(train_idx).isdisjoint(set(test_idx))
