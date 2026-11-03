"""
Unit Tests for Data Cleaning Module

Author: Akash Das
"""

import pytest
import pandas as pd
from expense_tracker.data.data_cleaning import clean_transactions, inspect_data_quality


@pytest.fixture
def uncleaned_df():
    """Return an uncleaned DataFrame with whitespace, mixed casing, and currency strings."""
    return pd.DataFrame([
        {
            "transaction_id": "  TXN-001  ",
            "date": "2026/03/15",
            "type": " income ",
            "category": " salary ",
            "amount": " ₹85,000.50 ",
            "payment_method": " bank transfer ",
            "description": "  Monthly Payroll Transfer  ",
        },
        {
            "transaction_id": "TXN-002",
            "date": "15-03-2026",
            "type": "EXPENSE",
            "category": "groceries",
            "amount": " $1,250.00 ",
            "payment_method": "upi",
            "description": "Blinkit Quick Delivery",
        },
    ])


def test_clean_transactions_whitespace_normalization(uncleaned_df):
    """Verify whitespace is trimmed across all text fields."""
    cleaned = clean_transactions(uncleaned_df)
    assert cleaned.loc[0, "transaction_id"] == "TXN-001"
    assert cleaned.loc[0, "description"] == "Monthly Payroll Transfer"
    assert cleaned.loc[0, "type"] == "Income"
    assert cleaned.loc[0, "category"] == "Salary"


def test_clean_transactions_text_normalization(uncleaned_df):
    """Verify case normalization for type, category, and payment method."""
    cleaned = clean_transactions(uncleaned_df)
    assert cleaned.loc[0, "type"] == "Income"
    assert cleaned.loc[1, "type"] == "Expense"
    assert cleaned.loc[0, "category"] == "Salary"
    assert cleaned.loc[1, "category"] == "Groceries"
    assert cleaned.loc[0, "payment_method"] == "Bank Transfer"
    assert cleaned.loc[1, "payment_method"] == "UPI"


def test_clean_transactions_date_standardization(uncleaned_df):
    """Verify dates are formatted into standard ISO YYYY-MM-DD strings."""
    cleaned = clean_transactions(uncleaned_df)
    assert cleaned.loc[0, "date"] == "2026-03-15"
    assert cleaned.loc[1, "date"] == "2026-03-15"


def test_clean_transactions_numeric_amount_conversion(uncleaned_df):
    """Verify currency symbols and commas are stripped and amounts converted to float."""
    cleaned = clean_transactions(uncleaned_df)
    assert isinstance(cleaned.loc[0, "amount"], (float, int))
    assert cleaned.loc[0, "amount"] == 85000.50
    assert cleaned.loc[1, "amount"] == 1250.00


def test_clean_transactions_empty_dataframe():
    """Verify empty DataFrame is handled gracefully without crashing."""
    empty_df = pd.DataFrame()
    cleaned = clean_transactions(empty_df)
    assert isinstance(cleaned, pd.DataFrame)
    assert cleaned.empty

    cleaned_df, report = clean_transactions(empty_df, return_report=True)
    assert cleaned_df.empty
    assert report["total_rows"] == 0
    assert report["is_valid"] is False


def test_clean_transactions_input_not_mutated(uncleaned_df):
    """Verify caller's input DataFrame is not mutated."""
    original_type = uncleaned_df.loc[0, "type"]
    _ = clean_transactions(uncleaned_df)
    assert uncleaned_df.loc[0, "type"] == original_type


def test_clean_transactions_invalid_records_reported():
    """Verify invalid records are not silently dropped but reported with reasons."""
    df_with_invalid = pd.DataFrame([
        {
            "transaction_id": "TXN-999",
            "date": "2026-01-01",
            "type": "Expense",
            "category": "Groceries",
            "amount": -50.0,  # Negative amount
            "payment_method": "Cash",
            "description": "Invalid Negative Expense",
        }
    ])
    cleaned, report = clean_transactions(df_with_invalid, return_report=True)

    # Row is preserved (not dropped)
    assert len(cleaned) == 1
    assert report["is_valid"] is False
    assert report["invalid_rows_count"] == 1
    assert len(report["invalid_records"]) == 1
    assert "TXN-999" == report["invalid_records"][0]["transaction_id"]


