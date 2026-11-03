"""
Unit Tests for Feature Engineering Module

Author: Akash Das
Description: Comprehensive unit tests for calendar features, flow indicators, amount transformations,
             temporal sequence/rolling window metrics, categorical encodings, text features,
             and target leakage prevention.
"""

import math
import numpy as np
import pandas as pd
import pytest

from expense_tracker.features.feature_engineering import (
    CANONICAL_CATEGORIES,
    CANONICAL_PAYMENT_METHODS,
    encode_categorical_features,
    engineer_features,
    extract_amount_features,
    extract_calendar_features,
    extract_flow_indicators,
    extract_ground_truth_labels,
    extract_temporal_features,
    extract_temporal_sequence_features,
    extract_text_features,
    get_model_feature_matrix,
)


@pytest.fixture
def sample_transactions_df():
    """Return a clean, representative DataFrame of transactions."""
    return pd.DataFrame([
        {
            "transaction_id": "TXN-001",
            "date": "2024-02-29",  # Thursday, leap year
            "type": "Income",
            "category": "Salary",
            "amount": 75000.0,
            "payment_method": "Bank Transfer",
            "description": "Monthly Payroll Transfer",
        },
        {
            "transaction_id": "TXN-002",
            "date": "2024-03-01",  # Friday
            "type": "Expense",
            "category": "Rent",
            "amount": 15000.0,
            "payment_method": "Bank Transfer",
            "description": "Apartment Maintenance and Rent",
        },
        {
            "transaction_id": "TXN-003",
            "date": "2024-03-02",  # Saturday (weekend)
            "type": "Expense",
            "category": "Groceries",
            "amount": 1200.0,
            "payment_method": "UPI",
            "description": "Weekly grocery shopping",
        },
        {
            "transaction_id": "TXN-004",
            "date": "2024-03-03",  # Sunday (weekend)
            "type": "Expense",
            "category": "Entertainment",
            "amount": 2500.0,
            "payment_method": "Credit Card",
            "description": "Movie tickets and snacks",
        },
        {
            "transaction_id": "TXN-005",
            "date": "2024-03-10",  # Sunday (weekend)
            "type": "Expense",
            "category": "Healthcare",
            "amount": 45000.0,
            "payment_method": "Credit Card",
            "description": "Emergency surgery [UNUSUAL] shock",
        },
    ])


# -----------------------------------------------------------------------------
# 1. Calendar / Temporal Feature Extraction Tests
# -----------------------------------------------------------------------------

def test_extract_calendar_features_values(sample_transactions_df):
    """Verify exact values and types for extracted calendar features."""
    enriched = extract_calendar_features(sample_transactions_df)

    # Check Thursday leap year row (2024-02-29)
    row0 = enriched.iloc[0]
    assert row0["year"] == 2024
    assert row0["month"] == 2
    assert row0["month_name"] == "February"
    assert row0["quarter"] == 1
    assert row0["day_of_month"] == 29
    assert row0["day_of_week"] == 3  # Thursday (Monday=0)
    assert row0["day_name"] == "Thursday"
    assert row0["is_weekend"] == 0

    # Check Saturday row (2024-03-02)
    row2 = enriched.iloc[2]
    assert row2["month"] == 3
    assert row2["day_of_month"] == 2
    assert row2["day_of_week"] == 5  # Saturday
    assert row2["day_name"] == "Saturday"
    assert row2["is_weekend"] == 1

    # Check Sunday row (2024-03-03)
    row3 = enriched.iloc[3]
    assert row3["day_of_week"] == 6  # Sunday
    assert row3["day_name"] == "Sunday"
    assert row3["is_weekend"] == 1


def test_extract_temporal_features_alias(sample_transactions_df):
    """Verify extract_temporal_features functions as a backward-compatible alias."""
    res_alias = extract_temporal_features(sample_transactions_df)
    res_calendar = extract_calendar_features(sample_transactions_df)
    pd.testing.assert_frame_equal(res_alias, res_calendar)


