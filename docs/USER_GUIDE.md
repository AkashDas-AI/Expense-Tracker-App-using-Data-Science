# User Guide & Operational Walkthrough

**Author: Akash Das**  
**Project**: Expense Tracker App using Data Science  

---

## 1. Installation & Environment Setup

### Step 1: Clone Repository
Clone the project repository to your local system and navigate to the project directory.

### Step 2: Set Up Virtual Environment
Create and activate the project-isolated virtual environment:

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## 2. Running the Application

Launch the Streamlit interactive dashboard:

```powershell
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 3. Navigating the Dashboard Pages

1. **Overview Page**: High-level financial summary, net balance, monthly burn rate, and top category breakdown.
2. **Spending Page**: Detailed inspection of expenses, filterable by date range, category, and payment method.
3. **Budget Page**: Set monthly allowances per category and view real-time budget utilization progress bars.
4. **Forecasting & Anomalies Page**: Review future predicted expenditures with confidence intervals and examine flagged unusual transactions.

