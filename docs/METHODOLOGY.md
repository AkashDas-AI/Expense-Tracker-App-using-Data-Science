# Data Science & Analytical Methodology

**Author: Akash Das**  
**Project**: Expense Tracker App using Data Science  
**Phase**: Phase 2 — Synthetic Data Generation & Schema Validation  

---

## 1. End-to-End Data Pipeline Lifecycle

```mermaid
flowchart LR
    Generation[Synthetic Generator] --> CSV[(Sample CSV)]
    CSV --> Validation[Schema Validator]
    Validation --> Database[SQLite Storage]
    Database --> FeatureEng[Feature Engineering]
    FeatureEng --> Modeling[Forecasting & Anomalies]
    Modeling --> Dashboard[Streamlit Dashboard]
```

---

## 2. Synthetic Data Generation Methodology

### 2.1. Objectives & Parameters
To ensure full reproducibility without exposing private financial records, the project uses a synthetic transaction generator (`src/expense_tracker/data/data_generator.py`).

- **Total Records**: 5,000 transactions
- **Time Horizon**: 12 months (2025-11-01 to 2026-10-31)
- **Base Currency**: Indian Rupee (INR / ₹)
- **Random Seed**: `42` (using `np.random.default_rng(42)`)
- **Target Persona**: Urban salaried technology/consulting professional in India with supplementary freelance and investment income.

### 2.2. Algorithmic Composition & Logic

1. **Monthly Recurring Income (Deterministic Frequency)**:
   - Salary credited on or around the 1st of each month (12 transactions total).
   - Base amount modeled via Gaussian distribution: $\mathcal{N}(\mu=85000, \sigma=3500)$ bounded above ₹70,000.
   - Payment method: Bank Transfer.

2. **Monthly Recurring Fixed Expenses**:
   - **Rent**: Paid during the 1st–5th of each month (12 transactions). $\mathcal{N}(\mu=25000, \sigma=1000)$ bounded above ₹22,000. Payment: Bank Transfer (70%) or UPI (30%).
   - **Subscriptions**: 2 to 3 subscription renewals per month (28 transactions total) with standard price points: Netflix (₹649), Spotify (₹179), Amazon Prime (₹1,499), YouTube Premium (₹189), iCloud (₹219), Gym (₹1,500–₹3,000).

3. **Deliberate Outlier / Anomaly Injection**:
   - 12 rare, high-magnitude transactions (~0.24% of the total dataset) are injected across the timeline.
   - Identified in generation metadata with a prefix: `[UNUSUAL]`.
   - Examples: MacBook purchase (₹135,000–₹165,000), Emergency hospitalization (₹85,000–₹115,000), Luxury international vacation booking (₹95,000–₹140,000).
   - Purpose: Serves as reproducible ground-truth test cases for the Phase 6 Anomaly Detection engine.

4. **Variable Discretionary & Non-Discretionary Transactions**:
   - The remaining ~4,948 transactions are distributed across the 12-month timeline.
   - **Supplementary Income** (~6% of variable records): Freelance projects (₹12k–₹45k), business revenue (₹8k–₹35k), dividends (₹2.5k–₹15k).
   - **Variable Expenses** (~94% of variable records):
     - **Groceries & Dining**: Modeled with right-skewed lognormal distributions ($\mu=6.5, \sigma=0.6$ and $\mu=6.2, \sigma=0.7$) reflecting frequent small-to-moderate orders with occasional bulk shopping.
     - **Transport & Utilities**: Daily/weekly mobility (Uber, Metro, Fuel) and monthly power/gas/broadband utility bills.
     - **Shopping, Travel & Entertainment**: Discretionary expenditures reflecting urban lifestyle spending patterns.

### 2.3. Statistical Distribution Highlights (5,000 Records)
- **Total Expenditure**: ₹9,365,016.87 (4,697 transactions, median ₹1,021.31)
- **Total Income**: ₹6,757,596.88 (303 transactions, median ₹19,573.47)
- **Payment Split**: UPI (52.1%), Credit Card (27.1%), Cash (8.1%), Debit Card (6.4%), Bank Transfer (6.4%).

### 2.4. Limitations of Synthetic Data
- **Illustrative Model**: This dataset is generated algorithmically for educational, analytical, and machine learning demonstration purposes. It does not represent actual bank statements or real individual consumer records.
- **Seasonality Approximations**: While monthly salary/rent cycles and festival discretionary spikes are captured, sudden macroeconomic shocks (e.g. inflation, policy shifts) are not simulated.

---

## 3. Schema Validation & Integrity Assurance