def test_extract_calendar_features_empty_df():
    """Verify empty DataFrame returns empty DataFrame with expected calendar columns."""
    df_empty = pd.DataFrame(columns=["transaction_id", "date", "amount"])
    result = extract_calendar_features(df_empty)
    assert len(result) == 0
    expected_cols = ["year", "month", "month_name", "quarter", "day_of_month", "day_of_week", "day_name", "is_weekend"]
    for col in expected_cols:
        assert col in result.columns


def test_extract_calendar_features_invalid_date():
    """Verify ValueError is raised on invalid date string."""
    bad_df = pd.DataFrame([{"date": "not-a-date", "amount": 100.0}])
    with pytest.raises(ValueError, match="invalid or unparseable date"):
        extract_calendar_features(bad_df)


def test_extract_calendar_features_missing_column():
    """Verify ValueError is raised when date column is absent."""
    df_no_date = pd.DataFrame([{"amount": 100.0}])
    with pytest.raises(ValueError, match="not found in DataFrame"):
        extract_calendar_features(df_no_date)


def test_extract_calendar_features_non_dataframe():
    """Verify TypeError is raised when input is not a DataFrame."""
    with pytest.raises(TypeError, match="Expected pandas DataFrame"):
        extract_calendar_features([{"date": "2024-01-01"}])


# -----------------------------------------------------------------------------
# 2. Flow Indicator Extraction Tests
# -----------------------------------------------------------------------------

def test_extract_flow_indicators(sample_transactions_df):
    """Verify is_income and is_expense binary indicators."""
    res = extract_flow_indicators(sample_transactions_df)
    assert res.loc[0, "is_income"] == 1
    assert res.loc[0, "is_expense"] == 0

    assert res.loc[1, "is_income"] == 0
    assert res.loc[1, "is_expense"] == 1


def test_extract_flow_indicators_empty_df():
    """Verify empty DataFrame handling for flow indicators."""
    empty_df = pd.DataFrame(columns=["type"])
    res = extract_flow_indicators(empty_df)
    assert len(res) == 0
    assert "is_income" in res.columns
    assert "is_expense" in res.columns


def test_extract_flow_indicators_missing_col():
    """Verify ValueError when type column is absent."""
    df_no_type = pd.DataFrame([{"amount": 100.0}])
    with pytest.raises(ValueError, match="not found in DataFrame"):
        extract_flow_indicators(df_no_type)


# -----------------------------------------------------------------------------
# 3. Amount Transformation Tests
# -----------------------------------------------------------------------------

def test_extract_amount_features_log(sample_transactions_df):
    """Verify log_amount produces np.log1p(amount)."""
    res = extract_amount_features(sample_transactions_df)
    assert "log_amount" in res.columns
    for idx, row in sample_transactions_df.iterrows():
        expected_log = round(float(np.log1p(row["amount"])), 4)
        assert abs(res.loc[idx, "log_amount"] - expected_log) < 1e-4


def test_extract_amount_features_negative_or_zero_rejected():
    """Verify non-positive amounts raise ValueError."""
    bad_zero = pd.DataFrame([{"amount": 0.0}])
    with pytest.raises(ValueError, match="non-positive"):
        extract_amount_features(bad_zero)

    bad_neg = pd.DataFrame([{"amount": -50.0}])
    with pytest.raises(ValueError, match="non-positive"):
        extract_amount_features(bad_neg)


def test_extract_amount_features_non_numeric_rejected():
    """Verify non-numeric amounts raise ValueError."""
    bad_str = pd.DataFrame([{"amount": "abc"}])
    with pytest.raises(ValueError, match="non-positive"):
        extract_amount_features(bad_str)


# -----------------------------------------------------------------------------
# 4. Temporal Sequence and Rolling Window Tests
# -----------------------------------------------------------------------------

