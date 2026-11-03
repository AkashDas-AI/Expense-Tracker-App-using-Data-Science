"""
Financial Metrics Module

Author: Akash Das
Description: Reusable, robust financial KPIs and cash-flow indicator calculations
             including total income, total expenditure, net savings, savings rate,
             and expense-to-income ratios in Indian Rupees (₹ / INR).
"""

from typing import Any, Dict, Optional
import numpy as np
import pandas as pd


def _validate_financial_input(df: pd.DataFrame, required_columns: Optional[list] = None) -> None:
    """Validate DataFrame type, required columns, and numeric integrity."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if required_columns is None:
        required_columns = ["type", "amount"]

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


def calculate_total_income(df: pd.DataFrame) -> float:
    """Calculate aggregate income across all income transactions.

    Args:
        df: Transaction DataFrame containing 'type' and 'amount'.

    Returns:
        Total income in INR as a float rounded to 2 decimal places. Returns 0.0 for empty data.
    """
    _validate_financial_input(df)
    if df.empty:
        return 0.0
    inc_mask = df["type"] == "Income"
    total = float(df.loc[inc_mask, "amount"].sum())
    return round(total, 2)


def calculate_total_expenses(df: pd.DataFrame) -> float:
    """Calculate aggregate expenditure across all expense transactions.

    Args:
        df: Transaction DataFrame containing 'type' and 'amount'.

    Returns:
        Total expenses in INR as a float rounded to 2 decimal places. Returns 0.0 for empty data.
    """
    _validate_financial_input(df)
    if df.empty:
        return 0.0
    exp_mask = df["type"] == "Expense"
    total = float(df.loc[exp_mask, "amount"].sum())
    return round(total, 2)


def calculate_net_savings(df: pd.DataFrame) -> float:
    """Calculate net savings = Total Income - Total Expenses.

    Args:
        df: Transaction DataFrame containing 'type' and 'amount'.

    Returns:
        Net savings in INR rounded to 2 decimal places. Can be negative (net deficit).
    """
    _validate_financial_input(df)
    if df.empty:
        return 0.0
    net = calculate_total_income(df) - calculate_total_expenses(df)
    return round(net, 2)


def calculate_savings_rate(
    df: pd.DataFrame,
    zero_income_default: float = np.nan,
) -> float:
    """Calculate savings rate percentage = (Net Savings / Total Income) * 100.

    Zero-Income Policy:
    When total income is 0.0:
    - If total expenses are also 0.0 (no activity), returns 0.0.
    - If expenses exist without income, the rate is mathematically undefined and returns
      `zero_income_default` (default: np.nan).

    Args:
        df: Transaction DataFrame containing 'type' and 'amount'.
        zero_income_default: Value to return when total income is 0 but expenses > 0.

    Returns:
        Savings rate percentage rounded to 2 decimal places, or zero_income_default.
    """
    _validate_financial_input(df)
    if df.empty:
        return 0.0

    income = calculate_total_income(df)
    expenses = calculate_total_expenses(df)

    if income == 0.0:
        return 0.0 if expenses == 0.0 else zero_income_default

    rate = ((income - expenses) / income) * 100.0
    return round(rate, 2)


def calculate_expense_to_income_ratio(
    df: pd.DataFrame,
    zero_income_default: float = np.nan,
) -> float:
    """Calculate ratio of total expenses to total income = Total Expenses / Total Income.

    Zero-Income Policy:
    When total income is 0.0:
    - If total expenses are also 0.0, returns 0.0.
    - If expenses exist without income, returns zero_income_default (default: np.nan).

    Args:
        df: Transaction DataFrame containing 'type' and 'amount'.
        zero_income_default: Value to return when income is 0 but expenses > 0.

    Returns:
        Ratio rounded to 4 decimal places, or zero_income_default.
    """
    _validate_financial_input(df)
    if df.empty:
        return 0.0

    income = calculate_total_income(df)
    expenses = calculate_total_expenses(df)

    if income == 0.0:
        return 0.0 if expenses == 0.0 else zero_income_default

    ratio = expenses / income
    return round(ratio, 4)


def calculate_average_income(df: pd.DataFrame) -> float:
    """Calculate mean ticket size of income transactions.

    Args:
        df: Transaction DataFrame containing 'type' and 'amount'.

    Returns:
        Average income in INR rounded to 2 decimal places. Returns 0.0 if no income records.
    """
    _validate_financial_input(df)
    if df.empty:
        return 0.0
    inc_df = df[df["type"] == "Income"]
    if inc_df.empty:
        return 0.0
    avg = float(inc_df["amount"].mean())
    return round(avg, 2)


def calculate_average_expense(df: pd.DataFrame) -> float:
    """Calculate mean ticket size of expense transactions.

    Args:
        df: Transaction DataFrame containing 'type' and 'amount'.

    Returns:
        Average expense in INR rounded to 2 decimal places. Returns 0.0 if no expense records.
    """
    _validate_financial_input(df)
    if df.empty:
        return 0.0
    exp_df = df[df["type"] == "Expense"]
    if exp_df.empty:
        return 0.0
    avg = float(exp_df["amount"].mean())
    return round(avg, 2)


def calculate_median_expense(df: pd.DataFrame) -> float:
    """Calculate median ticket size of expense transactions.

    Args:
        df: Transaction DataFrame containing 'type' and 'amount'.

    Returns:
        Median expense in INR rounded to 2 decimal places. Returns 0.0 if no expense records.
    """
    _validate_financial_input(df)
    if df.empty:
        return 0.0
    exp_df = df[df["type"] == "Expense"]
    if exp_df.empty:
        return 0.0
    median_val = float(exp_df["amount"].median())
    return round(median_val, 2)


def calculate_transaction_counts(df: pd.DataFrame) -> Dict[str, int]:
    """Count transactions partitioned by flow direction.

    Args:
        df: Transaction DataFrame containing 'type'.

    Returns:
        Dictionary with keys 'total', 'income', and 'expense'.
    """
    _validate_financial_input(df, required_columns=["type"])
    if df.empty:
        return {"total": 0, "income": 0, "expense": 0}

    total = len(df)
    income_count = int((df["type"] == "Income").sum())
    expense_count = int((df["type"] == "Expense").sum())

    return {
        "total": total,
        "income": income_count,
        "expense": expense_count,
    }


def compute_financial_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate comprehensive suite of high-level financial health indicators.

    Notice on Synthetic Data:
    These KPI calculations reflect the underlying parameters of the synthetic dataset
    and demonstrate financial data engineering algorithms. They must not be interpreted
    as actual individual household finances.

    Args:
        df: Transaction DataFrame containing 'type' and 'amount'.

    Returns:
        Dictionary containing all primary financial KPIs:
        - total_income (float)
        - total_expenses (float)
        - net_savings (float)
        - savings_rate_pct (float)
        - expense_to_income_ratio (float)
        - total_transactions (int)
        - income_count (int)
        - expense_count (int)
        - average_income / avg_income_transaction (float)
        - average_expense / avg_expense_transaction (float)
        - median_expense / median_expense_transaction (float)
        - transaction_counts (dict)
    """
    _validate_financial_input(df)

    counts = calculate_transaction_counts(df)
    tot_inc = calculate_total_income(df)
    tot_exp = calculate_total_expenses(df)
    net_sav = calculate_net_savings(df)
    sav_rate = calculate_savings_rate(df)
    ratio = calculate_expense_to_income_ratio(df)
    avg_inc = calculate_average_income(df)
    avg_exp = calculate_average_expense(df)
    med_exp = calculate_median_expense(df)

    return {
        "total_income": tot_inc,
        "total_expenses": tot_exp,
        "net_savings": net_sav,
        "savings_rate_pct": sav_rate,
        "expense_to_income_ratio": ratio,
        "total_transactions": counts["total"],
        "income_count": counts["income"],
        "expense_count": counts["expense"],
        "average_income": avg_inc,
        "average_expense": avg_exp,
        "median_expense": med_exp,
        "avg_income_transaction": avg_inc,
        "avg_expense_transaction": avg_exp,
        "median_expense_transaction": med_exp,
        "transaction_counts": counts,
    }
