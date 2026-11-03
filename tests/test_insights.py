"""
Unit Tests for Financial Insights Generation Module

Author: Akash Das
Description: Rigorous test coverage for automated evidence-based financial insight
             generation, edge-case resilience, budget overrun flagging, and
             distinction between observations and recommendations.
"""

import pandas as pd
import pytest

from expense_tracker.analytics.insights import (
    FinancialInsight,
    generate_financial_insights,
)


@pytest.fixture
def sample_cashflow_df() -> pd.DataFrame:
    """Fixture providing transactions with income and expenses."""
    return pd.DataFrame({
        "transaction_id": ["TXN-01", "TXN-02", "TXN-03", "TXN-04", "TXN-05"],
        "date": ["2026-01-01", "2026-01-05", "2026-01-10", "2026-01-15", "2026-01-20"],
        "type": ["Income", "Expense", "Expense", "Expense", "Income"],
        "category": ["Salary", "Rent", "Groceries", "Dining", "Freelance"],
        "amount": [60000.0, 25000.0, 10000.0, 5000.0, 15000.0],
        "payment_method": ["Bank Transfer", "UPI", "Debit Card", "UPI", "Bank Transfer"],
        "description": ["Monthly Salary", "House Rent", "Supermarket", "Restaurant Dinner", "Freelance Project"],
    })


def test_generate_financial_insights_surplus(sample_cashflow_df: pd.DataFrame) -> None:
    """Verify insight generation on positive capital accumulation surplus."""
    insights = generate_financial_insights(sample_cashflow_df)
    assert len(insights) > 0
    assert all(isinstance(ins, FinancialInsight) for ins in insights)

    # Check for CashFlow insight
    cf_insights = [i for i in insights if i.category == "CashFlow"]
    assert len(cf_insights) == 1
    cf = cf_insights[0]
    assert cf.severity == "OPTIMAL"
    assert "Surplus" in cf.title or "Positive" in cf.title
    assert "surplus" in cf.observation.lower()
    assert len(cf.recommendation) > 0


def test_generate_financial_insights_deficit() -> None:
    """Verify insight generation on net cash flow deficit."""
    deficit_df = pd.DataFrame({
        "date": ["2026-01-01", "2026-01-05"],
        "type": ["Income", "Expense"],
        "category": ["Salary", "Shopping"],
        "amount": [20000.0, 50000.0],
        "payment_method": ["Bank Transfer", "Credit Card"],
        "description": ["Income", "Luxury Purchase"],
    })
    insights = generate_financial_insights(deficit_df)
    cf_insights = [i for i in insights if i.category == "CashFlow"]
    assert len(cf_insights) == 1
    cf = cf_insights[0]
    assert cf.severity == "CRITICAL"
    assert "Deficit" in cf.title


def test_generate_financial_insights_zero_income() -> None:
    """Verify insight generation when income is zero."""
    no_inc_df = pd.DataFrame({
        "date": ["2026-01-05", "2026-01-10"],
        "type": ["Expense", "Expense"],
        "category": ["Groceries", "Transport"],
        "amount": [3000.0, 1200.0],
        "payment_method": ["UPI", "Cash"],
        "description": ["Food", "Cab"],
    })
    insights = generate_financial_insights(no_inc_df)
    cf_insights = [i for i in insights if i.category == "CashFlow"]
    assert len(cf_insights) == 1
    assert "Zero Recorded Income" in cf_insights[0].title


def test_generate_financial_insights_budget_overruns() -> None:
    """Verify budget overrun detection and unbudgeted category identification."""
    df = pd.DataFrame({
        "date": ["2026-01-05", "2026-01-10"],
        "type": ["Expense", "Expense"],
        "category": ["Dining", "Travel"],
        "amount": [8000.0, 12000.0],
        "payment_method": ["Credit Card", "UPI"],
        "description": ["Dinners", "Flights"],
    })
    budgets = {"Dining": 5000.0}  # Dining overrun by 3000; Travel is unbudgeted

    insights = generate_financial_insights(df, budgets=budgets, include_unbudgeted=True)
    budget_insights = [i for i in insights if i.category == "Budget"]
    assert len(budget_insights) >= 1

    titles = [i.title for i in budget_insights]
    assert any("Overrun" in t for t in titles)
    assert any("Unbudgeted" in t for t in titles)


def test_generate_financial_insights_empty_dataframe() -> None:
    """Verify graceful handling of an empty DataFrame."""
    empty_df = pd.DataFrame(columns=["date", "type", "category", "amount"])
    insights = generate_financial_insights(empty_df)
    assert len(insights) == 1
    assert insights[0].category == "General"
    assert "No Transaction Activity" in insights[0].title


def test_financial_insight_dataclass_conversion() -> None:
    """Verify FinancialInsight serialization to dictionary."""
    ins = FinancialInsight(
        category="Spending",
        title="High Shopping",
        observation="Shopping is 40% of spend",
        recommendation="Set a monthly limit",
        severity="WARNING",
        supporting_metric={"share": 40.0},
    )
    d = ins.to_dict()
    assert isinstance(d, dict)
    assert d["category"] == "Spending"
    assert d["severity"] == "WARNING"


def test_generate_financial_insights_threshold_configurability(sample_cashflow_df: pd.DataFrame) -> None:
    """Verify that heuristic thresholds are configurable and alter insight triggering."""
    # Under default category_concentration_threshold = 15.0%, Rent (25k/40k = 62.5%) and Groceries (10k/40k = 25%) trigger High Concentration
    default_insights = generate_financial_insights(sample_cashflow_df)
    default_conc = [i for i in default_insights if i.title == "High Expenditure Concentration"]
    assert len(default_conc) == 1

    # Setting threshold higher to 70% suppresses the multiple-category concentration insight
    custom_insights = generate_financial_insights(
        sample_cashflow_df,
        category_concentration_threshold=70.0,
    )
    custom_conc = [i for i in custom_insights if i.title == "High Expenditure Concentration"]
    assert len(custom_conc) == 0