def test_extract_temporal_sequence_features_lags(sample_transactions_df):
    """Verify lag and delta calculations in chronological order."""
    res = extract_temporal_sequence_features(sample_transactions_df)

    # First transaction (TXN-001, 2024-02-29): lags should be NaN
    assert math.isnan(res.loc[0, "days_since_prev_txn"])
    assert math.isnan(res.loc[0, "prev_amount"])

    # Second transaction (TXN-002, 2024-03-01): 1 day difference, prev amount = 75000.0
    assert res.loc[1, "days_since_prev_txn"] == 1.0
    assert res.loc[1, "prev_amount"] == 75000.0

    # Third transaction (TXN-003, 2024-03-02): 1 day difference, prev amount = 15000.0
    assert res.loc[2, "days_since_prev_txn"] == 1.0
    assert res.loc[2, "prev_amount"] == 15000.0


def test_extract_temporal_sequence_features_expense_isolation(sample_transactions_df):
    """Verify expense rolling and lag features are isolated from income."""
    res = extract_temporal_sequence_features(sample_transactions_df)

    # Row 0 is Income: all expense-specific features must be NaN
    assert math.isnan(res.loc[0, "days_since_prev_expense"])
    assert math.isnan(res.loc[0, "prev_expense_amount"])
    assert math.isnan(res.loc[0, "rolling_expense_7d_sum"])
    assert math.isnan(res.loc[0, "rolling_expense_30d_sum"])

    # Row 1 is the first Expense (2024-03-01): previous expense lags must be NaN
    assert math.isnan(res.loc[1, "days_since_prev_expense"])
    assert math.isnan(res.loc[1, "prev_expense_amount"])

    # Row 2 is second Expense (2024-03-02): days_since_prev_expense=1.0, prev_expense_amount=15000.0
    assert res.loc[2, "days_since_prev_expense"] == 1.0
    assert res.loc[2, "prev_expense_amount"] == 15000.0


def test_temporal_rolling_windows_no_future_leakage(sample_transactions_df):
    """Verify rolling statistics strictly exclude the current transaction (closed='left')."""
    res = extract_temporal_sequence_features(sample_transactions_df)

    # Row 1: First expense on 2024-03-01. Prior 7-day window has NO prior expenses.
    # Without prior observations, rolling statistics are NaN (absent history preserved).
    assert math.isnan(res.loc[1, "rolling_expense_7d_sum"])
    assert math.isnan(res.loc[1, "rolling_expense_7d_count"])
    assert math.isnan(res.loc[1, "rolling_expense_7d_mean"])

    # Row 2: Expense on 2024-03-02 (amount 1200.0).
    # Prior 7-day window contains only Row 1 (15000.0).
    # Current row amount (1200.0) MUST NOT be included!
    assert res.loc[2, "rolling_expense_7d_sum"] == 15000.0
    assert res.loc[2, "rolling_expense_7d_count"] == 1
    assert res.loc[2, "rolling_expense_7d_mean"] == 15000.0

    # Row 3: Expense on 2024-03-03 (amount 2500.0).
    # Prior 7-day window contains Row 1 (15000.0) + Row 2 (1200.0) = 16200.0.
    assert res.loc[3, "rolling_expense_7d_sum"] == 16200.0
    assert res.loc[3, "rolling_expense_7d_count"] == 2
    assert res.loc[3, "rolling_expense_7d_mean"] == 8100.0

    # Row 4: Expense on 2024-03-10 (amount 45000.0).
    # 7-day window strictly prior to 2024-03-10 (i.e. [2024-03-03, 2024-03-10)):
    # Row 1 (03-01) is 9 days prior -> outside 7D window!
    # Row 2 (03-02) is 8 days prior -> outside 7D window!
    # Row 3 (03-03) is 7 days prior -> inside [2024-03-03, 2024-03-10) window!
    assert res.loc[4, "rolling_expense_7d_sum"] == 2500.0
    assert res.loc[4, "rolling_expense_7d_count"] == 1

    # But for 30-day window, Row 1 (15000.0), Row 2 (1200.0), Row 3 (2500.0) are all included = 18700.0!
    assert res.loc[4, "rolling_expense_30d_sum"] == 18700.0
    assert res.loc[4, "rolling_expense_30d_count"] == 3


