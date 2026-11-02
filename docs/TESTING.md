# Testing & Quality Assurance Guide

**Author: Akash Das**  
**Project**: Expense Tracker App using Data Science  

---

## 1. Testing Philosophy
The project enforces high testability across all business logic, data pipelines, analytics computations, and model scaffolding. Test execution is fully isolated and does not modify production databases.

---

## 2. Test Suite Structure

```text
tests/
├── __init__.py
├── conftest.py                       # Shared fixtures and sys.path configuration
├── test_data_generator.py            # Synthetic generator interface tests
├── test_data_cleaning.py             # Data normalization & missing value tests
├── test_validation.py                # Schema validation tests
├── test_database.py                  # SQLite connection and operation tests
├── test_feature_engineering.py       # Temporal and text transformation tests
├── test_financial_metrics.py         # Financial KPI calculation tests
├── test_budget_analysis.py           # Budget variance tests
└── test_anomaly_detection.py         # Statistical & ML anomaly detection tests
```

---

## 3. Running Tests

Execute the full test suite using the project-local `.venv`:

```powershell
# Windows PowerShell
.\.venv\Scripts\pytest tests/ -v
```

```bash
# Unix / Linux / macOS
.venv/bin/pytest tests/ -v
```

---

## 4. Continuous Integration (CI)
GitHub Actions workflow is located at `.github/workflows/tests.yml`. It runs automatically on pull requests and pushes to `main` / `master` using Python 3.11.