Implemented in `src/expense_tracker/data/validation.py`, the validator verifies 11 distinct constraints before data can enter downstream stages:
1. `DataFrame` type check.
2. Non-empty check.
3. Required column presence (`transaction_id`, `date`, `type`, `category`, `amount`, `payment_method`, `description`).
4. Complete absence of null/NaN values across mandatory fields.
5. Absolute uniqueness and non-blank formatting of `transaction_id`.
6. Date format and validity verification.
7. Allowed `type` enum check (`Income`, `Expense`).
8. Category-to-Type relationship enforcement (cross-type contamination checks).
9. Allowed `payment_method` enum verification.
10. Strict numeric, finite, positive (`> 0.0`) amount verification.
11. Non-blank string verification for `description`.

---

## 4. Ingestion, Cleaning & Storage Pipeline (Phase 3)

### 4.1. CSV Ingestion Architecture (`data_loader.py`)
- **Safe Parsing**: Explicit type enforcement preventing unwanted downcasting.
- **Fail-Fast Error Handling**: Detects missing files, zero-byte empty files, unreadable files, corrupt delimiters, and missing schema headers.
- **Preservation Policy**: Zero data filtering at load time; all records are preserved for cleaning and validation.

### 4.2. Non-Destructive Cleaning Rules (`data_cleaning.py`)
- **Input Isolation**: Deep-copies incoming DataFrames to prevent caller-side side effects.
- **Whitespace Sanitization**: Trims leading and trailing whitespace across all string attributes.
- **Text Standardization**: Case-insensitively aligns `type`, `category`, and `payment_method` to canonical project taxonomy.
- **Explicit Date Parsing**: Deterministically parses three supported formats without heuristic guessing:
  - `YYYY-MM-DD` (ISO 8601)
  - `YYYY/MM/DD` (Slash ISO)
  - `DD-MM-YYYY` (Indian financial standard, e.g. `01-02-2026` -> 1 February 2026)
  - Out-of-range dates (`2026-02-31`), nulls, and unsupported formats (e.g. `MM/DD/YYYY`, text dates) are strictly rejected (`None`) and flagged.
- **Numeric Normalization**: Strips currency prefixes (`₹`, `$`) and thousands commas (`,`), converting amounts to 2-decimal floats.
- **Invalid Record Policy**: Invalid records are flagged and reported with row indices and specific constraint reasons; records are **never silently dropped**.

### 4.3. SQLite Persistence & Idempotency (`database/`)
- **Engine**: Local SQLite database located by default at `data/processed/expenses.db`.
- **Database Engine Constraints**: The SQLite table DDL enforces:
  - Valid transaction types: `CHECK(type IN ('Income', 'Expense'))`.
  - Positive amounts: `CHECK(amount > 0)`.
  - Valid payment methods: `CHECK(payment_method IN ('UPI', 'Cash', 'Debit Card', 'Credit Card', 'Bank Transfer'))`.
  - Composite Category-to-Type consistency:
    - Income categories strictly restricted to: Salary, Freelance, Business Income, Investment Income, Other Income.
    - Expense categories strictly restricted to: Rent, Groceries, Utilities, Transport, Healthcare, Education, Shopping, Entertainment, Dining, Travel, Subscriptions, Other Expenses.
- **Atomic Transactions**: All bulk inserts occur within transactional context blocks; any unhandled error triggers an immediate, full rollback.
- **Duplicate Prevention Policy**: On bulk insert, existing `transaction_id` entries in SQLite are detected and safely skipped (`on_conflict="skip"`). Re-ingesting a CSV file is fully idempotent and creates zero duplicate rows.

### 4.4. How to Execute the Pipeline
```python
from expense_tracker.data.data_loader import ingest_transaction_file

stats = ingest_transaction_file(
    file_path="data/sample/transactions.csv",
    db_path="data/processed/expenses.db",
    on_conflict="skip",
)
print(stats)
```

---

## 5. Exploratory Data Analysis Methodology (Phase 4)

### 5.1. EDA Architecture & Notebook
The exploratory analysis is executed in [`notebooks/01_exploratory_data_analysis.ipynb`](../notebooks/01_exploratory_data_analysis.ipynb) covering 13 structured sections from data quality to outlier exploration.

### 5.2. Core Analytical Findings
1. **Transaction Volume vs Frequency Asymmetry**:
   - `Expense`: 4,697 transactions (93.94% count) totaling ₹9,365,016.87 (58.09% volume).
   - `Income`: 303 transactions (6.06% count) totaling ₹6,757,596.88 (41.91% volume).
   - Demonstrates that transaction frequency cannot be equated with monetary impact.
2. **Heavy-Tailed Expense Distribution**:
   - Expense amounts follow a log-normal shape: Median = ₹1,021.31, Mean = ₹1,993.83, Max = ₹161,884.82.
   - Requires $\log_{1p}$ transformation during feature engineering to stabilize variance.
