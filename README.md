# Expense Tracker App using Data Science

An intelligent, data science-driven expense tracking and personal finance analytics application designed to analyze transaction patterns, forecast expenditures, manage budgets, and detect spending anomalies.

---

## Author
**Akash Das**

---

## Project Status
**Phase 1: Setup, Local Virtual Environment & Modular Scaffolding — COMPLETED**  
*Core architecture, isolated environment, and interface contracts established. Business logic, data pipelines, and machine learning models are scheduled for subsequent phases.*

---

## Key Features & Capabilities
- **Transaction Ingestion & Processing**: Robust loading, cleaning, validation, and schema enforcement for transaction records.
- **Financial Analytics & Budgeting**: Detailed metrics on spending categories, monthly burn rates, and budget variance.
- **Data Science & Machine Learning**:
  - Time-series expense trend analysis and forecasting.
  - Anomaly detection for unusual or irregular transactions.
  - Automated category classification and feature engineering.
- **Interactive Multi-Page Dashboard**: Built with Streamlit, offering visual summaries, spending breakdowns, budget tracking, and predictive insights.

---

## Technology Stack
- **Programming Language**: Python 3.11+
- **Data Manipulation**: Pandas, NumPy
- **Data Persistence**: SQLite (`sqlite3`)
- **Data Visualization**: Matplotlib, Seaborn, Plotly
- **Interactive Dashboard**: Streamlit
- **Machine Learning & Statistics**: Scikit-Learn, Statsmodels
- **Testing & Quality Assurance**: Pytest
- **Exploratory Analysis**: Jupyter

---

## Project Structure

```text
Expense-Tracker-App-Data-Science/
│
├── .venv/                      # Local Python virtual environment
├── app.py                      # Main Streamlit dashboard entry point
├── README.md                   # Project overview and documentation
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # License information
├── requirements.txt            # Project dependencies
├── .gitignore                  # Git ignore rules
├── .env.example                # Environment configuration template
│
├── data/                       # Data storage stages
│   ├── raw/                    # Raw, unprocessed transaction records
│   ├── interim/                # Intermediate, transformed datasets
│   ├── processed/              # Cleaned datasets ready for modeling
│   └── sample/                 # Tracked sample data for testing/demo
│
├── notebooks/                  # Jupyter notebooks for EDA and prototyping
│
├── src/                        # Core source code
│   └── expense_tracker/        # Reusable application package
│       ├── config/             # Configuration and environment settings
│       ├── data/               # Ingestion, generation, cleaning, validation
│       ├── database/           # SQLite connection and database operations
│       ├── features/           # Feature engineering and transformations
│       ├── analytics/          # Financial, spending, budget, and trend metrics
│       ├── models/             # Anomaly detection and forecasting models
│       └── utils/              # Helper utilities and shared functions
│
├── dashboard/                  # Streamlit dashboard pages
│   ├── overview.py             # Dashboard overview and KPIs
│   ├── spending.py             # Detailed spending breakdown
│   ├── budgets.py              # Budget vs. actuals tracking
│   └── forecasting.py          # Predictive trends and forecasts
│
├── models/                     # Saved trained model artifacts
├── outputs/                    # Exported reports and generated charts
│   ├── exports/
│   └── figures/
├── reports/                    # Documentation figures and analytical summaries
│   └── figures/
├── docs/                       # Comprehensive technical documentation
├── tests/                      # Unit and integration test suite
└── .github/workflows/          # CI/CD workflows (GitHub Actions)
```

---

## Getting Started

### 1. Prerequisites
- Python 3.11 or later installed on your system.

### 2. Environment Setup
Create and activate the project-local virtual environment:

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Running the Dashboard
```powershell
streamlit run app.py
```

### 5. Running Tests
```powershell
pytest tests/ -v
```

---

## Documentation
Comprehensive technical documentation is maintained in the [`docs/`](docs/) directory:
- [System Architecture](docs/ARCHITECTURE.md)
- [Project Requirements](docs/PROJECT_REQUIREMENTS.md)
- [Data Dictionary](docs/DATA_DICTIONARY.md)
- [Methodology](docs/METHODOLOGY.md)
- [Testing Guide](docs/TESTING.md)
- [User Guide](docs/USER_GUIDE.md)
- [Interview Preparation](docs/INTERVIEW_PREPARATION.md)
- [Screenshot Checklist](docs/SCREENSHOT_CHECKLIST.md)