def test_temporal_sequence_preserves_caller_order():
    """Verify original row ordering is restored when restore_order=True."""
    shuffled_df = pd.DataFrame([
        {"transaction_id": "T3", "date": "2024-03-03", "amount": 10.0, "type": "Expense"},
        {"transaction_id": "T1", "date": "2024-03-01", "amount": 20.0, "type": "Expense"},
        {"transaction_id": "T2", "date": "2024-03-02", "amount": 30.0, "type": "Expense"},
    ])

    res = extract_temporal_sequence_features(shuffled_df, restore_order=True)
    assert list(res["transaction_id"]) == ["T3", "T1", "T2"]

    # Even though row 0 was T3 in original order, its chronological lag must reflect T2!
    assert res.loc[0, "prev_amount"] == 30.0


# -----------------------------------------------------------------------------
# 5. Categorical Encoding Tests
# -----------------------------------------------------------------------------

def test_encode_categorical_features_canonical(sample_transactions_df):
    """Verify canonical category and payment method dummy columns."""
    encoded = encode_categorical_features(sample_transactions_df)

    # 17 category dummies + 5 payment dummies = 22 dummy columns
    cat_cols = [c for c in encoded.columns if c.startswith("cat_")]
    pay_cols = [c for c in encoded.columns if c.startswith("pay_")]

    assert len(cat_cols) == 17
    assert len(pay_cols) == 5

    # Check Salary row
    assert encoded.loc[0, "cat_salary"] == 1
    assert encoded.loc[0, "cat_rent"] == 0
    assert encoded.loc[0, "pay_bank_transfer"] == 1
    assert encoded.loc[0, "pay_upi"] == 0

    # Original columns must be preserved
    assert "category" in encoded.columns
    assert "payment_method" in encoded.columns


def test_encode_categorical_features_unseen_values():
    """Verify unseen categories and payment methods result in all zero dummies."""
    df_unseen = pd.DataFrame([
        {
            "category": "Cryptocurrency",
            "payment_method": "Gold Coins",
        }
    ])
    encoded = encode_categorical_features(df_unseen)
    cat_cols = [c for c in encoded.columns if c.startswith("cat_")]
    pay_cols = [c for c in encoded.columns if c.startswith("pay_")]

    assert (encoded[cat_cols] == 0).all().all()
    assert (encoded[pay_cols] == 0).all().all()


# -----------------------------------------------------------------------------
# 6. Text Metadata and Ground Truth Extraction Tests
# -----------------------------------------------------------------------------

def test_extract_text_features(sample_transactions_df):
    """Verify character length and word count calculations."""
    res = extract_text_features(sample_transactions_df)
    assert "desc_char_length" in res.columns
    assert "desc_word_count" in res.columns

    # "Monthly Payroll Transfer" -> 24 chars, 3 words
    assert res.loc[0, "desc_char_length"] == len("Monthly Payroll Transfer")
    assert res.loc[0, "desc_word_count"] == 3


def test_extract_ground_truth_labels(sample_transactions_df):
    """Verify [UNUSUAL] marker extraction as evaluation ground-truth label."""
    labels = extract_ground_truth_labels(sample_transactions_df)
    assert labels.tolist() == [0, 0, 0, 0, 1]


# -----------------------------------------------------------------------------
# 7. End-to-End Pipeline and Immutability Tests
# -----------------------------------------------------------------------------

