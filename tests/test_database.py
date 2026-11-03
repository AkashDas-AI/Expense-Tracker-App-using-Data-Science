"""
Unit Tests for SQLite Database Storage Layer

Author: Akash Das
"""

import sqlite3
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from expense_tracker.database.connection import get_db_connection, get_db_context
from expense_tracker.database.operations import (
    initialize_database,
    insert_transaction,
    insert_transactions,
    query_transactions,
    transaction_exists,
)


@pytest.fixture
def temp_db_path():
    """Create an isolated temporary SQLite database path for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_expenses.db"
        yield db_path


@pytest.fixture
def sample_transactions_df():
    """Return a standard 3-row test DataFrame."""
    return pd.DataFrame([
        {
            "transaction_id": "TXN-001",
            "date": "2026-01-10",
            "type": "Income",
            "category": "Salary",
            "amount": 85000.0,
            "payment_method": "Bank Transfer",
            "description": "Monthly Salary",
        },
        {
            "transaction_id": "TXN-002",
            "date": "2026-01-12",
            "type": "Expense",
            "category": "Groceries",
            "amount": 1500.0,
            "payment_method": "UPI",
            "description": "Blinkit Order",
        },
        {
            "transaction_id": "TXN-003",
            "date": "2026-01-15",
            "type": "Expense",
            "category": "Rent",
            "amount": 25000.0,
            "payment_method": "Bank Transfer",
            "description": "Flat Rent",
        },
    ])


def test_initialize_database_and_tables(temp_db_path):
    """Verify database initialization creates the transactions table and indices."""
    initialize_database(temp_db_path)
    assert temp_db_path.exists()

    with get_db_context(temp_db_path) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='transactions';"
        )
        assert cursor.fetchone() is not None

        # Verify index creation
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_transactions_date';"
        )
        assert cursor.fetchone() is not None


def test_single_transaction_insert_and_exists(temp_db_path):
    """Verify single transaction insertion and transaction_exists check."""
    initialize_database(temp_db_path)
    assert not transaction_exists("TXN-100", db_path=temp_db_path)

    record = {
        "transaction_id": "TXN-100",
        "date": "2026-02-01",
        "type": "Income",
        "category": "Freelance",
        "amount": 18000.0,
        "payment_method": "Bank Transfer",
        "description": "UI Design Contract",
    }
    inserted = insert_transaction(record, db_path=temp_db_path)
    assert inserted is True
    assert transaction_exists("TXN-100", db_path=temp_db_path)


def test_bulk_insert_and_retrieval(temp_db_path, sample_transactions_df):
    """Verify bulk insertion and round-trip retrieval as DataFrame."""
    count = insert_transactions(sample_transactions_df, db_path=temp_db_path)
    assert count == 3

    retrieved = query_transactions(db_path=temp_db_path)
    assert len(retrieved) == 3
    assert list(retrieved["transaction_id"]) == ["TXN-001", "TXN-002", "TXN-003"]
    assert retrieved.loc[0, "amount"] == 85000.0
    assert retrieved.loc[1, "category"] == "Groceries"


def test_query_filtering(temp_db_path, sample_transactions_df):
    """Verify query_transactions filters by date, type, category, and payment method."""
    insert_transactions(sample_transactions_df, db_path=temp_db_path)

    # Filter by type
    income_df = query_transactions(filters={"type": "Income"}, db_path=temp_db_path)
    assert len(income_df) == 1
    assert income_df.loc[0, "transaction_id"] == "TXN-001"

    # Filter by date range
    date_df = query_transactions(
        filters={"start_date": "2026-01-11", "end_date": "2026-01-13"},
        db_path=temp_db_path,
    )
    assert len(date_df) == 1
    assert date_df.loc[0, "transaction_id"] == "TXN-002"

    # Filter by category
    cat_df = query_transactions(filters={"category": "Rent"}, db_path=temp_db_path)
    assert len(cat_df) == 1
    assert cat_df.loc[0, "transaction_id"] == "TXN-003"


def test_duplicate_handling_skip_policy(temp_db_path, sample_transactions_df):
    """Verify on_conflict='skip' skips duplicate IDs without creating duplicates."""
    first_insert = insert_transactions(sample_transactions_df, db_path=temp_db_path)
    assert first_insert == 3

    # Re-importing exact same DataFrame
    second_insert = insert_transactions(
        sample_transactions_df,
        db_path=temp_db_path,
        on_conflict="skip",
    )
    assert second_insert == 0

    # Ensure total in DB is still 3
    df_all = query_transactions(db_path=temp_db_path)
    assert len(df_all) == 3


def test_duplicate_handling_fail_policy(temp_db_path, sample_transactions_df):
    """Verify on_conflict='fail' raises IntegrityError on duplicate IDs."""
    insert_transactions(sample_transactions_df, db_path=temp_db_path)

    with pytest.raises(sqlite3.IntegrityError):
        insert_transactions(
            sample_transactions_df,
            db_path=temp_db_path,
            on_conflict="fail",
        )


def test_invalid_transaction_constraints(temp_db_path):
    """Verify CHECK constraints reject negative amounts and invalid types."""
    initialize_database(temp_db_path)

    # Negative amount
    bad_amount_record = {
        "transaction_id": "TXN-ERR1",
        "date": "2026-01-01",
        "type": "Expense",
        "category": "Dining",
        "amount": -100.0,
        "payment_method": "Cash",
        "description": "Invalid Negative",
    }
    with pytest.raises(sqlite3.IntegrityError):
        insert_transaction(bad_amount_record, db_path=temp_db_path)

    # Invalid type
    bad_type_record = {
        "transaction_id": "TXN-ERR2",
        "date": "2026-01-01",
        "type": "Investment",  # Not Income or Expense
        "category": "Stocks",
        "amount": 5000.0,
        "payment_method": "UPI",
        "description": "Invalid Type",
    }
    with pytest.raises(sqlite3.IntegrityError):
        insert_transaction(bad_type_record, db_path=temp_db_path)


def test_atomic_rollback_on_failed_bulk_insert(temp_db_path):
    """Verify batch insertion rolls back atomically if a constraint is violated."""
    initialize_database(temp_db_path)

    # Batch where 1st is valid, 2nd is invalid
    mixed_df = pd.DataFrame([
        {
            "transaction_id": "TXN-VALID",
            "date": "2026-01-01",
            "type": "Income",
            "category": "Salary",
            "amount": 50000.0,
            "payment_method": "Bank Transfer",
            "description": "Valid Salary",
        },
        {
            "transaction_id": "TXN-INVALID",
            "date": "2026-01-01",
            "type": "Expense",
            "category": "Dining",
            "amount": -500.0,  # Fails CHECK(amount > 0)
            "payment_method": "Cash",
            "description": "Fails constraint",
        },
    ])

    with pytest.raises(sqlite3.IntegrityError):
        insert_transactions(mixed_df, db_path=temp_db_path, on_conflict="fail")

    # Due to atomic rollback, TXN-VALID must NOT be in DB
    assert not transaction_exists("TXN-VALID", db_path=temp_db_path)
    all_records = query_transactions(db_path=temp_db_path)
    assert len(all_records) == 0


def test_empty_dataframe_insert(temp_db_path):
    """Verify empty DataFrame returns 0 inserted records."""
    count = insert_transactions(pd.DataFrame(), db_path=temp_db_path)
    assert count == 0


def test_sqlite_category_type_composite_constraints(temp_db_path):
    """Verify SQLite composite CHECK constraint rejects invalid category-to-type combinations."""
    initialize_database(temp_db_path)

    # 1. Income + Groceries (Invalid category for Income)
    bad_income_record = {
        "transaction_id": "TXN-INV-INC",
        "date": "2026-01-01",
        "type": "Income",
        "category": "Groceries",
        "amount": 1000.0,
        "payment_method": "UPI",
        "description": "Invalid Income Groceries",
    }
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        insert_transaction(bad_income_record, db_path=temp_db_path)

    # 2. Expense + Salary (Invalid category for Expense)
    bad_expense_record = {
        "transaction_id": "TXN-INV-EXP",
        "date": "2026-01-01",
        "type": "Expense",
        "category": "Salary",
        "amount": 50000.0,
        "payment_method": "Bank Transfer",
        "description": "Invalid Expense Salary",
    }
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        insert_transaction(bad_expense_record, db_path=temp_db_path)


def test_sqlite_payment_method_constraint(temp_db_path):
    """Verify SQLite CHECK constraint rejects unsupported payment methods."""
    initialize_database(temp_db_path)

    unsupported_payment_record = {
        "transaction_id": "TXN-INV-PAY",
        "date": "2026-01-01",
        "type": "Expense",
        "category": "Groceries",
        "amount": 150.0,
        "payment_method": "Bitcoin",  # Not in allowed payment methods
        "description": "Crypto Grocery Purchase",
    }
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        insert_transaction(unsupported_payment_record, db_path=temp_db_path)


def test_sqlite_valid_category_type_combinations_insert_successfully(temp_db_path):
    """Verify valid Income + Salary and Expense + Groceries insert without constraint errors."""
    initialize_database(temp_db_path)

    valid_income = {
        "transaction_id": "TXN-VAL-INC",
        "date": "2026-01-01",
        "type": "Income",
        "category": "Salary",
        "amount": 85000.0,
        "payment_method": "Bank Transfer",
        "description": "Valid Salary Credit",
    }
    valid_expense = {
        "transaction_id": "TXN-VAL-EXP",
        "date": "2026-01-02",
        "type": "Expense",
        "category": "Groceries",
        "amount": 1250.0,
        "payment_method": "UPI",
        "description": "Valid Grocery Purchase",
    }

    assert insert_transaction(valid_income, db_path=temp_db_path) is True
    assert insert_transaction(valid_expense, db_path=temp_db_path) is True
    assert transaction_exists("TXN-VAL-INC", db_path=temp_db_path) is True
    assert transaction_exists("TXN-VAL-EXP", db_path=temp_db_path) is True
