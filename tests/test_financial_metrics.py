"""Tests for financial metrics scaffolding."""

import pytest
import pandas as pd
from expense_tracker.analytics.financial_metrics import compute_financial_kpis


def test_compute_financial_kpis_scaffolding():
    """Verify financial metrics calculation placeholder."""
    df = pd.DataFrame()
    with pytest.raises(NotImplementedError):
        compute_financial_kpis(df)

