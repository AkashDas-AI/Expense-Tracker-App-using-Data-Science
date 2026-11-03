# Dashboard Screenshot and Visual Asset Checklist

**Author:** Akash Das  
**Project:** Expense Tracker App using Data Science  
**Status:** Phase 9 Completed: All Visual Assets, High-Resolution Screenshots, and Results Generated  

This checklist tracks screenshots, analytical figures, and numerical assets required for technical documentation, reports, and portfolio presentations.

---

## Visual Assets Checklist

- [x] **Overview Page (`images/dashboard_overview.png`)**:
  - [x] Executive KPI cards (Total Income, Total Expenses, Net Savings Surplus/Deficit, Savings Rate, Total Transactions, Average Ticket Size).
  - [x] Monthly Trajectory grouped bar chart (Income vs Expenditure).
  - [x] Cash Flow Volume and Share comparison bar chart.
  - [x] Monthly Net Savings bar chart with dynamic green surplus / red deficit bars and INR 0 baseline.
  - [x] Recent transactions preview table with masked evaluation markers.
- [x] **Spending Breakdown Page (`images/spending_analysis.png`)**:
  - [x] Spending snapshot metrics (Total Expenses, Top Category, Top-5 Categories Share %, Total Expense Transactions).
  - [x] Descending horizontal category spending bar chart.
  - [x] Category allocation donut chart.
  - [x] Detailed category table with ticket sizes and percentages.
  - [x] Payment channel donut chart and transaction breakdown table.
  - [x] Mean vs Median ticket size skew grouped bar chart.
- [x] **Budget Management Page (`images/budget_analysis.png`)**:
  - [x] Dedicated calendar month selector and unbudgeted category toggle.
  - [x] Benchmark budget preset selector and interactive category allocation editor.
  - [x] Portfolio budget health KPIs (Planned Budget, Actual Spend, Net Balance, Utilization %).
  - [x] Dynamic status alert banner with category counts.
  - [x] Budget vs actuals comparison bar chart with color-coded overrun indicators.
  - [x] Category variance ledger table with status badges.
- [x] **Forecasting and Anomaly Detection Page**:
  - [x] **Tab 1: Financial Insights (`images/financial_insights.png`)**: Cards with severity badges, observations, and actionable recommendations.
  - [x] **Tab 2: Anomaly Detection (`images/anomaly_detection.png`)**: Isolation Forest controls (contamination slider, summary telemetry, ranked anomaly table with masked descriptions, ground-truth benchmark confusion matrix).
  - [x] **Tab 3: Expense Forecasting (`images/expense_forecasting.png`)**: Data sufficiency diagnostic, ADF stationarity diagnostic, out-of-sample holdout validation table vs 7-day rolling mean, Plotly forecast chart with 95% CI ribbon.
- [x] **System Architecture (`images/architecture.png`)**:
  - [x] Decoupled 6-layer architecture flowchart diagram.
- [x] **Analytical Figures (`reports/figures/`)**:
  - [x] `transaction_type_distribution.png`
  - [x] `expense_category_distribution.png`
  - [x] `monthly_income_expense.png`
  - [x] `payment_method_distribution.png`
  - [x] `expense_amount_distribution.png`
  - [x] `category_spending.png`
  - [x] `monthly_financial_trends.png`
  - [x] `budget_vs_actual.png`
  - [x] `anomaly_detection.png`
  - [x] `expense_forecast.png`
- [x] **Numerical Deliverables (`reports/results/`)**:
  - [x] `financial_summary.csv`
  - [x] `category_analysis.csv`
  - [x] `monthly_trends.csv`
  - [x] `budget_analysis.csv`
  - [x] `anomaly_evaluation.json`
  - [x] `forecast_evaluation.csv`
  - [x] `forecast_predictions.csv`
  - [x] `insights_summary.json`

All production visual assets are maintained in `images/` (1080p dashboard captures + architecture diagram), `reports/figures/` (10 analytical plots), and `reports/results/` (8 numerical files).
