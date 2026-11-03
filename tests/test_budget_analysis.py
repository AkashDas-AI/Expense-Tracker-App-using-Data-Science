"""
Unit Tests for Budget Analysis Module

Author: Akash Das
Description: Test suite for category budget tracking, variance analysis, utilization,
             and portfolio budget summarization in Indian Rupees (₹ / INR).
"""

import numpy as np
import pandas as pd
import pytest

from expense_tracker.analytics.budget_analysis import (
    compute_budget_summary,
    compute_budget_variance,
)


@pytest.fixture
def actual_transactions_df() -> pd.DataFrame:
    """Fixture providing transaction actuals for budget comparison."""
    return pd.DataFrame([
        {"type": "Income", "category": "Salary", "amount": 60000.0},
        {"type": "Expense", "category": "Rent", "amount": 25000.0},
        {"type": "Expense", "category": "Groceries", "amount": 8500.0},
        {"type": "Expense", "category": "Utilities", "amount": 4200.0},
        {"type": "Expense", "category": "Dining", "amount": 6000.0},
        {"type": "Expense", "category": "Shopping", "amount": 12000.0},
    ])


@pytest.fixture
def standard_budgets_dict() -> dict:
    """Standard category monthly budget dictionary in INR."""
    return {
        "Rent": 25000.0,       # Exact match (utilization = 100%)
        "Groceries": 10000.0,  # Under budget (utilization = 85%)
        "Utilities": 5000.0,   # Under budget (utilization = 84%)
        "Dining": 4000.0,      # Over budget (utilization = 150%)
        "Transport": 3000.0,   # Zero spend (utilization = 0%)
    }


def test_compute_budget_variance_with_dict(
    actual_transactions_df: pd.DataFrame,
    standard_budgets_dict: dict,
):
    """Verify budget variance calculation using a dictionary budget definition."""
    variance_df = compute_budget_variance(actual_transactions_df, standard_budgets_dict)

    assert len(variance_df) == 5
    assert set(variance_df.columns) == {
        "category",
        "budget_amount",
        "actual_amount",
        "remaining_budget",
        "budget_variance",
        "utilization_pct",
        "is_over_budget",
    }

    # Rent: 25k budget, 25k actual -> 0 remaining, 0 variance, 100% util, False
    rent_row = variance_df[variance_df["category"] == "Rent"].iloc[0]
    assert rent_row["budget_amount"] == 25000.0
    assert rent_row["actual_amount"] == 25000.0
    assert rent_row["remaining_budget"] == 0.0
    assert rent_row["budget_variance"] == 0.0
    assert rent_row["utilization_pct"] == 100.0
    assert bool(rent_row["is_over_budget"]) is False

    # Dining: 4k budget, 6k actual -> -2k remaining, +2k variance, 150% util, True
    dining_row = variance_df[variance_df["category"] == "Dining"].iloc[0]
    assert dining_row["budget_amount"] == 4000.0
    assert dining_row["actual_amount"] == 6000.0
    assert dining_row["remaining_budget"] == -2000.0
    assert dining_row["budget_variance"] == 2000.0
    assert dining_row["utilization_pct"] == 150.0
    assert bool(dining_row["is_over_budget"]) is True

    # Transport: 3k budget, 0 actual -> 3k remaining, -3k variance, 0% util, False
    transport_row = variance_df[variance_df["category"] == "Transport"].iloc[0]
    assert transport_row["budget_amount"] == 3000.0
    assert transport_row["actual_amount"] == 0.0
    assert transport_row["remaining_budget"] == 3000.0
    assert transport_row["budget_variance"] == -3000.0
    assert transport_row["utilization_pct"] == 0.0
    assert bool(transport_row["is_over_budget"]) is False


def test_compute_budget_variance_with_dataframe(
    actual_transactions_df: pd.DataFrame,
    standard_budgets_dict: dict,
):
    """Verify budget variance calculation using a DataFrame budget definition."""
    budget_df = pd.DataFrame([
        {"category": k, "budget_amount": v} for k, v in standard_budgets_dict.items()
    ])

    variance_df = compute_budget_variance(actual_transactions_df, budget_df)
    assert len(variance_df) == 5

    groceries_row = variance_df[variance_df["category"] == "Groceries"].iloc[0]
    assert groceries_row["actual_amount"] == 8500.0
    assert groceries_row["budget_amount"] == 10000.0
    assert groceries_row["remaining_budget"] == 1500.0
    assert groceries_row["utilization_pct"] == 85.0
    assert bool(groceries_row["is_over_budget"]) is False


