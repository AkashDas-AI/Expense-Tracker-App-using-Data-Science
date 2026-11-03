"""
Unit and Integration Tests for Anomaly Detection Module

Author: Akash Das
Description: Rigorous test coverage for statistical outlier baselines, Isolation Forest
             multivariate anomaly detection, evaluation metrics, feature leakage
             prevention, and ground-truth marker invariance.
"""

import numpy as np
import pandas as pd
import pytest

from expense_tracker.config.settings import RANDOM_SEED
from expense_tracker.features.feature_engineering import extract_ground_truth_labels
from expense_tracker.models.anomaly_detection import (
    detect_anomalies_isolation_forest,
    detect_outliers_statistical,
    evaluate_anomaly_detection,
    evaluate_anomaly_detection_out_of_sample,
    get_anomaly_records,
    train_isolation_forest,
)


@pytest.fixture
def synthetic_transactions_sample() -> pd.DataFrame:
    """Fixture providing a deterministic small dataset with known normal and unusual records."""
    np.random.seed(RANDOM_SEED)
    dates = pd.date_range("2026-01-01", periods=100, freq="D").strftime("%Y-%m-%d").tolist()

    records = []
    for i, d in enumerate(dates):
        # 3 deliberately injected acute shocks
        if i in (10, 45, 80):
            amt = 85000.0 + i * 100
            desc = f"[UNUSUAL] Emergency medical payment {i}"
            cat = "Healthcare"
        else:
            amt = float(np.random.uniform(200.0, 3000.0))
            desc = f"Routine grocery supermarket run {i}"
            cat = "Groceries"

        records.append({
            "transaction_id": f"TXN-{i:04d}",
            "date": d,
            "type": "Expense",
            "category": cat,
            "amount": round(amt, 2),
            "payment_method": "UPI",
            "description": desc,
        })

    return pd.DataFrame(records)


# ==============================================================================
# 1. Statistical Baseline Tests (IQR & Z-score)
# ==============================================================================


def test_detect_outliers_statistical_iqr(synthetic_transactions_sample: pd.DataFrame) -> None:
    """Verify IQR statistical method correctly flags extreme upper-tail spending spikes."""
    outliers = detect_outliers_statistical(
        synthetic_transactions_sample,
        method="iqr",
        threshold=1.5,
        column="amount",
    )
    assert isinstance(outliers, pd.Series)
    assert len(outliers) == len(synthetic_transactions_sample)
    assert outliers.dtype == bool

    # The 3 acute spikes (index 10, 45, 80) must be flagged
    assert outliers.iloc[10] == True
    assert outliers.iloc[45] == True
    assert outliers.iloc[80] == True


def test_detect_outliers_statistical_zscore(synthetic_transactions_sample: pd.DataFrame) -> None:
    """Verify Z-score method flags spending spikes exceeding 3 standard deviations."""
    outliers = detect_outliers_statistical(
        synthetic_transactions_sample,
        method="zscore",
        threshold=3.0,
        column="amount",
    )
    assert isinstance(outliers, pd.Series)
    assert outliers.dtype == bool
    # Spikes of 85k on a series with mean ~5k must exceed 3 sigma
    assert outliers.iloc[10] == True
    assert outliers.iloc[45] == True
    assert outliers.iloc[80] == True


def test_detect_outliers_statistical_empty_and_edge_cases() -> None:
    """Verify statistical outlier detector handles empty or single-value datasets gracefully."""
    empty_df = pd.DataFrame(columns=["amount"])
    assert detect_outliers_statistical(empty_df).empty

    # Single value series (zero variance)
    single_val_df = pd.DataFrame({"amount": [500.0, 500.0, 500.0]})
    res = detect_outliers_statistical(single_val_df)
    assert not res.any()


def test_detect_outliers_statistical_invalid_method() -> None:
    """Verify ValueError is raised when an unsupported outlier method is specified."""
    df = pd.DataFrame({"amount": [10.0, 20.0, 30.0, 40.0, 50.0]})
    with pytest.raises(ValueError, match="Unsupported outlier detection method"):
        detect_outliers_statistical(df, method="invalid_method")


# ==============================================================================
# 2. Isolation Forest Anomaly Detection Tests
# ==============================================================================