3. **Category Concentration**:
   - Top expenditure categories: `Shopping` (₹18.27 Lakhs) and `Travel` (₹14.65 Lakhs).
   - Top frequency categories: `Groceries` (1,412 transactions) and `Transport` (879 transactions).
4. **Channel Dynamics**:
   - `UPI` accounts for 52.1% of transactions (predominantly micro-expenses).
   - `Bank Transfer` commands 41.1% of monetary volume (payroll credits, freelance invoices, monthly rent).
5. **Outlier Characterization**:
   - **Statistical Upper Bound**: $Q_3 + 1.5 \times IQR = ₹3,957.50$ flags 354 statistical outliers (7.54% of expenses).
   - **Deliberate Shocks**: Exactly 12 injected shock transactions (`[UNUSUAL]`), ranging from ₹65,935.31 to ₹161,884.82, all exceed the IQR fence.
   - **Target Leakage Precaution**: The `[UNUSUAL]` text description prefix must be strictly excluded from downstream feature matrices to prevent artificial label leakage.

### 5.3. Synthetic Data Limitations
- **12-Month Horizon**: Cannot confirm multi-year macroeconomic seasonality or structural trends.
- **Controlled Generation Rules**: Fixed monthly salary (~₹84k) and rent (~₹25k) reflect synthetic simulation rules rather than dynamic consumer adjustments.

---

## 6. Feature Engineering Methodology (Phase 5)

Phase 5 implements deterministic, reusable analytical feature engineering across financial transactions, transforming cleaned records into predictive feature representations while establishing mathematical safeguards against data and target leakage.

### 6.1. Architectural Principles
1. **Zero Caller Mutation**: All feature transformation functions deep-copy input DataFrames; caller DataFrames are guaranteed immutable.
2. **Deterministic Reproducibility**: Transactions with identical calendar dates are deterministically sequenced using secondary sorting on `transaction_id`.
3. **Restoration of Original Sequence**: The orchestrator (`engineer_features`) preserves caller row indexing and restores original row order (`restore_order=True`).
4. **Canonical Categorical Consistency**: Categorical dummies are generated against fixed canonical taxonomies (17 categories, 5 payment methods), guaranteeing consistent matrix dimensions across different train/test splits.

### 6.2. Mathematical Formulations & Feature Groups

#### 1. Log Amount Transformation
As identified during Phase 4 EDA, transaction amounts exhibit extreme positive skewness (expenses: max ₹161,884.82 vs median ₹1,021.31). The variance is stabilized using natural logarithm plus one:
$$\text{log\_amount} = \ln(1 + \text{amount})$$

#### 2. Temporal Lag Features
Elapsed calendar time and magnitude of previous events are derived sequentially:
$$\Delta t_{\text{txn}} = \frac{t_i - t_{i-1}}{86400 \text{ seconds}}$$
$$\Delta t_{\text{expense}} = \frac{t_i - t_{i-1}^{(\text{expense})}}{86400 \text{ seconds}}$$
Income transactions do not evaluate expense lags; they produce explicit `NaN` values to prevent cross-stream contamination.

#### 3. Calendar Rolling Windows (Strictly Past-Looking with Same-Day Isolation)
Rolling statistics over 7-day and 30-day horizons are computed exclusively on preceding calendar events using `closed='left'`:
$$\text{Window}(T_i, W) = [T_i - W, T_i)$$
$$\text{rolling\_expense\_sum}_{W}(T_i) = \sum_{t_j \in [T_i - W, T_i)} \text{amount}_j^{(\text{expense})}$$
$$\text{rolling\_expense\_mean}_{W}(T_i) = \frac{1}{|\text{Window}(T_i, W)|} \sum_{t_j \in [T_i - W, T_i)} \text{amount}_j^{(\text{expense})}$$

##### Same-Day Rolling Semantics:
- **Exclusion of Same Date**: Because the time-offset interval $[T_i - W, T_i)$ is strictly open on the right ($t_j < T_i$), every transaction occurring on date $T_i$ receives a baseline computed solely from calendar dates strictly prior to $T_i$.
- **Intra-Day Invariance & Universal Attachment**: Transactions occurring earlier or later on date $T_i$ cannot influence another transaction's historical baseline for that date. All transactions occurring on date $T_i$ (both Income and Expense) receive identical historical rolling statistics.
- **Expense Stream Isolation**: Inflows (`type == 'Income'`) are strictly partitioned and never enter the expense aggregation series. Income amounts never contribute to expense rolling sums, means, or counts.

##### Missing Historical Information vs. Genuine Zero Spend:
- **Lookback Window Boundary (9 Missing Values)**:
  - For the 9 transactions occurring on the first calendar date of the dataset ($T_0 = \text{2025-11-01}$: 2 Income + 7 Expenses), the preceding window $[T_0 - W, T_0)$ contains zero observations because no prior data exists in the timeline.
  - Rather than arbitrarily coercing this absent history to ₹0 (which would distort variance and mislead models into assuming zero expenditures occurred), rolling `sum`, `mean`, and `count` evaluate to `NaN` under the documented empty-window policy.
  - All subsequent 4,991 transactions (from 2025-11-02 through 2026-10-31) have complete, non-NaN rolling expense baselines.

