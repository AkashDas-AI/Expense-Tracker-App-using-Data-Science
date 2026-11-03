# Dashboard Screenshot & Visual Asset Checklist

**Author: Akash Das**  
**Project**: Expense Tracker App using Data Science  
**Status**: Phase 8 Insights, Anomaly Detection & Forecasting Implemented  

This checklist tracks screenshots and figures required for technical documentation, reports, and portfolio presentations.

---

## Visual Assets Checklist

- [ ] **Overview Page (`dashboard/overview.py`)**:
  - [ ] Executive KPI cards (Total Income, Total Expenses, Net Savings Surplus/Deficit, Savings Rate, Total Transactions, Average Ticket Size).
  - [ ] Monthly Trajectory grouped bar chart (Income vs. Expenditure).
  - [ ] Cash Flow Volume & Share comparison bar chart.
  - [ ] Monthly Net Savings bar chart with dynamic green surplus / red deficit bars and ₹0 baseline.
  - [ ] Recent transactions preview table with masked `[UNUSUAL]` evaluation markers.
- [ ] **Spending Breakdown Page (`dashboard/spending.py`)**:
  - [ ] Spending snapshot metrics (Total Expenses, Top Category, Top-5 Categories Share %, Total Expense Transactions).
  - [ ] Descending horizontal category spending bar chart.
  - [ ] Category allocation donut chart.
  - [ ] Detailed category table with ticket sizes and percentages.
  - [ ] Payment channel donut chart and transaction breakdown table.
  - [ ] Mean vs. Median ticket size skew grouped bar chart.
- [ ] **Budget Management Page (`dashboard/budgets.py`)**:
  - [ ] Benchmark budget preset selector and unbudgeted category toggle.
  - [ ] Interactive category budget allocation editor (`st.data_editor`).
  - [ ] Portfolio budget health KPIs (Planned Budget, Actual Spend, Net Balance, Utilization %).
  - [ ] Dynamic status alert banner with category counts (`🚨 Over Budget`, `✅ Within Budget`, `⚪ Unbudgeted`).
  - [ ] Budget vs. actuals comparison bar chart with color-coded overrun indicators.
  - [ ] Category variance ledger table with status badges.
- [ ] **Forecasting & Anomaly Detection Page (`dashboard/forecasting.py`)**:
  - [ ] Tab 1: Financial Insights cards (severity badges, observations, actionable recommendations).
  - [ ] Tab 2: Anomaly Detection controls (contamination slider, summary telemetry, ranked anomaly table with masked descriptions, ground-truth benchmark confusion matrix).
  - [ ] Tab 3: Expense Forecasting (data sufficiency diagnostic, ADF stationarity diagnostic, out-of-sample hold-out validation table vs. 7-day rolling mean, Plotly forecast chart with 95% CI ribbon).
- [ ] **Global Application Frame (`app.py`)**:
  - [ ] Sidebar filters (Date Range, Transaction Types, Category multiselect, Payment Channel multiselect, Active Records Telemetry).
  - [ ] Wide layout responsive views on desktop and mobile viewports.

All final visual assets will be saved in `docs/images/`, `reports/figures/`, and `outputs/figures/`.
