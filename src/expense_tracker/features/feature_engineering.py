"""
Feature Engineering Module

Author: Akash Das
Description: Reusable feature engineering functions for transforming financial transactions
             into predictive, temporal, categorical, and behavioral features while strictly
             preventing target leakage.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from expense_tracker.data.data_cleaning import parse_explicit_date
from expense_tracker.data.validation import (
    ALLOWED_TRANSACTION_TYPES,
    ALLOWED_INCOME_CATEGORIES,
    ALLOWED_EXPENSE_CATEGORIES,
    ALLOWED_PAYMENT_METHODS,
    REQUIRED_COLUMNS,
)

# Canonical taxonomies for stable one-hot encoding
CANONICAL_CATEGORIES: List[str] = sorted(
    list(ALLOWED_INCOME_CATEGORIES) + list(ALLOWED_EXPENSE_CATEGORIES)
)

CANONICAL_PAYMENT_METHODS: List[str] = sorted(list(ALLOWED_PAYMENT_METHODS))


def _slugify(name: str) -> str:
    """Convert category/payment string to a clean identifier slug."""
    return name.lower().replace(" ", "_").replace("-", "_")


def extract_calendar_features(
    df: pd.DataFrame,
    date_column: str = "date",
) -> pd.DataFrame:
    """Derive calendar and cyclical date features from the transaction date.

    Features generated:
    - 'year': 4-digit calendar year (int).
    - 'month': Calendar month from 1 to 12 (int).
    - 'month_name': Full month name (e.g. 'January', 'November') (str).
    - 'quarter': Calendar quarter from 1 to 4 (int).
    - 'day_of_month': Day of month from 1 to 31 (int).
    - 'day_of_week': Day of week with Monday = 0 through Sunday = 6 (int).
    - 'day_name': Full day name (e.g. 'Monday', 'Sunday') (str).
    - 'is_weekend': Binary indicator where 1 = Saturday/Sunday, 0 = Weekday (int).

    Args:
        df: Input DataFrame containing the transaction date column.
        date_column: Name of the date column.

    Returns:
        New DataFrame augmented with calendar features. Input is never mutated.

    Raises:
        TypeError: If input is not a pandas DataFrame.
        ValueError: If date_column is missing or contains unparseable dates.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if df.empty:
        res = df.copy()
        for col, dtype in [
            ("year", int), ("month", int), ("month_name", object),
            ("quarter", int), ("day_of_month", int), ("day_of_week", int),
            ("day_name", object), ("is_weekend", int)
        ]:
            res[col] = pd.Series(dtype=dtype)
        return res

    if date_column not in df.columns:
        raise ValueError(f"Date column '{date_column}' not found in DataFrame.")

    res = df.copy()

    # Parse dates strictly using Phase 3 explicit format rules
    parsed_dates = [parse_explicit_date(d) for d in res[date_column]]
    if any(p is None for p in parsed_dates):
        invalid_idx = next(i for i, p in enumerate(parsed_dates) if p is None)
        invalid_val = res[date_column].iloc[invalid_idx]
        raise ValueError(f"Column '{date_column}' contains invalid or unparseable date at row {invalid_idx}: '{invalid_val}'.")

    dt_series = pd.Series(pd.to_datetime(parsed_dates), index=res.index)

    res["year"] = dt_series.dt.year.astype(int)
    res["month"] = dt_series.dt.month.astype(int)
    res["month_name"] = dt_series.dt.month_name()
    res["quarter"] = dt_series.dt.quarter.astype(int)
    res["day_of_month"] = dt_series.dt.day.astype(int)
    res["day_of_week"] = dt_series.dt.day_of_week.astype(int)
    res["day_name"] = dt_series.dt.day_name()
    res["is_weekend"] = dt_series.dt.day_of_week.isin([5, 6]).astype(int)

    return res


def extract_temporal_features(
    df: pd.DataFrame,
    date_column: str = "date",
) -> pd.DataFrame:
    """Extract temporal calendar features (backward-compatible alias for extract_calendar_features).

    Args:
        df: Input DataFrame containing the transaction date column.
        date_column: Name of the date column.

    Returns:
        DataFrame augmented with temporal calendar features.
    """
    return extract_calendar_features(df, date_column=date_column)


