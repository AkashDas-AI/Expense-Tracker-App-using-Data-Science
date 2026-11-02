# Interview Preparation & Technical Deep-Dive

**Author: Akash Das**  
**Project**: Expense Tracker App using Data Science  

---

## 1. Project Motivation & Problem Statement
Personal expense tracking often suffers from high user friction and poor analytical value. Most tools act simply as digital ledgers without predictive intelligence. This project bridges that gap by combining:
1. Automated data ingestion and preprocessing.
2. Robust financial analytics and budget variance modeling.
3. Machine learning (unsupervised anomaly detection and time-series forecasting).

---

## 2. Key Architecture & Engineering Decisions

### Why Modular Layering over Monolithic Script?
- **Separation of Concerns**: Presentation (`dashboard/` / `app.py`) is completely separated from business logic (`src/expense_tracker/`).
- **Testability**: Core functions are decoupled from Streamlit rendering, enabling fast, isolated unit testing in `pytest`.
- **Portability**: The `expense_tracker` package can easily be packaged, deployed as a REST API (e.g. FastAPI), or run as a scheduled CLI batch job without rewriting logic.

### Why SQLite for Persistence?
- Zero-configuration, serverless, self-contained, and built directly into Python's standard library (`sqlite3`).
- Highly performant for single-user analytical applications while retaining full ACID compliance.

### Why ARIMA/SARIMAX for Expense Forecasting?
- Expenses exhibit distinct weekly and monthly seasonal cycles (paydays, rent cycles, weekend dining).
- Time-series statistical models provide explicit confidence intervals, which are critical for budget risk assessment.

### Why Isolation Forest for Anomaly Detection?
- Requires no labeled ground truth (unsupervised).
- Highly effective at isolating rare outliers in multi-dimensional numerical and temporal feature spaces without assuming a normal distribution.

---

## 3. Potential Interview Questions & Answers

**Q: How do you prevent data leakage during time-series modeling?**  
*A: Unlike standard cross-validation which randomly shuffles data, time-series evaluation requires strict temporal splitting (e.g., rolling window or expanding window walk-forward validation). The model is never exposed to future records during preprocessing, scaling, or training.*

**Q: What considerations are made for production readiness and security?**  
*A: Sensitive financial data files, databases, and local secrets are excluded from Git via `.gitignore`. Dependencies are pinned in `requirements.txt` with isolated `.venv`, and an automated GitHub Actions CI pipeline guarantees tests pass on every pull request.*

