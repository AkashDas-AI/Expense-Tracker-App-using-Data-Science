# Testing & Quality Assurance Guide

**Author: Akash Das**  
**Project**: Expense Tracker App using Data Science  
**Status**: Phase 8 Testing Implemented  

---

## 1. Testing Philosophy
The project enforces high testability across all business logic, data pipelines, analytics computations, visualization modules, and interactive dashboards. Test execution is fully isolated and does not modify production databases.

---

## 2. Test Suite Structure

```text
tests/
├── __init__.py
├── conftest.py                       # Shared fixtures and sys.path configuration
├── test_data_generator.py            # Synthetic generator functional tests (10 tests)
├── test_validation.py                # Schema validation tests (14 tests)
├── test_data_cleaning.py             # Data normalization & non-destructive tests (11 tests)
├── test_data_loader.py               # CSV loader and end-to-end integration tests (8 tests)
├── test_database.py                  # SQLite CRUD, transactions, rollback tests (12 tests)
├── test_feature_engineering.py       # Calendar, lags, rolling stats, dummies, same-day & leakage tests (29 tests)
├── test_financial_metrics.py         # Financial KPIs, totals, savings rate, ratios, ticket sizes (11 tests)
├── test_spending_analysis.py         # Category spending, top-N, payment methods, cash flow breakdown (8 tests)
├── test_budget_analysis.py           # Budget variance, utilization, unbudgeted tracking, portfolio summary (7 tests)
├── test_trend_analysis.py            # Monthly trends, continuous ranges, MoM metrics, rolling trends (6 tests)
├── test_dashboard.py                 # Data loading, masking, inclusive filters, charts, dark theme, budget semantics, calendar month budgeting, app integration (45 tests)
├── test_anomaly_detection.py         # Statistical baselines, Isolation Forest, leakage invariance, out-of-sample eval (15 tests)
├── test_insights.py                  # Financial insights, surplus/deficit, budget overruns, configurable thresholds (7 tests)
└── test_forecasting.py               # Time-series prep, ADF over-differencing, selected rolling mean, ARIMA, hold-out eval, walk-forward CV, MAPE/RMSE symmetry (13 tests)
```
*Total permanent automated unit & integration tests: 196 tests (100% passing).*

---

## 3. Test Modules Breakdown (Phases 2–5)

### 3.1. Data Generation (`test_data_generator.py`)
- Record count accuracy, column adherence, unique sequential IDs.
- Date boundary adherence, positive amount values, dual income/expense representation.
- Canonical category/payment taxonomy validation, deterministic seed reproducibility.

### 3.2. Schema Validation (`test_validation.py`)
- Compliance checking on valid datasets.
- Detection of missing columns, null values, duplicate IDs, and blank descriptions.
- Rejection of invalid types, category mismatches, non-positive and non-numeric amounts.

### 3.3. Data Cleaning (`test_data_cleaning.py`)
- Whitespace stripping and case normalization across text columns.
- Explicit date parsing tests:
  - `YYYY-MM-DD` (ISO) -> resolves to `YYYY-MM-DD` (e.g. `2026-02-01` -> 1 February 2026).
  - `YYYY/MM/DD` (Slash ISO) -> resolves to `YYYY-MM-DD` (e.g. `2026/02/01` -> 1 February 2026).
  - `DD-MM-YYYY` (Indian format) -> resolves to `YYYY-MM-DD` (e.g. `01-02-2026` -> 1 February 2026).
  - Rejection of invalid dates (`2026-02-31`), null dates, and unsupported ambiguous formats (`02/15/2026`).
- Multi-currency symbol stripping (`₹`, `$`, commas) and float conversion.
- Input DataFrame immutability and non-destructive invalid row reporting.

### 3.4. CSV Data Loader & Integration (`test_data_loader.py`)
- File presence checks, empty file rejection, malformed CSV error reporting.
- Schema column verification.
- **End-to-End Integration**: CSV -> Loader -> Cleaner -> Validator -> SQLite -> Retrieval.

