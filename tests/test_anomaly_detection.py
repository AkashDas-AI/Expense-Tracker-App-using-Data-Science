"""Tests for anomaly detection scaffolding."""

import pytest
import pandas as pd
from expense_tracker.models.anomaly_detection import (
    detect_outliers_statistical,
    detect_anomalies_isolation_forest,
)


def test_anomaly_detection_scaffolding():
    """Verify anomaly detection placeholder."""
    df = pd.DataFrame()
    with pytest.raises(NotImplementedError):
        detect_outliers_statistical(df)
    with pytest.raises(NotImplementedError):
        detect_anomalies_isolation_forest(df)

