"""Tests for budget analysis scaffolding."""

import pytest
import pandas as pd
from expense_tracker.analytics.budget_analysis import compute_budget_variance


def test_compute_budget_variance_scaffolding():
    """Verify budget variance calculation placeholder."""
    df = pd.DataFrame()
    with pytest.raises(NotImplementedError):
        compute_budget_variance(df, {})