### 6.3. Target Leakage Prevention & Ground-Truth Quarantining
- **Synthetic Shock Marker**: In the synthetic sample dataset, deliberate shock transactions carry the `[UNUSUAL]` prefix in their `description`.
- **Description-Derived Feature Leakage**: While `desc_char_length` and `desc_word_count` are derived for exploratory analysis, they are **strictly excluded from model training inputs**. The presence of `[UNUSUAL]` directly increases string length by +9 characters and word count by +1 word, creating an artificial proxy leakage for anomaly detection algorithms.
- **Marker Invariance Property**: Model feature matrices generated by `get_model_feature_matrix()` are guaranteed mathematically invariant to the presence or absence of the `[UNUSUAL]` description marker.
- **Quarantined Evaluation Label**: `extract_ground_truth_labels()` extracts this marker into a binary evaluation series (`is_unusual_ground_truth`). This label is strictly quarantined for benchmarking Phase 6 anomaly detection algorithms.
- **Modeling Feature Matrix**: `get_model_feature_matrix()` strips `transaction_id`, `description`, `desc_char_length`, `desc_word_count`, `date`, `category`, `payment_method`, `type`, `month_name`, `day_name`, and any ground truth columns, returning **42 purely numeric features** (or 20 without categorical dummies).

---

## 7. Financial Analysis & KPI Methodology (Phase 6)

### 7.1. Core Financial Indicators & Formulations

Financial health indicators are computed in Indian Rupees (₹ / INR) using modular, vectorised Pandas operations:

1. **Total Income & Total Expenses**:
   $$\text{Total Income} = \sum_{i \in \text{Income}} \text{amount}_i$$
   $$\text{Total Expenses} = \sum_{j \in \text{Expense}} \text{amount}_j$$

2. **Net Savings**:
   $$\text{Net Savings} = \text{Total Income} - \text{Total Expenses}$$
   A positive value represents net capital accumulation; a negative value indicates a net deficit.

3. **Savings Rate Percentage**:
   $$\text{Savings Rate (\%)} = \left(\frac{\text{Net Savings}}{\text{Total Income}}\right) \times 100.0$$
   *Zero-Income Policy*: When total income is ₹0.0:
   - If total expenses are also ₹0.0 (zero activity), the rate evaluates to `0.0%`.
   - If expenses exist without income, the rate is mathematically undefined and returns `NaN` (or an explicit configurable default).

4. **Expense-to-Income Ratio**:
   $$\text{Expense-to-Income Ratio} = \frac{\text{Total Expenses}}{\text{Total Income}}$$
   Measures cash flow coverage; values $< 1.0$ indicate living within cash inflows.

5. **Ticket Size Statistics**:
   - Mean Income: $\mu_{\text{income}} = \frac{1}{N_{\text{inc}}} \sum_{i \in \text{Income}} \text{amount}_i$
   - Mean Expense: $\mu_{\text{expense}} = \frac{1}{N_{\text{exp}}} \sum_{j \in \text{Expense}} \text{amount}_j$
   - Median Expense: $\text{Med}(\{\text{amount}_j \mid j \in \text{Expense}\})$ (robust against positive transaction skewness).

### 7.2. Spending Breakdown & Top-N Analysis

1. **Income Exclusion**:
   Spending aggregations (`get_spending_by_category()`, `get_top_n_expense_categories()`) strictly filter `type == 'Expense'`. Income records are partitioned completely and never reduce or offset category expenditures.

2. **Category Percentage Share**:
   $$\text{Percentage}_c = \left(\frac{\text{Total Spend}_c}{\text{Total Expenses}}\right) \times 100.0$$
   Category totals are sorted descending by expenditure to prioritize key cash outflows.

3. **Payment Method Analysis**:
   Aggregates transaction count, total volume, and average ticket size across `UPI`, `Credit Card`, `Bank Transfer`, `Debit Card`, and `Cash`. Supports both expense-only filtering and total cash-flow volume mode.

### 7.3. Budget Variance & Portfolio Health