def extract_flow_indicators(
    df: pd.DataFrame,
    type_column: str = "type",
) -> pd.DataFrame:
    """Extract binary indicators for transaction flow direction.

    Features generated:
    - 'is_income': 1 if type == 'Income', 0 otherwise.
    - 'is_expense': 1 if type == 'Expense', 0 otherwise.

    Args:
        df: Input DataFrame containing the transaction type column.
        type_column: Name of the transaction flow type column.

    Returns:
        New DataFrame augmented with flow indicators.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if df.empty:
        res = df.copy()
        res["is_income"] = pd.Series(dtype=int)
        res["is_expense"] = pd.Series(dtype=int)
        return res

    if type_column not in df.columns:
        raise ValueError(f"Type column '{type_column}' not found in DataFrame.")

    res = df.copy()
    res["is_income"] = (res[type_column] == "Income").astype(int)
    res["is_expense"] = (res[type_column] == "Expense").astype(int)
    return res


def extract_amount_features(
    df: pd.DataFrame,
    amount_column: str = "amount",
) -> pd.DataFrame:
    """Extract non-linear transformations of transaction amounts.

    Features generated:
    - 'log_amount': np.log1p(amount), stabilizing variance and reducing positive skew.

    Args:
        df: Input DataFrame containing the transaction amount column.
        amount_column: Name of the numerical amount column.

    Returns:
        New DataFrame augmented with log-transformed amount.

    Raises:
        ValueError: If amount_column is missing or contains non-positive/non-numeric values.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if df.empty:
        res = df.copy()
        res["log_amount"] = pd.Series(dtype=float)
        return res

    if amount_column not in df.columns:
        raise ValueError(f"Amount column '{amount_column}' not found in DataFrame.")

    res = df.copy()
    amt_numeric = pd.to_numeric(res[amount_column], errors="coerce")

    if amt_numeric.isna().any() or (amt_numeric <= 0).any():
        invalid_count = int(amt_numeric.isna().sum() + (amt_numeric <= 0).sum())
        raise ValueError(f"Column '{amount_column}' contains {invalid_count} non-positive, non-numeric, or missing values.")

    res["log_amount"] = np.log1p(amt_numeric.astype(float)).round(4)
    return res


