"""
Unit and Integration Tests for Expense Forecasting Module

Author: Akash Das
Description: Rigorous test coverage for time-series aggregation, ADF stationarity testing,
             data sufficiency evaluation, chronological train/test separation,
             baseline benchmarks, ARIMA projections, and forecast evaluation metrics.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from dashboard.charts import create_forecast_chart
from expense_tracker.models.forecasting import (
    assess_data_sufficiency,
    check_stationarity,
    evaluate_forecast,
    evaluate_model_selection_walk_forward,
    forecast_baseline,
    forecast_expenses_arima,
    forecast_expenses_rolling_mean,
    prepare_expense_time_series,
    split_time_series_chronological,
    train_arima_model,
)


@pytest.fixture
def synthetic_expense_df() -> pd.DataFrame:
    """Fixture providing 100 days of daily expense transactions."""
    np.random.seed(42)
    dates = pd.date_range("2026-01-01", periods=100, freq="D").strftime("%Y-%m-%d").tolist()

    records = []
    for i, d in enumerate(dates):
        # 80 expense days, 20 income days
        t_type = "Expense" if i % 5 != 0 else "Income"
        amt = float(np.random.uniform(500.0, 5000.0))
        records.append({
            "transaction_id": f"TXN-{i:04d}",
            "date": d,
            "type": t_type,
            "category": "Groceries" if t_type == "Expense" else "Salary",
            "amount": round(amt, 2),
        })

    return pd.DataFrame(records)


# ==============================================================================
# 1. Time Series Preparation & Data Sufficiency Tests
# ==============================================================================


def test_prepare_expense_time_series(synthetic_expense_df: pd.DataFrame) -> None:
    """Verify time-series preparation strictly isolates expenses and creates continuous daily index."""
    series = prepare_expense_time_series(synthetic_expense_df, frequency="D")
    assert isinstance(series, pd.Series)
    assert len(series) == 100
    assert isinstance(series.index, pd.DatetimeIndex)
    # On income-only days, expenses are reindexed with 0.0
    assert (series >= 0.0).all()


def test_assess_data_sufficiency() -> None:
    """Verify assessment flags 12 monthly points as insufficient and 365 daily points as sufficient."""
    # Monthly with 12 points
    short_monthly = pd.Series(np.random.uniform(1000, 5000, size=12))
    suff_m = assess_data_sufficiency(short_monthly, frequency="M")
    assert suff_m["is_sufficient"] is False
    assert "Insufficient" in suff_m["limitation_note"] or "only 12" in suff_m["limitation_note"]

    # Daily with 365 points
    full_daily = pd.Series(np.random.uniform(1000, 5000, size=365))
    suff_d = assess_data_sufficiency(full_daily, frequency="D")
    assert suff_d["is_sufficient"] is True


# ==============================================================================
# 2. Stationarity Testing (ADF)
# ==============================================================================


def test_check_stationarity(synthetic_expense_df: pd.DataFrame) -> None:
    """Verify Augmented Dickey-Fuller stationarity test execution."""
    series = prepare_expense_time_series(synthetic_expense_df, frequency="D")
    res = check_stationarity(series)

    assert "adf_statistic" in res
    assert "p_value" in res
    assert "is_stationary" in res
    assert "critical_values" in res
    assert isinstance(res["is_stationary"], bool)
    assert not np.isnan(res["adf_statistic"])


# ==============================================================================
# 3. Chronological Train/Test Separation
# ==============================================================================


def test_split_time_series_chronological(synthetic_expense_df: pd.DataFrame) -> None:
    """Verify strictly chronological train/test split with zero future-data leakage."""
    series = prepare_expense_time_series(synthetic_expense_df, frequency="D")
    train, test = split_time_series_chronological(series, test_size=0.2)

    assert len(train) == 80
    assert len(test) == 20
    # Training timestamps strictly precede test timestamps
    assert train.index.max() < test.index.min()


# ==============================================================================
# 4. Baseline Forecasting Benchmarks
# ==============================================================================


def test_forecast_baseline(synthetic_expense_df: pd.DataFrame) -> None:
    """Verify simple forecasting baselines (rolling_mean, naive, mean)."""
    series = prepare_expense_time_series(synthetic_expense_df, frequency="D")
    train, test = split_time_series_chronological(series, test_size=10)

    # Rolling mean baseline
    base_roll = forecast_baseline(train, test_periods=10, method="rolling_mean", window=7)
    assert len(base_roll) == 10
    assert base_roll.index[0] > train.index[-1]
    expected_roll = float(train.iloc[-7:].mean())
    assert np.isclose(base_roll.iloc[0], expected_roll)

    # Naive baseline
    base_naive = forecast_baseline(train, test_periods=10, method="naive")
    assert np.isclose(base_naive.iloc[0], float(train.iloc[-1]))


# ==============================================================================
# 5. ARIMA Model Training, Projections, & Confidence Intervals
# ==============================================================================


def test_forecast_expenses_arima(synthetic_expense_df: pd.DataFrame) -> None:
    """Verify experimental ARIMA forward projection and confidence interval bounds."""
    series = prepare_expense_time_series(synthetic_expense_df, frequency="D")
    forecast_df = forecast_expenses_arima(
        series,
        forecast_periods=14,
        order=(1, 1, 1),
        confidence_level=0.95,
    )

    assert isinstance(forecast_df, pd.DataFrame)
    assert len(forecast_df) == 14
    for col in ["forecast", "lower_bound", "upper_bound", "raw_lower_bound", "raw_upper_bound"]:
        assert col in forecast_df.columns

    # Verify presentation constraint: displayed lower bound is clipped to >= 0.0
    assert (forecast_df["lower_bound"] >= 0.0).all()
    # Displayed upper bounds must be >= forecast
    assert (forecast_df["upper_bound"] >= forecast_df["forecast"]).all()
    # Raw upper bound >= raw lower bound
    assert (forecast_df["raw_upper_bound"] >= forecast_df["raw_lower_bound"]).all()


def test_forecast_expenses_rolling_mean_selected_model(synthetic_expense_df: pd.DataFrame) -> None:
    """Verify selected 7-day rolling mean baseline forward projections and interval bounds."""
    series = prepare_expense_time_series(synthetic_expense_df, frequency="D")
    forecast_df = forecast_expenses_rolling_mean(
        series,
        forecast_periods=14,
        window=7,
        confidence_level=0.95,
    )

    assert isinstance(forecast_df, pd.DataFrame)
    assert len(forecast_df) == 14
    for col in ["forecast", "lower_bound", "upper_bound", "raw_lower_bound", "raw_upper_bound"]:
        assert col in forecast_df.columns

    # Value checks: forecast equals the mean of the last 7 values
    expected_mean = round(float(series.iloc[-7:].mean()), 2)
    assert np.isclose(forecast_df["forecast"].iloc[0], expected_mean)

    # Interval ordering checks
    assert (forecast_df["raw_lower_bound"] <= forecast_df["forecast"]).all()
    assert (forecast_df["forecast"] <= forecast_df["raw_upper_bound"]).all()
    assert (forecast_df["lower_bound"] <= forecast_df["forecast"]).all()
    assert (forecast_df["forecast"] <= forecast_df["upper_bound"]).all()

    # Presentation clipping: displayed lower bound must be >= 0.0
    assert (forecast_df["lower_bound"] >= 0.0).all()

    # Insufficient / empty data behavior
    empty_res = forecast_expenses_rolling_mean(pd.Series(dtype=float))
    assert empty_res.empty
    short_res = forecast_expenses_rolling_mean(pd.Series([100.0, 200.0, 300.0]))
    assert short_res.empty


def test_selected_model_beats_arima_on_holdout() -> None:
    """Verify empirically that 7-day rolling mean achieves lower hold-out MAE than ARIMA(1, 1, 1)."""
    from dashboard.data_processing import load_dashboard_data
    df = load_dashboard_data("data/sample/transactions.csv")
    series = prepare_expense_time_series(df, frequency="D")

    train_series, test_series = split_time_series_chronological(series, test_size=0.2)

    # Selected Model: 7-day rolling mean
    base_pred = forecast_baseline(train_series, len(test_series), method="rolling_mean", window=7)
    base_eval = evaluate_forecast(test_series, base_pred)

    # Experimental Model: ARIMA(1, 1, 1)
    arima_fit = train_arima_model(train_series, order=(1, 1, 1))
    arima_pred = pd.Series(arima_fit.get_forecast(steps=len(test_series)).predicted_mean.values, index=test_series.index)
    arima_eval = evaluate_forecast(test_series, arima_pred)

    # Rigorous assertion: Selected model has lower MAE on unseen test set
    assert base_eval["mae"] < arima_eval["mae"], (
        f"Expected selected rolling mean MAE ({base_eval['mae']}) < ARIMA MAE ({arima_eval['mae']})"
    )


def test_check_stationarity_overdifferencing_diagnostic(synthetic_expense_df: pd.DataFrame) -> None:
    """Verify ADF stationarity returns variance ratio and interprets unit-root null correctly."""
    series = prepare_expense_time_series(synthetic_expense_df, frequency="D")
    res = check_stationarity(series)

    assert "raw_variance" in res
    assert "first_diff_variance" in res
    assert "variance_ratio" in res
    assert not np.isnan(res["variance_ratio"])
    # Text interpretation mentions unit-root null hypothesis
    assert "unit-root null" in res["interpretation"] or "H0" in res["interpretation"]


# ==============================================================================
# 6. Forecast Evaluation Metrics & MAPE Zero-Division Handling
# ==============================================================================


def test_evaluate_forecast_metrics() -> None:
    """Verify MAE, RMSE, and MAPE calculations with safe zero handling."""
    idx = pd.date_range("2026-01-01", periods=4, freq="D")
    actual = pd.Series([100.0, 200.0, 0.0, 400.0], index=idx)
    predicted = pd.Series([110.0, 190.0, 10.0, 420.0], index=idx)

    metrics = evaluate_forecast(actual, predicted)
    assert metrics["mae"] == 12.5
    assert np.isclose(metrics["rmse"], 13.23, atol=0.01)
    assert np.isclose(metrics["mape"], 6.67, atol=0.01)


def test_mape_and_rmse_symmetry_and_holdout_consistency() -> None:
    """Verify MAPE zero handling, RMSE symmetry in both error directions, and holdout consistency."""
    # 1. Zero handling edge cases for MAPE
    idx_zeros = pd.date_range("2026-01-01", periods=3, freq="D")
    all_zero_act = pd.Series([0.0, 0.0, 0.0], index=idx_zeros)
    pred_vals = pd.Series([50.0, 100.0, 150.0], index=idx_zeros)
    zero_metrics = evaluate_forecast(all_zero_act, pred_vals)
    assert np.isnan(zero_metrics["mape"]), "All-zero actuals must evaluate to NaN MAPE"

    # 2. RMSE symmetry: over-predictions and under-predictions of equal magnitude yield identical RMSE
    idx_sym = pd.date_range("2026-01-01", periods=1, freq="D")
    over_pred = evaluate_forecast(pd.Series([100.0], index=idx_sym), pd.Series([160.0], index=idx_sym))  # +60 over
    under_pred = evaluate_forecast(pd.Series([160.0], index=idx_sym), pd.Series([100.0], index=idx_sym))  # -60 under
    assert over_pred["rmse"] == under_pred["rmse"] == 60.0, "RMSE must be symmetric in both error directions"

    # 3. Canonical holdout consistency on project sample data
    from dashboard.data_processing import load_dashboard_data
    df = load_dashboard_data("data/sample/transactions.csv")
    series = prepare_expense_time_series(df, frequency="D")
    train, test = split_time_series_chronological(series, test_size=0.2)

    roll7_pred = forecast_baseline(train, len(test), method="rolling_mean", window=7)
    naive_pred = forecast_baseline(train, len(test), method="naive")
    hist_pred = forecast_baseline(train, len(test), method="mean")
    arima_fit = train_arima_model(train, order=(1, 1, 1))
    arima_pred = pd.Series(arima_fit.get_forecast(len(test)).predicted_mean.values, index=test.index)

    ev_roll7 = evaluate_forecast(test, roll7_pred)
    ev_naive = evaluate_forecast(test, naive_pred)
    ev_hist = evaluate_forecast(test, hist_pred)
    ev_arima = evaluate_forecast(test, arima_pred)

    # Exact metrics on the 73-day holdout
    assert ev_roll7["mae"] == 9179.72
    assert ev_roll7["rmse"] == 15908.52
    assert ev_roll7["mape"] == 57.79

    assert ev_naive["mae"] == 8615.66
    assert ev_naive["rmse"] == 16129.58
    assert ev_naive["mape"] == 47.50

    assert ev_arima["mae"] == 10881.64
    assert ev_arima["rmse"] == 16554.07
    assert ev_arima["mape"] == 77.23

    assert ev_hist["mae"] == 11308.29
    assert ev_hist["rmse"] == 16781.57
    assert ev_hist["mape"] == 81.12

    # Trade-off assertions
    assert ev_naive["mae"] < ev_roll7["mae"], "Naive must have lower MAE on holdout"
    assert ev_roll7["rmse"] < ev_naive["rmse"], "Rolling-7 must have lower RMSE on holdout"
    assert ev_roll7["rmse"] < ev_arima["rmse"], "Rolling-7 must beat ARIMA on RMSE"
    assert ev_roll7["mae"] < ev_arima["mae"], "Rolling-7 must beat ARIMA on MAE"


def test_create_forecast_chart_selected_and_experimental_labels(synthetic_expense_df: pd.DataFrame) -> None:
    """Verify create_forecast_chart distinguishes selected from experimental models."""
    series = prepare_expense_time_series(synthetic_expense_df, frequency="D")
    train, test = split_time_series_chronological(series, test_size=10)
    selected_fc = forecast_expenses_rolling_mean(train, forecast_periods=10)
    arima_fc = forecast_expenses_arima(train, forecast_periods=10)

    fig = create_forecast_chart(
        historical_series=train,
        forecast_df=selected_fc,
        test_series=test,
        test_forecast=selected_fc["forecast"],
        model_name="Selected 7-Day Rolling Mean",
        experimental_forecast_df=arima_fc,
        experimental_test_forecast=arima_fc["forecast"],
    )
    assert isinstance(fig, go.Figure)
    trace_names = [t.name for t in fig.data if t.name]
    assert any("Selected" in name for name in trace_names)
    assert any("ARIMA" in name for name in trace_names)


def test_evaluate_model_selection_walk_forward() -> None:
    """Verify pre-test walk-forward validation on training data establishes model selection."""
    from dashboard.data_processing import load_dashboard_data
    df = load_dashboard_data("data/sample/transactions.csv")
    series = prepare_expense_time_series(df, frequency="D")
    train_series, _ = split_time_series_chronological(series, test_size=0.2)

    val_res = evaluate_model_selection_walk_forward(train_series, horizon=7, step=7, min_train=90)

    assert val_res["folds_evaluated"] == 28
    assert "primary_criterion" in val_res
    assert "RMSE" in val_res["primary_criterion"]
    assert val_res["selected_model"] == "7_day_rolling_mean"

    models = val_res["models"]
    assert "7_day_rolling_mean" in models
    assert "naive_baseline" in models
    assert "historical_mean" in models

    roll_metrics = models["7_day_rolling_mean"]
    naive_metrics = models["naive_baseline"]

    # Rolling mean achieved lower average RMSE on training folds
    assert roll_metrics["mean_rmse"] < naive_metrics["mean_rmse"]
    assert roll_metrics["mean_mae"] < naive_metrics["mean_mae"]

    # Insufficient data edge case
    short_series = pd.Series([100.0] * 50, index=pd.date_range("2026-01-01", periods=50, freq="D"))
    empty_res = evaluate_model_selection_walk_forward(short_series, horizon=7, step=7, min_train=90)
    assert empty_res["folds_evaluated"] == 0