def test_engineer_features_immutability(sample_transactions_df):
    """Verify input DataFrame is not mutated by engineer_features."""
    original_copy = sample_transactions_df.copy(deep=True)
    _ = engineer_features(sample_transactions_df, include_categorical_encoding=True)

    pd.testing.assert_frame_equal(sample_transactions_df, original_copy)


def test_engineer_features_output_shape(sample_transactions_df):
    """Verify column counts with and without categorical encodings."""
    # Base mode: 7 original + 8 calendar + 2 flow + 1 amount + 10 temporal sequence + 2 text = 30 columns
    res_base = engineer_features(sample_transactions_df, include_categorical_encoding=False)
    assert res_base.shape == (5, 30)

    # Full mode: 30 + 17 category + 5 payment = 52 columns
    res_full = engineer_features(sample_transactions_df, include_categorical_encoding=True)
    assert res_full.shape == (5, 52)


def test_engineer_features_empty_dataframe():
    """Verify empty DataFrame processed without error and returns matching empty schema."""
    empty_df = pd.DataFrame(columns=[
        "transaction_id", "date", "type", "category", "amount", "payment_method", "description"
    ])
    res = engineer_features(empty_df, include_categorical_encoding=True)
    assert len(res) == 0
    assert res.shape[1] == 52


# -----------------------------------------------------------------------------
# 8. Target Leakage Prevention and Modeling Matrix Tests
# -----------------------------------------------------------------------------

def test_get_model_feature_matrix_leakage_prevention(sample_transactions_df):
    """Verify modeling matrix strictly removes raw text, IDs, dates, and ground truth."""
    enriched = engineer_features(sample_transactions_df, include_categorical_encoding=True)
    enriched["is_unusual_ground_truth"] = extract_ground_truth_labels(sample_transactions_df)

    matrix = get_model_feature_matrix(enriched, include_categorical_dummies=True)

    banned = [
        "transaction_id",
        "description",
        "date",
        "type",
        "category",
        "payment_method",
        "month_name",
        "day_name",
        "desc_char_length",
        "desc_word_count",
        "is_unusual_ground_truth",
        "is_unusual",
        "unusual",
        "ground_truth",
    ]

    for col in banned:
        assert col not in matrix.columns, f"Banned column '{col}' leaked into feature matrix!"

    # Ensure all remaining columns are numeric
    for col in matrix.columns:
        assert pd.api.types.is_numeric_dtype(matrix[col]), f"Column '{col}' is not numeric!"

    # Model matrix must have exactly 42 numeric features
    assert matrix.shape == (5, 42)


def test_marker_invariance_leakage_regression(sample_transactions_df):
    """Direct leakage regression test: adding [UNUSUAL] marker must not alter model feature matrix.

    This test constructs two identical datasets where one transaction's description is modified
    to add the [UNUSUAL] shock marker. The resulting model feature matrices must be 100% identical.
    """
    df_a = sample_transactions_df.copy(deep=True)
    df_b = sample_transactions_df.copy(deep=True)

    # In df_a, ensure no unusual marker on row 3
    df_a.loc[3, "description"] = "Movie tickets and snacks"
    # In df_b, add the deliberate shock marker to row 3
    df_b.loc[3, "description"] = "Movie tickets and snacks [UNUSUAL] shock"

    # Enriched datasets retain text features and descriptions for audit/EDA
    enriched_a = engineer_features(df_a, include_categorical_encoding=True)
    enriched_b = engineer_features(df_b, include_categorical_encoding=True)

    enriched_a["is_unusual_ground_truth"] = extract_ground_truth_labels(df_a)
    enriched_b["is_unusual_ground_truth"] = extract_ground_truth_labels(df_b)

    # Text features differ in enriched representations
    assert enriched_a.loc[3, "desc_char_length"] != enriched_b.loc[3, "desc_char_length"]
    assert enriched_a.loc[3, "desc_word_count"] != enriched_b.loc[3, "desc_word_count"]
    assert enriched_a.loc[3, "is_unusual_ground_truth"] == 0
    assert enriched_b.loc[3, "is_unusual_ground_truth"] == 1

    # Extract modeling matrices
    matrix_a = get_model_feature_matrix(enriched_a, include_categorical_dummies=True)
    matrix_b = get_model_feature_matrix(enriched_b, include_categorical_dummies=True)

    # Model feature matrices MUST be strictly identical
    pd.testing.assert_frame_equal(matrix_a, matrix_b)

    # Explicitly assert banned columns are completely absent
    for col in [
        "description",
        "desc_char_length",
        "desc_word_count",
        "is_unusual_ground_truth",
        "transaction_id",
    ]:
        assert col not in matrix_a.columns, f"'{col}' leaked into matrix_a!"
        assert col not in matrix_b.columns, f"'{col}' leaked into matrix_b!"