def extract_temporal_sequence_features(
    df: pd.DataFrame,
    date_column: str = "date",
    amount_column: str = "amount",
    type_column: str = "type",
    id_column: str = "transaction_id",
    restore_order: bool = True,
) -> pd.DataFrame:
    """Derive chronological sequence, lag, and historical rolling window features.

    Features generated:
    - 'days_since_prev_txn': Calendar days elapsed since the immediately prior transaction (NaN for 1st txn).
    - 'prev_amount': Amount of the immediately prior transaction (lag 1) (NaN for 1st txn).
    - 'days_since_prev_expense': Calendar days since the immediately prior expense transaction (NaN for 1st expense and Income rows).
    - 'prev_expense_amount': Amount of the immediately prior expense transaction (NaN for 1st expense and Income rows).
    - 'rolling_expense_7d_sum': Total expense volume in the prior 7-day calendar window (excluding current transaction date).
    - 'rolling_expense_7d_mean': Mean expense ticket size in the prior 7-day calendar window.
    - 'rolling_expense_7d_count': Number of expense transactions in the prior 7-day calendar window.
    - 'rolling_expense_30d_sum': Total expense volume in the prior 30-day calendar window (excluding current transaction date).
    - 'rolling_expense_30d_mean': Mean expense ticket size in the prior 30-day calendar window.
    - 'rolling_expense_30d_count': Number of expense transactions in the prior 30-day calendar window.

    Safeguards:
    - Strictly past-looking: `closed='left'` ensures no future information leakage.
    - Expense-isolated: Income transactions do NOT contaminate expense rolling statistics.
    - Preserves input order: If `restore_order=True`, restores original caller-supplied row order.

    Args:
        df: Input DataFrame.
        date_column: Transaction date column.
        amount_column: Transaction monetary amount column.
        type_column: Transaction flow type column.
        id_column: Unique transaction identifier column for deterministic secondary sorting.
        restore_order: If True, returns rows matching the original input index.

    Returns:
        New DataFrame augmented with temporal sequence and rolling window features.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    temporal_cols = [
        "days_since_prev_txn", "prev_amount",
        "days_since_prev_expense", "prev_expense_amount",
        "rolling_expense_7d_sum", "rolling_expense_7d_mean", "rolling_expense_7d_count",
        "rolling_expense_30d_sum", "rolling_expense_30d_mean", "rolling_expense_30d_count",
    ]

    if df.empty:
        res = df.copy()
        for c in temporal_cols:
            res[c] = pd.Series(dtype=float)
        return res

    for col in [date_column, amount_column, type_column]:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in DataFrame.")

    res = df.copy()
    orig_index = res.index

    # Parse dates strictly
    parsed_dates = [parse_explicit_date(d) for d in res[date_column]]
    if any(p is None for p in parsed_dates):
        invalid_idx = next(i for i, p in enumerate(parsed_dates) if p is None)
        raise ValueError(f"Column '{date_column}' contains invalid date at row {invalid_idx}: '{res[date_column].iloc[invalid_idx]}'.")

    res["_dt"] = pd.to_datetime(parsed_dates)
    sort_cols = ["_dt"]
    if id_column in res.columns:
        sort_cols.append(id_column)
    res_sorted = res.sort_values(by=sort_cols).copy()

    # 1. Overall transaction sequence features
    res_sorted["days_since_prev_txn"] = res_sorted["_dt"].diff().dt.total_seconds() / 86400.0
    res_sorted["prev_amount"] = res_sorted[amount_column].shift(1)

    # 2. Expense-specific sequence lags (isolated to Expense transactions)
    res_sorted["days_since_prev_expense"] = np.nan
    res_sorted["prev_expense_amount"] = np.nan

    exp_mask = res_sorted[type_column] == "Expense"
    exp_indices = res_sorted[exp_mask].index

    if len(exp_indices) > 0:
        exp_sub = res_sorted.loc[exp_indices].copy()
        res_sorted.loc[exp_indices, "days_since_prev_expense"] = exp_sub["_dt"].diff().dt.total_seconds() / 86400.0
        res_sorted.loc[exp_indices, "prev_expense_amount"] = exp_sub[amount_column].shift(1)

    # 3. Date-level historical rolling expense baseline [T-W, T)
    # Built strictly from expense transactions, and attached to EVERY transaction on date T (including income)
    for c in [
        "rolling_expense_7d_sum", "rolling_expense_7d_mean", "rolling_expense_7d_count",
        "rolling_expense_30d_sum", "rolling_expense_30d_mean", "rolling_expense_30d_count",
    ]:
        res_sorted[c] = np.nan

    if len(exp_indices) > 0:
        daily_exp = exp_sub.groupby("_dt")[amount_column].agg(daily_sum="sum", daily_count="count")

        min_date = res_sorted["_dt"].min()
        max_date = res_sorted["_dt"].max()
        full_dates = pd.date_range(min_date, max_date, freq="D")
        daily_full = daily_exp.reindex(full_dates, fill_value=0.0)

        # 7-day rolling window
        r7_sum = daily_full["daily_sum"].rolling("7D", closed="left").sum()
        r7_count = daily_full["daily_count"].rolling("7D", closed="left").sum()
        r7_mean = (r7_sum / r7_count).replace([np.inf, -np.inf], np.nan)

        # Empty window policy: when no prior expenses exist in lookback window, features evaluate to NaN
        empty_7 = (r7_count == 0) | (r7_count.isna())
        r7_sum[empty_7] = np.nan
        r7_count[empty_7] = np.nan
        r7_mean[empty_7] = np.nan

        # 30-day rolling window
        r30_sum = daily_full["daily_sum"].rolling("30D", closed="left").sum()
        r30_count = daily_full["daily_count"].rolling("30D", closed="left").sum()
        r30_mean = (r30_sum / r30_count).replace([np.inf, -np.inf], np.nan)

        empty_30 = (r30_count == 0) | (r30_count.isna())
        r30_sum[empty_30] = np.nan
        r30_count[empty_30] = np.nan
        r30_mean[empty_30] = np.nan

        date_stats = pd.DataFrame({
            "rolling_expense_7d_sum": r7_sum,
            "rolling_expense_7d_mean": r7_mean,
            "rolling_expense_7d_count": r7_count,
            "rolling_expense_30d_sum": r30_sum,
            "rolling_expense_30d_mean": r30_mean,
            "rolling_expense_30d_count": r30_count,
        }, index=full_dates)

        for col in date_stats.columns:
            res_sorted[col] = res_sorted["_dt"].map(date_stats[col])

    res_sorted = res_sorted.drop(columns=["_dt"])

    if restore_order:
        res_sorted = res_sorted.loc[orig_index]

    return res_sorted


def encode_categorical_features(
    df: pd.DataFrame,
    category_column: str = "category",
    payment_column: str = "payment_method",
) -> pd.DataFrame:
    """Produce stable, documented one-hot encodings for categories and payment instruments.

    Creates fixed binary columns:
    - 17 category indicator columns prefixed with 'cat_' (e.g. 'cat_salary', 'cat_groceries').
    - 5 payment indicator columns prefixed with 'pay_' (e.g. 'pay_upi', 'pay_credit_card').

    Unseen categories are safely encoded as all zeros across standard dummy columns.
    Original human-readable columns are preserved.

    Args:
        df: Input DataFrame.
        category_column: Name of the transaction category column.
        payment_column: Name of the payment method column.

    Returns:
        New DataFrame augmented with one-hot encoded binary indicator columns.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    res = df.copy()

    # 1. Category dummies
    if category_column in res.columns:
        for cat in CANONICAL_CATEGORIES:
            col_name = f"cat_{_slugify(cat)}"
            res[col_name] = (res[category_column] == cat).astype(int)
    else:
        for cat in CANONICAL_CATEGORIES:
            res[f"cat_{_slugify(cat)}"] = pd.Series(0, index=res.index, dtype=int)

    # 2. Payment method dummies
    if payment_column in res.columns:
        for pay in CANONICAL_PAYMENT_METHODS:
            col_name = f"pay_{_slugify(pay)}"
            res[col_name] = (res[payment_column] == pay).astype(int)
    else:
        for pay in CANONICAL_PAYMENT_METHODS:
            res[f"pay_{_slugify(pay)}"] = pd.Series(0, index=res.index, dtype=int)

    return res


