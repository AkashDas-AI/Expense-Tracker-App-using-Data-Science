"""
Financial Insights Generation Module

Author: Akash Das
Description: Derives evidence-based, structured financial observations and actionable
             budgeting hygiene recommendations from calculated metrics and transaction history.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from expense_tracker.analytics.budget_analysis import compute_budget_summary, compute_budget_variance
from expense_tracker.analytics.financial_metrics import compute_financial_kpis
from expense_tracker.analytics.spending_analysis import (
    get_highest_spending_category,
    get_spending_by_category,
    get_spending_by_payment_method,
    get_top_n_expense_categories,
)
from expense_tracker.analytics.trend_analysis import compute_monthly_trends, summarize_financial_trends
from expense_tracker.utils.helpers import format_currency, format_percentage

# Configurable Analytical Heuristics (Defaults)
# Note: These are configurable operational thresholds, not universal financial laws.
DEFAULT_CATEGORY_CONCENTRATION_THRESHOLD: float = 15.0  # Categories accounting for >= 15% of expenses
DEFAULT_PAYMENT_CHANNEL_THRESHOLD: float = 35.0         # Payment channels accounting for >= 35% of outflows
DEFAULT_MOM_SPIKE_PCT_THRESHOLD: float = 20.0          # MoM expense increase >= 20%
DEFAULT_HIGH_BUDGET_UTILIZATION_PCT: float = 90.0      # Budget utilization >= 90% flagged as high
DEFAULT_CRITICAL_BUDGET_UTILIZATION_PCT: float = 100.0  # Budget utilization > 100% flagged as exceeded

# Aliases for backward compatibility
SIGNIFICANT_CATEGORY_SHARE_PCT = DEFAULT_CATEGORY_CONCENTRATION_THRESHOLD
TOP_PAYMENT_CHANNEL_SHARE_PCT = DEFAULT_PAYMENT_CHANNEL_THRESHOLD
HIGH_BUDGET_UTILIZATION_PCT = DEFAULT_HIGH_BUDGET_UTILIZATION_PCT
CRITICAL_BUDGET_UTILIZATION_PCT = DEFAULT_CRITICAL_BUDGET_UTILIZATION_PCT


@dataclass
class FinancialInsight:
    """Structured representation of a single evidence-based financial insight."""
    category: str  # e.g., 'Spending', 'Budget', 'Savings', 'Outliers', 'CashFlow'
    title: str
    observation: str
    recommendation: str
    severity: str  # 'INFO', 'OPTIMAL', 'WARNING', 'CRITICAL'
    supporting_metric: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert insight dataclass into a serializable dictionary."""
        return asdict(self)


