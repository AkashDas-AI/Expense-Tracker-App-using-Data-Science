"""
Spending Analysis Module

Author: Akash Das
Description: Category-level and payment-method spending aggregations, breakdowns,
             and rankings in Indian Rupees (₹ / INR).
"""

from typing import Any, Dict, Optional
import numpy as np
import pandas as pd


def _validate_spending_input(df: pd.DataFrame, required_columns: list) -> None:
    """Validate DataFrame type and presence of required columns."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in DataFrame.")

    if not df.empty and "amount" in df.columns:
        amt_numeric = pd.to_numeric(df["amount"], errors="coerce")
        if amt_numeric.isna().any() or np.isinf(amt_numeric).any():
            nan_count = int(amt_numeric.isna().sum() + np.isinf(amt_numeric).sum())
            raise ValueError(f"Column 'amount' contains {nan_count} non-numeric or infinite values.")
        if (amt_numeric < 0).any():
            neg_count = int((amt_numeric < 0).sum())
            raise ValueError(f"Column 'amount' contains {neg_count} negative values.")


def get_spending_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate expenditure broken down by expense category.

    Requirements:
    - Excludes income transactions entirely from calculation.
    - Computes category total, percentage of total expenses, transaction count,
      average ticket size, and median ticket size.
    - Sorts categories descending by total spending amount.

    Args:
        df: Transaction DataFrame containing 'type', 'category', and 'amount'.

    Returns:
        pd.DataFrame with columns:
        ['category', 'total_amount', 'percentage', 'transaction_count', 'average_amount', 'median_amount']
    """
    _validate_spending_input(df, ["type", "category", "amount"])

    output_cols = [
        "category",
        "total_amount",
        "percentage",
        "transaction_count",
        "average_amount",
        "median_amount",
    ]

    if df.empty:
        return pd.DataFrame(columns=output_cols)

    exp_df = df[df["type"] == "Expense"].copy()
    if exp_df.empty:
        return pd.DataFrame(columns=output_cols)

    total_expense = exp_df["amount"].sum()

    grouped = (
        exp_df.groupby("category", as_index=False)
        .agg(
            total_amount=("amount", "sum"),
            transaction_count=("amount", "count"),
            average_amount=("amount", "mean"),
            median_amount=("amount", "median"),
        )
        .sort_values(by="total_amount", ascending=False)
        .reset_index(drop=True)
    )

    if total_expense > 0:
        grouped["percentage"] = ((grouped["total_amount"] / total_expense) * 100.0).round(2)
    else:
        grouped["percentage"] = 0.0

    grouped["total_amount"] = grouped["total_amount"].round(2)
    grouped["average_amount"] = grouped["average_amount"].round(2)
    grouped["median_amount"] = grouped["median_amount"].round(2)

    return grouped[output_cols]