### 3.5. Database Storage Layer (`test_database.py`)
- Schema initialization, table creation, and index creation in temporary databases.
- Single and bulk insertions with atomic rollback on constraint violation.
- Parameterized query filtering (date range, type, category, payment method).
- Duplicate skipping (`on_conflict="skip"`) and failure handling (`on_conflict="fail"`).
- **SQLite Engine Constraints Tests**:
  - Verification that low-level DB inserts reject invalid category-to-type combinations (Income + Groceries, Expense + Salary).
  - Verification that low-level DB inserts reject unsupported payment methods.
  - Verification that valid combinations (Income + Salary, Expense + Groceries) insert successfully.

### 3.6. Exploratory Data Analysis Verification (Phase 4)
- **Top-to-Bottom Notebook Execution**: Verification that all 22 code cells in `notebooks/01_exploratory_data_analysis.ipynb` execute without runtime errors.
- **Dataset Consistency**: Confirms sample dataset maintains 5,000 rows, 7 columns, zero missing values, and zero duplicate IDs.
- **Visual Output Verification**: Confirms generation of 5 publication-quality analytical plots in `reports/figures/`.
- **Target Leakage Safeguard Audit**: Ensures `[UNUSUAL]` text markers are flagged as synthetic ground-truth test labels and excluded from predictive features.

### 3.7. Feature Engineering (`test_feature_engineering.py` - 29 Tests)
- **Calendar & Temporal Extraction**: Exact derivation of `year`, `month`, `quarter`, `day_of_month`, `day_of_week` (Monday=0), `day_name`, and `is_weekend`. Includes leap year tests (`2024-02-29`) and backward-compatible alias verification.
- **Flow Direction & Magnitude**: Validates binary directional indicators (`is_income`, `is_expense`) and log-transformation $\log_{1p}(\text{amount})$ with strict rejection of negative/zero/non-numeric amounts.
- **Temporal Sequence & Inter-Transaction Lags**: Verifies chronological elapsed days and lag amounts, isolation of expense streams, secondary sorting on `transaction_id`, and preservation of caller row ordering (`restore_order=True`).
- **Calendar Rolling Windows (`closed='left'`)**: Verifies 7-day and 30-day backward-looking rolling expense statistics strictly exclude current-day transactions to prevent future data leakage. Verifies absent history evaluates to `NaN`.
- **Same-Day Rolling Semantics & Order Invariance**: Proves every transaction on date $T$ (both Income and Expense) receives an identical baseline computed strictly from dates prior to $T$. Proves transactions later in the chronological sequence cannot influence same-day rolling statistics. Proves that shuffling same-day transaction rows produces identical rolling statistics.
- **Multi-Day Rolling Scenario Verification (`test_rolling_expense_features_multiday_scenario`)**: Proves that across multiple dates (March 1, 2, 3) with intermixed income and expenses:
  - March 1 transactions receive `NaN` (no prior history).
  - March 2 transactions (including ₹5,000 Income) receive identical rolling sum ₹3,000, mean ₹1,500, count 2.
  - March 3 transactions (including ₹8,000 Income) receive identical rolling sum ₹4,200, mean ₹1,050, count 4.
  - Income amounts never enter expense calculations.
  - Shuffling input rows does not change date-level rolling values.
  - Adding future transactions (e.g. March 4) cannot change earlier historical features.
- **Canonical Categorical Encoding**: Enforces deterministic generation of 17 category dummy columns and 5 payment method dummy columns. Validates that novel or unseen categories evaluate to all-zero vectors without errors.
- **Text Metadata & Ground-Truth Extraction**: Asserts character length and word count calculations, and validates `extract_ground_truth_labels()` correctly tags `[UNUSUAL]` descriptions for evaluation benchmarking.
- **Target Leakage Prevention & Marker Invariance**:
  - `test_marker_invariance_leakage_regression`: Builds two identical transaction datasets, alters one description with the `[UNUSUAL]` shock marker, and asserts that the resulting model feature matrices are 100% identical (`assert_frame_equal`).
  - Explicitly asserts that `get_model_feature_matrix()` strictly drops identifiers (`transaction_id`), descriptions, timestamps (`date`), raw categorical strings, description-derived features (`desc_char_length`, `desc_word_count`), and ground-truth labels, producing a 42-column purely numeric modeling matrix.