def test_same_day_rolling_window_semantics():
    """Verify rolling calculations strictly exclude current date, isolate expenses, and attach to all date transactions."""
    data = [
        {"transaction_id": "TXN-01", "date": "2026-03-01", "type": "Income", "category": "Salary", "amount": 100000.0, "payment_method": "Bank Transfer", "description": "Salary"},
        {"transaction_id": "TXN-02", "date": "2026-03-01", "type": "Expense", "category": "Groceries", "amount": 1000.0, "payment_method": "UPI", "description": "Groceries 1"},
        {"transaction_id": "TXN-03", "date": "2026-03-01", "type": "Expense", "category": "Dining", "amount": 2000.0, "payment_method": "UPI", "description": "Dinner"},
        {"transaction_id": "TXN-04", "date": "2026-03-02", "type": "Income", "category": "Freelance", "amount": 5000.0, "payment_method": "Bank Transfer", "description": "Gig"},
        {"transaction_id": "TXN-05", "date": "2026-03-02", "type": "Expense", "category": "Groceries", "amount": 500.0, "payment_method": "UPI", "description": "Groceries 2"},
        {"transaction_id": "TXN-06", "date": "2026-03-02", "type": "Expense", "category": "Transport", "amount": 700.0, "payment_method": "UPI", "description": "Uber"},
        {"transaction_id": "TXN-07", "date": "2026-03-02", "type": "Expense", "category": "Entertainment", "amount": 300.0, "payment_method": "UPI", "description": "Movie"},
        {"transaction_id": "TXN-08", "date": "2026-03-03", "type": "Expense", "category": "Utilities", "amount": 1500.0, "payment_method": "UPI", "description": "Power"},
    ]
    df = pd.DataFrame(data)
    res = extract_temporal_sequence_features(df)

    # 1. Day 1 Transactions (TXN-01, TXN-02, TXN-03): closed='left' means no prior history exists -> NaN
    for idx in [0, 1, 2]:
        assert math.isnan(res.loc[idx, "rolling_expense_7d_sum"])
        assert math.isnan(res.loc[idx, "rolling_expense_7d_mean"])
        assert math.isnan(res.loc[idx, "rolling_expense_7d_count"])
        assert math.isnan(res.loc[idx, "rolling_expense_30d_sum"])

    # 2. Day 2 Transactions (Income TXN-04, Expenses TXN-05, TXN-06, TXN-07):
    # Historical 7-day window [2026-03-02 - 7D, 2026-03-02) strictly includes Day 1 expenses (1000 + 2000 = 3000)
    # Income TXN-01 (100,000) and TXN-04 (5,000) MUST NOT contribute to expense sums/counts.
    # Every transaction on Day 2 (INCLUDING Income TXN-04) receives the same historical baseline (3000, 2, 1500).
    for idx in [3, 4, 5, 6]:
        assert res.loc[idx, "rolling_expense_7d_sum"] == 3000.0
        assert res.loc[idx, "rolling_expense_7d_count"] == 2.0
        assert res.loc[idx, "rolling_expense_7d_mean"] == 1500.0
        assert res.loc[idx, "rolling_expense_30d_sum"] == 3000.0
        assert res.loc[idx, "rolling_expense_30d_count"] == 2.0
        assert res.loc[idx, "rolling_expense_30d_mean"] == 1500.0

    # 3. Day 3 Expense (TXN-08):
    # Prior window includes Day 1 (1000 + 2000) + Day 2 (500 + 700 + 300) = 4500.0 across 5 transactions
    assert res.loc[7, "rolling_expense_7d_sum"] == 4500.0
    assert res.loc[7, "rolling_expense_7d_count"] == 5.0
    assert res.loc[7, "rolling_expense_7d_mean"] == 900.0