def test_income_exclusion_in_budget(actual_transactions_df: pd.DataFrame):
    """Verify that income transactions (e.g. Salary) do not affect budget variance."""
    # Even if Salary is budgeted as an expense, only Expense records are summed
    budget = {"Salary": 50000.0, "Rent": 25000.0}
    variance_df = compute_budget_variance(actual_transactions_df, budget)

    salary_row = variance_df[variance_df["category"] == "Salary"].iloc[0]
    # In actual_transactions_df, Salary is type='Income' of 60,000; expense spend must be 0
    assert salary_row["actual_amount"] == 0.0
    assert salary_row["remaining_budget"] == 50000.0
    assert bool(salary_row["is_over_budget"]) is False


def test_include_unbudgeted_flag(
    actual_transactions_df: pd.DataFrame,
    standard_budgets_dict: dict,
):
    """Verify handling of unbudgeted categories when include_unbudgeted is True."""
    # actual_transactions_df includes Shopping (12,000) which is not in standard_budgets_dict
    variance_without = compute_budget_variance(
        actual_transactions_df, standard_budgets_dict, include_unbudgeted=False
    )
    assert "Shopping" not in variance_without["category"].values

    variance_with = compute_budget_variance(
        actual_transactions_df, standard_budgets_dict, include_unbudgeted=True
    )
    assert "Shopping" in variance_with["category"].values

    shopping_row = variance_with[variance_with["category"] == "Shopping"].iloc[0]
    assert np.isnan(shopping_row["budget_amount"])
    assert shopping_row["actual_amount"] == 12000.0
    assert np.isnan(shopping_row["remaining_budget"])
    assert np.isnan(shopping_row["budget_variance"])
    assert np.isnan(shopping_row["utilization_pct"])
    # Semantic correction: Unbudgeted categories are NOT over budget; status is pd.NA
    assert pd.isna(shopping_row["is_over_budget"])
    assert shopping_row["is_over_budget"] is pd.NA


def test_budget_status_and_summary_count_distinction():
    """Verify distinct handling of over-budget, under-budget, zero-budget, and unbudgeted categories."""
    actual_df = pd.DataFrame([
        {"type": "Expense", "category": "AboveBudget", "amount": 6000.0},
        {"type": "Expense", "category": "BelowBudget", "amount": 3000.0},
        {"type": "Expense", "category": "ZeroBudgetWithSpend", "amount": 500.0},
        {"type": "Expense", "category": "UnbudgetedWithSpend", "amount": 2000.0},
    ])

    budgets = {
        "AboveBudget": 4000.0,
        "BelowBudget": 5000.0,
        "ZeroBudgetWithSpend": 0.0,
        "ZeroBudgetZeroSpend": 0.0,
    }

    variance_df = compute_budget_variance(actual_df, budgets, include_unbudgeted=True)

    # 1. Category with a budget and actual spending above it
    above_row = variance_df[variance_df["category"] == "AboveBudget"].iloc[0]
    assert above_row["budget_amount"] == 4000.0
    assert above_row["actual_amount"] == 6000.0
    assert above_row["remaining_budget"] == -2000.0
    assert above_row["budget_variance"] == 2000.0
    assert above_row["utilization_pct"] == 150.0
    assert above_row["is_over_budget"] == True

    # 2. Category with a budget and actual spending below it
    below_row = variance_df[variance_df["category"] == "BelowBudget"].iloc[0]
    assert below_row["budget_amount"] == 5000.0
    assert below_row["actual_amount"] == 3000.0
    assert below_row["remaining_budget"] == 2000.0
    assert below_row["budget_variance"] == -2000.0
    assert below_row["utilization_pct"] == 60.0
    assert below_row["is_over_budget"] == False

    # 3. Category with a zero budget and actual spending above it (spend > 0)
    zero_spend_row = variance_df[variance_df["category"] == "ZeroBudgetWithSpend"].iloc[0]
    assert zero_spend_row["budget_amount"] == 0.0
    assert zero_spend_row["actual_amount"] == 500.0
    assert zero_spend_row["remaining_budget"] == -500.0
    assert zero_spend_row["budget_variance"] == 500.0
    assert np.isnan(zero_spend_row["utilization_pct"])
    assert zero_spend_row["is_over_budget"] == True

    # 4. Category with a zero budget and zero spending (spend == 0)
    zero_zero_row = variance_df[variance_df["category"] == "ZeroBudgetZeroSpend"].iloc[0]
    assert zero_zero_row["budget_amount"] == 0.0
    assert zero_zero_row["actual_amount"] == 0.0
    assert zero_zero_row["remaining_budget"] == 0.0
    assert zero_zero_row["budget_variance"] == 0.0
    assert zero_zero_row["utilization_pct"] == 0.0
    assert zero_zero_row["is_over_budget"] == False

    # 5. Category with actual spending and no budget
    unbudgeted_row = variance_df[variance_df["category"] == "UnbudgetedWithSpend"].iloc[0]
    assert np.isnan(unbudgeted_row["budget_amount"])
    assert unbudgeted_row["actual_amount"] == 2000.0
    assert np.isnan(unbudgeted_row["remaining_budget"])
    assert np.isnan(unbudgeted_row["budget_variance"])
    assert np.isnan(unbudgeted_row["utilization_pct"])
    assert pd.isna(unbudgeted_row["is_over_budget"])
    assert unbudgeted_row["is_over_budget"] is pd.NA

    # 6. Verify summary counts exclude unbudgeted from over-budget and under-budget counts
    summary_with = compute_budget_summary(actual_df, budgets, include_unbudgeted=True)
    # Genuinely over budget: AboveBudget, ZeroBudgetWithSpend -> 2
    assert summary_with["over_budget_category_count"] == 2
    # Genuinely under/within budget: BelowBudget, ZeroBudgetZeroSpend -> 2
    assert summary_with["under_budget_category_count"] == 2
    # Unbudgeted/not-assessable: UnbudgetedWithSpend -> 1
    assert summary_with["unbudgeted_category_count"] == 1

    # Verify summary without unbudgeted excludes unbudgeted category completely
    summary_without = compute_budget_summary(actual_df, budgets, include_unbudgeted=False)
    assert summary_without["over_budget_category_count"] == 2
    assert summary_without["under_budget_category_count"] == 2
    assert summary_without["unbudgeted_category_count"] == 0