- **Pipeline Integrity & Immutability**: Asserts input DataFrame is never mutated and empty DataFrames are handled gracefully with full column schemas.

### 3.8. Financial Analytics Engine (`tests/test_financial_metrics.py`, `tests/test_spending_analysis.py`, `tests/test_budget_analysis.py`, `tests/test_trend_analysis.py` - 30 Tests)
- **Financial Metrics (`test_financial_metrics.py` - 11 Tests)**:
  - Validates aggregate income, aggregate expense, and net savings accuracy in INR.
  - Validates savings rate percentage and expense-to-income ratio.
  - Verifies ticket size metrics: average income, average expense, and median expense.
  - Validates transaction counts partitioned across total, income, and expense.
  - Verifies `compute_financial_kpis()` output dictionary completeness and formatting.
  - Validates zero-income policy (returns `NaN` when expenses exist without income; returns 0.0 when both are 0).
  - Asserts strict input validation rejecting non-DataFrames, missing columns, non-numeric amounts, infinite amounts, and negative amounts.
  - Proves input DataFrame immutability.
- **Spending Analysis (`test_spending_analysis.py` - 8 Tests)**:
  - Asserts category-level expenditure grouping strictly excludes income transactions.
  - Asserts category percentages sum to 100.0% and rows are sorted descending by expenditure.
  - Validates `get_highest_spending_category()` identification and handles empty DataFrames returning `None`.
  - Asserts `get_top_n_expense_categories()` extracts top N and validates parameter types (rejecting non-integers, 0, and negative numbers).
  - Validates payment method breakdowns with both `expense_only=True` and `expense_only=False` cash-flow modes.
  - Validates `get_income_vs_expense_breakdown()` volume and percentage calculations.
  - Validates monthly expense chronological rollups.
- **Budget Analysis (`test_budget_analysis.py` - 7 Tests)**:
  - Validates category budget variance with dictionary and DataFrame budget inputs.
  - Asserts remaining budget, variance, utilization percentage, and over-budget boolean flags.
  - Proves income transactions never reduce or contaminate expense category budgets.
  - Validates `include_unbudgeted=True` flag surfacing unbudgeted categories with `NaN` budget and nullable boolean `is_over_budget = pd.NA`.
  - Asserts that categories with actual spending and no budget are never classified as over-budget (`is_over_budget is pd.NA`).
  - Asserts categories with budget and spending above it are flagged `is_over_budget == True`.
  - Asserts categories with budget and spending below it are flagged `is_over_budget == False`.
  - Validates zero-budget category semantics (spending > 0 evaluates to `is_over_budget == True`; spending == 0 evaluates to `is_over_budget == False`).
  - Validates portfolio health summary calculations (`compute_budget_summary()`) ensuring summary counts strictly distinguish genuinely over-budget, under-budget, and unbudgeted/not-assessable categories.
  - Asserts strict validation rejecting duplicate categories, negative budgets, non-numeric budgets, and invalid input types.
- **Trend Analysis (`test_trend_analysis.py` - 6 Tests)**:
  - Validates chronological monthly aggregation of income, expense, net savings, and savings rate.
  - Deterministically validates the Transparent Savings Percentage-Change Policy across all 7 scenarios (`test_mom_savings_percentage_all_seven_scenarios`):
    1. Positive savings to higher positive savings (calculates conventional growth rate).
    2. Positive savings to lower positive savings (calculates conventional negative growth rate).
    3. Negative savings to less-negative savings (returns `NaN` to prevent misleading deficit growth rates).
    4. Negative savings to positive savings (sign flip; returns `NaN` and preserves absolute change).
    5. Positive savings to negative savings (sign flip; returns `NaN` and preserves absolute change).
    6. Zero previous-month savings (returns `NaN` for undefined baseline).
    7. Initial month with no previous month (evaluates to `NaN` for all MoM metrics).
  - Verifies continuous period range construction with `start_date` and `end_date`, inserting ₹0.0 records for zero-transaction gap months.
  - Validates high-level trend summaries (`summarize_financial_trends()`) identifying peak expense, income, and savings months.
  - Validates resampled spending trends and 4-period rolling moving averages.
  - Asserts strict validation rejecting inverted date bounds (`start_date > end_date`), missing columns, and non-numeric amounts.

