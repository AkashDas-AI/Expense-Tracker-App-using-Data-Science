"""
Dashboard Spending Breakdown Page

Author: Akash Das
Description: Granular expense category analytics, payment method breakdown,
             mean vs. median ticket size comparisons, and spending distributions
             in Indian Rupees (₹ / INR).
"""

from typing import Optional
import pandas as pd
import streamlit as st

from dashboard.charts import (
    create_category_avg_median_chart,
    create_category_spending_bar_chart,
    create_category_spending_donut_chart,
    create_payment_method_chart,
)
from expense_tracker.analytics.spending_analysis import (
    get_highest_spending_category,
    get_spending_by_category,
    get_spending_by_payment_method,
    get_top_n_expense_categories,
)
from expense_tracker.utils.helpers import format_currency, format_percentage


def render_spending_page(df: Optional[pd.DataFrame] = None) -> None:
    """Render detailed spending breakdown and expenditure analytics.

    Strictly focuses on expense transactions, omitting income records.

    Args:
        df: Filtered transaction DataFrame. If None or empty, displays warning.
    """
    st.header("💳 Spending Breakdown & Analysis")
    st.caption("Deep-dive exploration of expenditure allocations, payment channels, and ticket size patterns.")

    if df is None or df.empty:
        st.warning("⚠️ No transactions match the selected filters. Please adjust your filter criteria in the sidebar.")
        return

    # Strictly filter for expense transactions
    expense_df = df[df["type"] == "Expense"].copy()

    if expense_df.empty:
        st.warning(
            "⚠️ No expense transactions available in the filtered dataset. "
            "Please ensure 'Expense' is selected under Transaction Types in the sidebar."
        )
        return

    # Derive spending analytics
    cat_df = get_spending_by_category(expense_df)
    highest_cat = get_highest_spending_category(expense_df)
    top_5_df = get_top_n_expense_categories(expense_df, n=5)
    total_expense = float(expense_df["amount"].sum())
    top_5_share = float(top_5_df["percentage"].sum()) if not top_5_df.empty else 0.0

    # Key Spending Metrics
    st.markdown("### 📊 Expenditure Snapshot")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Expenses",
            value=format_currency(total_expense),
            help="Total outflow across all expense transactions.",
        )

    with col2:
        top_cat_name = highest_cat["category"] if highest_cat else "None"
        top_cat_amt = format_currency(highest_cat["total_amount"]) if highest_cat else "₹0.00"
        st.metric(
            label="Top Spending Category",
            value=top_cat_name,
            delta=top_cat_amt,
            delta_color="off",
            help="Category with the single highest cumulative expenditure.",
        )

    with col3:
        st.metric(
            label="Top 5 Categories Share",
            value=format_percentage(top_5_share),
            help="Cumulative percentage of total expenditure accounted for by the 5 largest categories.",
        )

    with col4:
        st.metric(
            label="Expense Transactions",
            value=f"{len(expense_df):,}",
            help="Total number of discrete expense transactions recorded.",
        )

    st.markdown("---")

    # Visualizations: Category Allocation
    st.markdown("### 🏷️ Category Spending Breakdown")
    col_bar, col_pie = st.columns([1.2, 1.0])

    with col_bar:
        st.plotly_chart(create_category_spending_bar_chart(expense_df), use_container_width=True)

    with col_pie:
        st.plotly_chart(create_category_spending_donut_chart(expense_df), use_container_width=True)

    # Detailed Category Table
    with st.expander("📋 View Complete Category Spending Table", expanded=False):
        st.dataframe(
            cat_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "category": "Category",
                "total_amount": st.column_config.NumberColumn("Total Spend", format="₹%.2f"),
                "percentage": st.column_config.NumberColumn("Share (%)", format="%.2f%%"),
                "transaction_count": st.column_config.NumberColumn("Count", format="%d"),
                "average_amount": st.column_config.NumberColumn("Mean Ticket", format="₹%.2f"),
                "median_amount": st.column_config.NumberColumn("Median Ticket", format="₹%.2f"),
            },
        )

    st.markdown("---")

    # Payment Channel Distribution & Ticket Size Skew
    col_pm, col_skew = st.columns([1.0, 1.2])

    with col_pm:
        st.markdown("### 💳 Payment Channels")
        st.plotly_chart(create_payment_method_chart(expense_df), use_container_width=True)

        pm_df = get_spending_by_payment_method(expense_df, expense_only=True)
        st.dataframe(
            pm_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "payment_method": "Payment Method",
                "total_amount": st.column_config.NumberColumn("Total Spend", format="₹%.2f"),
                "percentage": st.column_config.NumberColumn("Share (%)", format="%.2f%%"),
                "transaction_count": st.column_config.NumberColumn("Transactions", format="%d"),
                "average_amount": st.column_config.NumberColumn("Avg Ticket", format="₹%.2f"),
            },
        )

    with col_skew:
        st.markdown("### ⚖️ Ticket Size Skew: Mean vs. Median")
        st.plotly_chart(create_category_avg_median_chart(expense_df), use_container_width=True)

        st.info(
            "💡 **Analytical Insight**: When the **mean ticket size** is substantially higher than the "
            "**median ticket size** within a category (e.g. Travel or Healthcare), it signals a right-skewed "
            "distribution driven by infrequent, high-value shock purchases rather than routine daily spending."
        )


if __name__ == "__main__":
    from dashboard.data_processing import load_dashboard_data

    sample_df = load_dashboard_data()
    render_spending_page(sample_df)
