"""
Unit Tests for Trend Analysis Module

Author: Akash Das
Description: Test suite for chronological monthly aggregation, Month-over-Month (MoM)
             changes, savings rate trajectories, and rolling expenditure patterns in INR (₹).
"""

import numpy as np
import pandas as pd
import pytest

from expense_tracker.analytics.trend_analysis import (
    compute_monthly_trends,
    compute_spending_trends,
    summarize_financial_trends,
)


@pytest.fixture
def multi_month_df() -> pd.DataFrame:
    """Fixture providing transactions spanning three consecutive months."""
    return pd.DataFrame([
        # January 2026: Income 60,000, Expense 30,000, Net 30,000
        {"date": "2026-01-05", "type": "Income", "category": "Salary", "amount": 60000.0},
        {"date": "2026-01-10", "type": "Expense", "category": "Rent", "amount": 20000.0},
        {"date": "2026-01-15", "type": "Expense", "category": "Groceries", "amount": 10000.0},
        # February 2026: Income 70,000, Expense 40,000, Net 30,000
        {"date": "2026-02-05", "type": "Income", "category": "Salary", "amount": 70000.0},
        {"date": "2026-02-12", "type": "Expense", "category": "Rent", "amount": 20000.0},
        {"date": "2026-02-20", "type": "Expense", "category": "Travel", "amount": 20000.0},
        # March 2026: Income 50,000, Expense 20,000, Net 30,000
        {"date": "2026-03-05", "type": "Income", "category": "Salary", "amount": 50000.0},
        {"date": "2026-03-15", "type": "Expense", "category": "Rent", "amount": 20000.0},
    ])


def test_compute_monthly_trends_basic(multi_month_df: pd.DataFrame):
    """Verify monthly aggregation and MoM calculations across consecutive months."""
    trends = compute_monthly_trends(multi_month_df)

    assert len(trends) == 3
    assert list(trends["month"]) == ["2026-01", "2026-02", "2026-03"]

    # Month 1: 2026-01
    m1 = trends.iloc[0]
    assert m1["income"] == 60000.0
    assert m1["expense"] == 30000.0
    assert m1["net_savings"] == 30000.0
    assert m1["savings_rate_pct"] == 50.0
    # First month has no previous baseline
    assert np.isnan(m1["mom_income_change"])
    assert np.isnan(m1["mom_income_pct"])
    assert np.isnan(m1["mom_expense_change"])
    assert np.isnan(m1["mom_expense_pct"])

    # Month 2: 2026-02
    m2 = trends.iloc[1]
    assert m2["income"] == 70000.0
    assert m2["expense"] == 40000.0
    assert m2["net_savings"] == 30000.0
    assert m2["mom_income_change"] == 10000.0
    # (10,000 / 60,000) * 100 = 16.67%
    assert m2["mom_income_pct"] == 16.67
    assert m2["mom_expense_change"] == 10000.0
    # (10,000 / 30,000) * 100 = 33.33%
    assert m2["mom_expense_pct"] == 33.33
    assert m2["mom_savings_change"] == 0.0
    assert m2["mom_savings_pct"] == 0.0

    # Month 3: 2026-03
    m3 = trends.iloc[2]
    assert m3["income"] == 50000.0
    assert m3["expense"] == 20000.0
    assert m3["mom_income_change"] == -20000.0
    # (-20,000 / 70,000) * 100 = -28.57%
    assert m3["mom_income_pct"] == -28.57
    assert m3["mom_expense_change"] == -20000.0
    # (-20,000 / 40,000) * 100 = -50.0%
    assert m3["mom_expense_pct"] == -50.0


