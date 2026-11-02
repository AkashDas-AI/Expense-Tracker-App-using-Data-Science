# Project Requirements & Scope

**Author: Akash Das**  
**Project**: Expense Tracker App using Data Science  
**Status**: Active / Phase 1 Setup Completed  

---

## 1. Executive Summary
The **Expense Tracker App** is an intelligent personal finance management application that integrates core data science and machine learning techniques to help individuals track expenditures, predict future spending, analyze budget compliance, and detect abnormal transactions.

---

## 2. Functional Requirements

### 2.1. Transaction Ingestion & Management
- Support ingestion of transaction records from multiple sources (CSV uploads, manual entry, synthetic generator).
- Enforce strict schema validation on critical attributes (Date, Amount, Category, Description, Payment Method).
- Provide automated data cleaning: missing value handling, text normalization, and deduplication.

### 2.2. Financial Analytics & Budgeting
- Compute core financial KPIs: total expenditure, savings rate, burn rate, and discretionary vs. non-discretionary ratios.
- Aggregate spending across multiple granularities: daily, weekly, monthly, and category-level.
- Implement budget variance tracking with threshold alerts for overspending.

### 2.3. Machine Learning & Predictive Modeling
- **Anomaly Detection**: Flag unusual transactions using both statistical metrics (IQR, Z-score) and machine learning models (Isolation Forest).
- **Time-Series Forecasting**: Predict upcoming expenditures over 7, 30, and 90-day horizons using ARIMA/SARIMAX statistical forecasting models.
- **Categorization Assistance**: Assist in automated classification of raw transaction descriptions.

### 2.4. Interactive Dashboard
- Provide an intuitive multi-page Streamlit web dashboard:
  - **Overview**: Executive KPI cards, summary charts, and recent activity.
  - **Spending**: Interactive category breakdowns, merchant distributions, and temporal trends.
  - **Budgets**: Budget vs. actuals comparison, progress gauges, and variance analysis.
  - **Forecasting & Anomalies**: Predictive projection lines, confidence bounds, and outlier inspection tables.

---

## 3. Non-Functional Requirements

### 3.1. Code Quality & Modularity
- Clean architecture separating presentation (`dashboard/`), business logic (`src/expense_tracker/`), and storage (`data/`).
- Adherence to PEP 8, comprehensive type hints, and descriptive docstrings.
- Fully local execution using a project-isolated Python virtual environment (`.venv`).

### 3.2. Data Privacy & Git Hygiene
- Protect private transactions, databases, and secrets using comprehensive `.gitignore` rules.
- Maintain tracked sample datasets for testing and verification without exposing real financial records.

### 3.3. Testability
- Unit test coverage across all core modules using `pytest`.
- Automated CI pipeline via GitHub Actions.

