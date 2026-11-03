# User Guide & Operational Walkthrough

**Author: Akash Das**  
**Project**: Expense Tracker App using Data Science  
**Status**: Phase 8 Insights, Anomaly Detection & Forecasting Implemented  

---

## 1. Installation & Environment Setup

### Step 1: Navigate to Project Directory
Ensure your terminal session is rooted at the project workspace:
```powershell
cd "D:\Projects\Data Science\Expense Tracker App"
```

### Step 2: Activate Virtual Environment
Use the existing, verified Python 3.11 virtual environment:
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
If setting up a fresh machine, install dependencies from `requirements.txt`:
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## 2. Launching the Interactive Dashboard

Launch the multi-page Streamlit analytics dashboard using the virtual environment interpreter:

```powershell
# Windows PowerShell
.\.venv\Scripts\streamlit.exe run app.py
```

```bash
# macOS / Linux
streamlit run app.py
```

The application automatically initializes in your default web browser at:
`http://localhost:8501`

### 2.1. Professional Dark Theme and Appearance Settings

The dashboard defaults to an executive dark theme configured via `.streamlit/config.toml` (`#111827` main background, `#1F2937` secondary cards, `#F9FAFB` high-contrast typography, and dark-themed Plotly charts with transparent canvases).

Users can adjust theme settings via Streamlit's native interface:
1. Click the menu icon in the top right corner of the dashboard.
2. Select **Settings**.
3. Under **Theme**, choose between **Dark** (default), **Light**, or **Use system setting**.

---

## 3. Sidebar Navigation & Data Filters

The left-hand sidebar provides global navigation and pure, non-mutating data filters that apply across all dashboard views in real time:

1. **Navigation Menu**: Select between the four primary dashboard views:
   - `📊 Overview`
   - `💳 Spending Analysis`
   - `🎯 Budget Analysis`
   - `📈 Forecasting & Anomalies`
2. **Date Range (Inclusive)**:
   - Calendar date picker allowing you to select start and end dates.
   - Filter boundaries are strictly inclusive: transactions occurring on the start date and end date are fully included.
3. **Transaction Type**:
   - Filter between `Income`, `Expense`, or both flows simultaneously.
4. **Category Filter**:
   - Multi-select dropdown dynamically populated with all available categories from the dataset.
5. **Payment Channel Filter**:
   - Multi-select filter for payment methods (`UPI`, `Cash`, `Debit Card`, `Credit Card`, `Bank Transfer`).
6. **Active Records Telemetry**:
   - Real-time indicator showing active filtered record counts and percentage of the total sample dataset (e.g. `Active Records: 5,000 / 5,000 (100.0%)`).

---

## 4. Dashboard View Walkthroughs

### 4.1. 📊 Financial Overview Page
Designed for high-level executive financial health monitoring:
- **Portfolio Summary KPIs**:
  - **Total Income**: Aggregate income credits across the selected window (formatted in `₹ INR`).
  - **Total Expenses**: Aggregate debits and expenditures.
  - **Net Savings**: Net financial position (`Total Income - Total Expenses`) with dynamic surplus/deficit badges.
  - **Savings Rate**: Percentage of income retained. Transparently displays `N/A (No Income)` when income is zero to maintain mathematical integrity.
  - **Total Transactions**: Total record volume partitioned by flow direction.
  - **Average Expense Ticket**: Mean outflow per expense transaction.
- **Cash Flow Visualizations**:
  - **Monthly Trends**: Chronological grouped bar chart comparing monthly income against monthly expenses.
  - **Income vs. Expense**: Cash flow volume and percentage share comparison.
  - **Net Savings Trajectory**: Monthly net savings bar chart colored dynamically (Emerald Green for capital surplus, Rose Red for net deficit) against a ₹0 horizontal baseline.
- **Recent Transactions Preview**:
  - Displays the 15 most recent transactions with column formatting.
  - Ground-truth evaluation markers (`[UNUSUAL]`) are masked in the user-facing description column to preserve presentation quality.

### 4.2. 💳 Spending Analysis Page
Dedicated deep-dive into expense patterns (strictly isolates `Expense` transactions):
- **Expenditure Snapshot**: Total expenses, top spending category name and amount, top-5 categories cumulative share (%), and total expense transaction count.
- **Category Spending Allocations**:
  - Descending horizontal bar chart showing category total expenditures and percentage shares.
  - Category allocation donut chart displaying proportional expenditure breakdown.
  - Collapsible full category spending data table with sortable columns (Total Spend, Share %, Count, Mean Ticket, Median Ticket).
- **Payment Channel Distribution**:
  - Donut chart and breakdown table illustrating spending distribution across UPI, Cards, Cash, and Transfers.
