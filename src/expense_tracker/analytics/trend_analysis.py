"""
Trend Analysis Module

Author: Akash Das
Description: Historical trend analysis, month-over-month (MoM) trajectories,
             savings rate trends, and resampled expenditure patterns in Indian Rupees (₹ / INR).
"""

from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd


def _validate_trend_input(df: pd.DataFrame, required_columns: Optional[List[str]] = None) -> None:
    """Validate DataFrame type, required columns, and numeric integrity."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}.")

    if required_columns is None:
        required_columns = ["date", "type", "amount"]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in DataFrame.")

    if not df.empty and "amount" in df.columns:
        amt_numeric = pd.to_numeric(df["amount"], errors="coerce")
        if amt_numeric.isna().any() or np.isinf(amt_numeric).any():
            nan_count = int(amt_numeric.isna().sum() + np.isinf(amt_numeric).sum())
            raise ValueError(f"Column 'amount' contains {nan_count} non-numeric or infinite values.")
        if (amt_numeric < 0).any():
            neg_count = int((amt_numeric < 0).sum())
            raise ValueError(f"Column 'amount' contains {neg_count} negative values.")


def compute_monthly_trends(
    df: pd.DataFrame,
    start_date: Optional[Union[str, pd.Timestamp]] = None,
    end_date: Optional[Union[str, pd.Timestamp]] = None,
) -> pd.DataFrame:
    """Compute monthly income, expense, net savings, savings rate, and MoM changes.

    Requirements:
    - Chronologically aggregates transactions by calendar month (YYYY-MM).
    - If `start_date` and `end_date` are provided, constructs a continuous monthly period
      range so missing months with 0 transactions are recorded with 0.0 values.
    - Computes Month-over-Month (MoM) absolute changes and percentage changes.
    - Transparent Savings Percentage-Change Policy:
      - Preserves MoM absolute savings change in all valid cases.
      - Returns NaN when the previous month's savings are zero.
      - Returns NaN when the previous month's savings are negative (avoiding misleading growth on deficits).
      - Returns NaN when savings change sign (positive to negative or negative to positive).
      - Calculates conventional percentage growth strictly for positive baselines with non-negative current savings.
    - First month always has NaN for all MoM metrics (absent preceding baseline).

    Args:
        df: Transaction DataFrame containing 'date', 'type', and 'amount'.
        start_date: Optional start boundary (inclusive).
        end_date: Optional end boundary (inclusive).

    Returns:
        pd.DataFrame with columns:
        ['month', 'income', 'expense', 'net_savings', 'savings_rate_pct',
         'mom_income_change', 'mom_income_pct', 'mom_expense_change', 'mom_expense_pct',
         'mom_savings_change', 'mom_savings_pct']
    """
    _validate_trend_input(df)

    output_cols = [
        "month",
        "income",
        "expense",
        "net_savings",
        "savings_rate_pct",
        "mom_income_change",
        "mom_income_pct",
        "mom_expense_change",
        "mom_expense_pct",
        "mom_savings_change",
        "mom_savings_pct",
    ]

    # Convert start/end dates if provided
    start_ts = pd.to_datetime(start_date) if start_date is not None else None
    end_ts = pd.to_datetime(end_date) if end_date is not None else None

    if start_ts is not None and end_ts is not None and start_ts > end_ts:
        raise ValueError(f"start_date ({start_date}) cannot be after end_date ({end_date}).")

    if df.empty:
        if start_ts is not None and end_ts is not None:
            # Generate periods from start to end with 0s
            periods = pd.period_range(start=start_ts, end=end_ts, freq="M")
            records = []
            for p in periods:
                records.append({
                    "month": str(p),
                    "income": 0.0,
                    "expense": 0.0,
                    "net_savings": 0.0,
                    "savings_rate_pct": 0.0,
                    "mom_income_change": np.nan,
                    "mom_income_pct": np.nan,
                    "mom_expense_change": np.nan,
                    "mom_expense_pct": np.nan,
                    "mom_savings_change": np.nan,
                    "mom_savings_pct": np.nan,
                })
            res_df = pd.DataFrame(records, columns=output_cols)
            # If multiple empty months, fill mom changes after first month
            if len(res_df) > 1:
                res_df.loc[1:, "mom_income_change"] = 0.0
                res_df.loc[1:, "mom_income_pct"] = 0.0
                res_df.loc[1:, "mom_expense_change"] = 0.0
                res_df.loc[1:, "mom_expense_pct"] = 0.0
                res_df.loc[1:, "mom_savings_change"] = 0.0
                res_df.loc[1:, "mom_savings_pct"] = np.nan
            return res_df
        return pd.DataFrame(columns=output_cols)

    # Copy and parse dates
    df_clean = df.copy()
    try:
        df_clean["parsed_date"] = pd.to_datetime(df_clean["date"])
    except Exception as e:
        raise ValueError(f"Failed to parse 'date' column into datetime: {e}")

    # Apply date boundaries if provided
    if start_ts is not None:
        df_clean = df_clean[df_clean["parsed_date"] >= start_ts]
    if end_ts is not None:
        df_clean = df_clean[df_clean["parsed_date"] <= end_ts]

    if df_clean.empty:
        if start_ts is not None and end_ts is not None:
            periods = pd.period_range(start=start_ts, end=end_ts, freq="M")
            records = []
            for p in periods:
                records.append({
                    "month": str(p),
                    "income": 0.0,
                    "expense": 0.0,
                    "net_savings": 0.0,
                    "savings_rate_pct": 0.0,
                    "mom_income_change": np.nan,
                    "mom_income_pct": np.nan,
                    "mom_expense_change": np.nan,
                    "mom_expense_pct": np.nan,
                    "mom_savings_change": np.nan,
                    "mom_savings_pct": np.nan,
                })
            res_df = pd.DataFrame(records, columns=output_cols)
            if len(res_df) > 1:
                res_df.loc[1:, "mom_income_change"] = 0.0
                res_df.loc[1:, "mom_income_pct"] = 0.0
                res_df.loc[1:, "mom_expense_change"] = 0.0
                res_df.loc[1:, "mom_expense_pct"] = 0.0
                res_df.loc[1:, "mom_savings_change"] = 0.0
                res_df.loc[1:, "mom_savings_pct"] = np.nan
            return res_df
        return pd.DataFrame(columns=output_cols)

    df_clean["period"] = df_clean["parsed_date"].dt.to_period("M")

    # Determine period index range
    min_p = start_ts.to_period("M") if start_ts is not None else df_clean["period"].min()
    max_p = end_ts.to_period("M") if end_ts is not None else df_clean["period"].max()
    full_periods = pd.period_range(start=min_p, end=max_p, freq="M")

    # Group by period and type
    inc_df = df_clean[df_clean["type"] == "Income"]
    exp_df = df_clean[df_clean["type"] == "Expense"]

    inc_series = inc_df.groupby("period")["amount"].sum().reindex(full_periods, fill_value=0.0)
    exp_series = exp_df.groupby("period")["amount"].sum().reindex(full_periods, fill_value=0.0)

    records = []
    prev_inc: Optional[float] = None
    prev_exp: Optional[float] = None
    prev_sav: Optional[float] = None

    for p in full_periods:
        inc = float(inc_series[p])
        exp = float(exp_series[p])
        sav = inc - exp

        # Savings rate
        if inc > 0:
            sav_rate = (sav / inc) * 100.0
        else:
            sav_rate = 0.0 if exp == 0.0 else np.nan

        # MoM Income
        if prev_inc is None:
            mom_inc_chg = np.nan
            mom_inc_pct = np.nan
        else:
            mom_inc_chg = inc - prev_inc
            if prev_inc == 0.0:
                mom_inc_pct = 0.0 if inc == 0.0 else np.nan
            else:
                mom_inc_pct = (mom_inc_chg / prev_inc) * 100.0

        # MoM Expense
        if prev_exp is None:
            mom_exp_chg = np.nan
            mom_exp_pct = np.nan
        else:
            mom_exp_chg = exp - prev_exp
            if prev_exp == 0.0:
                mom_exp_pct = 0.0 if exp == 0.0 else np.nan
            else:
                mom_exp_pct = (mom_exp_chg / prev_exp) * 100.0

        # MoM Savings
        if prev_sav is None:
            mom_sav_chg = np.nan
            mom_sav_pct = np.nan
        else:
            mom_sav_chg = sav - prev_sav
            # Semantic Policy for Savings Percentage Change:
            # - When previous savings are zero (prev_sav == 0), return NaN (undefined baseline).
            # - When previous savings are negative (prev_sav < 0), return NaN (growth on deficit is misleading).
            # - When savings change sign from positive to negative (prev_sav > 0 and sav < 0), return NaN (sign change makes percentage growth misleading).
            # - For strictly positive baseline to non-negative current (prev_sav > 0 and sav >= 0), calculate conventional percentage change.
            if prev_sav <= 0.0 or sav < 0.0:
                mom_sav_pct = np.nan
            else:
                mom_sav_pct = (mom_sav_chg / prev_sav) * 100.0

        records.append({
            "month": str(p),
            "income": round(inc, 2),
            "expense": round(exp, 2),
            "net_savings": round(sav, 2),
            "savings_rate_pct": round(sav_rate, 2) if not np.isnan(sav_rate) else np.nan,
            "mom_income_change": round(mom_inc_chg, 2) if not np.isnan(mom_inc_chg) else np.nan,
            "mom_income_pct": round(mom_inc_pct, 2) if not np.isnan(mom_inc_pct) else np.nan,
            "mom_expense_change": round(mom_exp_chg, 2) if not np.isnan(mom_exp_chg) else np.nan,
            "mom_expense_pct": round(mom_exp_pct, 2) if not np.isnan(mom_exp_pct) else np.nan,
            "mom_savings_change": round(mom_sav_chg, 2) if not np.isnan(mom_sav_chg) else np.nan,
            "mom_savings_pct": round(mom_sav_pct, 2) if not np.isnan(mom_sav_pct) else np.nan,
        })

        prev_inc = inc
        prev_exp = exp
        prev_sav = sav

    return pd.DataFrame(records, columns=output_cols)


def summarize_financial_trends(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute overall summary KPIs across historical monthly trends.

    Args:
        df: Transaction DataFrame containing 'date', 'type', and 'amount'.

    Returns:
        Dict[str, Any] containing:
        - total_months: Total count of active monthly periods.
        - avg_monthly_income: Mean monthly income (INR).
        - avg_monthly_expense: Mean monthly expenditure (INR).
        - avg_monthly_savings: Mean monthly net savings (INR).
        - highest_expense_month: 'YYYY-MM' of peak expense month, or None.
        - highest_income_month: 'YYYY-MM' of peak income month, or None.
        - best_savings_month: 'YYYY-MM' of maximum savings month, or None.
        - worst_savings_month: 'YYYY-MM' of lowest savings / highest deficit month, or None.
    """
    trends_df = compute_monthly_trends(df)

    if trends_df.empty:
        return {
            "total_months": 0,
            "avg_monthly_income": 0.0,
            "avg_monthly_expense": 0.0,
            "avg_monthly_savings": 0.0,
            "highest_expense_month": None,
            "highest_income_month": None,
            "best_savings_month": None,
            "worst_savings_month": None,
        }

    total_months = len(trends_df)
    avg_inc = round(float(trends_df["income"].mean()), 2)
    avg_exp = round(float(trends_df["expense"].mean()), 2)
    avg_sav = round(float(trends_df["net_savings"].mean()), 2)

    max_exp_idx = trends_df["expense"].idxmax()
    highest_exp_month = str(trends_df.loc[max_exp_idx, "month"]) if trends_df["expense"].max() > 0 else None

    max_inc_idx = trends_df["income"].idxmax()
    highest_inc_month = str(trends_df.loc[max_inc_idx, "month"]) if trends_df["income"].max() > 0 else None

    best_sav_idx = trends_df["net_savings"].idxmax()
    best_sav_month = str(trends_df.loc[best_sav_idx, "month"])

    worst_sav_idx = trends_df["net_savings"].idxmin()
    worst_sav_month = str(trends_df.loc[worst_sav_idx, "month"])

    return {
        "total_months": total_months,
        "avg_monthly_income": avg_inc,
        "avg_monthly_expense": avg_exp,
        "avg_monthly_savings": avg_sav,
        "highest_expense_month": highest_exp_month,
        "highest_income_month": highest_inc_month,
        "best_savings_month": best_sav_month,
        "worst_savings_month": worst_sav_month,
    }