### 3.9. Dashboard & Visualization Pipeline (`test_dashboard.py` - 42 Tests)
- **Data Loading & Sanitization**:
  - `test_load_dashboard_data_sample`: Confirms loading 5,000 records with all 7 core schema columns plus derived columns (`parsed_date`, `display_description`).
  - `test_load_dashboard_data_masks_unusual_marker`: Asserts raw descriptions contain `[UNUSUAL]` ground-truth shock markers while `display_description` strictly masks them to prevent leakage in user-facing views.
  - `test_load_dashboard_data_missing_file_raises`: Validates `FileNotFoundError` raised when target CSV does not exist.
- **Pure Multi-Criteria Filtering**:
  - `test_filter_transactions_pure_function`: Proves input DataFrame is never mutated during filtering (`assert_frame_equal`).
  - `test_filter_transactions_inclusive_dates`: Confirms inclusive calendar boundaries ($start \le date \le end$), including boundary dates.
  - `test_filter_transactions_exact_single_day`: Validates single-day filtering where `start_date == end_date`.
  - `test_filter_transactions_by_type`: Validates isolation of `Income` vs. `Expense` flows.
  - `test_filter_transactions_by_category`: Validates arbitrary category subset filtering.
  - `test_filter_transactions_by_payment_method`: Validates payment channel filtering.
  - `test_filter_transactions_empty_result`: Confirms empty result preservation with reset index and preserved schema.
  - `test_filter_transactions_empty_input`: Validates empty DataFrame input handled gracefully.
- **Helper Utilities**:
  - `test_get_dataset_date_bounds`: Verifies accurate extraction of minimum and maximum calendar dates, with fallback handling for empty DataFrames.
  - `test_get_available_categories`: Verifies sorted unique category extraction with optional transaction type filtering.
  - `test_get_available_payment_methods`: Verifies sorted unique payment methods extraction.
- **Plotly Visualizations Smoke & Empty Data Tests**:
  - Smoke tests asserting all 8 chart functions return valid `plotly.graph_objects.Figure` instances:
    `create_income_vs_expense_chart`, `create_monthly_trends_chart`, `create_monthly_savings_chart`,
    `create_category_spending_bar_chart`, `create_category_spending_donut_chart`, `create_payment_method_chart`,
    `create_category_avg_median_chart`, and `create_budget_vs_actual_chart`.
  - `test_chart_functions_handle_empty_data`: Asserts that passing empty DataFrames to all chart functions safely renders fallback annotations without throwing exceptions.
- **Budget Health Alert Severity Tiers**:
  - `test_get_budget_utilization_alert_tiers`: Validates status level (`INFO`, `OPTIMAL`, `WARNING`, `CRITICAL`) and guidance text across utilization percentages ($NaN$, $115.5\%$, $94.2\%$, $68.0\%$).
- **Budget Semantics Regression Suite**:
  - `test_budget_semantics_zero_budget_with_positive_spending`: Validates explicit ₹0 budget with positive spend is strictly flagged as `is_over_budget == True` and counted in `over_budget_category_count`.
  - `test_budget_semantics_zero_budget_with_zero_spending`: Validates explicit ₹0 budget with zero spend is classified as `is_over_budget == False` (0% utilization) and counted in `under_budget_category_count`.
  - `test_budget_semantics_missing_budget_with_positive_spending`: Validates absent budget with positive spend receives `pd.NA` for `is_over_budget`, is isolated from over/under counts, and is counted in `unbudgeted_category_count`.
  - `test_budget_semantics_missing_budget_with_zero_spending`: Validates absent budget with zero spend is not assessed and not classified as over budget.
  - `test_budget_semantics_summary_counts_and_chart_labels_all_cases`: Validates summary counts and Plotly chart tooltips, custom data, and color assignments (`COLOR_EXPENSE`, `COLOR_INCOME`, `COLOR_UNBUDGETED`) across all four cases.
  - `test_benchmark_presets_semantics`: Verifies benchmark presets distinguish explicit zero budgets from unbudgeted/omitted categories.