def test_detect_anomalies_isolation_forest_execution(synthetic_transactions_sample: pd.DataFrame) -> None:
    """Verify Isolation Forest executes cleanly and outputs valid boolean flags and scores."""
    is_anomaly, scores = detect_anomalies_isolation_forest(
        synthetic_transactions_sample,
        contamination=0.03,
        random_state=42,
    )
    assert isinstance(is_anomaly, pd.Series)
    assert isinstance(scores, pd.Series)
    assert len(is_anomaly) == len(synthetic_transactions_sample)
    assert len(scores) == len(synthetic_transactions_sample)
    assert is_anomaly.dtype == bool
    assert pd.api.types.is_float_dtype(scores)

    # With contamination=0.03 on 100 records, exactly ~3 anomalies should be flagged
    assert 2 <= is_anomaly.sum() <= 4


def test_detect_anomalies_isolation_forest_reproducibility(synthetic_transactions_sample: pd.DataFrame) -> None:
    """Verify deterministic output with identical random_state seed."""
    flags1, scores1 = detect_anomalies_isolation_forest(
        synthetic_transactions_sample,
        contamination=0.02,
        random_state=42,
    )
    flags2, scores2 = detect_anomalies_isolation_forest(
        synthetic_transactions_sample,
        contamination=0.02,
        random_state=42,
    )
    pd.testing.assert_series_equal(flags1, flags2)
    pd.testing.assert_series_equal(scores1, scores2)


def test_detect_anomalies_isolation_forest_marker_invariance(synthetic_transactions_sample: pd.DataFrame) -> None:
    """Verify model predictions and scores are strictly invariant to the synthetic '[UNUSUAL]' text marker.

    Proves target leakage prevention: presence or absence of '[UNUSUAL]' in descriptions
    does not alter numeric modeling features or Isolation Forest scores.
    """
    df_with_markers = synthetic_transactions_sample.copy()

    # Create twin dataset where '[UNUSUAL]' is completely removed from all descriptions
    df_without_markers = synthetic_transactions_sample.copy()
    df_without_markers["description"] = (
        df_without_markers["description"].str.replace(r"\[UNUSUAL\]\s*", "", regex=True)
    )

    flags_a, scores_a = detect_anomalies_isolation_forest(
        df_with_markers,
        contamination=0.03,
        random_state=42,
    )
    flags_b, scores_b = detect_anomalies_isolation_forest(
        df_without_markers,
        contamination=0.03,
        random_state=42,
    )

    pd.testing.assert_series_equal(flags_a, flags_b)
    pd.testing.assert_series_equal(scores_a, scores_b)


def test_detect_anomalies_empty_dataframe() -> None:
    """Verify Isolation Forest returns empty Series when passed an empty DataFrame."""
    empty_df = pd.DataFrame(columns=["date", "type", "category", "amount", "payment_method", "description"])
    flags, scores = detect_anomalies_isolation_forest(empty_df)
    assert flags.empty
    assert scores.empty


# ==============================================================================
# 3. Anomaly Records Extraction and Masking Tests
# ==============================================================================


def test_get_anomaly_records_masks_unusual_marker(synthetic_transactions_sample: pd.DataFrame) -> None:
    """Verify get_anomaly_records extracts flagged records and masks synthetic [UNUSUAL] markers."""
    is_anomaly, scores = detect_anomalies_isolation_forest(
        synthetic_transactions_sample,
        contamination=0.03,
        random_state=42,
    )
    records = get_anomaly_records(synthetic_transactions_sample, is_anomaly, scores)

    assert isinstance(records, pd.DataFrame)
    assert len(records) == is_anomaly.sum()
    assert "anomaly_score" in records.columns
    assert "display_description" in records.columns

    # Verify no description in display_description contains '[UNUSUAL]'
    unusual_present = records["display_description"].str.contains(r"\[UNUSUAL\]", regex=True)
    assert unusual_present.sum() == 0


def test_get_anomaly_records_empty() -> None:
    """Verify get_anomaly_records returns empty DataFrame with schema when no anomalies flagged."""
    df = pd.DataFrame({
        "transaction_id": ["TXN-01"],
        "date": ["2026-01-01"],
        "type": ["Expense"],
        "category": ["Dining"],
        "amount": [100.0],
    })
    no_anomalies = pd.Series([False], index=df.index)
    res = get_anomaly_records(df, no_anomalies)
    assert res.empty


# ==============================================================================
# 4. Anomaly Evaluation Metrics Tests
# ==============================================================================