def extract_text_features(
    df: pd.DataFrame,
    text_column: str = "description",
) -> pd.DataFrame:
    """Extract descriptive text metadata (character length and word count).

    Target Leakage Precaution:
    Raw transaction descriptions and ground-truth shock labels ('[UNUSUAL]') are
    strictly excluded from model training feature matrices.

    Args:
        df: Input DataFrame.
        text_column: Name of the description column.

    Returns:
        New DataFrame augmented with 'desc_char_length' and 'desc_word_count'.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if df.empty:
        res = df.copy()
        res["desc_char_length"] = pd.Series(dtype=int)
        res["desc_word_count"] = pd.Series(dtype=int)
        return res

    if text_column not in df.columns:
        raise ValueError(f"Text column '{text_column}' not found in DataFrame.")

    res = df.copy()
    desc_str = res[text_column].astype(str)
    res["desc_char_length"] = desc_str.str.len().astype(int)
    res["desc_word_count"] = desc_str.str.split().str.len().astype(int)
    return res


def extract_ground_truth_labels(
    df: pd.DataFrame,
    text_column: str = "description",
) -> pd.Series:
    """Extract synthetic ground-truth anomaly indicator from description.

    Returns:
        pd.Series of binary integers (1 if '[UNUSUAL]' in description, 0 otherwise).
        Designated exclusively as an evaluation ground-truth label for benchmarking
        Phase 6 anomaly detection algorithms. Must NEVER be provided as an input feature
        to any machine learning training routine (target leakage prevention).
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if df.empty or text_column not in df.columns:
        return pd.Series(dtype=int)

    return df[text_column].astype(str).str.contains(r"\[UNUSUAL\]", regex=True).astype(int)


