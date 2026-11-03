"""
Data Ingestion and Loading Module

Author: Akash Das
Description: Robust ingestion of transaction records from CSV files with comprehensive
             error handling for missing, empty, or malformed data, plus an end-to-end
             ingestion-to-storage pipeline workflow.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union
import pandas as pd

from expense_tracker.data.data_cleaning import clean_transactions
from expense_tracker.data.validation import REQUIRED_COLUMNS, validate_transaction_schema
from expense_tracker.database.operations import (
    initialize_database,
    insert_transactions,
    transaction_exists,
)


def load_transactions(file_path: Union[str, Path]) -> pd.DataFrame:
    """Load transaction records from a CSV file into a pandas DataFrame.

    Validates file existence, non-emptiness, valid CSV formatting, and
    presence of required schema columns. Does not silently drop or filter rows.

    Args:
        file_path: Path to the CSV transaction file.

    Returns:
        pd.DataFrame containing the raw transaction records.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If file is empty, malformed, or missing required columns.
        TypeError: If file_path is invalid.
    """
    if file_path is None:
        raise TypeError("file_path cannot be None.")

    path = Path(file_path)

    # 1. Existence check
    if not path.is_file():
        raise FileNotFoundError(f"Transaction file not found at: '{path.resolve()}'.")

    # 2. Empty file check
    if path.stat().st_size == 0:
        raise ValueError(f"Transaction file is completely empty (0 bytes): '{path.resolve()}'.")

    # 3. CSV parsing
    try:
        df = pd.read_csv(
            path,
            dtype={
                "transaction_id": str,
                "description": str,
                "type": str,
                "category": str,
                "payment_method": str,
            },
        )
    except pd.errors.EmptyDataError as e:
        raise ValueError(f"CSV file contains no data or headers: '{path.resolve()}'.") from e
    except Exception as e:
        raise ValueError(f"Failed to parse CSV file at '{path.resolve()}': {e}") from e

    # 4. Empty rows / zero data rows check
    if df.empty:
        raise ValueError(f"CSV file contains headers but no data records: '{path.resolve()}'.")

    # 5. Schema column existence check
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(
            f"CSV file '{path.name}' is missing required schema columns: {sorted(missing_columns)}. "
            f"Expected all of: {sorted(REQUIRED_COLUMNS)}."
        )

    return df


def ingest_transaction_file(
    file_path: Union[str, Path],
    db_path: Optional[Union[str, Path]] = None,
    on_conflict: str = "skip",
) -> Dict[str, Any]:
    """Execute end-to-end ingestion pipeline: Load -> Clean -> Validate -> Store in SQLite.

    Pipeline stages:
    1. Loads raw CSV data into DataFrame.
    2. Normalizes whitespace, text, casing, and amounts.
    3. Validates against schema rules and checks for invalid rows.
    4. Persists valid transactions to SQLite database table.
    5. Compiles and returns comprehensive ingestion statistics.

    Args:
        file_path: Path to raw transaction CSV.
        db_path: Optional path to target SQLite database.
        on_conflict: Conflict resolution policy ('skip' or 'fail').

    Returns:
        Dict[str, Any] with ingestion statistics:
            - 'file_path': Source file path.
            - 'rows_loaded': Total rows loaded from CSV.
            - 'valid_rows': Rows passing schema validation.
            - 'invalid_rows': Rows failing schema validation.
            - 'inserted_records': Rows successfully committed to SQLite.
            - 'skipped_duplicates': Existing duplicate transactions skipped.
            - 'validation_errors': List of schema validation error messages.
    """
    # 1. Load CSV
    raw_df = load_transactions(file_path)
    total_loaded = len(raw_df)

    # 2. Clean data
    cleaned_df, cleaning_report = clean_transactions(raw_df, return_report=True)

    # 3. Validation
    is_valid = cleaning_report["is_valid"]
    validation_errors = cleaning_report["validation_errors"]
    invalid_rows_count = cleaning_report["invalid_rows_count"]
    valid_rows_count = total_loaded - invalid_rows_count

    inserted_count = 0
    skipped_duplicates = 0

    # 4. Database Storage (only if valid rows exist)
    if is_valid and valid_rows_count > 0:
        initialize_database(db_path)
        # Determine duplicates prior to insertion for explicit reporting
        existing_count = 0
        for tid in cleaned_df["transaction_id"]:
            if transaction_exists(str(tid), db_path=db_path):
                existing_count += 1

        inserted_count = insert_transactions(cleaned_df, db_path=db_path, on_conflict=on_conflict)
        skipped_duplicates = existing_count

    return {
        "file_path": str(Path(file_path).resolve()),
        "rows_loaded": total_loaded,
        "valid_rows": valid_rows_count,
        "invalid_rows": invalid_rows_count,
        "inserted_records": inserted_count,
        "skipped_duplicates": skipped_duplicates,
        "validation_errors": validation_errors,
    }