- **Mean vs. Median Ticket Size Skew Analysis**:
  - Grouped bar chart comparing the mean ticket size against the median ticket size for each expense category.
  - Analytical callout explaining right-skewed category distributions caused by large, infrequent shock purchases (e.g. Travel or Healthcare).

### 4.3. 🎯 Budget Management Page
Interactive category budget planning, variance auditing, and portfolio health monitoring:
- **Calendar Month Budgeting & Dedicated Period Selector**:
  - Category budget targets are calibrated as monthly baselines. To eliminate dimensional mismatch (e.g. evaluating 1 month of budget against 12 months of expenditures), the page incorporates a dedicated calendar-month selector.
  - Automatically identifies complete calendar months and defaults to the latest complete month in the dataset (**October 2026**).
  - Evaluates actual spending strictly from the 1st day of the selected month to the final calendar day inclusive.
  - **Global Sidebar Date Filter Isolation**: The global sidebar date filter does not truncate or prorate monthly budget targets. The Budget Analysis page uses the complete dataset for the selected calendar month while honoring category and payment channel filters.
  - **Period-Specific KPI Metric Cards & Labels**: All four KPI cards, the health alert banner, chart titles, and the variance ledger dynamically reflect the evaluated period (e.g., `Total Planned Budget (October 2026)`, `Total Actual Spend (October 2026)`).
- **Benchmark Budget Presets**:
  - Choose between pre-configured illustrative presets:
    - *Balanced Illustrative Benchmark (Full Portfolio)*: Comprehensive category allocations (Total: ₹84,500/month).
    - *Essential Core Preset (Select Categories Budgeted)*: Demonstrates unbudgeted category handling by omitting discretionary categories.
    - *Frugal / Austere Preset*: Reduced discretionary spending targets (Total: ₹57,000/month).
    - *Zero-Discretionary Allocation Preset (Explicit ₹0 Budget)*: Demonstrates explicit ₹0 budgets for discretionary categories alongside essential allocations.
- **Interactive Budget Customizer & Distinction of Zero vs. Unbudgeted**:
  - Collapsible `st.data_editor` featuring explicit **'Is Budgeted'** checkboxes and **'Monthly Budget (₹)'** inputs:
    - **Explicit ₹0 Budget** (`Is Budgeted` checked, amount = `₹0.00`): The category is under active budget enforcement with zero spending permitted. If actual spend > 0, it is classified as **🚨 Over Budget**. If actual spend == 0, it is classified as **✅ Within Budget** (with 0% utilization).
    - **Unbudgeted / Not Assessed** (`Is Budgeted` unchecked): The category is absent from the budget definition. When *Include Unbudgeted Categories* is enabled, it appears in the ledger with `NaN` budget and a nullable boolean `pd.NA` status (**⚪ Not Assessed (Unbudgeted)**). It is strictly excluded from over-budget and under-budget counts. If spending is also zero, it does not appear in variance analysis.
- **Unbudgeted Category Inclusion Toggle**:
  - Checkbox enabling or isolating categories with spending but no assigned budget.
- **Portfolio Health Indicators**:
  - Total Planned Budget, Total Actual Spend, Net Budget Balance (Remaining Surplus or Overrun), and Budget Utilization Rate, all scoped to the evaluated calendar month.
  - Dynamic alert banner indicating portfolio status (`OPTIMAL`, `WARNING`, `CRITICAL`) with category counts (`🚨 Over Budget`, `✅ Within Budget`, `⚪ Unbudgeted Categories`).
- **Budget vs. Actual Chart**:
  - Visual comparison displaying planned budget bars against actual spending bars, with dynamic red bars for over-budget categories and grey bars for unbudgeted categories.
  - Chart title dynamically states the evaluated month (e.g., `Category Budget vs. Actual Expenditure (October 2026)`).
  - Hover tooltips distinguish explicit zero budgets (`Planned Budget: ₹0.00`) from unbudgeted categories (`Planned Budget: Unbudgeted / Not Assessed`).
- **Category Variance Ledger**:
  - Comprehensive ledger detailing Planned Budget, Actual Spend, Variance, Remaining Budget, Utilization (%), and Status badges for the selected month.

### 4.4. 📈 Predictive Forecasting & Anomaly Detection Page
An interactive machine-learning and data science workspace partitioned into three dedicated tabs:

#### Tab 1: 💡 Financial Insights
Automated synthesis of empirical portfolio findings and actionable financial hygiene recommendations:
- **Evidence-Based Observations**: Derived strictly from calculated metrics without fabricated numbers or hardcoded assumptions.
- **Configurable Analytical Heuristics**:
  - **Cash Flow Health**: Capital surplus rate analysis or net deficit warnings. Handles zero-income subsets with explicit warnings and undefined savings rate notes.
  - **Category Concentration (Default: 15%)**: Highlights dominant expenditure categories. Note: A single structural commitment (e.g. rent) may legitimately take 30–40% without reflecting mismanagement.
  - **Payment Channel Dependency (Default: 35%)**: Highlights payment channels capturing $\ge 35\%$ of total transaction volume (reflects consumer convenience, not credit risk).
  - **Month-over-Month Trajectory (Default: 20%)**: Detects monthly spending acceleration spikes ($> 20\%$) (often reflects calendar seasonality, not discretionary overspending).
  - **Budget Variance & Enforcement**: Flags categories exceeding planned budget allocations and highlights active spending in unbudgeted categories.
  - **Statistical Outlier Spikes**: Flags extreme single-transaction expenditures exceeding Tukey's upper fence ($Q_3 + 1.5 \times \text{IQR}$).
- **Non-Causal Hygiene Guidance**: Recommendations offer standard financial hygiene suggestions rather than asserting causal conclusions.
- **Severity-Tiered Visual Cards**: Each insight displays a title, severity badge (`OPTIMAL`, `INFO`, `WARNING`, `CRITICAL`), empirical observation text with exact INR figures, and an actionable financial hygiene recommendation.

#### Tab 2: 🚨 Anomaly Detection (Isolation Forest)
Unsupervised multi-dimensional outlier detection powered by Scikit-Learn:
- **Target Leakage Safeguard**: Trained strictly on the 42-feature numeric matrix (`get_model_feature_matrix`). Quarantines transaction IDs, descriptions, text length proxies, and synthetic evaluation markers. Warmup lookback NaNs are imputed with `0.0`.
- **A Priori Parameter Specification**: The default contamination rate of 0.02 was specified as an operational domain heuristic (~2% expected anomalies) and was not tuned on the evaluation labels.
- **Interactive Contamination Control**: Sidebar/tab slider allowing users to adjust expected anomaly contamination rate from `0.5%` to `5.0%` (default: `2.0%`).
- **Telemetry KPIs**: Immediate calculation of Flagged Anomalies Count, Anomaly Share (%), and Average Anomalous Ticket Size.
- **Severity-Ranked Anomaly Ledger**: Data table sorting flagged anomalies by isolation decision score. Synthetic `[UNUSUAL]` tags are cleanly masked from `display_description` to preserve presentation quality.
- **Ground-Truth Benchmark Audit & Sample-Size Disclosures**:
  - **Full-Dataset Transductive Audit**: Evaluates Isolation Forest across all 5,000 records at the active slider contamination setting ($N_{\text{pos}} = 12 / 5,000$, Precision: 2.00%, Recall: 16.67%, F1: 3.57%, $TP=2, FP=98, TN=4890, FN=10$).
  - **Inductive Out-of-Sample Hold-Out**: Chronological 80% train / 20% test split. Trains strictly on 4,000 records and evaluates on 1,000 unseen test records.
  - **100% Test Recall Representation**: Test positive count is **exactly 1 positive anomaly** ($N_{\text{pos}} = 1 / 1,000$). The 100% recall represents detecting **one out of one** positive test sample ($TP=1, FN=0, FP=30, TN=969$). Precision is 3.23% ($1 / 31$).
  - **Extreme Sample-Size Uncertainty Warning**: With $N_{\text{pos}} = 1$, performance estimates carry extreme statistical uncertainty (missing one transaction drops recall from 100% to 0%).
  - **Real-World Efficacy Limitation**: This benchmark demonstrates algorithm execution on synthetic data and should **not** be construed as evidence of reliable real-world fraud or crime detection.
- **Multi-Dimensional vs. Univariate Benchmark Explanation**:
  - The 12 evaluation anomalies were generated exclusively as univariate monetary shocks on `amount` (₹65,000–₹162,000). A simple Z-score rule on amount isolates them with 100% precision and recall due to this single-variable synthetic construction.
  - This 100% synthetic Z-score result is an artifact of the benchmark design and does not imply superiority in real-world fraud detection where fraudulent transactions mimic typical amounts.
  - Isolation Forest constructs recursive partitions across all 42 feature dimensions simultaneously. It isolates multi-attribute outliers (e.g. rare payment methods on atypical days), which appear as 'false positives' under a univariate monetary benchmark but are mathematically valid multidimensional anomalies.
- **Honest Metrics**: Weak precision and recall results are reported transparently without artificial tuning.