def engineer_features(
    df: pd.DataFrame,
    include_categorical_encoding: bool = False,
    restore_order: bool = True,
) -> pd.DataFrame:
    """Execute the full feature-engineering pipeline on validated financial transactions.

    Pipeline stages:
    1. Input isolation: Creates a deep copy guaranteeing zero mutation of caller's DataFrame.
    2. Calendar features: Extracts year, month, quarter, day of week, day of month, and weekend indicator.
    3. Flow indicators: Generates binary flags ('is_income', 'is_expense').
    4. Amount transformations: Generates log-transformed amount ('log_amount').
    5. Temporal sequence: Generates lag features and strictly past-looking 7D/30D rolling expense stats.
    6. Text metadata: Generates character length and word count for exploratory/evaluation tracking.
    7. Optional one-hot encodings: Appends 17 category and 5 payment method dummy columns.

    Args:
        df: Input DataFrame conforming to transaction schema.
        include_categorical_encoding: If True, appends one-hot encoded category and payment dummies.
        restore_order: If True, guarantees output row order matches the input DataFrame.

    Returns:
        New enriched DataFrame containing all original columns plus engineered features.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if df.empty:
        # Return empty copy with enriched schema
        empty_cal = extract_calendar_features(df)
        empty_flow = extract_flow_indicators(empty_cal)
        empty_amt = extract_amount_features(empty_flow)
        empty_seq = extract_temporal_sequence_features(empty_amt)
        if "description" in empty_seq.columns:
            empty_seq = extract_text_features(empty_seq)
        if include_categorical_encoding:
            empty_seq = encode_categorical_features(empty_seq)
        return empty_seq

    # 1. Calendar features
    enriched = extract_calendar_features(df)

    # 2. Flow indicators
    enriched = extract_flow_indicators(enriched)

    # 3. Amount features
    enriched = extract_amount_features(enriched)

    # 4. Temporal sequence & rolling features
    enriched = extract_temporal_sequence_features(enriched, restore_order=restore_order)

    # 5. Text metadata features
    if "description" in enriched.columns:
        enriched = extract_text_features(enriched)

    # 6. Categorical encodings (optional)
    if include_categorical_encoding:
        enriched = encode_categorical_features(enriched)

    return enriched


def get_model_feature_matrix(
    df: pd.DataFrame,
    include_categorical_dummies: bool = True,
    drop_na_rows: bool = False,
) -> pd.DataFrame:
    """Extract a clean, numeric modeling feature matrix strictly devoid of target leakage.

    Enforces strict safeguards:
    - Eliminates 'transaction_id' (entity identifier).
    - Eliminates raw 'description' (prevents '[UNUSUAL]' label leakage).
    - Eliminates description-derived text features ('desc_char_length', 'desc_word_count')
      to prevent proxy leakage of synthetic evaluation shock markers.
    - Eliminates raw 'date' strings / timestamps (calendar features represent temporal signals).
    - Eliminates raw categorical text strings ('category', 'payment_method', 'type', 'month_name', 'day_name').
    - Eliminates evaluation target labels ('is_unusual_ground_truth').

    Args:
        df: Enriched transaction DataFrame.
        include_categorical_dummies: If True, includes stable one-hot encoded category and payment features.
        drop_na_rows: If True, drops initial warm-up rows containing NaNs from historical rolling/lag windows.

    Returns:
        pd.DataFrame containing strictly approved numeric modeling features.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if df.empty:
        return pd.DataFrame()

    matrix = df.copy()

    # Ensure categorical dummies exist if requested
    if include_categorical_dummies:
        has_dummies = any(c.startswith("cat_") for c in matrix.columns)
        if not has_dummies and "category" in matrix.columns:
            matrix = encode_categorical_features(matrix)

    # Explicit list of columns strictly banned from the modeling matrix to prevent target leakage
    banned_columns = [
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

    cols_to_drop = [
        c for c in matrix.columns
        if c in banned_columns
        or c.startswith("desc_")
        or "ground_truth" in c
        or "unusual" in c
    ]
    matrix = matrix.drop(columns=cols_to_drop)

    # Retain strictly numerical or boolean columns
    numeric_cols = [c for c in matrix.columns if pd.api.types.is_numeric_dtype(matrix[c])]
    matrix = matrix[numeric_cols]

    if drop_na_rows:
        matrix = matrix.dropna()

    return matrix
