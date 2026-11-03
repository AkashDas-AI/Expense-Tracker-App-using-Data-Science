"""
Dashboard Budget Management Page

Author: Akash Das
Description: Category budget planning, interactive benchmark allocation,
             variance tracking, utilization rate alerts, and portfolio health
             monitoring in Indian Rupees (₹ / INR).
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import streamlit as st

from dashboard.charts import create_budget_vs_actual_chart
from expense_tracker.analytics.budget_analysis import (
    compute_budget_summary,
    compute_budget_variance,
)
from expense_tracker.data.validation import ALLOWED_EXPENSE_CATEGORIES
from expense_tracker.utils.helpers import format_currency, format_percentage


def get_budget_utilization_alert(utilization_pct: float) -> Dict[str, str]:
    """Derive health status alert level and advisory message based on budget utilization.

    Args:
        utilization_pct: Cumulative utilization percentage across budgeted categories.

    Returns:
        Dict with 'level' ('OPTIMAL', 'WARNING', 'CRITICAL', 'INFO') and 'message'.
    """
    if pd.isna(utilization_pct):
        return {
            "level": "INFO",
            "message": "No active category budgets allocated for the selected period.",
        }
    if utilization_pct > 100.0:
        return {
            "level": "CRITICAL",
            "message": f"Portfolio budget exceeded by {utilization_pct - 100.0:.1f}% overrun.",
        }
    if utilization_pct >= 90.0:
        return {
            "level": "WARNING",
            "message": f"Spending near limit at {utilization_pct:.1f}% utilization.",
        }
    return {
        "level": "OPTIMAL",
        "message": f"Spending within limits at {utilization_pct:.1f}% utilization.",
    }

# Illustrative benchmark presets (clearly distinguished from actual transaction dataset)
BENCHMARK_PRESETS: Dict[str, Dict[str, float]] = {
    "Balanced Illustrative Benchmark (Full Portfolio)": {
        "Rent": 25000.0,
        "Groceries": 12000.0,
        "Dining": 6000.0,
        "Shopping": 8000.0,
        "Utilities": 5000.0,
        "Transport": 4000.0,
        "Entertainment": 4000.0,
        "Healthcare": 3000.0,
        "Education": 3000.0,
        "Subscriptions": 1500.0,
        "Travel": 10000.0,
        "Other Expenses": 3000.0,
    },
    "Essential Core Preset (Select Categories Budgeted)": {
        "Rent": 25000.0,
        "Groceries": 14000.0,
        "Utilities": 5500.0,
        "Transport": 5000.0,
        "Healthcare": 4000.0,
        "Education": 3500.0,
        # Discretionary categories (Dining, Shopping, Travel, etc.) left unbudgeted
    },
    "Frugal / Austere Preset": {
        "Rent": 20000.0,
        "Groceries": 9000.0,
        "Dining": 3000.0,
        "Shopping": 3000.0,
        "Utilities": 4000.0,
        "Transport": 3000.0,
        "Entertainment": 1500.0,
        "Healthcare": 2500.0,
        "Education": 2500.0,
        "Subscriptions": 1000.0,
        "Travel": 4000.0,
        "Other Expenses": 2000.0,
    },
    "Zero-Discretionary Allocation Preset (Explicit ₹0 Budget)": {
        "Rent": 25000.0,
        "Groceries": 12000.0,
        "Utilities": 5000.0,
        "Transport": 4000.0,
        "Healthcare": 3000.0,
        "Education": 3000.0,
        "Subscriptions": 1500.0,
        "Dining": 0.0,         # Explicit ₹0 budget: spending triggers Over Budget
        "Shopping": 0.0,       # Explicit ₹0 budget: spending triggers Over Budget
        "Entertainment": 0.0,  # Explicit ₹0 budget: spending triggers Over Budget
        "Travel": 0.0,         # Explicit ₹0 budget: spending triggers Over Budget
        "Other Expenses": 0.0, # Explicit ₹0 budget: spending triggers Over Budget
    },
}


def get_available_budget_months(
    df: pd.DataFrame,
) -> Tuple[List[Dict[str, Any]], int]:
    """Extract chronological calendar months from transaction dataset with completeness metadata.

    Args:
        df: Input transaction DataFrame containing a 'date' column.

    Returns:
        Tuple containing:
        - List of dicts per calendar month with keys:
            'key': str 'YYYY-MM'
            'label': str (e.g. 'October 2026')
            'start_date': str 'YYYY-MM-01'
            'end_date': str 'YYYY-MM-DD'
            'is_complete': bool (True if transactions span from 1st to last calendar day)
            'actual_min': str 'YYYY-MM-DD'
            'actual_max': str 'YYYY-MM-DD'
            'transaction_count': int
        - int: Default index pointing to the latest complete calendar month in the dataset.
               If no complete month exists, points to the latest available month (or 0 if empty).
    """
    if df is None or df.empty or "date" not in df.columns:
        return [], 0

    dates = pd.to_datetime(df["date"], errors="coerce").dropna()
    if dates.empty:
        return [], 0

    temp_df = pd.DataFrame({"parsed_date": dates})
    temp_df["period"] = temp_df["parsed_date"].dt.to_period("M")

    unique_periods = sorted(temp_df["period"].unique())
    months: List[Dict[str, Any]] = []
    latest_complete_idx = -1

    for idx, p in enumerate(unique_periods):
        m_dates = temp_df.loc[temp_df["period"] == p, "parsed_date"]
        actual_min_dt = m_dates.min()
        actual_max_dt = m_dates.max()

        start_date_dt = p.start_time
        end_date_dt = p.end_time

        # Check completeness: transactions present on the 1st day and the last day of the calendar month
        is_complete = bool(
            (actual_min_dt.day == 1) and (actual_max_dt.day == end_date_dt.day)
        )
        if is_complete:
            latest_complete_idx = idx

        months.append({
            "key": str(p),
            "label": p.strftime("%B %Y"),
            "start_date": start_date_dt.strftime("%Y-%m-%d"),
            "end_date": end_date_dt.strftime("%Y-%m-%d"),
            "is_complete": is_complete,
            "actual_min": actual_min_dt.strftime("%Y-%m-%d"),
            "actual_max": actual_max_dt.strftime("%Y-%m-%d"),
            "transaction_count": len(m_dates),
        })

    # Default to latest complete month; fallback to latest available month if none is complete
    default_idx = latest_complete_idx if latest_complete_idx >= 0 else max(0, len(months) - 1)
    return months, default_idx


def filter_budget_actuals_by_month(
    df: pd.DataFrame,
    start_date: Union[str, date, pd.Timestamp],
    end_date: Union[str, date, pd.Timestamp],
    categories: Optional[List[str]] = None,
    payment_methods: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Filter transactions strictly to the inclusive start and end dates of the selected budget month.

    Args:
        df: Input transaction DataFrame.
        start_date: Start date of the budget month (inclusive, 'YYYY-MM-DD').
        end_date: End date of the budget month (inclusive, 'YYYY-MM-DD').
        categories: Optional category filter to preserve.
        payment_methods: Optional payment method filter to preserve.

    Returns:
        pd.DataFrame: Filtered DataFrame containing transactions within the exact calendar month.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=df.columns if df is not None else [])

    filtered = df.copy()
    if "parsed_date" not in filtered.columns:
        filtered["parsed_date"] = pd.to_datetime(filtered["date"], errors="coerce")

    start_ts = pd.to_datetime(start_date).normalize()
    end_ts = pd.to_datetime(end_date).normalize()

    filtered = filtered[
        (filtered["parsed_date"] >= start_ts) & (filtered["parsed_date"] <= end_ts)
    ]

    if categories is not None and len(categories) > 0:
        filtered = filtered[filtered["category"].isin(categories)]

    if payment_methods is not None and len(payment_methods) > 0:
        filtered = filtered[filtered["payment_method"].isin(payment_methods)]

    return filtered.reset_index(drop=True)


def render_budgets_page(
    df: Optional[pd.DataFrame] = None,
    full_df: Optional[pd.DataFrame] = None,
    categories: Optional[List[str]] = None,
    payment_methods: Optional[List[str]] = None,
    **kwargs: Any,
) -> None:
    """Render interactive budget variance and portfolio health page.

    Evaluates category-level monthly budgets against actual expenditures strictly within
    a selected complete calendar month, eliminating dimensional mismatch with multi-month datasets.

    Args:
        df: Filtered transaction DataFrame from sidebar.
        full_df: Unfiltered transaction DataFrame from data loader to protect against
                 accidental calendar month truncation by narrow sidebar date filters.
        categories: Optional list of categories filtered in the sidebar to respect.
        payment_methods: Optional list of payment methods filtered in the sidebar to respect.
        **kwargs: Additional keyword arguments for backwards-compatible invocation.
    """
    if full_df is None:
        full_df = kwargs.get("full_df", kwargs.get("raw_df", None))
    if categories is None:
        categories = kwargs.get("categories", None)
    if payment_methods is None:
        payment_methods = kwargs.get("payment_methods", None)

    st.header("🎯 Budget Management & Variance Analysis")
    st.caption("Plan category spending targets, monitor variances, and audit portfolio budget utilization.")

    source_df = full_df if full_df is not None and not full_df.empty else df
    if source_df is None or source_df.empty:
        st.warning("⚠️ No transactions match the selected filters. Please adjust your filter criteria in the sidebar.")
        return

    available_months, default_month_idx = get_available_budget_months(source_df)
    if not available_months:
        st.warning("⚠️ No valid transaction date records available to construct budget evaluation periods.")
        return

    # Month Selector, Preset Selection & Interactive Configuration
    st.markdown("### ⚙️ Budget Configuration & Presets")
    st.caption(
        "Select an evaluation month, choose a pre-calibrated benchmark preset, or customize targets. "
        "Category budget targets are monthly baselines evaluated strictly against expenditures within a single calendar month."
    )

    col_month, col_preset, col_toggle = st.columns([1.5, 1.5, 1])

    with col_month:
        month_options = [m["label"] for m in available_months]
        selected_month_label = st.selectbox(
            "Select Evaluation Month",
            options=month_options,
            index=default_month_idx,
            help="Select the complete calendar month to evaluate category spending against monthly budget targets.",
        )
        selected_month = available_months[month_options.index(selected_month_label)]

    with col_preset:
        preset_names = list(BENCHMARK_PRESETS.keys())
        selected_preset = st.selectbox(
            "Select Benchmark Budget Preset",
            options=preset_names,
            index=0,
            help="Choose an illustrative preset or customize individual category allocations.",
        )

    with col_toggle:
        st.write("")  # Spacing alignment
        st.write("")
        include_unbudgeted = st.checkbox(
            "Include Unbudgeted Categories",
            value=True,
            help="When enabled, categories with actual expenditure but no allocated budget are displayed as unbudgeted.",
        )

    period_label = selected_month["label"]

    # Prominent Budget Period Disclosure Banner
    if selected_month.get("is_complete", True):
        st.info(
            f"📅 **Budget Period: {period_label}** (inclusive: {selected_month['start_date']} to {selected_month['end_date']}). "
            f"Category budget targets are monthly baselines compared strictly against actual expenditures "
            f"within this complete calendar month. The global sidebar date range filter does not truncate or prorate monthly budget targets."
        )
    else:
        st.warning(
            f"⚠️ **Incomplete Calendar Month: {period_label}** "
            f"(available records: {selected_month['actual_min']} to {selected_month['actual_max']}; "
            f"full month: {selected_month['start_date']} to {selected_month['end_date']}). "
            f"Category budget targets are monthly baselines; evaluating against an incomplete month understates actual utilization."
        )

    # Prepare initial editor data from selected preset
    base_budget = BENCHMARK_PRESETS[selected_preset]
    all_categories = sorted(list(ALLOWED_EXPENSE_CATEGORIES))

    preset_records = []
    for cat in all_categories:
        is_preset_budgeted = cat in base_budget
        preset_records.append({
            "Category": cat,
            "Is Budgeted": is_preset_budgeted,
            "Monthly Budget (₹)": float(base_budget[cat]) if is_preset_budgeted else 0.0,
        })
    budget_editor_df = pd.DataFrame(preset_records)

    with st.expander("✏️ Customize Category Budget Allocations", expanded=False):
        st.info(
            "💡 **Budget Semantics Guide**:\n"
            "- **Checked 'Is Budgeted'**: The category has an active budget allocation.\n"
            "  - If **Monthly Budget = ₹0.00** and actual spend > 0: Strictly flagged as **🚨 Over Budget**.\n"
            "  - If **Monthly Budget = ₹0.00** and actual spend = 0: Flagged as **✅ Within Budget** (0% utilization).\n"
            "- **Unchecked 'Is Budgeted'**: The category is absent from the budget (**⚪ Unbudgeted / Not Assessed**).\n"
            "  - Unbudgeted categories are isolated with `pd.NA` status and excluded from over/under budget counts."
        )
        edited_budget_df = st.data_editor(
            budget_editor_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Category": st.column_config.TextColumn("Expense Category", disabled=True),
                "Is Budgeted": st.column_config.CheckboxColumn(
                    "Is Budgeted",
                    help="Enable to track an active budget for this category. Disable to mark as Unbudgeted / Not Assessed.",
                    default=True,
                ),
                "Monthly Budget (₹)": st.column_config.NumberColumn(
                    "Monthly Budget Target (₹)",
                    min_value=0.0,
                    step=500.0,
                    format="₹%.2f",
                    help="Allocated budget in INR. An explicit ₹0.00 allocation strictly flags positive spending as an overrun.",
                ),
            },
            key=f"budget_editor_{selected_preset}",
        )

    # Convert edited table into dictionary mapping:
    # Categories with 'Is Budgeted' == True are included in active_budgets (including explicit 0.0!).
    # Categories with 'Is Budgeted' == False are omitted from active_budgets (genuinely unbudgeted).
    active_budgets: Dict[str, float] = {}
    for _, row in edited_budget_df.iterrows():
        cat = str(row["Category"])
        is_budgeted = bool(row["Is Budgeted"])
        if is_budgeted:
            active_budgets[cat] = float(row["Monthly Budget (₹)"])

    # Filter source transactions strictly to the selected calendar month
    month_df = filter_budget_actuals_by_month(
        source_df,
        start_date=selected_month["start_date"],
        end_date=selected_month["end_date"],
        categories=categories,
        payment_methods=payment_methods,
    )
    month_expense_df = month_df[month_df["type"] == "Expense"].copy()

    if month_expense_df.empty:
        st.info(
            f"ℹ️ No expense transactions recorded for **{period_label}**. "
            f"All budgeted categories reflect ₹0.00 actual expenditure (0.0% utilization)."
        )

    # Execute centralized budget analytics preserving Phase 6 semantics
    variance_df = compute_budget_variance(
        month_expense_df,
        budgets=active_budgets,
        include_unbudgeted=include_unbudgeted,
    )
    summary = compute_budget_summary(
        month_expense_df,
        budgets=active_budgets,
        include_unbudgeted=include_unbudgeted,
    )

    st.markdown("---")

    # Portfolio Budget Summary KPIs
    st.markdown("### 📊 Portfolio Budget Health")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label=f"Total Planned Budget ({period_label})",
            value=format_currency(summary["total_budget"]),
            help=f"Cumulative planned allocation across all budgeted categories for {period_label}.",
        )

    with col2:
        st.metric(
            label=f"Total Actual Spend ({period_label})",
            value=format_currency(summary["total_actual_spend"]),
            help=f"Total actual expenditure across evaluated categories recorded in {period_label}.",
        )

    with col3:
        remaining_amt = summary["overall_remaining"]
        rem_color = "normal" if remaining_amt >= 0 else "inverse"
        st.metric(
            label=f"Net Budget Balance ({period_label})",
            value=format_currency(remaining_amt),
            delta="Remaining Surplus" if remaining_amt >= 0 else "Spending Overrun",
            delta_color=rem_color,
            help=f"Total Planned Budget minus Total Actual Spend for {period_label} (positive = remaining surplus).",
        )

    with col4:
        util_str = format_percentage(summary["overall_utilization_pct"])
        st.metric(
            label=f"Budget Utilization ({period_label})",
            value=util_str,
            help=f"Actual Spend divided by Planned Budget on budgeted categories for {period_label}.",
        )

    # Category Health Tally & Alert
    alert = get_budget_utilization_alert(summary["overall_utilization_pct"])
    alert_box = st.error if alert["level"] in ("CRITICAL", "EXCEEDED") else (st.warning if alert["level"] == "WARNING" else st.success)
    alert_box(
        f"**Status ({period_label}): {alert['level']}** — {alert['message']} | "
        f"🚨 **Over Budget**: {summary['over_budget_category_count']} | "
        f"✅ **Within Budget**: {summary['under_budget_category_count']} | "
        f"⚪ **Unbudgeted Categories**: {summary['unbudgeted_category_count']}"
    )

    st.markdown("---")

    # Plotly Budget vs. Actual Visual
    st.markdown(f"### ⚖️ Budget vs. Actual Expenditure ({period_label})")
    st.plotly_chart(
        create_budget_vs_actual_chart(variance_df, period_label=period_label),
        use_container_width=True,
    )

    st.markdown("---")

    # Detailed Variance Table
    st.markdown(f"### 📋 Category Variance Ledger ({period_label})")

    # Format variance table for user presentation
    table_df = variance_df.copy()

    status_labels = []
    for _, row in table_df.iterrows():
        if pd.isna(row["is_over_budget"]):
            status_labels.append("⚪ Not Assessed (Unbudgeted)")
        elif row["is_over_budget"] == True:
            status_labels.append("🚨 Over Budget")
        else:
            status_labels.append("✅ Within Budget")

    table_df["Status"] = status_labels

    st.dataframe(
        table_df[[
            "category",
            "budget_amount",
            "actual_amount",
            "budget_variance",
            "remaining_budget",
            "utilization_pct",
            "Status",
        ]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "category": "Category",
            "budget_amount": st.column_config.NumberColumn(f"Planned Budget ({period_label})", format="₹%.2f"),
            "actual_amount": st.column_config.NumberColumn(f"Actual Spend ({period_label})", format="₹%.2f"),
            "budget_variance": st.column_config.NumberColumn(
                "Variance",
                format="₹%.2f",
                help="Budget minus Actual. Negative values denote spending overrun.",
            ),
            "remaining_budget": st.column_config.NumberColumn("Remaining", format="₹%.2f"),
            "utilization_pct": st.column_config.NumberColumn("Utilization", format="%.2f%%"),
            "Status": st.column_config.TextColumn("Status"),
        },
    )


if __name__ == "__main__":
    from dashboard.data_processing import load_dashboard_data

    sample_df = load_dashboard_data()
    render_budgets_page(sample_df)
