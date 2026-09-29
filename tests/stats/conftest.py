import pytest

from mattgpt.stats.schema import records_to_wide
from mattgpt.stats.synthetic import generate_synthetic_dataset


@pytest.fixture(scope="module")
def synthetic():
    """~200 days — enough to clear the Tier 3 data-sufficiency gate."""
    records, truth = generate_synthetic_dataset(n_days=200, seed=42)
    return records_to_wide(records), truth


@pytest.fixture(scope="module")
def small_synthetic():
    """Too small to clear the Tier 3 data-sufficiency gate."""
    records, truth = generate_synthetic_dataset(n_days=20, seed=7, gap_start_day=None)
    return records_to_wide(records), truth