def test_clean_transactions_invalid_input_type():
    """Verify TypeError on non-DataFrame input."""
    with pytest.raises(TypeError, match="Expected pandas DataFrame"):
        clean_transactions("not a dataframe")  # type: ignore


def test_inspect_data_quality(uncleaned_df):
    """Verify inspect_data_quality helper returns valid report structure."""
    report = inspect_data_quality(uncleaned_df)
    assert "is_valid" in report
    assert "total_rows" in report
    assert report["total_rows"] == 2


def test_clean_transactions_explicit_date_formats():
    """Verify explicit date parsing for YYYY-MM-DD, YYYY/MM/DD, and DD-MM-YYYY."""
    df = pd.DataFrame([
        {
            "transaction_id": "TXN-D1",
            "date": "2026-02-01",  # ISO YYYY-MM-DD
            "type": "Income",
            "category": "Salary",
            "amount": 80000.0,
            "payment_method": "Bank Transfer",
            "description": "ISO date",
        },
        {
            "transaction_id": "TXN-D2",
            "date": "2026/02/01",  # Slash ISO YYYY/MM/DD
            "type": "Expense",
            "category": "Groceries",
            "amount": 1500.0,
            "payment_method": "UPI",
            "description": "Slash ISO date",
        },
        {
            "transaction_id": "TXN-D3",
            "date": "01-02-2026",  # Indian DD-MM-YYYY -> 1 February 2026
            "type": "Expense",
            "category": "Rent",
            "amount": 25000.0,
            "payment_method": "Bank Transfer",
            "description": "Indian format date",
        },
    ])

    cleaned, report = clean_transactions(df, return_report=True)
    assert report["is_valid"] is True
    assert report["invalid_rows_count"] == 0

    # All three must resolve to 1 February 2026
    assert cleaned.loc[0, "date"] == "2026-02-01"
    assert cleaned.loc[1, "date"] == "2026-02-01"
    assert cleaned.loc[2, "date"] == "2026-02-01"


def test_clean_transactions_invalid_and_unsupported_date_formats():
    """Verify invalid dates, null dates, and unsupported formats are rejected."""
    df = pd.DataFrame([
        {
            "transaction_id": "TXN-BAD1",
            "date": "2026-02-31",  # Invalid day for February
            "type": "Expense",
            "category": "Groceries",
            "amount": 200.0,
            "payment_method": "Cash",
            "description": "Feb 31 invalid date",
        },
        {
            "transaction_id": "TXN-BAD2",
            "date": None,  # Null date
            "type": "Income",
            "category": "Salary",
            "amount": 50000.0,
            "payment_method": "Bank Transfer",
            "description": "Null date",
        },
        {
            "transaction_id": "TXN-BAD3",
            "date": "02/15/2026",  # Unsupported ambiguous MM/DD/YYYY format
            "type": "Expense",
            "category": "Transport",
            "amount": 350.0,
            "payment_method": "UPI",
            "description": "Ambiguous MM/DD/YYYY date",
        },
    ])

    cleaned, report = clean_transactions(df, return_report=True)

    # Must be marked invalid
    assert report["is_valid"] is False
    assert report["invalid_rows_count"] == 3
    assert len(report["invalid_records"]) == 3

    # Preserves rows (non-destructive)
    assert len(cleaned) == 3

    # Check parse_explicit_date unit-level behavior
    from expense_tracker.data.data_cleaning import parse_explicit_date
    assert parse_explicit_date("2026-02-01") == "2026-02-01"
    assert parse_explicit_date("2026/02/01") == "2026-02-01"
    assert parse_explicit_date("01-02-2026") == "2026-02-01"
    assert parse_explicit_date("2026-02-31") is None
    assert parse_explicit_date(None) is None
    assert parse_explicit_date("02/15/2026") is None
    assert parse_explicit_date("Feb 1, 2026") is None