1. **Calendar Month Budgeting & Period Alignment Contract (Phase 8 Architecture)**:
   - **Monthly Baseline Granularity**: Category budget targets (including the benchmark presets) are calibrated as single-month expenditure limits.
   - **Elimination of Multi-Month Dimensional Mismatch**: Comparing a monthly budget target (e.g. ₹84,500) against an entire year of transactions (₹9,365,016.87 across 12 months) causes artificial portfolio overruns ($>11,000\%$ utilization). The Budget Analysis dashboard strictly enforces **Calendar Month Budgeting**:
     - A dedicated calendar-month selector isolates transaction actuals to a single, complete calendar month (from the 1st of the month to the last calendar day inclusive).
     - The selector automatically identifies complete calendar months and defaults to the latest complete calendar month in the dataset (October 2026). If an incomplete month is selected, a clear user disclosure highlights the partial-month limitation.
     - **Global Date Filter Isolation**: The global sidebar date range filter does not truncate or prorate monthly budget targets. The dashboard utilizes the full dataset as the source for budget evaluation, strictly bounding actual expenditures by the selected calendar month's start and end dates while continuing to respect category and payment channel filters.
     - Metric cards, chart titles, and ledger tables dynamically display the evaluated calendar month (e.g., `Total Planned Budget (October 2026)`, `Total Actual Spend (October 2026)`).

2. **Category Budget Formulations**:
   - $\text{Remaining Budget}_c = \text{Budget}_c - \text{Actual Spend}_c$
   - $\text{Budget Variance}_c = \text{Actual Spend}_c - \text{Budget}_c$ (positive values indicate overage).
   - $\text{Utilization Rate}_c = \left(\frac{\text{Actual Spend}_c}{\text{Budget}_c}\right) \times 100.0$ (evaluates to $0.0\%$ if budget and actual are ₹0; `NaN` if budget is ₹0 with actual $> 0$).
   - $\text{Over Budget Flag}_c = (\text{Actual Spend}_c > \text{Budget}_c)$ for categories with an active budget allocation. Explicit ₹0.00 budget allocation flags any positive spend as Over Budget and zero spend as Within Budget ($0.0\%$ utilization).

3. **Unbudgeted Category Status Policy (`include_unbudgeted=True`)**:
   When transactions occur in categories with no allocated budget:
   - The application does not fabricate arbitrary budget baselines.
   - An unbudgeted category is **not classified as over budget**. Its over-budget status is represented as unknown / not-assessable via a nullable Boolean (`pd.NA`).
   - The category remains visible with: `budget_amount = NaN`, `remaining_budget = NaN`, `budget_variance = NaN`, `utilization_pct = NaN`, and `is_over_budget = pd.NA`.

4. **Portfolio Budget Health Summary & Count Distinction**:
   Summary metrics strictly distinguish between budgeted evaluations and unbudgeted expenditures:
   - `total_budget`: Sum of all non-null category budget allocations.
   - `budgeted_actual_spend`: Expenditure strictly within budgeted categories.
   - `unbudgeted_actual_spend`: Expenditure occurring in unbudgeted categories.
   - `total_actual_spend`: Overall expenditure across all visible categories.
   - `over_budget_category_count`: Number of categories where $\text{Actual} > \text{Budget}$ (`is_over_budget == True`). Strictly excludes unbudgeted categories.
   - `under_budget_category_count`: Number of categories where $\text{Actual} \le \text{Budget}$ (`is_over_budget == False`). Strictly excludes unbudgeted categories.
   - `unbudgeted_category_count`: Number of unbudgeted / not-assessable categories (`is_over_budget is pd.NA`).

### 7.4. Historical Trend & Month-over-Month (MoM) Growth Analysis

1. **Continuous Period Construction**:
   Transactions are aggregated chronologically by calendar month ($YYYY\text{-}MM$). When date bounds $[T_{\text{start}}, T_{\text{end}}]$ are specified, continuous monthly periods are generated so months with zero transactions appear with ₹0.0 rather than distorting sequential trend analysis.

2. **Income and Expense MoM Percentage Growth**:
   - $\Delta \text{Metric}_t = \text{Metric}_t - \text{Metric}_{t-1}$
   - $\text{MoM Growth (\%)}_t = \left(\frac{\text{Metric}_t - \text{Metric}_{t-1}}{\text{Metric}_{t-1}}\right) \times 100.0$ for strictly positive baselines ($\text{Metric}_{t-1} > 0$).
   - *Baseline Zero Handling*: If $\text{Metric}_{t-1} = 0$:
     - If $\text{Metric}_t = 0$, growth evaluates to `0.0%`.
     - If $\text{Metric}_t \neq 0$, division by zero is avoided by returning `NaN`.
   - The initial month in any historical series receives `NaN` for all MoM metrics due to absent preceding baselines.