def test_continuous_period_range_with_gap():
    """Verify that specifying date boundaries inserts empty months with 0.0 values."""
    # Transactions in Jan and Mar 2026 (Feb has 0 transactions)
    df_gap = pd.DataFrame([
        {"date": "2026-01-10", "type": "Expense", "amount": 5000.0},
        {"date": "2026-03-10", "type": "Expense", "amount": 8000.0},
    ])

    trends = compute_monthly_trends(df_gap, start_date="2026-01-01", end_date="2026-03-31")

    assert len(trends) == 3
    assert list(trends["month"]) == ["2026-01", "2026-02", "2026-03"]

    # Feb 2026 should be 0.0
    feb_row = trends[trends["month"] == "2026-02"].iloc[0]
    assert feb_row["income"] == 0.0
    assert feb_row["expense"] == 0.0
    assert feb_row["net_savings"] == 0.0
    assert feb_row["mom_expense_change"] == -5000.0


def test_mom_savings_percentage_all_seven_scenarios():
    """Verify deterministic Month-over-Month savings percentage-change semantics across all 7 scenarios."""
    # Scenario 7: Initial month with no previous month
    df_init = pd.DataFrame([
        {"date": "2026-01-10", "type": "Income", "amount": 50000.0},
        {"date": "2026-01-15", "type": "Expense", "amount": 20000.0},
    ])
    trends_init = compute_monthly_trends(df_init)
    assert np.isnan(trends_init.iloc[0]["mom_savings_change"])
    assert np.isnan(trends_init.iloc[0]["mom_savings_pct"])

    # Scenario 1: Positive savings to higher positive savings (e.g. +10,000 to +15,000)
    df_pos_higher = pd.DataFrame([
        {"date": "2026-01-10", "type": "Income", "amount": 30000.0},
        {"date": "2026-01-15", "type": "Expense", "amount": 20000.0},  # Net: +10,000
        {"date": "2026-02-10", "type": "Income", "amount": 35000.0},
        {"date": "2026-02-15", "type": "Expense", "amount": 20000.0},  # Net: +15,000
    ])
    trends_1 = compute_monthly_trends(df_pos_higher)
    assert trends_1.iloc[1]["mom_savings_change"] == 5000.0
    assert trends_1.iloc[1]["mom_savings_pct"] == 50.0  # (5,000 / 10,000) * 100

    # Scenario 2: Positive savings to lower positive savings (e.g. +20,000 to +10,000)
    df_pos_lower = pd.DataFrame([
        {"date": "2026-01-10", "type": "Income", "amount": 40000.0},
        {"date": "2026-01-15", "type": "Expense", "amount": 20000.0},  # Net: +20,000
        {"date": "2026-02-10", "type": "Income", "amount": 30000.0},
        {"date": "2026-02-15", "type": "Expense", "amount": 20000.0},  # Net: +10,000
    ])
    trends_2 = compute_monthly_trends(df_pos_lower)
    assert trends_2.iloc[1]["mom_savings_change"] == -10000.0
    assert trends_2.iloc[1]["mom_savings_pct"] == -50.0  # (-10,000 / 20,000) * 100

    # Scenario 3: Negative savings to less-negative savings (e.g. -20,000 to -10,000)
    df_neg_less = pd.DataFrame([
        {"date": "2026-01-10", "type": "Income", "amount": 10000.0},
        {"date": "2026-01-15", "type": "Expense", "amount": 30000.0},  # Net: -20,000
        {"date": "2026-02-10", "type": "Income", "amount": 10000.0},
        {"date": "2026-02-15", "type": "Expense", "amount": 20000.0},  # Net: -10,000
    ])
    trends_3 = compute_monthly_trends(df_neg_less)
    assert trends_3.iloc[1]["mom_savings_change"] == 10000.0
    assert np.isnan(trends_3.iloc[1]["mom_savings_pct"])

    # Scenario 4: Negative savings to positive savings (e.g. -10,000 to +5,000)
    df_neg_to_pos = pd.DataFrame([
        {"date": "2026-01-10", "type": "Income", "amount": 10000.0},
        {"date": "2026-01-15", "type": "Expense", "amount": 20000.0},  # Net: -10,000
        {"date": "2026-02-10", "type": "Income", "amount": 25000.0},
        {"date": "2026-02-15", "type": "Expense", "amount": 20000.0},  # Net: +5,000
    ])
    trends_4 = compute_monthly_trends(df_neg_to_pos)
    assert trends_4.iloc[1]["mom_savings_change"] == 15000.0
    assert np.isnan(trends_4.iloc[1]["mom_savings_pct"])

    # Scenario 5: Positive savings to negative savings (e.g. +10,000 to -5,000)
    df_pos_to_neg = pd.DataFrame([
        {"date": "2026-01-10", "type": "Income", "amount": 30000.0},
        {"date": "2026-01-15", "type": "Expense", "amount": 20000.0},  # Net: +10,000
        {"date": "2026-02-10", "type": "Income", "amount": 15000.0},
        {"date": "2026-02-15", "type": "Expense", "amount": 20000.0},  # Net: -5,000
    ])
    trends_5 = compute_monthly_trends(df_pos_to_neg)
    assert trends_5.iloc[1]["mom_savings_change"] == -15000.0
    assert np.isnan(trends_5.iloc[1]["mom_savings_pct"])

    # Scenario 6: Zero previous-month savings (e.g. 0 to +5,000)
    df_zero_prev = pd.DataFrame([
        {"date": "2026-01-10", "type": "Income", "amount": 20000.0},
        {"date": "2026-01-15", "type": "Expense", "amount": 20000.0},  # Net: 0.0
        {"date": "2026-02-10", "type": "Income", "amount": 25000.0},
        {"date": "2026-02-15", "type": "Expense", "amount": 20000.0},  # Net: +5,000
    ])
    trends_6 = compute_monthly_trends(df_zero_prev)
    assert trends_6.iloc[1]["mom_savings_change"] == 5000.0
    assert np.isnan(trends_6.iloc[1]["mom_savings_pct"])


