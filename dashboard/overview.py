"""
Dashboard Overview Page

Author: Akash Das
Description: Primary executive financial overview featuring high-level KPIs,
             cash flow comparisons, monthly trajectories, net savings trends,
             and recent transaction activity in Indian Rupees (₹ / INR).
"""

from typing import Optional
import pandas as pd
import streamlit as st

from dashboard.charts import (
    create_income_vs_expense_chart,
    create_monthly_savings_chart,
    create_monthly_trends_chart,
)
from expense_tracker.analytics.financial_metrics import compute_financial_kpis
from expense_tracker.utils.helpers import format_currency, format_percentage


def render_overview_page(df: Optional[pd.DataFrame] = None) -> None:
    """Render high-level executive dashboard overview.

    Displays primary financial KPIs, cash flow comparison, monthly trends,
    and a preview of recent transactions.

    Args:
        df: Filtered transaction DataFrame. If None or empty, displays warning.
    """
    st.header("📊 Financial Overview")
    st.caption("Executive financial snapshot, cash flow trajectory, and primary portfolio KPIs.")

    if df is None or df.empty:
        st.warning("⚠️ No transactions match the selected filters. Please adjust your filter criteria in the sidebar.")
        return

    # Compute centralized financial KPIs
    kpis = compute_financial_kpis(df)

    # Primary KPI Cards - Row 1: Flow Totals & Net Position
    st.markdown("### 💼 Portfolio Summary")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total Income",
            value=format_currency(kpis["total_income"]),
            help="Total gross earnings and credits across the selected period.",
        )

    with col2:
        st.metric(
            label="Total Expenses",
            value=format_currency(kpis["total_expenses"]),
            help="Total debits and expenditures across the selected period.",
        )

    with col3:
        savings_color = "normal" if kpis["net_savings"] >= 0 else "inverse"
        st.metric(
            label="Net Savings",
            value=format_currency(kpis["net_savings"]),
            delta="Surplus" if kpis["net_savings"] >= 0 else "Deficit",
            delta_color=savings_color,
            help="Net financial surplus or deficit = Total Income - Total Expenses.",
        )

    # Primary KPI Cards - Row 2: Efficiencies & Ticket Sizes
    col4, col5, col6 = st.columns(3)

    with col4:
        savings_rate_str = (
            format_percentage(kpis["savings_rate_pct"])
            if not pd.isna(kpis["savings_rate_pct"])
            else "N/A (No Income)"
        )
        st.metric(
            label="Savings Rate",
            value=savings_rate_str,
            help="Net Savings divided by Total Income. Undefined when Total Income is ₹0.00.",
        )

    with col5:
        st.metric(
            label="Total Transactions",
            value=f"{kpis['total_transactions']:,}",
            help=f"Includes {kpis['income_count']:,} income and {kpis['expense_count']:,} expense records.",
        )

    with col6:
        st.metric(
            label="Average Expense Ticket",
            value=format_currency(kpis["average_expense"]),
            help="Mean expenditure amount per expense transaction.",
        )

    st.markdown("---")

    # Interactive Visualizations Section
    st.markdown("### 📈 Cash Flow & Trend Analysis")

    tab_trends, tab_comparison, tab_savings = st.tabs(
        ["📅 Monthly Trends", "⚖️ Income vs. Expense", "💰 Net Savings Trajectory"]
    )

    with tab_trends:
        st.plotly_chart(create_monthly_trends_chart(df), use_container_width=True)
        st.caption("Chronological comparison of monthly income vs. monthly expenses.")

    with tab_comparison:
        st.plotly_chart(create_income_vs_expense_chart(df), use_container_width=True)
        st.caption("Aggregate volume and relative percentage share between income and expense flows.")

    with tab_savings:
        st.plotly_chart(create_monthly_savings_chart(df), use_container_width=True)
        st.caption("Monthly net savings showing capital surplus (green) versus net deficit (red) against ₹0 baseline.")

    st.markdown("---")

    # Recent Transactions Preview
    st.markdown("### 📋 Recent Transactions Preview")

    # Sort descending by parsed date or string date
    sort_col = "parsed_date" if "parsed_date" in df.columns else "date"
    recent_df = df.sort_values(by=sort_col, ascending=False).head(15).copy()

    # Select display columns (using display_description to mask synthetic shock markers)
    display_cols = []
    col_mapping = {}

    if "date" in recent_df.columns:
        display_cols.append("date")
        col_mapping["date"] = "Date"

    if "type" in recent_df.columns:
        display_cols.append("type")
        col_mapping["type"] = "Type"

    if "category" in recent_df.columns:
        display_cols.append("category")
        col_mapping["category"] = "Category"

    if "amount" in recent_df.columns:
        display_cols.append("amount")
        col_mapping["amount"] = "Amount"

    if "payment_method" in recent_df.columns:
        display_cols.append("payment_method")
        col_mapping["payment_method"] = "Payment Method"

    desc_col = "display_description" if "display_description" in recent_df.columns else "description"
    if desc_col in recent_df.columns:
        display_cols.append(desc_col)
        col_mapping[desc_col] = "Description"

    table_data = recent_df[display_cols].rename(columns=col_mapping)

    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Amount": st.column_config.NumberColumn(
                "Amount",
                format="₹%.2f",
                help="Transaction amount in Indian Rupees (₹).",
            )
        },
    )
    st.caption(f"Showing the latest {len(table_data)} transactions matching active filter criteria.")


if __name__ == "__main__":
    from dashboard.data_processing import load_dashboard_data

    sample_df = load_dashboard_data()
    render_overview_page(sample_df)
