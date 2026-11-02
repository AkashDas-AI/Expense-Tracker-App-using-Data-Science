"""
Expense Tracker App — Streamlit Entry Point

Author: Akash Das
Description: Main application launcher for the Expense Tracker multi-page dashboard.
"""

import streamlit as st
from expense_tracker.config.settings import APP_NAME, APP_VERSION


def main() -> None:
    """Main application entry point."""
    st.set_page_config(
        page_title=f"{APP_NAME}",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title(f"💰 {APP_NAME}")
    st.caption(f"Version {APP_VERSION} | Author: Akash Das")
    st.info(
        "Welcome to the Expense Tracker App. Select a dashboard page from the navigation "
        "to explore spending analyses, budgets, anomaly detection, and forecasting."
    )


if __name__ == "__main__":
    main()

