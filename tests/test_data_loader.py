"""
Unit Tests for CSV Data Loader and Ingestion Pipeline

Author: Akash Das
"""

import tempfile
from pathlib import Path
import pytest
import pandas as pd

from expense_tracker.data.data_loader import load_transactions, ingest_transaction_file
from expense_tracker.database.operations import query_transactions


@pytest.fixture
def temp_csv_dir():
    """Create a temporary directory for isolated CSV tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


def test_load_transactions_success(temp_csv_dir):
    """Verify successful loading of a valid CSV file."""
    csv_file = temp_csv_dir / "valid.csv"
    csv_file.write_text(
        "transaction_id,date,type,category,amount,payment_method,description\n"
        "TXN-001,2026-01-01,Income,Salary,85000,Bank Transfer,Monthly Salary\n"
        "TXN-002,2026-01-02,Expense,Groceries,1500.50,UPI,Blinkit Delivery\n",
        encoding="utf-8",
    )
    df = load_transactions(csv_file)
    assert len(df) == 2
    assert list(df["transaction_id"]) == ["TXN-001", "TXN-002"]
    assert float(df.loc[1, "amount"]) == 1500.50


def test_load_transactions_missing_file():
    """Verify FileNotFoundError on non-existent file."""
    with pytest.raises(FileNotFoundError, match="not found"):
        load_transactions("non_existent_file.csv")


def test_load_transactions_empty_file(temp_csv_dir):
    """Verify ValueError on completely empty 0-byte file."""
    empty_file = temp_csv_dir / "empty.csv"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="completely empty"):
        load_transactions(empty_file)


def test_load_transactions_header_only_file(temp_csv_dir):
    """Verify ValueError on file with headers but zero data rows."""
    header_only = temp_csv_dir / "header_only.csv"
    header_only.write_text(
        "transaction_id,date,type,category,amount,payment_method,description\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="no data records"):
        load_transactions(header_only)


def test_load_transactions_missing_columns(temp_csv_dir):
    """Verify ValueError when required columns are absent."""
    missing_cols_file = temp_csv_dir / "missing_cols.csv"
    missing_cols_file.write_text(
        "transaction_id,date,amount\nTXN-001,2026-01-01,500\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing required schema columns"):
        load_transactions(missing_cols_file)


def test_load_transactions_malformed_csv(temp_csv_dir):
    """Verify error on malformed/corrupted CSV structure."""
    bad_csv = temp_csv_dir / "bad.csv"
    # Unbalanced quotes causing parser failure
    bad_csv.write_text(
        'transaction_id,date,type,category,amount,payment_method,description\n'
        'TXN-001,2026-01-01,Income,Salary,50000,UPI,"Unclosed description quote\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Failed to parse CSV"):
        load_transactions(bad_csv)


def test_load_transactions_none_path():
    """Verify TypeError when file_path is None."""
    with pytest.raises(TypeError, match="cannot be None"):
        load_transactions(None)  # type: ignore


def test_end_to_end_ingestion_pipeline(temp_csv_dir):
    """Integration test: CSV -> Loader -> Cleaner -> Validator -> SQLite -> Retrieval."""
    csv_file = temp_csv_dir / "raw_batch.csv"
    db_file = temp_csv_dir / "test_pipeline.db"

    # CSV with leading whitespace and unnormalized text to verify full pipeline
    lines = [
        "transaction_id,date,type,category,amount,payment_method,description",
        "  TXN-101 ,2026/02/01, income , salary , ₹90000.00 , bank transfer , Monthly Salary ",
        "  TXN-102 ,2026-02-03, expense , groceries , 2450.50 , upi , Zepto Essentials ",
        "  TXN-103 ,2026-02-05, expense , dining , 850 , credit card , Swiggy Dinner ",
    ]
    csv_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    stats = ingest_transaction_file(csv_file, db_path=db_file)

    assert stats["rows_loaded"] == 3
    assert stats["valid_rows"] == 3
    assert stats["invalid_rows"] == 0
    assert stats["inserted_records"] == 3
    assert stats["skipped_duplicates"] == 0

    # Retrieve from DB and verify cleaned round-trip values
    stored_df = query_transactions(db_path=db_file)
    assert len(stored_df) == 3
    assert list(stored_df["transaction_id"]) == ["TXN-101", "TXN-102", "TXN-103"]
    assert stored_df.loc[0, "type"] == "Income"
    assert stored_df.loc[0, "amount"] == 90000.0
    assert stored_df.loc[1, "category"] == "Groceries"
    assert stored_df.loc[1, "payment_method"] == "UPI"
    assert stored_df.loc[1, "amount"] == 2450.50
    assert stored_df.loc[0, "date"] == "2026-02-01"

    # Re-run pipeline with same CSV to verify duplicate skipping
    repeat_stats = ingest_transaction_file(csv_file, db_path=db_file)
    assert repeat_stats["inserted_records"] == 0
    assert repeat_stats["skipped_duplicates"] == 3

    # Total stored records remain 3
    assert len(query_transactions(db_path=db_file)) == 3