def test_rolling_expense_features_multiday_scenario():
    """Verify multi-day rolling scenario with same-day income/expenses, order invariance, and future invariance.

    Scenario:
    - March 1: Expense ₹1,000 and Expense ₹2,000
    - March 2: Income ₹5,000 and Expense ₹500 and Expense ₹700
    - March 3: Income ₹8,000 and Expense ₹1,500
    """
    scenario_data = [
        {"transaction_id": "T1", "date": "2026-03-01", "type": "Expense", "category": "Groceries", "amount": 1000.0, "payment_method": "UPI", "description": "Groceries 1"},
        {"transaction_id": "T2", "date": "2026-03-01", "type": "Expense", "category": "Dining", "amount": 2000.0, "payment_method": "UPI", "description": "Dinner"},
        {"transaction_id": "T3", "date": "2026-03-02", "type": "Income", "category": "Freelance", "amount": 5000.0, "payment_method": "Bank Transfer", "description": "Gig"},
        {"transaction_id": "T4", "date": "2026-03-02", "type": "Expense", "category": "Groceries", "amount": 500.0, "payment_method": "UPI", "description": "Groceries 2"},
        {"transaction_id": "T5", "date": "2026-03-02", "type": "Expense", "category": "Transport", "amount": 700.0, "payment_method": "UPI", "description": "Uber"},
        {"transaction_id": "T6", "date": "2026-03-03", "type": "Income", "category": "Business Income", "amount": 8000.0, "payment_method": "Bank Transfer", "description": "Contract"},
        {"transaction_id": "T7", "date": "2026-03-03", "type": "Expense", "category": "Utilities", "amount": 1500.0, "payment_method": "UPI", "description": "Power"},
    ]
    df = pd.DataFrame(scenario_data)
    res = extract_temporal_sequence_features(df)

    # 1. March 1: No prior expense history -> NaN sum, mean, count for all transactions
    m1 = res[res["date"] == "2026-03-01"]
    assert len(m1) == 2
    assert m1["rolling_expense_7d_sum"].isna().all()
    assert m1["rolling_expense_7d_mean"].isna().all()
    assert m1["rolling_expense_7d_count"].isna().all()

    # 2. March 2: Every transaction, including income, receives sum ₹3,000, mean ₹1,500, count 2
    m2 = res[res["date"] == "2026-03-02"]
    assert len(m2) == 3
    assert (m2["rolling_expense_7d_sum"] == 3000.0).all()
    assert (m2["rolling_expense_7d_mean"] == 1500.0).all()
    assert (m2["rolling_expense_7d_count"] == 2.0).all()

    # 3. March 3: Every transaction, including income, receives sum ₹4,200, mean ₹1,050, count 4
    # Income ₹5,000 on March 2 NEVER enters expense sum (which is 1000 + 2000 + 500 + 700 = 4200)
    m3 = res[res["date"] == "2026-03-03"]
    assert len(m3) == 2
    assert (m3["rolling_expense_7d_sum"] == 4200.0).all()
    assert (m3["rolling_expense_7d_mean"] == 1050.0).all()
    assert (m3["rolling_expense_7d_count"] == 4.0).all()

    # 4. Same-day transactions have identical rolling values
    for d in ["2026-03-01", "2026-03-02", "2026-03-03"]:
        sub = res[res["date"] == d]
        assert sub["rolling_expense_7d_sum"].nunique(dropna=False) == 1
        assert sub["rolling_expense_7d_mean"].nunique(dropna=False) == 1
        assert sub["rolling_expense_7d_count"].nunique(dropna=False) == 1

    # 5. Shuffling input rows does not change date-level rolling values
    df_shuffled = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    res_shuffled = extract_temporal_sequence_features(df_shuffled, restore_order=True)

    for tid in df["transaction_id"]:
        val_orig = res[res["transaction_id"] == tid]["rolling_expense_7d_sum"].values[0]
        val_shuf = res_shuffled[res_shuffled["transaction_id"] == tid]["rolling_expense_7d_sum"].values[0]
        if math.isnan(val_orig):
            assert math.isnan(val_shuf)
        else:
            assert val_orig == val_shuf

    # 6. Future transactions cannot change earlier historical features
    extended_data = scenario_data + [
        {"transaction_id": "T8", "date": "2026-03-04", "type": "Expense", "category": "Travel", "amount": 25000.0, "payment_method": "Credit Card", "description": "Flight"}
    ]
    df_ext = pd.DataFrame(extended_data)
    res_ext = extract_temporal_sequence_features(df_ext)

    # Values for T1..T7 must be completely unchanged by adding T8
    for col in ["rolling_expense_7d_sum", "rolling_expense_7d_mean", "rolling_expense_7d_count"]:
        pd.testing.assert_series_equal(
            res[col],
            res_ext.loc[:6, col],
            check_names=False,
        )