- **Calendar Month Budgeting & Period Alignment Suite**:
  - `test_get_available_budget_months`: Extracts 12 chronological calendar months, validates start/end dates and completeness flags, and confirms default points to latest complete month (October 2026).
  - `test_get_available_budget_months_empty`: Validates empty DataFrame input handled gracefully.
  - `test_filter_budget_actuals_by_month_inclusive`: Verifies boundary date inclusivity (1st and last calendar day).
  - `test_november_2025_actual_expenses_verified`: Confirms November 2025 expense transactions match exactly 391 records totaling ₹826,899.27.
  - `test_monthly_budget_comparison_isolation`: Verifies that monthly budget targets are evaluated strictly against single-month actuals (eliminates dimensional mismatch against full-year ₹9,365,016.87).
  - `test_budget_sidebar_date_filter_isolation`: Verifies `full_df` protection against narrow sidebar date ranges truncating monthly budget actuals.
  - `test_budget_empty_month_handled_gracefully`: Asserts zero actual spend (₹0.00, 0.0% utilization) and no errors for months with no expenses.
  - `test_create_budget_vs_actual_chart_with_period_label`: Verifies dynamic period labeling in the Plotly chart title.
- **App to Dashboard Integration & Runtime Regression Suite**:
  - `test_render_budgets_page_signature_accepts_full_df_and_kwargs`: Asserts that `render_budgets_page` explicitly accepts `full_df`, `categories`, `payment_methods`, and `**kwargs` with default `None`.
  - `test_app_to_render_budgets_page_call_site_integration`: Validates the exact `app.py` line 153 call site invocation (`render_budgets_page(filtered_df, full_df=raw_df, categories=..., payment_methods=...)`) under Streamlit execution without `TypeError`.
  - `test_app_main_executes_all_four_pages_without_runtime_error`: Executes `app.main()` for all 4 navigation pages (`📊 Overview`, `💳 Spending Analysis`, `🎯 Budget Analysis`, `📈 Forecasting & Anomalies`), proving clean routing and zero runtime exceptions across the entire dashboard.

### 3.10. Anomaly Detection, Insights & Forecasting Suite (`test_anomaly_detection.py`, `test_insights.py`, `test_forecasting.py` - 35 Tests)
- **Anomaly Detection Module (`test_anomaly_detection.py` - 15 Tests)**:
  - `test_detect_outliers_statistical_iqr`: Asserts Tukey's IQR rule flags upper-tail shocks on transaction amounts.
  - `test_detect_outliers_statistical_zscore`: Asserts standard Z-score rule flags 3-sigma spikes.
  - `test_detect_outliers_statistical_empty_and_edge_cases`: Validates handling of empty series and zero-variance series.
  - `test_detect_outliers_statistical_invalid_method`: Asserts `ValueError` on unsupported method strings.
  - `test_detect_anomalies_isolation_forest_execution`: Validates clean execution, output types, and contamination scaling.
  - `test_detect_anomalies_isolation_forest_reproducibility`: Proves deterministic outputs under identical random seed.
  - `test_detect_anomalies_isolation_forest_marker_invariance`: Proves target leakage prevention: presence or absence of `[UNUSUAL]` in descriptions does not alter modeling features or anomaly scores (`assert_series_equal`).
  - `test_detect_anomalies_empty_dataframe`: Confirms empty DataFrame handling.
  - `test_get_anomaly_records_masks_unusual_marker`: Asserts extracted records cleanly mask `[UNUSUAL]` in `display_description`.
  - `test_get_anomaly_records_empty`: Confirms schema preservation on empty inputs.
  - `test_evaluate_anomaly_detection_metrics`: Validates precision, recall, f1_score, and confusion matrix calculation.
  - `test_evaluate_anomaly_detection_empty_input`: Validates zero-division handling on empty evaluations.
  - `test_evaluate_anomaly_detection_out_of_sample`: Verifies chronological inductive holdout evaluation (80% train / 20% test).
  - `test_anomaly_feature_matrix_leakage_safeguard`: Proves that evaluation labels, raw descriptions, IDs, and text length proxies are absent from `get_model_feature_matrix`.
  - `test_zscore_univariate_vs_isolation_forest_multivariate_rationale`: Confirms 100% Z-score recall on synthetic amount shocks while documenting Isolation Forest's 42-dimensional geometry false-positive dynamics.
