"""
Unit Tests for Transaction Schema Validation

Author: Akash Das
"""

import pytest
import pandas as pd
import numpy as np
from expense_tracker.data.validation import validate_transaction_schema


@pytest.fixture
def valid_transactions_df():
    """Return a minimal valid transaction DataFrame for testing."""
    return pd.DataFrame([
        {
            "transaction_id": "TXN-00001",
            "date": "2026-01-15",
            "type": "Income",
            "category": "Salary",
            "amount": 85000.0,
            "payment_method": "Bank Transfer",
            "description": "Monthly Salary",
        },
        {
            "transaction_id": "TXN-00002",
            "date": "2026-01-16",
            "type": "Expense",
            "category": "Groceries",
            "amount": 1250.50,
            "payment_method": "UPI",
            "description": "Blinkit Quick Grocery Delivery",
        },
    ])


def test_validation_valid_dataset_passes(valid_transactions_df):
    """Verify that a compliant DataFrame validates successfully."""
    is_valid, errors = validate_transaction_schema(valid_transactions_df)
    assert is_valid is True
    assert errors == []


def test_validation_non_dataframe_input():
    """Verify non-DataFrame input is rejected with clear error."""
    is_valid, errors = validate_transaction_schema({"key": "value"})  # type: ignore
    assert is_valid is False
    assert any("expected pandas.DataFrame" in err for err in errors)


def test_validation_empty_dataset_rejected():
    """Verify empty DataFrame is explicitly rejected."""
    empty_df = pd.DataFrame()
    is_valid, errors = validate_transaction_schema(empty_df)
    assert is_valid is False
    assert any("DataFrame is empty" in err for err in errors)


def test_validation_missing_columns_rejected(valid_transactions_df):
    """Verify omission of required columns is detected."""
    df_missing = valid_transactions_df.drop(columns=["amount", "description"])
    is_valid, errors = validate_transaction_schema(df_missing)
    assert is_valid is False
    assert any("Missing required columns" in err for err in errors)


def test_validation_missing_values_rejected(valid_transactions_df):
    """Verify NaN / None values in required columns are caught."""
    df_null = valid_transactions_df.copy()
    df_null.loc[0, "payment_method"] = None
    is_valid, errors = validate_transaction_schema(df_null)
    assert is_valid is False
    assert any("contains 1 null or missing values" in err for err in errors)


def test_validation_duplicate_transaction_ids(valid_transactions_df):
    """Verify duplicate transaction_id values are rejected."""
    df_dup = valid_transactions_df.copy()
    df_dup.loc[1, "transaction_id"] = "TXN-00001"
    is_valid, errors = validate_transaction_schema(df_dup)
    assert is_valid is False
    assert any("duplicate values" in err for err in errors)


def test_validation_blank_transaction_ids(valid_transactions_df):
    """Verify blank or empty string transaction IDs are rejected."""
    df_blank = valid_transactions_df.copy()
    df_blank.loc[0, "transaction_id"] = "   "
    is_valid, errors = validate_transaction_schema(df_blank)
    assert is_valid is False
    assert any("empty string values" in err for err in errors)


def test_validation_invalid_dates(valid_transactions_df):
    """Verify unparseable date strings are rejected."""
    df_invalid_date = valid_transactions_df.copy()
    df_invalid_date.loc[0, "date"] = "not-a-valid-date"
    is_valid, errors = validate_transaction_schema(df_invalid_date)
    assert is_valid is False
    assert any("invalid or unparseable date values" in err for err in errors)


def test_validation_invalid_transaction_types(valid_transactions_df):
    """Verify non-standard transaction types are rejected."""
    df_bad_type = valid_transactions_df.copy()
    df_bad_type.loc[0, "type"] = "Transfer"
    is_valid, errors = validate_transaction_schema(df_bad_type)
    assert is_valid is False
    assert any("invalid values" in err for err in errors)


def test_validation_invalid_categories(valid_transactions_df):
    """Verify unknown or cross-mismatched categories are rejected."""
    # Unknown category
    df_unknown = valid_transactions_df.copy()
    df_unknown.loc[1, "category"] = "Cryptocurrency Gambling"
    is_valid, errors = validate_transaction_schema(df_unknown)
    assert is_valid is False
    assert any("Invalid categories found for 'Expense' type" in err for err in errors)

    # Cross-type mismatch (Expense with Salary category)
    df_mismatch = valid_transactions_df.copy()
    df_mismatch.loc[1, "category"] = "Salary"
    is_valid, errors = validate_transaction_schema(df_mismatch)
    assert is_valid is False
    assert any("Invalid categories found for 'Expense' type" in err for err in errors)


def test_validation_invalid_payment_method(valid_transactions_df):
    """Verify non-allowed payment method is rejected."""
    df_bad_pay = valid_transactions_df.copy()
    df_bad_pay.loc[0, "payment_method"] = "Bitcoin"
    is_valid, errors = validate_transaction_schema(df_bad_pay)
    assert is_valid is False
    assert any("Allowed payment methods" in err for err in errors)


def test_validation_negative_and_zero_amounts(valid_transactions_df):
    """Verify amounts <= 0 are rejected."""
    # Zero amount
    df_zero = valid_transactions_df.copy()
    df_zero.loc[0, "amount"] = 0.0
    is_valid, errors = validate_transaction_schema(df_zero)
    assert is_valid is False
    assert any("non-positive values" in err for err in errors)

    # Negative amount
    df_neg = valid_transactions_df.copy()
    df_neg.loc[1, "amount"] = -250.0
    is_valid, errors = validate_transaction_schema(df_neg)
    assert is_valid is False
    assert any("non-positive values" in err for err in errors)


def test_validation_non_numeric_and_infinite_amounts(valid_transactions_df):
    """Verify non-numeric or infinite amount values are rejected."""
    # Non-numeric
    df_str = valid_transactions_df.copy()
    df_str["amount"] = df_str["amount"].astype(object)
    df_str.loc[0, "amount"] = "one-thousand"
    is_valid, errors = validate_transaction_schema(df_str)
    assert is_valid is False
    assert any("non-numeric" in err for err in errors)

    # Infinite
    df_inf = valid_transactions_df.copy()
    df_inf.loc[1, "amount"] = np.inf
    is_valid, errors = validate_transaction_schema(df_inf)
    assert is_valid is False
    assert any("infinite or NaN values" in err for err in errors)


def test_validation_blank_descriptions(valid_transactions_df):
    """Verify blank or whitespace-only descriptions are rejected."""
    df_blank_desc = valid_transactions_df.copy()
    df_blank_desc.loc[0, "description"] = "     "
    is_valid, errors = validate_transaction_schema(df_blank_desc)
    assert is_valid is False
    assert any("blank or whitespace-only descriptions" in err for err in errors)