def test_same_day_rolling_window_input_order_invariance():
    """Verify same-day rolling statistics are invariant to input row ordering."""
    data = [
        {"transaction_id": "TXN-01", "date": "2026-03-01", "type": "Expense", "category": "Groceries", "amount": 1000.0},
        {"transaction_id": "TXN-02", "date": "2026-03-02", "type": "Expense", "category": "Groceries", "amount": 500.0},
        {"transaction_id": "TXN-03", "date": "2026-03-02", "type": "Expense", "category": "Transport", "amount": 700.0},
        {"transaction_id": "TXN-04", "date": "2026-03-02", "type": "Expense", "category": "Dining", "amount": 300.0},
    ]
    df_orig = pd.DataFrame(data)

    # Shuffled order of Day 2 transactions
    df_shuffled = pd.DataFrame([data[0], data[3], data[1], data[2]])

    res_orig = extract_temporal_sequence_features(df_orig, restore_order=True)
    res_shuffled = extract_temporal_sequence_features(df_shuffled, restore_order=True)

    # Verify each transaction receives identical rolling values regardless of row order
    for tid in ["TXN-02", "TXN-03", "TXN-04"]:
        val_orig = res_orig[res_orig["transaction_id"] == tid]["rolling_expense_7d_sum"].values[0]
        val_shuffled = res_shuffled[res_shuffled["transaction_id"] == tid]["rolling_expense_7d_sum"].values[0]
        assert val_orig == val_shuffled == 1000.0


def test_get_model_feature_matrix_drop_na(sample_transactions_df):
    """Verify drop_na_rows drops rows containing NaNs from sequence/rolling lags."""
    enriched = engineer_features(sample_transactions_df, include_categorical_encoding=True)
    matrix_with_na = get_model_feature_matrix(enriched, drop_na_rows=False)
    matrix_no_na = get_model_feature_matrix(enriched, drop_na_rows=True)

    assert len(matrix_with_na) == 5
    # Since row 0 (Income) has NaNs for expense rolling stats, and row 1 has NaNs for lags,
    # dropping NaNs leaves only rows with complete history
    assert len(matrix_no_na) < 5
