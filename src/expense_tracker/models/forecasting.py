"""
Expense Forecasting Module

Author: Akash Das
Description: Scaffolding for time-series forecasting of upcoming expenditures.
Implementation scheduled for subsequent phases.
"""

from typing import Dict, Any
import pandas as pd


def forecast_expenses_arima(
    series: pd.Series,
    forecast_periods: int = 30,
) -> pd.DataFrame:
    """Forecast future daily/monthly expenditures using ARIMA/SARIMAX.

    Args:
        series: Historical time-series expenditure data.
        forecast_periods: Number of periods to forecast into the future.

    Returns:
        DataFrame containing forecast values and confidence intervals.

    Raises:
        NotImplementedError: Scheduled for implementation in Machine Learning phase.
    """
    raise NotImplementedError("Time-series forecasting will be implemented in subsequent phase.")


def evaluate_forecast(actual: pd.Series, predicted: pd.Series) -> Dict[str, float]:
    """Calculate forecast accuracy metrics (MAE, RMSE, MAPE).

    Args:
        actual: Ground truth expenditures.
        predicted: Model predicted expenditures.

    Returns:
        Dictionary of error metrics.

    Raises:
        NotImplementedError: Scheduled for implementation in Machine Learning phase.
    """
    raise NotImplementedError("Forecast evaluation will be implemented in subsequent phase.")

