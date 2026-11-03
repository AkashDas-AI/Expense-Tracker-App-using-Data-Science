"""
Analytics Package

Author: Akash Das
Description: Financial metrics, spending analysis, budget tracking, and trend analysis.
"""

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
from expense_tracker.analytics.insights import (
    FinancialInsight,
    generate_financial_insights,
)
from expense_tracker.analytics.spending_analysis import (
    get_highest_spending_category,
    get_income_vs_expense_breakdown,
    get_monthly_spending_summary,
    get_spending_by_category,
    get_spending_by_payment_method,
    get_top_n_expense_categories,
)
from expense_tracker.analytics.budget_analysis import (
    compute_budget_summary,
    compute_budget_variance,
)
from expense_tracker.analytics.trend_analysis import (
    compute_monthly_trends,
    compute_spending_trends,
    summarize_financial_trends,
)

__all__ = [
    # Financial Metrics
    "calculate_total_income",
    "calculate_total_expenses",
    "calculate_net_savings",
    "calculate_savings_rate",
    "calculate_expense_to_income_ratio",
    "calculate_average_income",
    "calculate_average_expense",
    "calculate_median_expense",
    "calculate_transaction_counts",
    "compute_financial_kpis",
    # Spending Analysis
    "get_spending_by_category",
    "get_highest_spending_category",
    "get_top_n_expense_categories",
    "get_spending_by_payment_method",
    "get_income_vs_expense_breakdown",
    "get_monthly_spending_summary",
    # Budget Analysis
    "compute_budget_variance",
    "compute_budget_summary",
    # Trend Analysis
    "compute_monthly_trends",
    "compute_spending_trends",
    "summarize_financial_trends",
    # Financial Insights
    "FinancialInsight",
    "generate_financial_insights",
]
