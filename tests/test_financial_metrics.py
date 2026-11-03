"""
Unit Tests for Financial Metrics Module

Author: Akash Das
Description: Comprehensive test suite for income, expense, net savings, savings rate,
             and core financial KPI calculations in Indian Rupees (₹ / INR).
"""

import numpy as np
import pandas as pd
import pytest

from expense_tracker.analytics.financial_metrics import (
    calculate_average_expense,
    calculate_average_income,
    calculate_expense_to_income_ratio,
    calculate_median_expense,
    calculate_net_savings,
    calculate_savings_rate,
    calculate_total_expenses,
    calculate_total_income,
    calculate_transaction_counts,
    compute_financial_kpis,
)


@pytest.fixture
def sample_transactions_df() -> pd.DataFrame:
    """Fixture providing representative financial transactions."""
    return pd.DataFrame([
        {"transaction_id": 1, "date": "2026-01-05", "type": "Income", "category": "Salary", "amount": 50000.0, "payment_method": "Bank Transfer"},
        {"transaction_id": 2, "date": "2026-01-10", "type": "Income", "category": "Freelance", "amount": 15000.0, "payment_method": "UPI"},
        {"transaction_id": 3, "date": "2026-01-15", "type": "Expense", "category": "Rent", "amount": 20000.0, "payment_method": "Bank Transfer"},
        {"transaction_id": 4, "date": "2026-01-16", "type": "Expense", "category": "Groceries", "amount": 5000.0, "payment_method": "UPI"},
        {"transaction_id": 5, "date": "2026-01-20", "type": "Expense", "category": "Utilities", "amount": 3000.0, "payment_method": "Credit Card"},
        {"transaction_id": 6, "date": "2026-01-25", "type": "Expense", "category": "Dining", "amount": 2000.0, "payment_method": "Debit Card"},
    ])


def test_calculate_totals(sample_transactions_df: pd.DataFrame):
    """Verify total income, total expenses, and net savings calculations."""
    total_income = calculate_total_income(sample_transactions_df)
    total_expense = calculate_total_expenses(sample_transactions_df)
    net_savings = calculate_net_savings(sample_transactions_df)

    assert total_income == 65000.0
    assert total_expense == 30000.0
    assert net_savings == 35000.0


def test_calculate_savings_rate(sample_transactions_df: pd.DataFrame):
    """Verify savings rate percentage calculation."""
    # (35,000 / 65,000) * 100 = 53.846... -> 53.85%
    savings_rate = calculate_savings_rate(sample_transactions_df)
    assert savings_rate == 53.85


def test_calculate_expense_to_income_ratio(sample_transactions_df: pd.DataFrame):
    """Verify expense-to-income ratio calculation."""
    # 30,000 / 65,000 = 0.4615... -> 0.4615
    ratio = calculate_expense_to_income_ratio(sample_transactions_df)
    assert ratio == 0.4615


def test_averages_and_medians(sample_transactions_df: pd.DataFrame):
    """Verify ticket size averages and medians for income and expense."""
    avg_income = calculate_average_income(sample_transactions_df)
    avg_expense = calculate_average_expense(sample_transactions_df)
    med_expense = calculate_median_expense(sample_transactions_df)

    # Incomes: 50,000, 15,000 -> Mean: 32,500.0
    assert avg_income == 32500.0
    # Expenses: 20000, 5000, 3000, 2000 -> Mean: 7500.0
    assert avg_expense == 7500.0
    # Expenses: 2000, 3000, 5000, 20000 -> Median: (3000 + 5000) / 2 = 4000.0
    assert med_expense == 4000.0


def test_transaction_counts(sample_transactions_df: pd.DataFrame):
    """Verify count partition between income and expense."""
    counts = calculate_transaction_counts(sample_transactions_df)
    assert counts == {
        "total": 6,
        "income": 2,
        "expense": 4,
    }