#### Tab 3: ⏳ Expense Forecasting (Selected: Rolling Mean | Experimental: ARIMA)
Time-series expenditure modeling and 30-day forward projection:
- **Model Selection & Primary Metric Rationale**:
  - **Primary Metric**: **RMSE (Root Mean Squared Error)** is retained as the primary selection criterion because the training-only walk-forward cross-validation supports it (the 7-day rolling mean achieved lower mean RMSE across 28 training folds).
  - **Symmetry Clarification**: RMSE penalizes errors **quadratically and symmetrically in either direction** ($(\hat{y}_t - y_t)^2$). It is a statistical measure of error dispersion and variance, **not** specifically an under-prediction or liquidity-risk metric; RMSE does not inherently protect against under-predictions, overdrafts, or cash shortfalls.
  - **Chronological Hold-Out Results (80% Train / 20% Test, 73 Days)**:
    - **7-Day Rolling Mean (Selected Model)**: $\text{RMSE} = ₹15,908.52$ [Lowest RMSE], $\text{MAE} = ₹9,179.72$, $\text{MAPE} = 57.79\%$.
    - **Naive Baseline (Last Value)**: $\text{RMSE} = ₹16,129.58$, $\text{MAE} = ₹8,615.66$ [Lowest MAE & MAPE], $\text{MAPE} = 47.50\%$.
    - **ARIMA(1, 1, 1) (Experimental Comparison)**: $\text{RMSE} = ₹16,554.07$, $\text{MAE} = ₹10,881.64$, $\text{MAPE} = 77.23\%$.
    - **Historical Mean Baseline**: $\text{RMSE} = ₹16,781.57$, $\text{MAE} = ₹11,308.29$, $\text{MAPE} = 81.12\%$.
- **MAE vs. RMSE Trade-Off & Future Asymmetric Loss Enhancements**:
  - The **7-Day Rolling Mean is not universally superior** across all metrics.
  - The **Naive baseline achieves the lowest MAE** (₹8,615.66 vs. ₹9,179.72) and **lowest MAPE** (47.50% vs. 57.79%) because predicting the immediate previous value incurs low linear deviations during calm periods.
  - The 7-Day Rolling Mean achieves the **lowest RMSE** (₹15,908.52 vs. ₹16,129.58 for Naive and ₹16,554.07 for ARIMA). Rather than claiming it dynamically cushions sudden spending spikes in real time, its lower RMSE accurately reflects lower overall error variance across the evaluation window.
  - ARIMA(1, 1, 1) underperforms both baselines across all metrics due to variance inflation from over-differencing.
  - **Potential Future Improvements (Not Implemented)**: Standard RMSE and MAE penalize over-prediction and under-prediction equally. For applications requiring asymmetric protection against under-prediction (where under-forecasting expenses is costlier than over-forecasting), future enhancements could evaluate **asymmetric loss functions** (e.g., lin-lin loss) or **upper-quantile forecasting** (e.g., pinball loss at $\tau = 0.80$ or $0.90$). These represent potential future algorithmic directions, not currently implemented features.
- **Pre-Test Walk-Forward Validation Evidence**:
  - Model selection was validated *prior* to evaluating the test set using 28 chronological walk-forward folds strictly on the 292 training days (`min_train=90`, `horizon=7`, `step=7`).
  - Across the 28 training folds, 7-Day Rolling Mean achieved lower average RMSE (₹19,963.35 vs. ₹23,165.07) and lower average MAE (₹14,359.63 vs. ₹16,207.57) than Naive, confirming its selection without test-set leakage.
- **Stationarity & Over-Differencing Diagnostics (ADF Test)**:
  - Automated Augmented Dickey-Fuller unit-root test: ADF statistic = -20.76, p-value < 0.001. Rejects the unit-root null hypothesis (evidence against a unit root).
  - *Statistical Nuance*: Rejection of the unit-root null is not absolute proof of strict covariance stationarity.
  - *Over-Differencing*: First differencing doubles series variance from 551M to 1.20B ($2.18\times$), demonstrating that $d=1$ causes over-differencing.
- **Interactive 30-Day Forward Projection Chart**: Plotly time series visualization displaying historical daily expenses, out-of-sample hold-out validation, and 30-day forward projection with a 95% confidence interval ribbon. Clearly labels the Selected 7-Day Rolling Mean forecast and compares it with experimental ARIMA traces.
- **Confidence Interval Presentation Constraint**:
  - Lower bounds are clipped to ₹0.00 because financial expenditures cannot be negative.
  - *Statistical Coverage Disclosure*: Clipping truncates the distribution tail and alters coverage probability; therefore, the displayed interval does not retain nominal 95% statistical coverage under standard normal theory. Both raw unclipped bounds and display-clipped bounds are stored.
- **Evaluation Metrics & Zero-Spend MAPE Limitation**: Standard MAPE divides by zero on ₹0 spend days; MAPE is evaluated strictly across non-zero actual days ($y_t > 0$); MAE and RMSE in INR are the primary trustworthy metrics.

---

## 5. Running Verification Tests

To execute the test suite covering data loaders, schema validation, feature engineering, financial analytics, dashboard modules, anomaly detection, insights, and time-series forecasting:

```powershell
.\.venv\Scripts\pytest.exe tests/ -v
```

All 182 tests should execute and pass with zero failures.
