"""Tests for data validation module scaffolding."""

import pytest
import pandas as pd
from expense_tracker.data.validation import validate_transaction_schema


def test_validate_transaction_schema_scaffolding():
    """Verify function signature and scaffolding placeholder behavior."""
    df = pd.DataFrame()
    with pytest.raises(NotImplementedError):
        validate_transaction_schema(df)