def test_compute_financial_kpis_comprehensive(sample_transactions_df: pd.DataFrame):
    """Verify full financial KPIs bundle."""
    kpis = compute_financial_kpis(sample_transactions_df)

    assert kpis["total_income"] == 65000.0
    assert kpis["total_expenses"] == 30000.0
    assert kpis["net_savings"] == 35000.0
    assert kpis["savings_rate_pct"] == 53.85
    assert kpis["expense_to_income_ratio"] == 0.4615
    assert kpis["average_income"] == 32500.0
    assert kpis["average_expense"] == 7500.0
    assert kpis["median_expense"] == 4000.0
    assert kpis["total_transactions"] == 6
    assert kpis["income_count"] == 2
    assert kpis["expense_count"] == 4
    assert kpis["transaction_counts"]["total"] == 6
    assert kpis["transaction_counts"]["income"] == 2
    assert kpis["transaction_counts"]["expense"] == 4


def test_empty_dataframe():
    """Verify graceful handling of empty DataFrames."""
    empty_df = pd.DataFrame(columns=["type", "amount"])

    assert calculate_total_income(empty_df) == 0.0
    assert calculate_total_expenses(empty_df) == 0.0
    assert calculate_net_savings(empty_df) == 0.0
    assert calculate_savings_rate(empty_df) == 0.0
    assert calculate_expense_to_income_ratio(empty_df) == 0.0
    assert calculate_average_income(empty_df) == 0.0
    assert calculate_average_expense(empty_df) == 0.0
    assert calculate_median_expense(empty_df) == 0.0

    counts = calculate_transaction_counts(empty_df)
    assert counts == {"total": 0, "income": 0, "expense": 0}

    kpis = compute_financial_kpis(empty_df)
    assert kpis["total_income"] == 0.0
    assert kpis["net_savings"] == 0.0


def test_zero_income_policy():
    """Verify behavior when expenses exist but income is zero."""
    df_no_income = pd.DataFrame([
        {"type": "Expense", "amount": 5000.0},
        {"type": "Expense", "amount": 2500.0},
    ])

    assert calculate_total_income(df_no_income) == 0.0
    assert calculate_total_expenses(df_no_income) == 7500.0
    assert calculate_net_savings(df_no_income) == -7500.0

    # Default policy returns NaN
    assert np.isnan(calculate_savings_rate(df_no_income))
    assert np.isnan(calculate_expense_to_income_ratio(df_no_income))

    # Custom zero income default policy
    assert calculate_savings_rate(df_no_income, zero_income_default=0.0) == 0.0
    assert calculate_expense_to_income_ratio(df_no_income, zero_income_default=0.0) == 0.0


def test_only_income_transactions():
    """Verify behavior when only income transactions are present."""
    df_only_income = pd.DataFrame([
        {"type": "Income", "amount": 40000.0},
        {"type": "Income", "amount": 10000.0},
    ])

    assert calculate_total_income(df_only_income) == 50000.0
    assert calculate_total_expenses(df_only_income) == 0.0
    assert calculate_net_savings(df_only_income) == 50000.0
    assert calculate_savings_rate(df_only_income) == 100.0
    assert calculate_expense_to_income_ratio(df_only_income) == 0.0
    assert calculate_average_expense(df_only_income) == 0.0
    assert calculate_median_expense(df_only_income) == 0.0


def test_input_validation_errors():
    """Verify exceptions for missing columns, non-numeric, or negative amounts."""
    # Non-DataFrame input
    with pytest.raises(TypeError, match="Expected pandas DataFrame"):
        calculate_total_income([{"type": "Income", "amount": 1000}])

    # Missing required column
    missing_col_df = pd.DataFrame({"amount": [100.0, 200.0]})
    with pytest.raises(ValueError, match="Required column 'type' not found"):
        calculate_total_income(missing_col_df)

    # Negative amount
    neg_amt_df = pd.DataFrame({"type": ["Expense"], "amount": [-500.0]})
    with pytest.raises(ValueError, match="negative values"):
        calculate_total_expenses(neg_amt_df)

    # Non-numeric / NaN amount
    nan_amt_df = pd.DataFrame({"type": ["Expense"], "amount": ["invalid_amount"]})
    with pytest.raises(ValueError, match="non-numeric or infinite"):
        calculate_total_expenses(nan_amt_df)


def test_dataframe_immutability(sample_transactions_df: pd.DataFrame):
    """Verify that financial calculation functions do not mutate the input DataFrame."""
    df_copy = sample_transactions_df.copy()
    _ = compute_financial_kpis(sample_transactions_df)

    pd.testing.assert_frame_equal(sample_transactions_df, df_copy)