def test_compute_budget_summary(
    actual_transactions_df: pd.DataFrame,
    standard_budgets_dict: dict,
):
    """Verify portfolio-level budget health KPIs and aggregations."""
    # standard_budgets_dict total: 25k + 10k + 5k + 4k + 3k = 47,000.0
    # Actual spend on budgeted categories:
    # Rent: 25k, Groceries: 8.5k, Utilities: 4.2k, Dining: 6k, Transport: 0 -> Total = 43,700.0
    summary = compute_budget_summary(actual_transactions_df, standard_budgets_dict)

    assert summary["total_budget"] == 47000.0
    assert summary["total_actual_spend"] == 43700.0
    assert summary["overall_variance"] == -3300.0  # actual - budget
    assert summary["overall_remaining"] == 3300.0   # budget - actual
    # 43,700 / 47,000 = 92.978... -> 92.98%
    assert summary["overall_utilization_pct"] == 92.98
    assert summary["over_budget_category_count"] == 1   # Dining
    assert summary["under_budget_category_count"] == 4  # Rent, Groceries, Utilities, Transport
    assert summary["is_overall_over_budget"] is False


def test_budget_validation_errors():
    """Verify input validation and error raising."""
    # Negative budget in dict
    with pytest.raises(ValueError, match="cannot be negative"):
        compute_budget_variance(pd.DataFrame(), {"Rent": -100.0})

    # Non-numeric budget in dict
    with pytest.raises(ValueError, match="must be numeric"):
        compute_budget_variance(pd.DataFrame(), {"Rent": "invalid"})

    # Duplicate categories in DataFrame
    dup_df = pd.DataFrame([
        {"category": "Rent", "budget_amount": 20000.0},
        {"category": "Rent", "budget_amount": 25000.0},
    ])
    with pytest.raises(ValueError, match="Duplicate categories found"):
        compute_budget_variance(pd.DataFrame(), dup_df)

    # Missing column in budget DataFrame
    missing_col_budget = pd.DataFrame([{"category": "Rent"}])
    with pytest.raises(ValueError, match="Required column 'budget_amount'|must contain required column"):
        compute_budget_variance(pd.DataFrame(), missing_col_budget)

    # Invalid budgets type
    with pytest.raises(TypeError, match="must be a dictionary or DataFrame"):
        compute_budget_variance(pd.DataFrame(), ["Rent", 1000])  # type: ignore

    # Invalid actual_spending type
    with pytest.raises(TypeError, match="Expected pandas DataFrame"):
        compute_budget_variance([{"category": "Rent", "amount": 100}], {"Rent": 1000})  # type: ignore
