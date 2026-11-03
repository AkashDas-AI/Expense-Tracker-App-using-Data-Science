"""
Unit Tests for Synthetic Data Generator

Author: Akash Das
"""

import pytest
import pandas as pd
from expense_tracker.data.data_generator import (
    generate_synthetic_transactions,
    TRANSACTION_TYPES,
    INCOME_CATEGORIES,
    EXPENSE_CATEGORIES,
    PAYMENT_METHODS,
)


def test_generator_record_count_and_columns():
    """Verify generator produces requested record count and exact schema columns."""
    df = generate_synthetic_transactions(n_records=50, random_seed=123)
    assert len(df) == 50
    expected_cols = [
        "transaction_id",
        "date",
        "type",
        "category",
        "amount",
        "payment_method",
        "description",
    ]
    assert list(df.columns) == expected_cols


def test_generator_unique_transaction_ids():
    """Verify transaction IDs are unique, non-null, and correctly formatted."""
    df = generate_synthetic_transactions(n_records=75, random_seed=42)
    assert df["transaction_id"].is_unique
    assert not df["transaction_id"].isna().any()
    assert df["transaction_id"].str.startswith("TXN-").all()


def test_generator_date_boundaries():
    """Verify all generated transaction dates fall strictly within start and end range."""
    start_date = "2026-01-01"
    end_date = "2026-06-30"
    df = generate_synthetic_transactions(
        n_records=60,
        start_date=start_date,
        end_date=end_date,
        random_seed=42,
    )
    parsed_dates = pd.to_datetime(df["date"])
    assert (parsed_dates >= pd.to_datetime(start_date)).all()
    assert (parsed_dates <= pd.to_datetime(end_date)).all()


def test_generator_positive_amounts():
    """Verify all generated amounts are positive and finite numbers."""
    df = generate_synthetic_transactions(n_records=60, random_seed=42)
    assert (df["amount"] > 0).all()
    assert not df["amount"].isna().any()


def test_generator_contains_income_and_expense():
    """Verify both Income and Expense transactions are included."""
    df = generate_synthetic_transactions(n_records=100, random_seed=42)
    types_present = set(df["type"].unique())
    assert "Income" in types_present
    assert "Expense" in types_present


def test_generator_allowed_categories_and_payment_methods():
    """Verify all generated categories and payment methods match allowed specifications."""
    df = generate_synthetic_transactions(n_records=80, random_seed=42)
    
    # Check types
    assert set(df["type"].unique()).issubset(set(TRANSACTION_TYPES))

    # Check categories by type
    income_cats = set(df[df["type"] == "Income"]["category"].unique())
    assert income_cats.issubset(set(INCOME_CATEGORIES))

    expense_cats = set(df[df["type"] == "Expense"]["category"].unique())
    assert expense_cats.issubset(set(EXPENSE_CATEGORIES))

    # Check payment methods
    assert set(df["payment_method"].unique()).issubset(set(PAYMENT_METHODS))


def test_generator_reproducibility_same_seed():
    """Verify same seed produces identical dataset."""
    df_a = generate_synthetic_transactions(n_records=40, random_seed=99)
    df_b = generate_synthetic_transactions(n_records=40, random_seed=99)
    pd.testing.assert_frame_equal(df_a, df_b)


def test_generator_different_output_different_seed():
    """Verify different seeds produce distinct outputs."""
    df_a = generate_synthetic_transactions(n_records=40, random_seed=1)
    df_b = generate_synthetic_transactions(n_records=40, random_seed=2)
    assert not df_a.equals(df_b)


def test_generator_invalid_parameters():
    """Verify informative errors on invalid parameters."""
    # Count less than 10
    with pytest.raises(ValueError, match="n_records must be at least 10"):
        generate_synthetic_transactions(n_records=5)

    # Start date after end date
    with pytest.raises(ValueError, match="cannot be after end_date"):
        generate_synthetic_transactions(start_date="2026-12-31", end_date="2026-01-01")

    # Malformed date strings
    with pytest.raises(ValueError, match="Dates must be in 'YYYY-MM-DD' format"):
        generate_synthetic_transactions(start_date="invalid-date", end_date="2026-01-01")


def test_generator_backward_compatibility_kwargs():
    """Verify backward-compatible kwargs (num_records, random_state) work as expected."""
    df = generate_synthetic_transactions(num_records=25, random_state=42)
    assert len(df) == 25