def test_summarize_financial_trends(multi_month_df: pd.DataFrame):
    """Verify high-level trend summary KPIs."""
    summary = summarize_financial_trends(multi_month_df)

    assert summary["total_months"] == 3
    # Incomes: 60k, 70k, 50k -> Avg = 60,000.0
    assert summary["avg_monthly_income"] == 60000.0
    # Expenses: 30k, 40k, 20k -> Avg = 30,000.0
    assert summary["avg_monthly_expense"] == 30000.0
    # Savings: 30k, 30k, 30k -> Avg = 30,000.0
    assert summary["avg_monthly_savings"] == 30000.0
    assert summary["highest_expense_month"] == "2026-02"
    assert summary["highest_income_month"] == "2026-02"
    assert summary["best_savings_month"] in ["2026-01", "2026-02", "2026-03"]


def test_compute_spending_trends(multi_month_df: pd.DataFrame):
    """Verify resampled rolling spending trend indicator calculation."""
    trends = compute_spending_trends(multi_month_df, frequency="M")

    assert len(trends) == 3
    assert set(trends.columns) == {
        "period",
        "total_amount",
        "transaction_count",
        "average_amount",
        "rolling_avg_amount",
    }
    assert trends.iloc[0]["total_amount"] == 30000.0
    assert trends.iloc[1]["total_amount"] == 40000.0
    assert trends.iloc[2]["total_amount"] == 20000.0


def test_trend_validation_errors():
    """Verify input validation and error raising."""
    with pytest.raises(TypeError, match="Expected pandas DataFrame"):
        compute_monthly_trends("not_a_df")  # type: ignore

    with pytest.raises(ValueError, match="Required column 'date' not found"):
        compute_monthly_trends(pd.DataFrame({"type": ["Expense"], "amount": [100.0]}))

    with pytest.raises(ValueError, match="start_date .* cannot be after end_date"):
        compute_monthly_trends(
            pd.DataFrame(columns=["date", "type", "amount"]),
            start_date="2026-12-31",
            end_date="2026-01-01",
        )