def generate_financial_insights(
    df: pd.DataFrame,
    budgets: Optional[Dict[str, float]] = None,
    include_unbudgeted: bool = True,
    category_concentration_threshold: float = DEFAULT_CATEGORY_CONCENTRATION_THRESHOLD,
    payment_channel_threshold: float = DEFAULT_PAYMENT_CHANNEL_THRESHOLD,
    mom_spike_pct_threshold: float = DEFAULT_MOM_SPIKE_PCT_THRESHOLD,
) -> List[FinancialInsight]:
    """Generate evidence-based financial insights derived strictly from calculated metrics.

    Methodological Justifications & Heuristic Limitations:
    - Configurable Analytical Heuristics:
      1. Category Concentration (default 15.0%): Isolates dominant spending drivers.
         Limitation: In households with significant structural commitments (e.g. rent or education),
         a single category may legitimately exceed 30–40% without reflecting mismanagement.
      2. Payment Channel Concentration (default 35.0%): Monitors operational payment reliance (e.g. UPI vs Cards).
         Limitation: Reflects consumer convenience and merchant ecosystem acceptance rather than solvency risk.
      3. Month-over-Month Acceleration (default 20.0%): Identifies periods of rapid expenditure growth.
         Limitation: Monthly swings frequently reflect expected calendar seasonality (e.g. festival shopping,
         annual insurance renewals, holiday travel) rather than uncontrolled discretionary behavior.
    - Non-Causal Guidance: Recommendations provide descriptive hygiene suggestions and must not be
      interpreted as causal conclusions.
    - Edge Cases: Safely handles empty datasets, zero income, and negative savings without errors.

    Args:
        df: Validated transaction DataFrame containing 'date', 'type', 'category', 'amount'.
        budgets: Optional category budget dictionary {category: monthly_budget_amount}.
        include_unbudgeted: Whether to audit unbudgeted spending categories.
        category_concentration_threshold: Percentage threshold for category dominance (defaults to 15.0%).
        payment_channel_threshold: Percentage threshold for payment channel dominance (defaults to 35.0%).
        mom_spike_pct_threshold: Percentage threshold for MoM spending spike (defaults to 20.0%).

    Returns:
        List[FinancialInsight]: Ordered list of structured financial insights.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    insights: List[FinancialInsight] = []

    if df.empty:
        insights.append(
            FinancialInsight(
                category="General",
                title="No Transaction Activity",
                observation="No transaction records are present in the selected dataset or filter criteria.",
                recommendation="Expand the active date range or clear filter criteria to generate financial insights.",
                severity="INFO",
                supporting_metric={"record_count": 0},
            )
        )
        return insights

    # 1. Primary Financial Health & Net Cash Flow Insights
    kpis = compute_financial_kpis(df)
    net_savings = kpis["net_savings"]
    tot_income = kpis["total_income"]
    tot_expense = kpis["total_expenses"]
    sav_rate = kpis["savings_rate_pct"]

    if tot_income == 0.0 and tot_expense > 0.0:
        insights.append(
            FinancialInsight(
                category="CashFlow",
                title="Zero Recorded Income Inflow",
                observation=(
                    f"Total expenditures stand at {format_currency(tot_expense)}, with ₹0.00 recorded income inflows. "
                    "The savings rate is mathematically undefined."
                ),
                recommendation=(
                    "Verify whether income deposits were routed through unrecorded accounts or filter criteria "
                    "omitted income transactions."
                ),
                severity="WARNING",
                supporting_metric={"total_income": 0.0, "total_expenses": tot_expense},
            )
        )
    elif net_savings < 0:
        insights.append(
            FinancialInsight(
                category="CashFlow",
                title="Net Cash Flow Deficit",
                observation=(
                    f"Cumulative expenditures ({format_currency(tot_expense)}) exceeded total income inflows "
                    f"({format_currency(tot_income)}), resulting in a net deficit of {format_currency(abs(net_savings))} "
                    f"(savings rate of {format_percentage(sav_rate)})."
                ),
                recommendation=(
                    "Review discretionary spending categories (e.g. Shopping, Travel, Entertainment) to identify "
                    "curtailment opportunities and align outflows with incoming cash reserves."
                ),
                severity="CRITICAL",
                supporting_metric={
                    "total_income": tot_income,
                    "total_expenses": tot_expense,
                    "net_deficit": abs(net_savings),
                    "savings_rate_pct": sav_rate,
                },
            )
        )
    else:
        insights.append(
            FinancialInsight(
                category="CashFlow",
                title="Positive Capital Accumulation",
                observation=(
                    f"Total income inflows ({format_currency(tot_income)}) comfortably covered expenditures "
                    f"({format_currency(tot_expense)}), generating a net surplus of {format_currency(net_savings)} "
                    f"with a healthy savings rate of {format_percentage(sav_rate)}."
                ),
                recommendation=(
                    "Consider allocating a portion of surplus capital toward emergency reserves, systematic investment "
                    "plans (SIPs), or long-term financial goals."
                ),
                severity="OPTIMAL",
                supporting_metric={
                    "total_income": tot_income,
                    "total_expenses": tot_expense,
                    "net_savings": net_savings,
                    "savings_rate_pct": sav_rate,
                },
            )
        )

    # 2. Spending Concentration & Dominant Categories
    expense_df = df[df["type"] == "Expense"]
    if not expense_df.empty:
        cat_df = get_spending_by_category(expense_df)
        highest_cat = get_highest_spending_category(expense_df)

        if highest_cat:
            top_share = highest_cat["percentage"]
            top_name = highest_cat["category"]
            top_amount = highest_cat["total_amount"]

            severity_cat = "WARNING" if top_share >= 25.0 else "INFO"
            insights.append(
                FinancialInsight(
                    category="Spending",
                    title=f"Primary Expense Driver: {top_name}",
                    observation=(
                        f"'{top_name}' constitutes the largest expenditure category, accounting for "
                        f"{format_currency(top_amount)} ({top_share:.1f}% of total expenditures across "
                        f"{highest_cat['transaction_count']} transactions)."
                    ),
                    recommendation=(
                        f"Evaluate whether '{top_name}' expenditures represent essential structural commitments "
                        "(e.g., fixed housing/education costs) or variable discretionary purchases subject to optimization."
                    ),
                    severity=severity_cat,
                    supporting_metric=highest_cat,
                )
            )

        # Significant spending shares (>= category_concentration_threshold)
        heavy_cats = cat_df[cat_df["percentage"] >= category_concentration_threshold]
        if len(heavy_cats) > 1:
            cat_list_str = ", ".join([f"{r['category']} ({r['percentage']:.1f}%)" for _, r in heavy_cats.iterrows()])
            tot_heavy_pct = float(heavy_cats["percentage"].sum())
            insights.append(
                FinancialInsight(
                    category="Spending",
                    title="High Expenditure Concentration",
                    observation=(
                        f"A small cluster of {len(heavy_cats)} categories accounts for {tot_heavy_pct:.1f}% of all outflows: "
                        f"{cat_list_str}."
                    ),
                    recommendation=(
                        "Target budgeting limits and expense tracking specifically on these dominant categories, "
                        "as small percentage optimizations here yield the largest absolute monetary savings."
                    ),
                    severity="WARNING",
                    supporting_metric={
                        "concentrated_category_count": len(heavy_cats),
                        "combined_share_pct": round(tot_heavy_pct, 2),
                    },
                )
            )

        # Payment channel concentration
        pm_df = get_spending_by_payment_method(expense_df, expense_only=True)
        if not pm_df.empty:
            top_pm = pm_df.iloc[0]
            if top_pm["percentage"] >= payment_channel_threshold:
                insights.append(
                    FinancialInsight(
                        category="PaymentMethod",
                        title=f"Dominant Payment Channel: {top_pm['payment_method']}",
                        observation=(
                            f"{top_pm['percentage']:.1f}% of expense outflows ({format_currency(top_pm['total_amount'])}) "
                            f"are transacted via {top_pm['payment_method']} across {top_pm['transaction_count']} transactions."
                        ),
                        recommendation=(
                            f"Ensure adequate balance and fraud monitoring on your primary {top_pm['payment_method']} "
                            "account, and verify if credit or reward programs can optimize frequent transactions."
                        ),
                        severity="INFO",
                        supporting_metric=top_pm.to_dict(),
                    )
                )

    # 3. Monthly Trends & Volatility
    trends_df = compute_monthly_trends(df)
    if len(trends_df) >= 2:
        trend_summary = summarize_financial_trends(df)
        max_exp_month = trend_summary["highest_expense_month"]
        best_sav_month = trend_summary["best_savings_month"]

        # Month-over-month expense swings
        mom_exp_changes = trends_df["mom_expense_change"].dropna()
        if not mom_exp_changes.empty:
            largest_spike_idx = mom_exp_changes.idxmax()
            largest_spike_val = mom_exp_changes.loc[largest_spike_idx]
            largest_spike_month = trends_df.loc[largest_spike_idx, "month"]
            pct_val = trends_df.loc[largest_spike_idx, "mom_expense_pct"]

            if largest_spike_val > 0 and (pd.isna(pct_val) or pct_val >= mom_spike_pct_threshold):
                pct_str = f" (+{pct_val:.1f}%)" if not pd.isna(pct_val) else ""
                insights.append(
                    FinancialInsight(
                        category="Trends",
                        title=f"Peak Monthly Expense Spike: {largest_spike_month}",
                        observation=(
                            f"The largest single-month spending increase occurred in {largest_spike_month}, surging by "
                            f"{format_currency(largest_spike_val)}{pct_str} relative to the previous month."
                        ),
                        recommendation=(
                            "Audit seasonal or periodic expenses occurring in this calendar period (e.g. annual renewals, "
                            "festive shopping, or holiday travel) to build amortized sinking funds."
                        ),
                        severity="WARNING" if largest_spike_val > 50000 else "INFO",
                        supporting_metric={
                            "month": largest_spike_month,
                            "absolute_spike": largest_spike_val,
                            "percentage_spike": pct_val if not pd.isna(pct_val) else None,
                        },
                    )
                )

    # 4. Budget Variance & Overrun Insights (When budgets are provided)
    if budgets is not None and len(budgets) > 0 and not expense_df.empty:
        var_df = compute_budget_variance(expense_df, budgets=budgets, include_unbudgeted=include_unbudgeted)
        budget_summary = compute_budget_summary(expense_df, budgets=budgets, include_unbudgeted=include_unbudgeted)

        over_cats = var_df[var_df["is_over_budget"] == True]
        if not over_cats.empty:
            over_names = ", ".join([
                f"{r['category']} (+{format_currency(r['budget_variance'])})"
                for _, r in over_cats.iterrows()
            ])
            tot_overrun = float(over_cats["budget_variance"].sum())

            insights.append(
                FinancialInsight(
                    category="Budget",
                    title="Category Budget Overruns Detected",
                    observation=(
                        f"{len(over_cats)} category budget(s) were exceeded by a cumulative total of "
                        f"{format_currency(tot_overrun)}: {over_names}."
                    ),
                    recommendation=(
                        "Adjust category targets or implement mid-month spending alerts to curb discretionary "
                        "spending before monthly budget ceilings are breached."
                    ),
                    severity="CRITICAL",
                    supporting_metric={
                        "over_budget_category_count": len(over_cats),
                        "total_overrun_amount": round(tot_overrun, 2),
                    },
                )
            )

        # Unbudgeted Spending
        if include_unbudgeted:
            unbudgeted_cats = var_df[var_df["is_over_budget"].isna()]
            if not unbudgeted_cats.empty:
                unbudgeted_spend = float(unbudgeted_cats["actual_amount"].sum())
                unbudgeted_names = ", ".join(unbudgeted_cats["category"].tolist())
                insights.append(
                    FinancialInsight(
                        category="Budget",
                        title="Unbudgeted Expenditure Detected",
                        observation=(
                            f"{format_currency(unbudgeted_spend)} was expended across {len(unbudgeted_cats)} "
                            f"category(ies) without active budget allocations: {unbudgeted_names}."
                        ),
                        recommendation=(
                            "Assign explicit budget targets to these categories in the budget customizer "
                            "to ensure comprehensive portfolio spending governance."
                        ),
                        severity="WARNING",
                        supporting_metric={
                            "unbudgeted_category_count": len(unbudgeted_cats),
                            "unbudgeted_spending": round(unbudgeted_spend, 2),
                        },
                    )
                )

    # 5. High-Value Statistical Outliers / Spikes
    if len(expense_df) >= 10:
        amounts = expense_df["amount"].dropna()
        q1 = amounts.quantile(0.25)
        q3 = amounts.quantile(0.75)
        iqr = q3 - q1
        upper_fence = q3 + 1.5 * iqr

        outlier_txns = expense_df[expense_df["amount"] > upper_fence]
        if not outlier_txns.empty:
            max_txn = outlier_txns.sort_values(by="amount", ascending=False).iloc[0]
            max_amt = float(max_txn["amount"])
            max_cat = str(max_txn["category"])
            max_date = str(max_txn["date"])

            insights.append(
                FinancialInsight(
                    category="Outliers",
                    title="High-Value Transaction Spikes Identified",
                    observation=(
                        f"Identified {len(outlier_txns)} expense transactions exceeding the statistical upper fence "
                        f"of {format_currency(upper_fence)} (Q3 + 1.5×IQR). The peak single transaction was "
                        f"{format_currency(max_amt)} in '{max_cat}' on {max_date}."
                    ),
                    recommendation=(
                        "Inspect flagged outlier transactions in the Anomaly Detection module to distinguish planned "
                        "capital purchases from irregular shocks."
                    ),
                    severity="INFO",
                    supporting_metric={
                        "outlier_count": len(outlier_txns),
                        "upper_fence_threshold": round(float(upper_fence), 2),
                        "peak_amount": max_amt,
                        "peak_category": max_cat,
                    },
                )
            )

    return insights