def test_evaluate_anomaly_detection_metrics() -> None:
    """Verify precision, recall, f1_score, and confusion matrix calculations."""
    y_true = pd.Series([1, 1, 0, 0, 0, 0, 1, 0, 0, 0])
    y_pred = pd.Series([1, 0, 0, 0, 0, 1, 1, 0, 0, 0])

    # TP = 2 (indices 0, 6)
    # FN = 1 (index 1)
    # FP = 1 (index 5)
    # TN = 6
    metrics = evaluate_anomaly_detection(y_true, y_pred)

    assert metrics["ground_truth_count"] == 3
    assert metrics["predicted_count"] == 3
    assert metrics["total_samples"] == 10

    cm = metrics["confusion_matrix"]
    assert cm["tp"] == 2
    assert cm["fn"] == 1
    assert cm["fp"] == 1
    assert cm["tn"] == 6

    # Precision = TP / (TP + FP) = 2 / 3 = 0.6667
    assert metrics["precision"] == round(2 / 3, 4)
    # Recall = TP / (TP + FN) = 2 / 3 = 0.6667
    assert metrics["recall"] == round(2 / 3, 4)
    # F1 = 2 * P * R / (P + R) = 0.6667
    assert metrics["f1_score"] == round(2 / 3, 4)


def test_evaluate_anomaly_detection_empty_input() -> None:
    """Verify evaluation handles empty inputs safely without zero-division errors."""
    metrics = evaluate_anomaly_detection([], [])
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["f1_score"] == 0.0
    assert metrics["total_samples"] == 0


def test_evaluate_anomaly_detection_out_of_sample(synthetic_transactions_sample: pd.DataFrame) -> None:
    """Verify out-of-sample inductive hold-out evaluation partitions data chronologically."""
    res = evaluate_anomaly_detection_out_of_sample(
        synthetic_transactions_sample,
        test_size=0.2,
        contamination=0.03,
        random_state=42,
    )

    assert "precision" in res
    assert "recall" in res
    assert "f1_score" in res
    assert "confusion_matrix" in res
    assert res["train_samples"] == 80
    assert res["test_samples"] == 20
    assert res["train_ground_truth_count"] + res["test_ground_truth_count"] == 3


def test_anomaly_feature_matrix_leakage_safeguard(synthetic_transactions_sample: pd.DataFrame) -> None:
    """Verify strictly no target labels, descriptions, or proxy text lengths enter feature matrix."""
    from expense_tracker.features.feature_engineering import engineer_features, get_model_feature_matrix

    enriched = engineer_features(synthetic_transactions_sample, include_categorical_encoding=True)
    matrix = get_model_feature_matrix(enriched, include_categorical_dummies=True, drop_na_rows=False)

    forbidden_cols = [
        "is_unusual_ground_truth",
        "description",
        "transaction_id",
        "desc_char_length",
        "desc_word_count",
    ]
    for col in forbidden_cols:
        assert col not in matrix.columns, f"Target leakage detected! '{col}' is present in modeling matrix."


def test_zscore_univariate_vs_isolation_forest_multivariate_rationale() -> None:
    """Verify that univariate Z-score isolates synthetic amount shocks while IF evaluates 42 dims."""
    from dashboard.data_processing import load_dashboard_data
    df = load_dashboard_data("data/sample/transactions.csv")
    y_true = extract_ground_truth_labels(df)

    # 1. Univariate Z-Score on amount achieves 100% recall on the synthetic amount shocks
    z_outliers = detect_outliers_statistical(df, method="zscore", threshold=3.0, column="amount")
    z_eval = evaluate_anomaly_detection(y_true, z_outliers)
    assert z_eval["recall"] == 1.0, "Expected Z-score to achieve 100% recall on synthetic amount shocks."

    # 2. Isolation Forest at standard contamination=0.02 operates on 42 features
    is_anomaly, _ = detect_anomalies_isolation_forest(df, contamination=0.02, random_state=42)
    if_eval = evaluate_anomaly_detection(y_true, is_anomaly)

    # Document honest outcome: IF has lower precision/recall against univariate amount shocks
    assert if_eval["precision"] < 0.10, "Expected low precision when benchmarking 42D model against 1D shock."
    assert if_eval["confusion_matrix"]["fp"] > 50, "Expected multi-dimensional outliers flagged as false positives."