def compute_spending_trends(df: pd.DataFrame, frequency: str = "W") -> pd.DataFrame:
    """Compute rolling spending trends and moving averages for expenses.

    Resamples expense transactions at specified frequency ('D', 'W', 'M') and
    derives total amount, transaction count, average amount, and 4-period moving average.

    Args:
        df: Processed transaction DataFrame containing 'date', 'type', and 'amount'.
        frequency: Resampling frequency string (e.g. 'D', 'W', 'M').

    Returns:
        pd.DataFrame containing resampled spend trends and rolling statistics.
    """
    _validate_trend_input(df)

    output_cols = ["period", "total_amount", "transaction_count", "average_amount", "rolling_avg_amount"]

    if df.empty:
        return pd.DataFrame(columns=output_cols)

    df_clean = df[df["type"] == "Expense"].copy()
    if df_clean.empty:
        return pd.DataFrame(columns=output_cols)

    df_clean["parsed_date"] = pd.to_datetime(df_clean["date"])
    df_clean = df_clean.sort_values(by="parsed_date").set_index("parsed_date")

    # Map pandas resample frequencies safely
    freq_map = {"D": "D", "W": "W", "M": "ME", "ME": "ME", "MS": "MS"}
    resample_freq = freq_map.get(frequency.upper(), frequency)

    resampled = df_clean.resample(resample_freq).agg(
        total_amount=("amount", "sum"),
        transaction_count=("amount", "count"),
        average_amount=("amount", "mean"),
    ).fillna({"total_amount": 0.0, "transaction_count": 0, "average_amount": 0.0})

    resampled["rolling_avg_amount"] = resampled["total_amount"].rolling(window=4, min_periods=1).mean().round(2)
    resampled["total_amount"] = resampled["total_amount"].round(2)
    resampled["average_amount"] = resampled["average_amount"].round(2)

    resampled = resampled.reset_index()
    resampled["period"] = resampled["parsed_date"].dt.strftime("%Y-%m-%d")

    return resampled[output_cols]
