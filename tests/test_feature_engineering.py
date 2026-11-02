"""Tests for feature engineering module scaffolding."""

import pytest
import pandas as pd
from expense_tracker.features.feature_engineering import (
    extract_temporal_features,
    extract_text_features,
)


def test_feature_engineering_scaffolding():
    """Verify feature engineering scaffolding placeholder."""
    df = pd.DataFrame()
    with pytest.raises(NotImplementedError):
        extract_temporal_features(df)
    with pytest.raises(NotImplementedError):
        extract_text_features(df)

