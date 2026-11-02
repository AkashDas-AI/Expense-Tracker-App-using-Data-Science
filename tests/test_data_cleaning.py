"""Tests for data cleaning module scaffolding."""

import pytest
import pandas as pd
from expense_tracker.data.data_cleaning import clean_transactions


def test_clean_transactions_scaffolding():
    """Verify function signature and scaffolding placeholder behavior."""
    df = pd.DataFrame({"amount": [10.0]})
    with pytest.raises(NotImplementedError):
        clean_transactions(df)

