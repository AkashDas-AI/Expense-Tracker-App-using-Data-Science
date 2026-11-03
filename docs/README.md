# Expense Tracker App - Technical Documentation Suite

**Author:** Akash Das  
**Project:** Expense Tracker App using Data Science  
**Status:** Production-Ready (Phases 1-9 Completed)  

Welcome to the technical documentation directory for the **Expense Tracker App using Data Science**. This documentation suite provides in-depth architectural specifications, schema definitions, statistical methodologies, testing reports, and operational guides.

---

## Technical Documentation Suite

| Document | Primary Focus | Target Audience |
|---|---|---|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Modular system architecture, component decoupling, data flow diagrams, and interface contracts | System Architects, Senior Developers |
| [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) | Database schema, validation rules, 42 engineered features, and data constraints | Data Engineers, Database Administrators |
| [`METHODOLOGY.md`](METHODOLOGY.md) | Mathematical formulas, financial KPI logic, Isolation Forest anomaly detection, and time-series forecasting | Data Scientists, Quantitative Analysts |
| [`TESTING.md`](TESTING.md) | Test suite breakdown (193 tests), coverage report, and headless Streamlit verification | QA Engineers, CI/CD Maintainers |
| [`USER_GUIDE.md`](USER_GUIDE.md) | End-to-end installation manual, dashboard navigation, and operational procedures | End Users, Financial Analysts |
| [`SCREENSHOT_CHECKLIST.md`](SCREENSHOT_CHECKLIST.md) | Visual asset inventory and screenshot capture guidelines for portfolio presentation | UI/UX Reviewers, Portfolio Reviewers |
| [`06_execution_log.md`](06_execution_log.md) | Chronological development and phase audit history from Phase 1 through Phase 9 | Project Auditors, Code Reviewers |

---

## Architectural Principles

The platform is designed around four core architectural principles:

1. **Separation of Concerns**: Presentation (`app.py`, `dashboard/`) is strictly separated from analytical logic (`src/expense_tracker/analytics/`), feature engineering (`src/expense_tracker/features/`), machine learning (`src/expense_tracker/models/`), and persistence (`src/expense_tracker/database/`).
2. **Defensive Data Integrity**: Strict 11-rule schema validation rejects malformed inputs before database persistence. Parameterized SQL queries prevent SQL injection, and database operations execute within atomic transactions.
3. **Zero Data Leakage**: Temporal ordering is preserved across all training and evaluation splits. Backward-looking rolling statistics enforce `closed='left'` to prevent same-day lookahead leakage. Ground-truth evaluation tags (`[UNUSUAL]`) and description-derived proxy lengths are quarantined out of model matrices.
4. **Reproducible Engineering**: The entire analytics and modeling pipeline is deterministic, backed by 193 automated unit, integration, and headless UI tests running in under 12 seconds.
