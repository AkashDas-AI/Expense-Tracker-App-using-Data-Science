"""
Unit Tests for Spending Analysis Module

Author: Akash Das
Description: Test suite for expense category breakdowns, top-N rankings, payment method
             distributions, and cash flow breakdowns in Indian Rupees (₹ / INR).
"""

import numpy as np
import pandas as pd
import pytest

from expense_tracker.analytics.spending_analysis import (
    get_highest_spending_category,
    get_income_vs_expense_breakdown,
    get_monthly_spending_summary,
    get_spending_by_category,
    get_spending_by_payment_method,
    get_top_n_expense_categories,
)


@pytest.fixture
def multi_category_df() -> pd.DataFrame:
    """Fixture providing transactions across multiple categories and payment methods."""
    return pd.DataFrame([
        {"transaction_id": 1, "date": "2026-01-05", "type": "Income", "category": "Salary", "amount": 60000.0, "payment_method": "Bank Transfer"},
        {"transaction_id": 2, "date": "2026-01-06", "type": "Expense", "category": "Rent", "amount": 25000.0, "payment_method": "Bank Transfer"},
        {"transaction_id": 3, "date": "2026-01-08", "type": "Expense", "category": "Groceries", "amount": 4000.0, "payment_method": "UPI"},
        {"transaction_id": 4, "date": "2026-01-12", "type": "Expense", "category": "Groceries", "amount": 6000.0, "payment_method": "Debit Card"},
        {"transaction_id": 5, "date": "2026-01-15", "type": "Expense", "category": "Utilities", "amount": 5000.0, "payment_method": "Credit Card"},
        {"transaction_id": 6, "date": "2026-01-20", "type": "Expense", "category": "Dining", "amount": 3000.0, "payment_method": "UPI"},
        {"transaction_id": 7, "date": "2026-01-22", "type": "Expense", "category": "Transport", "amount": 2000.0, "payment_method": "Cash"},
        {"transaction_id": 8, "date": "2026-01-25", "type": "Expense", "category": "Entertainment", "amount": 1000.0, "payment_method": "Credit Card"},
    ])


def test_get_spending_by_category(multi_category_df: pd.DataFrame):
    """Verify category grouping, exclusion of income, percentages, and ordering."""
    cat_df = get_spending_by_category(multi_category_df)

    # 6 expense categories: Rent (25k), Groceries (10k), Utilities (5k), Dining (3k), Transport (2k), Entertainment (1k)
    # Total expenses = 46,000.0
    assert len(cat_df) == 6
    assert "Salary" not in cat_df["category"].values
    assert cat_df.iloc[0]["category"] == "Rent"
    assert cat_df.iloc[0]["total_amount"] == 25000.0
    assert cat_df.iloc[1]["category"] == "Groceries"
    assert cat_df.iloc[1]["total_amount"] == 10000.0
    assert cat_df.iloc[1]["transaction_count"] == 2
    assert cat_df.iloc[1]["average_amount"] == 5000.0
    assert cat_df.iloc[1]["median_amount"] == 5000.0

    # Percentages sum to 100%
    assert pytest.approx(cat_df["percentage"].sum(), 0.1) == 100.0


def test_get_highest_spending_category(multi_category_df: pd.DataFrame):
    """Verify identification of peak spending category."""
    highest = get_highest_spending_category(multi_category_df)
    assert highest is not None
    assert highest["category"] == "Rent"
    assert highest["total_amount"] == 25000.0
    assert highest["transaction_count"] == 1


def test_get_highest_spending_category_empty():
    """Verify None return for empty or non-expense DataFrames."""
    empty_df = pd.DataFrame(columns=["type", "category", "amount"])
    assert get_highest_spending_category(empty_df) is None

    only_income = pd.DataFrame([{"type": "Income", "category": "Salary", "amount": 50000.0}])
    assert get_highest_spending_category(only_income) is None


def test_get_top_n_expense_categories(multi_category_df: pd.DataFrame):
    """Verify top N extraction and parameter validation."""
    top_3 = get_top_n_expense_categories(multi_category_df, n=3)
    assert len(top_3) == 3
    assert list(top_3["category"]) == ["Rent", "Groceries", "Utilities"]

    # Requesting N larger than categories returns all available
    top_10 = get_top_n_expense_categories(multi_category_df, n=10)
    assert len(top_10) == 6

    # Invalid N validation
    with pytest.raises(ValueError, match="positive integer"):
        get_top_n_expense_categories(multi_category_df, n=0)

    with pytest.raises(ValueError, match="positive integer"):
        get_top_n_expense_categories(multi_category_df, n=-5)

    with pytest.raises(TypeError, match="Expected integer for 'n'"):
        get_top_n_expense_categories(multi_category_df, n=2.5)  # type: ignore


def test_get_spending_by_payment_method(multi_category_df: pd.DataFrame):
    """Verify breakdown across payment methods with expense_only flag."""
    # Expense only
    pm_exp = get_spending_by_payment_method(multi_category_df, expense_only=True)
    assert "Bank Transfer" in pm_exp["payment_method"].values
    bt_row = pm_exp[pm_exp["payment_method"] == "Bank Transfer"].iloc[0]
    # Bank Transfer has 1 expense of 25,000 (excluding 60,000 income)
    assert bt_row["total_amount"] == 25000.0
    assert bt_row["transaction_count"] == 1

    # Total volume (Income + Expense)
    pm_all = get_spending_by_payment_method(multi_category_df, expense_only=False)
    bt_all_row = pm_all[pm_all["payment_method"] == "Bank Transfer"].iloc[0]
    # Bank Transfer has 25,000 + 60,000 = 85,000
    assert bt_all_row["total_amount"] == 85000.0
    assert bt_all_row["transaction_count"] == 2


def test_get_income_vs_expense_breakdown(multi_category_df: pd.DataFrame):
    """Verify cash flow comparison between Income and Expense."""
    breakdown = get_income_vs_expense_breakdown(multi_category_df)
    assert len(breakdown) == 2
    assert set(breakdown["type"]) == {"Income", "Expense"}

    inc_row = breakdown[breakdown["type"] == "Income"].iloc[0]
    exp_row = breakdown[breakdown["type"] == "Expense"].iloc[0]

    assert inc_row["total_amount"] == 60000.0
    assert inc_row["transaction_count"] == 1
    assert exp_row["total_amount"] == 46000.0
    assert exp_row["transaction_count"] == 7
    assert pytest.approx(breakdown["percentage_of_total_volume"].sum(), 0.1) == 100.0


def test_get_monthly_spending_summary(multi_category_df: pd.DataFrame):
    """Verify monthly chronological aggregation of expenses."""
    monthly = get_monthly_spending_summary(multi_category_df)
    assert len(monthly) == 1
    assert monthly.iloc[0]["month"] == "2026-01"
    assert monthly.iloc[0]["total_amount"] == 46000.0
    assert monthly.iloc[0]["transaction_count"] == 7


def test_spending_validation_errors():
    """Verify input validation exceptions for spending analysis functions."""
    with pytest.raises(TypeError, match="Expected pandas DataFrame"):
        get_spending_by_category({"category": "Rent", "amount": 100})

    with pytest.raises(ValueError, match="Required column 'category' not found"):
        get_spending_by_category(pd.DataFrame({"type": ["Expense"], "amount": [100.0]}))

    with pytest.raises(ValueError, match="negative values"):
        get_spending_by_category(pd.DataFrame({
            "type": ["Expense"],
            "category": ["Rent"],
            "amount": [-100.0],
        }))
