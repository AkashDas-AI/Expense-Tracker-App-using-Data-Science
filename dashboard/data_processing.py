"""
Dashboard Data Processing and Filtering Module

Author: Akash Das
Description: Centralized, pure-function transaction loading, date-boundary filtering,
             and multi-criteria filtering for Streamlit dashboard views.
"""

from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from expense_tracker.config.settings import SAMPLE_DATA_DIR
from expense_tracker.data.data_cleaning import clean_transactions
from expense_tracker.data.data_loader import load_transactions

DEFAULT_DATA_PATH = SAMPLE_DATA_DIR / "transactions.csv"


def load_dashboard_data(file_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Load, clean, and prepare transaction records for dashboard rendering.

    - Loads data via verified data loader.
    - Sanitizes via non-destructive cleaning pipeline.
    - Masks synthetic evaluation markers ('[UNUSUAL]') from user-facing descriptions.
    - Derives parsed datetime column for inclusive date-range querying.

    Args:
        file_path: Optional file path. Defaults to data/sample/transactions.csv.

    Returns:
        pd.DataFrame: Ready-to-filter dashboard DataFrame.

    Raises:
        FileNotFoundError: If the source CSV cannot be located.
        ValueError: If dataset is malformed or fails schema checks.
    """
    target_path = Path(file_path) if file_path is not None else DEFAULT_DATA_PATH
    raw_df = load_transactions(target_path)
    cleaned_df = clean_transactions(raw_df)

    df = cleaned_df.copy()

    # Create parsed datetime column for fast date boundary evaluations
    df["parsed_date"] = pd.to_datetime(df["date"], errors="coerce")

    # Mask synthetic evaluation marker '[UNUSUAL]' so it is never exposed to dashboard users
    if "description" in df.columns:
        df["display_description"] = (
            df["description"].str.replace(r"\[UNUSUAL\]\s*", "", regex=True).str.strip()
        )
    else:
        df["display_description"] = ""

    return df


def filter_transactions(
    df: pd.DataFrame,
    start_date: Optional[Union[str, date, datetime, pd.Timestamp]] = None,
    end_date: Optional[Union[str, date, datetime, pd.Timestamp]] = None,
    transaction_types: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    payment_methods: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Apply multi-criteria filters to transactions without mutating the source DataFrame.

    Requirements:
    - Inclusive date boundaries: transactions occurring on start_date and end_date are included.
    - Pure function: does not alter the input DataFrame.
    - Gracefully handles empty DataFrames or filter combinations with zero matches.

    Args:
        df: Input transaction DataFrame.
        start_date: Inclusive start date.
        end_date: Inclusive end date.
        transaction_types: Optional list of flow types to retain (e.g. ['Income', 'Expense']).
        categories: Optional list of categories to retain.
        payment_methods: Optional list of payment methods to retain.

    Returns:
        pd.DataFrame: Filtered subset of transactions with reset index.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if df.empty:
        return df.copy()

    filtered = df.copy()

    # Ensure parsed_date exists
    if "parsed_date" not in filtered.columns:
        filtered["parsed_date"] = pd.to_datetime(filtered["date"], errors="coerce")

    # Inclusive date filtering
    if start_date is not None:
        start_ts = pd.to_datetime(start_date).normalize()
        filtered = filtered[filtered["parsed_date"] >= start_ts]

    if end_date is not None:
        end_ts = pd.to_datetime(end_date).normalize()
        # Dates in transactions have 00:00:00 time; compare <= end_ts
        filtered = filtered[filtered["parsed_date"] <= end_ts]

    # Transaction type filtering
    if transaction_types is not None and len(transaction_types) > 0:
        filtered = filtered[filtered["type"].isin(transaction_types)]

    # Category filtering
    if categories is not None and len(categories) > 0:
        filtered = filtered[filtered["category"].isin(categories)]

    # Payment method filtering
    if payment_methods is not None and len(payment_methods) > 0:
        filtered = filtered[filtered["payment_method"].isin(payment_methods)]

    return filtered.reset_index(drop=True)


def get_dataset_date_bounds(df: pd.DataFrame) -> Tuple[date, date]:
    """Retrieve minimum and maximum transaction calendar dates from dataset.

    Args:
        df: Transaction DataFrame containing 'date'.

    Returns:
        Tuple[date, date]: (earliest_date, latest_date).
    """
    if df.empty or "date" not in df.columns:
        today = date.today()
        return today, today

    parsed = pd.to_datetime(df["date"], errors="coerce").dropna()
    if parsed.empty:
        today = date.today()
        return today, today

    return parsed.min().date(), parsed.max().date()


def get_available_categories(df: pd.DataFrame, transaction_type: Optional[str] = None) -> List[str]:
    """Return sorted unique category list, optionally filtered by transaction type."""
    if df.empty or "category" not in df.columns:
        return []

    target_df = df if transaction_type is None else df[df["type"] == transaction_type]
    cats = sorted([str(c) for c in target_df["category"].dropna().unique()])
    return cats


def get_available_payment_methods(df: pd.DataFrame) -> List[str]:
    """Return sorted unique payment methods present in the dataset."""
    if df.empty or "payment_method" not in df.columns:
        return []

    methods = sorted([str(m) for m in df["payment_method"].dropna().unique()])
    return methods

