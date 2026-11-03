"""
Expense Tracker App — Streamlit Main Application

Author: Akash Das
Description: Interactive multi-page financial analytics dashboard powered by Streamlit,
             Plotly, and Pandas. Provides high-level executive summaries, deep spending
             breakdowns, interactive category budget tracking, and predictive forecasting
             specifications in Indian Rupees (₹ / INR).
"""

from typing import Tuple
import sys
from pathlib import Path

# Ensure src/ directory is on sys.path for direct script and Streamlit execution
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pandas as pd
import streamlit as st

from dashboard.budgets import render_budgets_page
from dashboard.data_processing import (
    filter_transactions,
    get_available_categories,
    get_available_payment_methods,
    get_dataset_date_bounds,
    load_dashboard_data,
)
from dashboard.forecasting import render_forecasting_page
from dashboard.overview import render_overview_page
from dashboard.spending import render_spending_page
from expense_tracker.config.settings import APP_NAME, APP_VERSION, AUTHOR


@st.cache_data
def get_cached_dashboard_data() -> pd.DataFrame:
    """Load and cache transaction records for high-performance dashboard re-rendering."""
    return load_dashboard_data()


def main() -> None:
    """Main Streamlit application entry point and router."""
    # Configure page settings
    st.set_page_config(
        page_title=f"{APP_NAME}",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Load baseline dataset
    try:
        raw_df = get_cached_dashboard_data()
    except Exception as exc:
        st.error(f"Failed to load dataset: {exc}")
        return

    # Sidebar Header
    st.sidebar.title(f"💰 {APP_NAME}")
    st.sidebar.caption(f"Version {APP_VERSION} | Author: {AUTHOR}")
    st.sidebar.markdown("---")

    # Navigation Menu
    nav_options = [
        "📊 Overview",
        "💳 Spending Analysis",
        "🎯 Budget Analysis",
        "📈 Forecasting & Anomalies",
    ]
    page_param = str(st.query_params.get("page", "")).lower()
    default_page_idx = 0
    if "spend" in page_param:
        default_page_idx = 1
    elif "budget" in page_param:
        default_page_idx = 2
    elif any(k in page_param for k in ("forecast", "anomal", "insight")):
        default_page_idx = 3

    selected_page = st.sidebar.radio(
        "Navigation",
        options=nav_options,
        index=default_page_idx,
        help="Switch between dashboard views and analytical modules.",
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Filter Data")

    # Date Range Filter
    min_date, max_date = get_dataset_date_bounds(raw_df)
    date_selection = st.sidebar.date_input(
        "Date Range (Inclusive)",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        help="Select calendar start and end dates to filter transactions.",
    )

    # Normalize date selection tuple safely
    if isinstance(date_selection, (tuple, list)):
        if len(date_selection) == 2:
            start_date, end_date = date_selection
        elif len(date_selection) == 1:
            start_date = end_date = date_selection[0]
        else:
            start_date, end_date = min_date, max_date
    else:
        start_date = end_date = date_selection

    # Transaction Type Filter
    all_types = ["Income", "Expense"]
    selected_types = st.sidebar.multiselect(
        "Transaction Type",
        options=all_types,
        default=all_types,
        help="Select cash flow directions to include.",
    )

    # Category Filter
    all_categories = get_available_categories(raw_df)
    selected_categories = st.sidebar.multiselect(
        "Category",
        options=all_categories,
        default=all_categories,
        help="Filter specific income or expense categories.",
    )

    # Payment Method Filter
    all_payment_methods = get_available_payment_methods(raw_df)
    selected_payment_methods = st.sidebar.multiselect(
        "Payment Channel",
        options=all_payment_methods,
        default=all_payment_methods,
        help="Filter transactions by payment instrument.",
    )

    # Apply pure filtering pipeline
    filtered_df = filter_transactions(
        raw_df,
        start_date=start_date,
        end_date=end_date,
        transaction_types=selected_types if selected_types else None,
        categories=selected_categories if selected_categories else None,
        payment_methods=selected_payment_methods if selected_payment_methods else None,
    )

    # Sidebar Filter Diagnostics
    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"**Active Records**: {len(filtered_df):,} / {len(raw_df):,} "
        f"({(len(filtered_df) / max(1, len(raw_df))) * 100:.1f}%)"
    )

    # Route to Selected Page
    if selected_page == "📊 Overview":
        render_overview_page(filtered_df)
    elif selected_page == "💳 Spending Analysis":
        render_spending_page(filtered_df)
    elif selected_page == "🎯 Budget Analysis":
        render_budgets_page(
            filtered_df,
            full_df=raw_df,
            categories=selected_categories if selected_categories else None,
            payment_methods=selected_payment_methods if selected_payment_methods else None,
        )
    elif selected_page == "📈 Forecasting & Anomalies":
        render_forecasting_page(filtered_df)

    # Application Footer
    st.markdown("---")
    st.caption(
        f"**{APP_NAME}** — Data Science & Analytics Portfolio Project | "
        f"Author: **{AUTHOR}** | Built with Streamlit, Plotly, and Pandas."
    )


if __name__ == "__main__":
    main()
