# Data Dictionary & Schema Specification

**Author: Akash Das**  
**Project**: Expense Tracker App using Data Science  
**Phase**: Phase 2 — Synthetic Data Generation & Schema Validation  

---

## 1. Transaction Entity Specification

The primary entity of the application is the financial **Transaction** represented in [`data/sample/transactions.csv`](file:///D:/Projects/Data%20Science/Expense%20Tracker%20App/data/sample/transactions.csv).

| Column Name | Expected Type | Format & Allowed Values | Description | Example Values | Validation Constraints |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `transaction_id` | String | `TXN-#####` | Unique sequential identifier for each transaction | `TXN-00001`, `TXN-04999` | Non-null, non-empty, unique across the entire dataset |
| `date` | String / Date | ISO 8601 (`YYYY-MM-DD`) | Date on which transaction was posted | `2025-11-01`, `2026-06-15` | Valid calendar date strictly within configured boundary range |
| `type` | String (Categorical) | `Income` \| `Expense` | Flow direction of the transaction funds | `Income`, `Expense` | Strictly one of allowed values (`Income`, `Expense`) |
| `category` | String (Categorical) | Documented Category Enums (see Section 2) | Classification of income source or expense purpose | `Salary`, `Groceries`, `Rent` | Non-null, must be valid for the corresponding `type` |
| `amount` | Numeric (Float64) | Positive real number rounded to 2 decimal places | Financial value of transaction in Indian Rupees (₹ / INR) | `1250.50`, `85000.00` | Numeric, finite, strictly positive (`> 0.0`) |
| `payment_method` | String (Categorical) | Enum: `UPI`, `Cash`, `Debit Card`, `Credit Card`, `Bank Transfer` | Channel or instrument used for transaction settlement | `UPI`, `Credit Card` | Non-null, strictly one of 5 permitted payment modes |
| `description` | String | UTF-8 text string | Merchant name, entity, or transaction narrative | `Blinkit Quick Grocery Delivery` | Non-null, non-blank (at least 1 non-whitespace character) |

---

## 2. Standard Category Taxonomy & Type Mapping

### 2.1. Income Categories (`type == "Income"`)
| Category | Description | Primary Payment Methods | Typical Frequency & Range |
| :--- | :--- | :--- | :--- |
| `Salary` | Regular monthly primary employer compensation | Bank Transfer | 1 per month, ₹70,000 – ₹95,000 |
| `Freelance` | Independent client projects, consulting, and contract milestones | Bank Transfer, UPI | Periodic (3–10/yr), ₹12,000 – ₹45,000 |
| `Business Income` | Secondary commerce revenue, digital sales, or direct business invoicing | Bank Transfer | Periodic, ₹8,000 – ₹35,000 |
| `Investment Income` | Mutual fund dividends, equity dividends, and fixed deposit interest | Bank Transfer | Quarterly/monthly, ₹2,500 – ₹15,000 |
| `Other Income` | Tax refunds, cashback rewards, employer reimbursements, family gifts | UPI, Bank Transfer, Cash | Occasional, ₹500 – ₹5,000 |

### 2.2. Expense Categories (`type == "Expense"`)
| Category | Description | Primary Payment Methods | Typical Range |
| :--- | :--- | :--- | :--- |
| `Rent` | Apartment monthly lease and society maintenance | Bank Transfer, UPI | Monthly, ₹22,000 – ₹28,000 |
| `Groceries` | Food staples, supermarkets, fresh produce, and quick-commerce | UPI, Credit Card, Cash | High frequency (2–4/wk), ₹300 – ₹3,500 |
| `Utilities` | Electricity, piped gas, broadband, water, and postpaid mobile bills | UPI, Credit Card, Bank Transfer | Monthly recurring, ₹400 – ₹4,500 |
| `Transport` | Rideshare (Uber/Ola), metro smart card, fuel (petrol/diesel), tolls | UPI, Cash, Credit Card | High frequency (daily/weekly), ₹60 – ₹1,800 |
| `Healthcare` | Pharmacy medications, doctor consultations, diagnostics, dental care | Credit Card, UPI, Cash | Occasional, ₹250 – ₹4,500 |
| `Education` | Courses, e-books, professional certifications, webinars | Credit Card, UPI | Periodic, ₹800 – ₹7,500 |
| `Shopping` | Apparel, footwear, electronics, home decor, personal goods | Credit Card, UPI, Debit Card | Discretionary, ₹800 – ₹8,000 |
| `Entertainment` | Cinema tickets, concerts, events, gaming cafes, theme parks | UPI, Credit Card | Weekends/discretionary, ₹300 – ₹3,500 |
| `Dining` | Restaurants, food delivery (Swiggy/Zomato), cafes, street food | UPI, Credit Card, Cash | High frequency (2–3/wk), ₹200 – ₹2,500 |
| `Travel` | Outstation flights, train reservations, hotel stays, holidays | Credit Card, Bank Transfer | Seasonal/quarterly, ₹2,500 – ₹22,000 |
| `Subscriptions` | Digital streaming (Netflix, Spotify), cloud storage, gym | Credit Card, UPI | Monthly recurring, ₹179 – ₹2,500 |
| `Other Expenses` | Courier, home hardware, pet care, dry cleaning, donations | UPI, Cash, Debit Card | Low frequency, ₹150 – ₹2,500 |

---

## 3. Deliberate Analytical Outliers (Synthetic Test Cases)
A small set of deliberate large expense transactions (~0.25% of total records) are embedded with the `[UNUSUAL]` prefix in their description to serve as ground-truth test cases for the subsequent Phase 6 Anomaly Detection module:
- Emergency Hospitalization & Surgery (₹85,000 – ₹115,000)
- High-end Laptop Purchase (₹135,000 – ₹165,000)
- International Vacation Booking (₹95,000 – ₹140,000)
- Designer Jewelry / Gold Purchase (₹80,000 – ₹120,000)
- Emergency Home Renovation & Plumbing Overhaul (₹65,000 – ₹90,000)

*Note: These outliers represent realistic personal financial shocks, not fraudulent transactions.*


---

## 4. SQLite Storage Schema (`transactions` Table)

The persistence tier stores records in SQLite (`data/processed/expenses.db`) conforming to strict database constraints and composite consistency rules:

```sql
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('Income', 'Expense')),
    category TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    payment_method TEXT NOT NULL CHECK(payment_method IN ('UPI', 'Cash', 'Debit Card', 'Credit Card', 'Bank Transfer')),
    description TEXT NOT NULL,
    CHECK (
        (type = 'Income' AND category IN (
            'Salary', 'Freelance', 'Business Income', 'Investment Income', 'Other Income'
        ))
        OR
        (type = 'Expense' AND category IN (
            'Rent', 'Groceries', 'Utilities', 'Transport', 'Healthcare',
            'Education', 'Shopping', 'Entertainment', 'Dining', 'Travel',
            'Subscriptions', 'Other Expenses'
        ))
    )
);

CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
```

### 4.1. Constraint and Duplicate Policy Summary
- **Primary Key Constraint**: Enforces global uniqueness across `transaction_id`.
- **Positive Amount Check**: `CHECK(amount > 0)` prevents negative or zero transaction amounts at the database engine level.
- **Transaction Type Check**: `CHECK(type IN ('Income', 'Expense'))` prevents invalid transaction types.
- **Payment Method Check**: `CHECK(payment_method IN ('UPI', 'Cash', 'Debit Card', 'Credit Card', 'Bank Transfer'))` rejects unsupported payment methods.
- **Category-to-Type Composite Constraint**: Enforces that Income transactions only allow Income categories (`Salary`, `Freelance`, `Business Income`, `Investment Income`, `Other Income`) and Expense transactions only allow Expense categories at the SQLite engine level.
- **Duplicate Policy**: Default bulk insertion (`on_conflict="skip"`) skips existing IDs without modifying or overwriting stored records, ensuring idempotent re-imports.

---

## 5. Explicit Date Parsing & Normalization Specification

The data cleaning pipeline (`clean_transactions`) implements strict, deterministic date parsing across three explicitly supported calendar formats:
1. `YYYY-MM-DD` (ISO 8601 standard, e.g., `2026-02-01` -> 1 February 2026)
2. `YYYY/MM/DD` (Slash ISO format, e.g., `2026/02/01` -> 1 February 2026)
3. `DD-MM-YYYY` (Indian financial standard, e.g., `01-02-2026` -> 1 February 2026)

### Rejection Policy:
- **No Guessing**: Ambiguous or unsupported formats (such as US `MM/DD/YYYY` like `02/15/2026`, textual formats like `Feb 1, 2026`, or 2-digit years) are explicitly rejected (`None`) rather than guessed.
- **Invalid Calendar Dates**: Out-of-range dates (such as `2026-02-31`) are strictly rejected.
- **Null / Missing Dates**: Rejected during schema validation. All rejected records are surfaced in the quality audit report without dropping rows from the cleaned DataFrame.

---

## 6. Engineered Features Specification (Phase 5)

Phase 5 enriches cleaned transactions into a 52-column analytical dataset (`data/processed/enriched_transactions.csv`), deriving temporal, cyclical, log-transformed, sequential lag, calendar rolling window, and text metadata features while strictly enforcing target leakage prevention.

### 6.1. Schema Overview

| Feature Category | Count | Column Names | Description |
| :--- | :---: | :--- | :--- |
| **Base Schema** | 7 | `transaction_id`, `date`, `type`, `category`, `amount`, `payment_method`, `description` | Ingested and cleaned canonical transaction records. |
| **Calendar / Temporal** | 8 | `year`, `month`, `month_name`, `quarter`, `day_of_month`, `day_of_week`, `day_name`, `is_weekend` | Cyclical calendar features derived from transaction date. |
| **Flow Indicators** | 2 | `is_income`, `is_expense` | Binary directional flags (`1` or `0`). |
| **Amount Transformations** | 1 | `log_amount` | `np.log1p(amount)` stabilizing variance across right-skewed amounts. |
| **Temporal Sequence & Rolling** | 10 | `days_since_prev_txn`, `prev_amount`, `days_since_prev_expense`, `prev_expense_amount`, `rolling_expense_7d_sum`, `rolling_expense_7d_mean`, `rolling_expense_7d_count`, `rolling_expense_30d_sum`, `rolling_expense_30d_mean`, `rolling_expense_30d_count` | Chronological inter-transaction lags and strictly past-looking calendar rolling stats. |
| **Text Metadata** | 2 | `desc_char_length`, `desc_word_count` | String length and word count for narrative auditing and EDA (quarantined from model inputs). |
| **Categorical Dummies** | 22 | 17 `cat_*` columns, 5 `pay_*` columns | Canonical one-hot encoded binary indicator variables. |
| **Total Enriched Columns** | **52** | — | **Full analytical feature set** |

---

### 6.2. Calendar and Cyclical Features

| Feature Name | Type | Range / Format | Description | Formula / Source |
| :--- | :--- | :--- | :--- | :--- |
| `year` | Integer | `2024` – `2026` | 4-digit calendar year | `date.year` |
| `month` | Integer | `1` – `12` | Calendar month index | `date.month` |
| `month_name` | String | `January` – `December` | Full English month name | `date.month_name()` |
| `quarter` | Integer | `1` – `4` | Calendar quarter of year | `date.quarter` |
| `day_of_month` | Integer | `1` – `31` | Day of calendar month | `date.day` |
| `day_of_week` | Integer | `0` – `6` | Day of week index (Monday = 0, Sunday = 6) | `date.day_of_week` |
| `day_name` | String | `Monday` – `Sunday` | Full English weekday name | `date.day_name()` |
| `is_weekend` | Integer | `0` \| `1` | Binary weekend indicator (`1` if Saturday or Sunday, `0` otherwise) | `day_of_week in [5, 6]` |

---

### 6.3. Flow and Amount Features

| Feature Name | Type | Range | Description | Formula / Behavior |
| :--- | :--- | :--- | :--- | :--- |
| `is_income` | Integer | `0` \| `1` | Binary flag for cash inflows | `1 if type == 'Income' else 0` |
| `is_expense` | Integer | `0` \| `1` | Binary flag for cash outflows | `1 if type == 'Expense' else 0` |
| `log_amount` | Float64 | `3.43` – `12.01` | Log-transformed transaction value | `np.log1p(amount).round(4)` |

---

### 6.4. Temporal Sequence and Historical Rolling Features

To prevent data leakage, all sequential and rolling window calculations are strictly backward-looking:
- **Same-Day Isolation (`closed='left'`)**: For any transaction occurring on date $T$, the rolling interval is $[T - \text{offset}, T)$. Because the interval is open on the right ($t < T$), every transaction on date $T$ receives an identical baseline computed strictly from dates prior to $T$. No transaction on date $T$ can influence another transaction on that same date.
- **Universal Date-Level Baseline**: Historical rolling expense baselines are constructed exclusively from **Expense** transactions, but are attached to **every transaction occurring on date $T$** (including Income transactions). Income transactions never contribute to expense sums, counts, or means.
- **Absent History Preservation vs. Zero Spend**: When a transaction has no prior observations in its lookback window (e.g. Day 1, where the dataset starts on 2025-11-01), rolling features evaluate to `NaN` under the empty-window policy. This correctly represents *unavailable historical information* rather than an unobserved assumption of ₹0 spending.

| Feature Name | Type | Unit | Description | Missing Values Mechanics |
| :--- | :--- | :--- | :--- | :--- |
| `days_since_prev_txn` | Float64 | Days | Elapsed days since the immediately prior transaction across all types. | Exactly 1 `NaN` (chronologically first transaction in dataset). |
| `prev_amount` | Float64 | INR (₹) | Monetary amount of the immediately prior transaction. | Exactly 1 `NaN` (chronologically first transaction). |
| `days_since_prev_expense` | Float64 | Days | Elapsed days since the immediately prior **Expense** transaction. | Exactly 304 `NaN`s (303 Income rows + 1st Expense transaction). |
| `prev_expense_amount` | Float64 | INR (₹) | Monetary amount of the immediately prior **Expense** transaction. | Exactly 304 `NaN`s (303 Income rows + 1st Expense transaction). |
| `rolling_expense_7d_sum` | Float64 | INR (₹) | Total expense volume over strictly preceding 7 calendar days `[t-7D, t)`. | Exactly 9 `NaN`s (all 9 transactions on Day 1, 2025-11-01: 2 Income + 7 Expenses). |
| `rolling_expense_7d_mean` | Float64 | INR (₹) | Mean expense amount over strictly preceding 7 calendar days `[t-7D, t)`. | Exactly 9 `NaN`s (all 9 transactions on Day 1, 2025-11-01: 2 Income + 7 Expenses). |
| `rolling_expense_7d_count` | Float64 | Count | Number of expense transactions over strictly preceding 7 calendar days `[t-7D, t)`. | Exactly 9 `NaN`s (all 9 transactions on Day 1, 2025-11-01: 2 Income + 7 Expenses). |
| `rolling_expense_30d_sum` | Float64 | INR (₹) | Total expense volume over strictly preceding 30 calendar days `[t-30D, t)`. | Exactly 9 `NaN`s (all 9 transactions on Day 1, 2025-11-01: 2 Income + 7 Expenses). |
| `rolling_expense_30d_mean` | Float64 | INR (₹) | Mean expense amount over strictly preceding 30 calendar days `[t-30D, t)`. | Exactly 9 `NaN`s (all 9 transactions on Day 1, 2025-11-01: 2 Income + 7 Expenses). |
| `rolling_expense_30d_count` | Float64 | Count | Number of expense transactions over strictly preceding 30 calendar days `[t-30D, t)`. | Exactly 9 `NaN`s (all 9 transactions on Day 1, 2025-11-01: 2 Income + 7 Expenses). |

---

### 6.5. Text Metadata Features

| Feature Name | Type | Range | Description | Target Leakage Quarantining |
| :--- | :--- | :--- | :--- | :--- |
| `desc_char_length` | Integer | `7` – `64` | Total character count of `description` string. | **Excluded from model matrix.** Acts as a proxy for `[UNUSUAL]` shock markers (+9 chars). |
| `desc_word_count` | Integer | `1` – `9` | Total whitespace-delimited word count of `description`. | **Excluded from model matrix.** Acts as a proxy for `[UNUSUAL]` shock markers (+1 word). |

---

### 6.6. One-Hot Encoded Categorical Dummies

Canonical one-hot encodings provide fixed columns regardless of training split:
- **Category Dummies (17)**: `cat_salary`, `cat_freelance`, `cat_business_income`, `cat_investment_income`, `cat_other_income`, `cat_rent`, `cat_groceries`, `cat_utilities`, `cat_transport`, `cat_healthcare`, `cat_education`, `cat_shopping`, `cat_entertainment`, `cat_dining`, `cat_travel`, `cat_subscriptions`, `cat_other_expenses`.
- **Payment Method Dummies (5)**: `pay_bank_transfer`, `pay_cash`, `pay_credit_card`, `pay_debit_card`, `pay_upi`.
- **Unseen Category Handling**: Any unexpected category evaluates to `0` across all dummy columns without crashing or raising errors.

---

### 6.7. Target Leakage Prevention & Model Feature Matrix

The modeling feature matrix generated by `get_model_feature_matrix()` contains **42 purely numeric features** (or 20 without categorical dummies):

#### 1. Columns Excluded from Model Matrix (10 Columns Total)
1. `transaction_id`: Entity identifier (non-predictive primary key).
2. `date`: Calendar timestamp string (represented via cyclical integer calendar features).
3. `type`: Categorical string (represented via binary `is_income`, `is_expense`).
4. `category`: Categorical string (represented via 17 one-hot dummies `cat_*`).
5. `payment_method`: Categorical string (represented via 5 one-hot dummies `pay_*`).
6. `description`: Narrative text containing synthetic shock markers (`[UNUSUAL]`).
7. `month_name`: String calendar attribute (redundant with integer `month`).
8. `day_name`: String calendar attribute (redundant with integer `day_of_week`).
9. `desc_char_length`: **Description-derived leakage proxy.** The synthetic `[UNUSUAL]` marker directly lengthens the description (+9 characters), leaking anomaly presence into training features.
10. `desc_word_count`: **Description-derived leakage proxy.** The synthetic `[UNUSUAL]` marker directly increments word count (+1 word), leaking anomaly presence into training features.

*Evaluation label `is_unusual_ground_truth` (extracted by `extract_ground_truth_labels()`) is strictly quarantined for benchmarking Phase 6 anomaly detection algorithms and is never admitted to model inputs.*

#### 2. Admitted Modeling Matrix Columns (42 Purely Numeric Columns)
`amount`, `year`, `month`, `quarter`, `day_of_month`, `day_of_week`, `is_weekend`, `is_income`, `is_expense`, `log_amount`, `days_since_prev_txn`, `prev_amount`, `days_since_prev_expense`, `prev_expense_amount`, `rolling_expense_7d_sum`, `rolling_expense_7d_mean`, `rolling_expense_7d_count`, `rolling_expense_30d_sum`, `rolling_expense_30d_mean`, `rolling_expense_30d_count`, `cat_business_income`, `cat_dining`, `cat_education`, `cat_entertainment`, `cat_freelance`, `cat_groceries`, `cat_healthcare`, `cat_investment_income`, `cat_other_expenses`, `cat_other_income`, `cat_rent`, `cat_salary`, `cat_shopping`, `cat_subscriptions`, `cat_transport`, `cat_travel`, `cat_utilities`, `pay_bank_transfer`, `pay_cash`, `pay_credit_card`, `pay_debit_card`, `pay_upi`.

---

## 7. Financial Analytics & Budgeting Entities and Schemas (Phase 6)

### 7.1. Financial KPI Dictionary Schema (`compute_financial_kpis`)

| Key Name | Type | Unit | Description | Null Policy |
| :--- | :--- | :--- | :--- | :--- |
| `total_income` | Float | ₹ (INR) | Sum of all transactions where `type == "Income"`. | Rounded to 2 decimals; 0.0 if empty. |
| `total_expenses` | Float | ₹ (INR) | Sum of all transactions where `type == "Expense"`. | Rounded to 2 decimals; 0.0 if empty. |
| `net_savings` | Float | ₹ (INR) | `total_income - total_expenses` (can be negative for deficit). | Rounded to 2 decimals; 0.0 if empty. |
| `savings_rate_pct` | Float | % | `(net_savings / total_income) * 100.0`. | Returns `NaN` if income is 0 with expenses > 0; 0.0 if both 0. |
| `expense_to_income_ratio` | Float | Ratio | `total_expenses / total_income`. | Returns `NaN` if income is 0 with expenses > 0; 0.0 if both 0. |
| `total_transactions` | Integer | Count | Total number of transactions analyzed. | `0` if empty. |
| `income_count` | Integer | Count | Total number of income transactions. | `0` if empty. |
| `expense_count` | Integer | Count | Total number of expense transactions. | `0` if empty. |
| `average_income` | Float | ₹ (INR) | Mean ticket size of income transactions. | 0.0 if no income transactions. |
| `average_expense` | Float | ₹ (INR) | Mean ticket size of expense transactions. | 0.0 if no expense transactions. |
| `median_expense` | Float | ₹ (INR) | Median ticket size of expense transactions. | 0.0 if no expense transactions. |
| `transaction_counts` | Dict[str, int] | Count | Partitioned counts: `total`, `income`, `expense`. | Always non-null dictionary. |

### 7.2. Category Spending Breakdown Schema (`get_spending_by_category`)

| Column Name | Type | Unit | Description | Null Policy |
| :--- | :--- | :--- | :--- | :--- |
| `category` | String | Categorical | Expense category name (strictly excludes income). | Non-null canonical string. |
| `total_amount` | Float | ₹ (INR) | Total expenditure in category. | Strictly positive, rounded to 2 decimals. |
| `percentage` | Float | % | Category share of total expenses: `(cat_total / total_exp) * 100.0`. | Sums to ~100.0%. |
| `transaction_count` | Integer | Count | Number of expense transactions in category. | $\ge 1$. |
| `average_amount` | Float | ₹ (INR) | Mean expenditure per transaction in category. | Rounded to 2 decimals. |
| `median_amount` | Float | ₹ (INR) | Median expenditure per transaction in category. | Rounded to 2 decimals. |

### 7.3. Category Budget Variance Schema (`compute_budget_variance`)

| Column Name | Type | Unit | Description | Null Policy |
| :--- | :--- | :--- | :--- | :--- |
| `category` | String | Categorical | Budgeted category identifier. | Non-null string. |
| `budget_amount` | Float | ₹ (INR) | Planned expenditure limit. | `NaN` for unbudgeted categories. |
| `actual_amount` | Float | ₹ (INR) | Actual expenditure in category (strictly expenses). | `0.0` if no transactions. |
| `remaining_budget` | Float | ₹ (INR) | Budget surplus: `budget_amount - actual_amount`. | `NaN` for unbudgeted categories. |
| `budget_variance` | Float | ₹ (INR) | Budget variance: `actual_amount - budget_amount` (positive = over budget). | `NaN` for unbudgeted categories. |
| `utilization_pct` | Float | % | Budget utilization: `(actual_amount / budget_amount) * 100.0`. | `NaN` if budget is 0 or unbudgeted. |
| `is_over_budget` | Nullable Boolean (`boolean`) | Flag | `actual_amount > budget_amount`. Evaluates to `pd.NA` for unbudgeted categories. | `pd.NA` for unbudgeted categories (unknown/not-assessable). Excluded from over/under budget counts. |

### 7.4. Monthly Financial Trends Schema (`compute_monthly_trends`)

| Column Name | Type | Unit | Description | Null Policy |
| :--- | :--- | :--- | :--- | :--- |
| `month` | String | YYYY-MM | Calendar month period. | Chronologically sorted. |
| `income` | Float | ₹ (INR) | Total monthly income. | `0.0` if no income transactions. |
| `expense` | Float | ₹ (INR) | Total monthly expenditure. | `0.0` if no expense transactions. |
| `net_savings` | Float | ₹ (INR) | Monthly net savings: `income - expense`. | Rounded to 2 decimals. |
| `savings_rate_pct` | Float | % | Monthly savings rate: `(net_savings / income) * 100.0`. | `NaN` if income is 0 with expense > 0. |
| `mom_income_change` | Float | ₹ (INR) | Month-over-month income difference: $I_t - I_{t-1}$. | `NaN` for first month. |
| `mom_income_pct` | Float | % | MoM percentage income growth: $((I_t - I_{t-1}) / I_{t-1}) * 100.0$. | `NaN` for first month or 0 baseline. |
| `mom_expense_change` | Float | ₹ (INR) | Month-over-month expense difference: $E_t - E_{t-1}$. | `NaN` for first month. |
| `mom_expense_pct` | Float | % | MoM percentage expense growth: $((E_t - E_{t-1}) / E_{t-1}) * 100.0$. | `NaN` for first month or 0 baseline. |
| `mom_savings_change` | Float | ₹ (INR) | Month-over-month savings difference: $S_t - S_{t-1}$. | `NaN` for first month. Preserved across all sign boundaries. |
| `mom_savings_pct` | Float | % | MoM percentage savings growth: $((S_t - S_{t-1}) / S_{t-1}) * 100.0$ strictly for positive baselines ($S_{t-1} > 0$ and $S_t \ge 0$). | `NaN` when $S_{t-1} \le 0$ or sign changes. Prevents misleading growth rates on deficits. |