def get_highest_spending_category(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """Identify the single expense category with the highest monetary expenditure.

    Args:
        df: Transaction DataFrame containing 'type', 'category', and 'amount'.

    Returns:
        Dictionary detailing highest-spending category, or None if no expenses exist.
    """
    cat_df = get_spending_by_category(df)
    if cat_df.empty:
        return None

    top_row = cat_df.iloc[0]
    return {
        "category": str(top_row["category"]),
        "total_amount": float(top_row["total_amount"]),
        "percentage": float(top_row["percentage"]),
        "transaction_count": int(top_row["transaction_count"]),
        "average_amount": float(top_row["average_amount"]),
        "median_amount": float(top_row["median_amount"]),
    }


def get_top_n_expense_categories(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Retrieve the top N expense categories ranked by total expenditure.

    Args:
        df: Transaction DataFrame containing 'type', 'category', and 'amount'.
        n: Number of categories to return (must be positive integer).

    Returns:
        pd.DataFrame containing top N ranked categories.

    Raises:
        TypeError: If n is not an integer.
        ValueError: If n <= 0.
    """
    if not isinstance(n, int):
        raise TypeError(f"Expected integer for 'n', got {type(n).__name__}.")
    if n <= 0:
        raise ValueError(f"Parameter 'n' must be a positive integer, got {n}.")

    cat_df = get_spending_by_category(df)
    return cat_df.head(n).reset_index(drop=True)


def get_spending_by_payment_method(
    df: pd.DataFrame,
    expense_only: bool = True,
) -> pd.DataFrame:
    """Aggregate expenditure broken down by payment method/channel.

    Args:
        df: Transaction DataFrame containing 'payment_method', 'amount', and optionally 'type'.
        expense_only: If True, aggregates strictly Expense transactions. If False, aggregates all.

    Returns:
        pd.DataFrame with columns:
        ['payment_method', 'total_amount', 'percentage', 'transaction_count', 'average_amount']
    """
    req_cols = ["payment_method", "amount"]
    if expense_only:
        req_cols.append("type")
    _validate_spending_input(df, req_cols)

    output_cols = [
        "payment_method",
        "total_amount",
        "percentage",
        "transaction_count",
        "average_amount",
    ]

    if df.empty:
        return pd.DataFrame(columns=output_cols)

    target_df = df[df["type"] == "Expense"].copy() if expense_only else df.copy()
    if target_df.empty:
        return pd.DataFrame(columns=output_cols)

    total_amount = target_df["amount"].sum()

    grouped = (
        target_df.groupby("payment_method", as_index=False)
        .agg(
            total_amount=("amount", "sum"),
            transaction_count=("amount", "count"),
            average_amount=("amount", "mean"),
        )
        .sort_values(by="total_amount", ascending=False)
        .reset_index(drop=True)
    )

    if total_amount > 0:
        grouped["percentage"] = ((grouped["total_amount"] / total_amount) * 100.0).round(2)
    else:
        grouped["percentage"] = 0.0

    grouped["total_amount"] = grouped["total_amount"].round(2)
    grouped["average_amount"] = grouped["average_amount"].round(2)

    return grouped[output_cols]


def get_income_vs_expense_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Produce a comparative breakdown of Income versus Expense cash flows.

    Args:
        df: Transaction DataFrame containing 'type' and 'amount'.

    Returns:
        pd.DataFrame with columns:
        ['type', 'total_amount', 'transaction_count', 'average_amount', 'percentage_of_total_volume']
    """
    _validate_spending_input(df, ["type", "amount"])

    output_cols = [
        "type",
        "total_amount",
        "transaction_count",
        "average_amount",
        "percentage_of_total_volume",
    ]

    rows = []
    total_volume = df["amount"].sum() if not df.empty else 0.0

    for flow_type in ["Income", "Expense"]:
        sub = df[df["type"] == flow_type] if not df.empty else pd.DataFrame()
        count = len(sub)
        total = float(sub["amount"].sum()) if count > 0 else 0.0
        avg = float(sub["amount"].mean()) if count > 0 else 0.0
        pct = (total / total_volume * 100.0) if total_volume > 0 else 0.0

        rows.append({
            "type": flow_type,
            "total_amount": round(total, 2),
            "transaction_count": count,
            "average_amount": round(avg, 2),
            "percentage_of_total_volume": round(pct, 2),
        })

    return pd.DataFrame(rows, columns=output_cols)


def get_monthly_spending_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate expense spending grouped chronologically by month.

    Args:
        df: Transaction DataFrame containing 'date', 'type', and 'amount'.

    Returns:
        pd.DataFrame with columns ['month', 'total_amount', 'transaction_count', 'average_amount'].
    """
    _validate_spending_input(df, ["date", "type", "amount"])

    output_cols = ["month", "total_amount", "transaction_count", "average_amount"]
    if df.empty:
        return pd.DataFrame(columns=output_cols)

    exp_df = df[df["type"] == "Expense"].copy()
    if exp_df.empty:
        return pd.DataFrame(columns=output_cols)

    dt_series = pd.to_datetime(exp_df["date"])
    exp_df["month"] = dt_series.dt.to_period("M").astype(str)

    monthly = (
        exp_df.groupby("month", as_index=False)
        .agg(
            total_amount=("amount", "sum"),
            transaction_count=("amount", "count"),
            average_amount=("amount", "mean"),
        )
        .sort_values(by="month")
        .reset_index(drop=True)
    )

    monthly["total_amount"] = monthly["total_amount"].round(2)
    monthly["average_amount"] = monthly["average_amount"].round(2)

    return monthly[output_cols]