- **Financial Insights Engine (`test_insights.py` - 7 Tests)**:
  - `test_generate_financial_insights_surplus`: Asserts generation of optimal cash flow insight for surplus portfolios.
  - `test_generate_financial_insights_deficit`: Asserts critical cash flow alert for deficit portfolios.
  - `test_generate_financial_insights_zero_income`: Validates explicit warning and undefined savings rate handling when income is zero.
  - `test_generate_financial_insights_budget_overruns`: Asserts detection of category budget overruns and unbudgeted expenditures.
  - `test_generate_financial_insights_empty_dataframe`: Asserts fallback general insight for empty filtered datasets.
  - `test_financial_insight_dataclass_conversion`: Validates dictionary serialization of `FinancialInsight`.
  - `test_generate_financial_insights_threshold_configurability`: Proves analytical thresholds (category concentration, payment channels, MoM acceleration) are configurable heuristics.
- **Expense Forecasting Engine (`test_forecasting.py` - 13 Tests)**:
  - `test_prepare_expense_time_series`: Asserts continuous chronological daily aggregation and zero-filling of non-expense days.
  - `test_assess_data_sufficiency`: Confirms sufficiency assessment flags 12 monthly points as insufficient and 365 daily points as sufficient.
  - `test_check_stationarity`: Validates Augmented Dickey-Fuller stationarity test execution.
  - `test_check_stationarity_overdifferencing_diagnostic`: Asserts over-differencing diagnostics (first differencing doubles variance) and correct unit-root null hypothesis interpretation.
  - `test_split_time_series_chronological`: Proves strictly chronological train/test separation with zero future-data leakage.
  - `test_forecast_baseline`: Asserts execution and accuracy of 7-day rolling mean, naive, and historical mean baselines.
  - `test_forecast_expenses_arima`: Validates experimental ARIMA forward projections, confidence bounds, and presentation clipping.
  - `test_forecast_expenses_rolling_mean_selected_model`: Validates selected 7-day rolling mean forward projections, interval ordering, non-negative clipping, and edge cases.
  - `test_selected_model_beats_arima_on_holdout`: Asserts empirically that the selected 7-day rolling mean baseline achieves lower out-of-sample MAE than ARIMA(1, 1, 1).
  - `test_evaluate_forecast_metrics`: Validates MAE, RMSE, and MAPE calculations with safe zero-actual division handling.
  - `test_mape_and_rmse_symmetry_and_holdout_consistency`: Asserts safe MAPE zero handling (NaN on all-zero actuals), proves RMSE error symmetry in both over- and under-prediction directions, and checks canonical holdout metrics consistency (Roll7: MAE 9179.72, RMSE 15908.52, MAPE 57.79%; Naive: MAE 8615.66, RMSE 16129.58, MAPE 47.50%; ARIMA: MAE 10881.64, RMSE 16554.07, MAPE 77.23%; HistMean: MAE 11308.29, RMSE 16781.57, MAPE 81.12%).
  - `test_create_forecast_chart_selected_and_experimental_labels`: Smoke tests Plotly forecast chart with clear Selected Model vs. Experimental Model trace labeling.
  - `test_evaluate_model_selection_walk_forward`: Validates 28-fold walk-forward cross-validation on training data, asserting RMSE as primary criterion and training-fold superiority of rolling mean over naive baseline.

---

## 4. Running Tests

Execute the full test suite using the project-local `.venv`:

```powershell
# Windows PowerShell
.\.venv\Scripts\pytest.exe tests/ -v
```

```bash
# Unix / Linux / macOS
.venv/bin/pytest tests/ -v
```

---

## 5. Continuous Integration (CI)
GitHub Actions workflow is located at `.github/workflows/tests.yml`. It runs automatically on pull requests and pushes to `main` / `master` using Python 3.11.