3. **Transparent Savings Percentage-Change Policy**:
   Net savings ($S_t = I_t - E_t$) can be positive (surplus), zero (balanced), or negative (deficit). Standard percentage change formulas like $(S_t - S_{t-1}) / |S_{t-1}|$ produce economically misleading growth percentages when baselines are negative or when crossing the zero boundary. The application enforces a transparent, rigorous policy:
   - **Absolute Change Preservation**: $\Delta S_t = S_t - S_{t-1}$ is always computed and preserved across all sign boundaries.
   - **Zero Baseline**: When previous month's savings are zero ($S_{t-1} = 0$), percentage growth evaluates to `NaN`.
   - **Negative Baseline**: When previous month's savings are negative ($S_{t-1} < 0$), percentage growth evaluates to `NaN` rather than presenting an artificial percentage rate on a deficit.
   - **Sign Inversion**: When savings transition across sign boundaries ($S_{t-1} > 0 \to S_t < 0$ or $S_{t-1} < 0 \to S_t > 0$), the absolute difference is retained and percentage growth evaluates to `NaN`.
   - **Positive Baseline**: When previous savings are strictly positive and current savings are non-negative ($S_{t-1} > 0$ and $S_t \ge 0$), conventional percentage growth is calculated:
     $$\text{MoM Savings (\%)}_t = \left(\frac{S_t - S_{t-1}}{S_{t-1}}\right) \times 100.0$$

