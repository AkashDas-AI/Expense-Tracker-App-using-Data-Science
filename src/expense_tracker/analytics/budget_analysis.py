"""
Budget Analysis Module

Author: Akash Das
Description: Category-level budget tracking, variance analysis, utilization rates,
             and portfolio budget health summarization in Indian Rupees (₹ / INR).
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd


def _normalize_budget_input(budgets: Union[Dict[str, float], pd.DataFrame]) -> Dict[str, float]:
    """Validate and normalize budget input into a mapping of category to budget amount.

    Args:
        budgets: Budget specification as a dictionary {category: amount} or
                 DataFrame with 'category' and 'budget_amount' columns.

    Returns:
        Dict[str, float]: Clean category-to-budget mapping.

    Raises:
        TypeError: If budgets is neither a dict nor a DataFrame.
        ValueError: If required columns are missing, duplicate categories exist,
                    or amounts are negative, non-numeric, or infinite.
    """
    if isinstance(budgets, pd.DataFrame):
        for col in ["category", "budget_amount"]:
            if col not in budgets.columns:
                raise ValueError(f"Budget DataFrame must contain required column '{col}'.")

        if budgets["category"].duplicated().any():
            dup_cats = budgets.loc[budgets["category"].duplicated(), "category"].tolist()
            raise ValueError(f"Duplicate categories found in budget definition: {dup_cats}.")

        b_amt = pd.to_numeric(budgets["budget_amount"], errors="coerce")
        if b_amt.isna().any() or np.isinf(b_amt).any():
            nan_count = int(b_amt.isna().sum() + np.isinf(b_amt).sum())
            raise ValueError(f"Budget amounts contain {nan_count} non-numeric or infinite values.")
        if (b_amt < 0).any():
            neg_count = int((b_amt < 0).sum())
            raise ValueError(f"Budget amounts cannot be negative; found {neg_count} negative entries.")

        return dict(zip(budgets["category"].astype(str), b_amt.astype(float)))

    elif isinstance(budgets, dict):
        budget_dict: Dict[str, float] = {}
        for cat, val in budgets.items():
            if not isinstance(cat, str) or not cat.strip():
                raise ValueError(f"Invalid category identifier in budget: {cat!r}.")
            try:
                numeric_val = float(val)
            except (ValueError, TypeError):
                raise ValueError(f"Budget amount for category '{cat}' must be numeric, got {val!r}.")

            if np.isnan(numeric_val) or np.isinf(numeric_val):
                raise ValueError(f"Budget amount for category '{cat}' must be finite numeric.")
            if numeric_val < 0:
                raise ValueError(f"Budget amount for category '{cat}' cannot be negative ({numeric_val}).")

            budget_dict[str(cat).strip()] = numeric_val

        return budget_dict

    else:
        raise TypeError(f"Budgets must be a dictionary or DataFrame, got {type(budgets).__name__}.")


def _extract_category_spending(actual_spending: pd.DataFrame) -> Dict[str, float]:
    """Validate and aggregate expense spending by category from input DataFrame.

    Supports raw transaction DataFrames (with 'type', 'category', 'amount') or
    pre-aggregated DataFrames (with 'category' and 'total_amount' / 'amount').

    Args:
        actual_spending: Input DataFrame.

    Returns:
        Dict[str, float]: Total actual expense spend per category.

    Raises:
        TypeError: If actual_spending is not a DataFrame.
        ValueError: If required columns are missing, or amounts are non-numeric or negative.
    """
    if not isinstance(actual_spending, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame for actual_spending, got {type(actual_spending).__name__}.")

    if actual_spending.empty:
        return {}

    if "category" not in actual_spending.columns:
        raise ValueError("Column 'category' not found in actual_spending DataFrame.")

    amt_col = "total_amount" if "total_amount" in actual_spending.columns else "amount"
    if amt_col not in actual_spending.columns:
        raise ValueError("DataFrame must contain 'amount' or 'total_amount' column.")

    amt_numeric = pd.to_numeric(actual_spending[amt_col], errors="coerce")
    if amt_numeric.isna().any() or np.isinf(amt_numeric).any():
        nan_count = int(amt_numeric.isna().sum() + np.isinf(amt_numeric).sum())
        raise ValueError(f"Column '{amt_col}' contains {nan_count} non-numeric or infinite values.")
    if (amt_numeric < 0).any():
        neg_count = int((amt_numeric < 0).sum())
        raise ValueError(f"Column '{amt_col}' contains {neg_count} negative values.")

    df_clean = actual_spending.copy()
    df_clean[amt_col] = amt_numeric

    # If transaction 'type' is present, strictly filter to 'Expense'
    if "type" in df_clean.columns:
        df_clean = df_clean[df_clean["type"] == "Expense"]
        if df_clean.empty:
            return {}

    spending_series = df_clean.groupby("category")[amt_col].sum()
    return {str(cat): float(val) for cat, val in spending_series.items()}


def compute_budget_variance(
    actual_spending: pd.DataFrame,
    budgets: Union[Dict[str, float], pd.DataFrame],
    include_unbudgeted: bool = False,
) -> pd.DataFrame:
    """Compare actual category expenditure against budgeted allocations.

    Calculates for each category:
    - budget_amount: Allocated budget in INR.
    - actual_amount: Actual expenditure in INR (0.0 if no transactions).
    - remaining_budget: Budget surplus = budget_amount - actual_amount.
    - budget_variance: Budget overage = actual_amount - budget_amount (positive = over budget).
    - utilization_pct: Percentage of budget spent = (actual_amount / budget_amount) * 100.
    - is_over_budget: Boolean flag indicating if actual spending exceeded budget.

    If `include_unbudgeted` is True:
    Categories with actual spending but no allocated budget are included with:
    - budget_amount: np.nan
    - remaining_budget: np.nan
    - budget_variance: np.nan
    - utilization_pct: np.nan
    - is_over_budget: pd.NA (nullable boolean; status is unbudgeted/not-assessable)

    Args:
        actual_spending: Transaction DataFrame or pre-aggregated spending DataFrame.
        budgets: Budget specification as Dict[str, float] or DataFrame.
        include_unbudgeted: Whether to include unbudgeted spending categories.

    Returns:
        pd.DataFrame with columns:
        ['category', 'budget_amount', 'actual_amount', 'remaining_budget',
         'budget_variance', 'utilization_pct', 'is_over_budget']
    """
    budget_dict = _normalize_budget_input(budgets)
    cat_spending = _extract_category_spending(actual_spending)

    output_cols = [
        "category",
        "budget_amount",
        "actual_amount",
        "remaining_budget",
        "budget_variance",
        "utilization_pct",
        "is_over_budget",
    ]

    records: List[Dict[str, Any]] = []

    # Process budgeted categories
    for category, budget_amt in budget_dict.items():
        actual_amt = cat_spending.get(category, 0.0)
        remaining = budget_amt - actual_amt
        variance = actual_amt - budget_amt

        if budget_amt > 0:
            util_pct = (actual_amt / budget_amt) * 100.0
        else:
            util_pct = 0.0 if actual_amt == 0.0 else np.nan

        is_over = bool(actual_amt > budget_amt)

        records.append({
            "category": category,
            "budget_amount": round(float(budget_amt), 2),
            "actual_amount": round(float(actual_amt), 2),
            "remaining_budget": round(float(remaining), 2),
            "budget_variance": round(float(variance), 2),
            "utilization_pct": round(float(util_pct), 2) if not np.isnan(util_pct) else np.nan,
            "is_over_budget": is_over,
        })

    # Process unbudgeted categories if requested
    if include_unbudgeted:
        for cat, actual_amt in cat_spending.items():
            if cat not in budget_dict and actual_amt > 0:
                records.append({
                    "category": cat,
                    "budget_amount": np.nan,
                    "actual_amount": round(float(actual_amt), 2),
                    "remaining_budget": np.nan,
                    "budget_variance": np.nan,
                    "utilization_pct": np.nan,
                    "is_over_budget": pd.NA,
                })

    if not records:
        empty_df = pd.DataFrame(columns=output_cols)
        empty_df["is_over_budget"] = empty_df["is_over_budget"].astype("boolean")
        return empty_df

    res_df = pd.DataFrame(records, columns=output_cols)
    res_df["is_over_budget"] = res_df["is_over_budget"].astype("boolean")
    return res_df


def compute_budget_summary(
    actual_spending: pd.DataFrame,
    budgets: Union[Dict[str, float], pd.DataFrame],
    include_unbudgeted: bool = False,
) -> Dict[str, Any]:
    """Compute aggregate portfolio-level budget health and variance KPIs.

    Summary counts strictly distinguish:
    - Genuinely over-budget categories (is_over_budget == True).
    - Genuinely under-budget categories (is_over_budget == False).
    - Unbudgeted / not-assessable categories (is_over_budget is pd.NA), which are
      strictly excluded from over-budget and under-budget counts.

    Args:
        actual_spending: Transaction DataFrame or pre-aggregated spending DataFrame.
        budgets: Budget specification as Dict[str, float] or DataFrame.
        include_unbudgeted: Whether to include unbudgeted spending categories in the summary.

    Returns:
        Dict[str, Any] containing:
        - total_budget: Total allocated budget across budgeted categories (INR).
        - total_actual_spend: Total actual spending across analyzed categories (INR).
        - budgeted_actual_spend: Actual spending strictly for budgeted categories (INR).
        - unbudgeted_actual_spend: Actual spending strictly for unbudgeted categories (INR).
        - overall_variance: total_actual_spend - total_budget (INR).
        - overall_remaining: total_budget - total_actual_spend (INR).
        - overall_utilization_pct: (total_actual_spend / total_budget) * 100.
        - over_budget_category_count: Count of categories exceeding budget.
        - under_budget_category_count: Count of categories within/under budget.
        - unbudgeted_category_count: Count of unbudgeted/not-assessable categories.
        - is_overall_over_budget: True if total spending exceeds total budget.
    """
    variance_df = compute_budget_variance(actual_spending, budgets, include_unbudgeted=include_unbudgeted)

    if variance_df.empty:
        return {
            "total_budget": 0.0,
            "total_actual_spend": 0.0,
            "budgeted_actual_spend": 0.0,
            "unbudgeted_actual_spend": 0.0,
            "overall_variance": 0.0,
            "overall_remaining": 0.0,
            "overall_utilization_pct": 0.0,
            "over_budget_category_count": 0,
            "under_budget_category_count": 0,
            "unbudgeted_category_count": 0,
            "is_overall_over_budget": False,
        }

    budgeted_mask = variance_df["budget_amount"].notna()
    unbudgeted_mask = variance_df["budget_amount"].isna()

    total_budget = round(float(variance_df.loc[budgeted_mask, "budget_amount"].sum()), 2)
    budgeted_actual = round(float(variance_df.loc[budgeted_mask, "actual_amount"].sum()), 2)
    unbudgeted_actual = round(float(variance_df.loc[unbudgeted_mask, "actual_amount"].sum()), 2)
    total_actual = round(float(variance_df["actual_amount"].sum()), 2)

    variance = round(total_actual - total_budget, 2)
    remaining = round(total_budget - total_actual, 2)

    if total_budget > 0:
        util_pct = round((total_actual / total_budget) * 100.0, 2)
    else:
        util_pct = 0.0 if total_actual == 0.0 else np.nan

    over_count = int((variance_df["is_over_budget"] == True).sum())
    under_count = int((variance_df["is_over_budget"] == False).sum())
    unbudgeted_count = int(variance_df["is_over_budget"].isna().sum())
    is_over = bool(total_actual > total_budget)

    return {
        "total_budget": total_budget,
        "total_actual_spend": total_actual,
        "budgeted_actual_spend": budgeted_actual,
        "unbudgeted_actual_spend": unbudgeted_actual,
        "overall_variance": variance,
        "overall_remaining": remaining,
        "overall_utilization_pct": util_pct,
        "over_budget_category_count": over_count,
        "under_budget_category_count": under_count,
        "unbudgeted_category_count": unbudgeted_count,
        "is_overall_over_budget": is_over,
    }