### 7.5. Disclaimer on Synthetic Data Interpretation
All aggregate KPIs, net savings figures, and category percentages computed on [`data/sample/transactions.csv`](file:///D:/Projects/Data%20Science/Expense%20Tracker%20App/data/sample/transactions.csv) reflect the synthetic generation seed and parameter distributions (e.g. simulated one-off high magnitude shock purchases). They are designed for data engineering and analytical demonstration, not to model actual household solvency.

---

## 8. Data Science & Machine Learning Methodologies (Phase 8 Implemented & Audited)

### 8.1. Automated Financial Insight Generation
The insight engine (`src/expense_tracker/analytics/insights.py`) synthesizes empirical findings across portfolio KPIs, category distributions, monthly trajectories, and budget variance:
1. **Evidence-Based Observations**: Derived strictly from calculated figures without invented numbers or thresholds.
2. **Actionable Recommendations**: Standard financial hygiene suggestions paired with each observation to guide budgeting decisions. Avoids presenting recommendations as causal conclusions (e.g. suggests reviewing discretionary allocations rather than asserting that a specific spend caused a net deficit).
3. **Configurable Analytical Heuristics**:
   - **Significant Category Share (default: 15.0%)**: Identifies dominant outflow categories.  
     *Limitation*: In households with structural contractual commitments (e.g., rent or tuition), a single category may legitimately exceed 30–40% without reflecting financial mismanagement.
   - **Dominant Payment Channel (default: 35.0%)**: Monitors operational payment reliance (e.g., UPI vs. credit cards).  
     *Limitation*: Captures consumer convenience and ecosystem acceptance rather than solvency or credit risk.
   - **Month-over-Month Spending Acceleration (default: 20.0%)**: Flags rapid expenditure surges relative to the previous month.  
     *Limitation*: Swings frequently reflect expected calendar seasonality (e.g., annual insurance premiums, festival gifts, travel) rather than discretionary overspending.
   - **High-Value Spending Spike**: Transaction amount exceeding Tukey's upper fence: $Q_3 + 1.5 \times \text{IQR}$.
   - **Budget Overrun**: Actual spend exceeding allocated budget amount.
4. **Edge-Case Resilience**: Explicit handling for missing data, zero income (savings rate undefined), and negative savings.

### 8.2. Anomaly Detection Architecture & Evaluation Audit
The anomaly detection engine (`src/expense_tracker/models/anomaly_detection.py`) pairs intuitive univariate statistical benchmarks with unsupervised multivariate machine learning:
1. **Statistical Baselines**:
   - **Tukey's IQR Fence**: $\text{Amount} > Q_3 + 1.5 \times (Q_3 - Q_1)$.
   - **Standardized Z-Score**: $Z = \frac{\text{Amount} - \mu}{\sigma} > 3.0$.
2. **Multivariate Isolation Forest**:
   - **Model Class**: `sklearn.ensemble.IsolationForest(contamination=0.02, random_state=42)`.
   - **Feature Space**: 42 numeric features derived via `get_model_feature_matrix()` (amount scale, calendar cycles, lag intervals, rolling statistics, category dummies, and payment dummies).
   - **Target Leakage Safeguard**: Strict quarantine of `transaction_id`, descriptions, text length proxies (`desc_char_length`, `desc_word_count`), and ground-truth evaluation markers (`[UNUSUAL]`). Proved invariant via automated regression tests.
   - **A Priori Parameter Selection**: The contamination rate parameter (default 0.02) was set a priori as an operational domain heuristic (~2% expected outliers) and was not tuned on the 12 evaluation labels.
   - **Preprocessing**: Imputation of initial lookback warmup NaNs with `0.0` (reflecting zero prior spend history).
3. **Evaluation Framework (Transductive & Out-of-Sample Hold-Out)**:
   - **Sample-Size Disclosure & Transductive Audit (Full 5,000 Records)**:
     - Ground-Truth Positives ($N_{\text{pos}}$): $12$ out of $5,000$ transactions ($0.24\%$).
     - Precision: $2.00\%$, Recall: $16.67\%$, F1-Score: $3.57\%$, Confusion Matrix: $TP=2, FP=98, TN=4890, FN=10$.
   - **Inductive Out-of-Sample Hold-Out (`evaluate_anomaly_detection_out_of_sample`)**:
     - Chronological 80/20 train/test split. Fits Isolation Forest strictly on 4,000 training records; evaluates on 1,000 unseen test records.
     - Test Ground-Truth Positives ($N_{\text{pos}}$): **Exactly 1 positive anomaly** out of 1,000 test transactions ($0.10\%$).
     - **100% Test Recall Representation**: The reported 100% recall represents detecting **one out of one** positive test example ($TP=1, FN=0, FP=30, TN=969$). Test Precision evaluates to $3.23\%$ ($1 / 31$), and F1 evaluates to $6.25\%$.
     - **Extreme Sample-Size Uncertainty Disclosure**: With only a single positive example ($N_{\text{pos}} = 1$), performance estimates carry extreme statistical uncertainty. If the single anomaly had been missed, test recall would drop from 100% to 0%.
     - **Real-World Efficacy Limitation**: This benchmark demonstrates algorithm execution on synthetic data and should **not** be construed as evidence of reliable real-world fraud or crime detection capabilities.
4. **Multivariate Geometry vs. Univariate Benchmark Rationale**:
   - The 12 evaluation anomalies were generated as pure univariate monetary shocks in `amount` (₹65,000–₹162,000). A simple Z-score rule on amount flags them with 100% precision and recall because of this single-variable synthetic generation method.
   - In contrast, Isolation Forest constructs recursive orthogonal partitions across all 42 feature dimensions simultaneously. It isolates transactions that are unusual across multi-attribute combinations (e.g. rare payment methods on atypical days with zero prior history).
   - Evaluated strictly against single-variable monetary shocks, these multidimensional outliers appear as 'false positives'. Weak precision (~2–3%) is the mathematically expected outcome of benchmarking a 42-dimensional geometry partitioner against a 1-dimensional benchmark.
   - *Disclaimer*: Z-score's 100% recall is an artifact of the synthetic benchmark and does not establish general superiority in real-world fraud detection where fraudulent transactions mimic typical amounts. Results are reported honestly without artificial tuning.

### 8.3. Time-Series Expenditure Forecasting & Model Selection Audit
The forecasting engine (`src/expense_tracker/models/forecasting.py`) implements statistical expenditure projection using Statsmodels:
1. **Data Sufficiency & Frequency Selection**:
   - *Limitation of Monthly Data*: A 12-month sample dataset yields only 12 points, which is mathematically insufficient for seasonal SARIMAX ($s=12$ requires at least 24–36 observations).
   - *Daily Resolution*: Resampling at daily frequency (`D`) yields 365 observations with zero-fill for missing gap intervals, providing sufficient sample size for chronological validation.
2. **Stationarity Diagnostics & Over-Differencing Review (ADF Test)**:
   - Evaluates unit-root presence using Augmented Dickey-Fuller test ($\alpha = 0.05$).
   - On the 365-day sample dataset, the test yields $\text{ADF} = -20.76$ ($p < 0.001$), rejecting the unit-root null hypothesis (H0).
   - *Statistical Nuance*: Rejection of H0 is evidence against a stochastic unit root, NOT absolute proof of strict covariance stationarity (heteroskedasticity or structural breaks may exist).
   - *Over-Differencing Diagnostic*: First differencing doubles series variance ($\text{Var}(\Delta y) = 1.20 \times 10^9$ vs. $\text{Var}(y) = 5.51 \times 10^8$, variance ratio: $2.18\times$). Taking first differences introduces artificial volatility and an artificial moving-average unit root, explaining why ARIMA(1, 1, 1) underperformed the stationary baseline.
3. **Chronological Hold-Out Model Selection & Metric Rationale**:
   - Partitions time series strictly chronologically (first 80% train = 292 days, final 20% test = 73 days) with zero lookahead leakage.
   - **Chronological Hold-Out Evaluation Metrics (Exact Calculated Values)**:
     - **7-Day Rolling Mean Baseline (SELECTED MODEL)**: $\text{RMSE} = ₹15,908.52$ [Lowest RMSE], $\text{MAE} = ₹9,179.72$, $\text{MAPE} = 57.79\%$.
     - **Naive Baseline (Last Value)**: $\text{RMSE} = ₹16,129.58$, $\text{MAE} = ₹8,615.66$ [Lowest MAE & MAPE], $\text{MAPE} = 47.50\%$.
     - **ARIMA(1, 1, 1) (EXPERIMENTAL COMPARISON)**: $\text{RMSE} = ₹16,554.07$, $\text{MAE} = ₹10,881.64$, $\text{MAPE} = 77.23\%$.
     - **Historical Mean Baseline**: $\text{RMSE} = ₹16,781.57$, $\text{MAE} = ₹11,308.29$, $\text{MAPE} = 81.12\%$.
   - **Primary Model-Selection Criterion & Symmetry Explanation**:
     - **RMSE (Root Mean Squared Error)** is retained as the primary selection criterion because the training-only walk-forward cross-validation supports it (the 7-day rolling mean achieved lower mean RMSE across 28 training folds).
     - *Symmetry Clarification*: RMSE squares error terms, penalizing large errors **quadratically and symmetrically in either direction** ($(\hat{y}_t - y_t)^2$). Positive errors (over-predictions) and negative errors (under-predictions) of equal magnitude receive identical penalties. RMSE is a standard statistical metric of error dispersion and variance; it is **not** specifically an under-prediction or liquidity-risk metric. RMSE does not inherently protect against under-predictions, overdrafts, or liquidity shortfalls.
   - **MAE vs. RMSE Trade-Off & Future Algorithmic Enhancements**:
     - The **7-Day Rolling Mean is not universally superior** across all error dimensions.
     - The **Naive baseline achieves lower MAE** (₹8,615.66 vs. ₹9,179.72) and **lower MAPE** (47.50% vs. 57.79%) because predicting the immediate previous value incurs smaller linear absolute deviations during calm, consecutive non-spending stretches.
     - The 7-Day Rolling Mean achieves the **lowest RMSE** (₹15,908.52 vs. ₹16,129.58 for Naive and ₹16,554.07 for ARIMA). Rather than claiming it dynamically "cushions sudden spikes" in real time (its forward projection is constant across the horizon), its lower RMSE accurately reflects lower overall error variance across the evaluation window.
     - ARIMA(1, 1, 1) underperforms both baselines across MAE, RMSE, and MAPE due to over-differencing.
     - *Potential Future Improvements (Not Implemented)*: Standard RMSE and MAE penalize over-prediction and under-prediction symmetrically. If an application specifically requires guarding against under-prediction (where underestimating expenditures is costlier than overestimating), potential future enhancements could evaluate **asymmetric loss functions** (such as lin-lin loss) or **upper-quantile forecasting** (such as pinball loss at $\tau = 0.80$ or $\tau = 0.90$). These represent potential future algorithmic directions, not currently implemented features.
   - **Zero-Leakage Pre-Test Validation Design (`evaluate_model_selection_walk_forward`)**:
     - To ensure model selection was not tuned post-hoc to the final holdout test set, model selection was verified on 28 chronological walk-forward validation folds strictly within the 292 training days (`min_train=90`, `horizon=7`, `step=7`).
     - Across the 28 training folds:
       - 7-Day Rolling Mean: Average $\text{RMSE} = ₹19,963.35$, Average $\text{MAE} = ₹14,359.63$.
       - Naive Baseline: Average $\text{RMSE} = ₹23,165.07$, Average $\text{MAE} = ₹16,207.57$.
       - Historical Mean: Average $\text{RMSE} = ₹24,258.91$, Average $\text{MAE} = ₹17,543.12$.
     - This establishes that the 7-day rolling mean achieved both lower mean RMSE and lower mean MAE on training data *prior* to unblinding the holdout test set.
4. **Evaluation Metrics & Zero-Division Policy**:
   - Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) in INR.
   - Mean Absolute Percentage Error (MAPE): Standard MAPE is mathematically undefined when actual spend is ₹0.00. MAPE is evaluated strictly across non-zero actual days ($y_t > 0$); MAE and RMSE are the primary trustworthy evaluation metrics.
5. **Confidence Interval Presentation Constraints & Coverage Disclosure**:
   - Forward projections include 95% confidence intervals derived from empirical rolling residual standard errors (for the rolling mean) and Gaussian asymptotic variance (for ARIMA).
   - **Non-Negativity Presentation Constraint**: Model-generated lower bounds frequently plunge into negative territory. Lower bounds are clipped to ₹0.00 to reflect the domain reality that personal expenses cannot be negative.
   - **Statistical Coverage Disclosure**: Clipping truncates the distribution tail and alters the coverage probability. Therefore, the displayed interval does not retain nominal 95% statistical coverage under standard normal theory. Both unclipped raw bounds (`raw_lower_bound`, `raw_upper_bound`) and display-clipped bounds (`lower_bound`, `upper_bound`) are explicitly exposed in returned DataFrames.
   - Outputs are explicitly disclaimed as statistical estimates, not financial guarantees.
