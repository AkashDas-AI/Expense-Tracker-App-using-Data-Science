"""
Unit Tests for Streamlit Dashboard Module

Author: Akash Das
Description: Comprehensive test coverage for dashboard data loading, inclusive date
             filtering, multi-criteria slicing, non-mutation integrity, helper utilities,
             and Plotly visualization generation.
"""

from datetime import date, datetime
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from dashboard.charts import (
    create_budget_vs_actual_chart,
    create_category_avg_median_chart,
    create_category_spending_bar_chart,
    create_category_spending_donut_chart,
    create_forecast_chart,
    create_income_vs_expense_chart,
    create_monthly_savings_chart,
    create_monthly_trends_chart,
    create_payment_method_chart,
)
from dashboard.data_processing import (
    filter_transactions,
    get_available_categories,
    get_available_payment_methods,
    get_dataset_date_bounds,
    load_dashboard_data,
)
from expense_tracker.analytics.budget_analysis import compute_budget_variance
from expense_tracker.config.settings import SAMPLE_DATA_DIR


@pytest.fixture
def sample_transactions_df() -> pd.DataFrame:
    """Fixture returning loaded sample transactions DataFrame."""
    return load_dashboard_data()


@pytest.fixture
def mock_transaction_df() -> pd.DataFrame:
    """Fixture providing a deterministic small transaction DataFrame."""
    return pd.DataFrame({
        "transaction_id": ["TXN-001", "TXN-002", "TXN-003", "TXN-004", "TXN-005"],
        "date": ["2026-01-01", "2026-01-15", "2026-02-01", "2026-02-15", "2026-03-01"],
        "type": ["Income", "Expense", "Expense", "Expense", "Income"],
        "category": ["Salary", "Rent", "Groceries", "Dining", "Freelance"],
        "amount": [50000.0, 20000.0, 5000.0, 2000.0, 15000.0],
        "payment_method": ["Bank Transfer", "UPI", "Debit Card", "UPI", "Bank Transfer"],
        "description": [
            "Monthly salary credit",
            "[UNUSUAL] Flat rent payment",
            "Supermarket grocery run",
            "Weekend family dinner",
            "[UNUSUAL] Client freelance milestone",
        ],
    })


# ==============================================================================
# 1. Data Loading and Sanitization Tests
# ==============================================================================


def test_load_dashboard_data_sample(sample_transactions_df: pd.DataFrame) -> None:
    """Verify load_dashboard_data correctly loads 5,000 records from the sample dataset."""
    assert len(sample_transactions_df) == 5000
    expected_cols = {
        "transaction_id",
        "date",
        "type",
        "category",
        "amount",
        "payment_method",
        "description",
        "parsed_date",
        "display_description",
    }
    assert expected_cols.issubset(set(sample_transactions_df.columns))


def test_load_dashboard_data_masks_unusual_marker(sample_transactions_df: pd.DataFrame) -> None:
    """Verify load_dashboard_data masks synthetic shock markers in display_description."""
    # Ensure raw descriptions may contain [UNUSUAL]
    unusual_raw = sample_transactions_df["description"].str.contains(r"\[UNUSUAL\]", regex=True)
    assert unusual_raw.sum() > 0

    # Ensure display_description strictly never contains [UNUSUAL]
    unusual_display = sample_transactions_df["display_description"].str.contains(r"\[UNUSUAL\]", regex=True)
    assert unusual_display.sum() == 0


def test_load_dashboard_data_missing_file_raises() -> None:
    """Verify FileNotFoundError is raised when target CSV does not exist."""
    with pytest.raises(FileNotFoundError):
        load_dashboard_data(Path("non_existent_directory/non_existent_file.csv"))


# ==============================================================================
# 2. Filtering Functionality and Boundary Tests
# ==============================================================================


def test_filter_transactions_pure_function(mock_transaction_df: pd.DataFrame) -> None:
    """Verify filter_transactions does not mutate the source DataFrame."""
    original_copy = mock_transaction_df.copy(deep=True)
    _ = filter_transactions(mock_transaction_df, transaction_types=["Expense"])
    pd.testing.assert_frame_equal(mock_transaction_df, original_copy)


def test_filter_transactions_inclusive_dates(mock_transaction_df: pd.DataFrame) -> None:
    """Verify start_date and end_date filters are strictly inclusive."""
    # Date window: Jan 15 to Feb 15 (should include TXN-002, TXN-003, TXN-004)
    filtered = filter_transactions(
        mock_transaction_df,
        start_date="2026-01-15",
        end_date="2026-02-15",
    )
    assert len(filtered) == 3
    assert set(filtered["transaction_id"]) == {"TXN-002", "TXN-003", "TXN-004"}


def test_filter_transactions_exact_single_day(mock_transaction_df: pd.DataFrame) -> None:
    """Verify single-day filtering where start_date == end_date."""
    filtered = filter_transactions(
        mock_transaction_df,
        start_date="2026-01-15",
        end_date="2026-01-15",
    )
    assert len(filtered) == 1
    assert filtered.iloc[0]["transaction_id"] == "TXN-002"


def test_filter_transactions_by_type(mock_transaction_df: pd.DataFrame) -> None:
    """Verify filtering by transaction type."""
    filtered_inc = filter_transactions(mock_transaction_df, transaction_types=["Income"])
    assert len(filtered_inc) == 2
    assert (filtered_inc["type"] == "Income").all()

    filtered_exp = filter_transactions(mock_transaction_df, transaction_types=["Expense"])
    assert len(filtered_exp) == 3
    assert (filtered_exp["type"] == "Expense").all()


def test_filter_transactions_by_category(mock_transaction_df: pd.DataFrame) -> None:
    """Verify filtering by categories."""
    filtered = filter_transactions(mock_transaction_df, categories=["Rent", "Dining"])
    assert len(filtered) == 2
    assert set(filtered["category"]) == {"Rent", "Dining"}


def test_filter_transactions_by_payment_method(mock_transaction_df: pd.DataFrame) -> None:
    """Verify filtering by payment methods."""
    filtered = filter_transactions(mock_transaction_df, payment_methods=["UPI"])
    assert len(filtered) == 2
    assert (filtered["payment_method"] == "UPI").all()


def test_filter_transactions_empty_result(mock_transaction_df: pd.DataFrame) -> None:
    """Verify non-matching filter returns an empty DataFrame with preserved columns."""
    filtered = filter_transactions(
        mock_transaction_df,
        categories=["Travel"],  # Not in mock
    )
    assert len(filtered) == 0
    assert list(filtered.columns) == list(mock_transaction_df.columns) + ["parsed_date"]


def test_filter_transactions_empty_input() -> None:
    """Verify filtering an empty DataFrame returns an empty DataFrame gracefully."""
    empty_df = pd.DataFrame(columns=["date", "type", "category", "amount"])
    result = filter_transactions(empty_df, start_date="2026-01-01")
    assert result.empty


# ==============================================================================
# 3. Helper Utility Tests
# ==============================================================================


def test_get_dataset_date_bounds(mock_transaction_df: pd.DataFrame) -> None:
    """Verify min and max date extraction."""
    min_d, max_d = get_dataset_date_bounds(mock_transaction_df)
    assert min_d == date(2026, 1, 1)
    assert max_d == date(2026, 3, 1)


def test_get_dataset_date_bounds_empty() -> None:
    """Verify date bounds fallback on empty DataFrame."""
    empty_df = pd.DataFrame()
    min_d, max_d = get_dataset_date_bounds(empty_df)
    assert min_d == date.today()
    assert max_d == date.today()


def test_get_available_categories(mock_transaction_df: pd.DataFrame) -> None:
    """Verify extraction of sorted categories."""
    cats = get_available_categories(mock_transaction_df)
    assert cats == ["Dining", "Freelance", "Groceries", "Rent", "Salary"]

    exp_cats = get_available_categories(mock_transaction_df, transaction_type="Expense")
    assert exp_cats == ["Dining", "Groceries", "Rent"]


def test_get_available_payment_methods(mock_transaction_df: pd.DataFrame) -> None:
    """Verify extraction of sorted payment methods."""
    pms = get_available_payment_methods(mock_transaction_df)
    assert pms == ["Bank Transfer", "Debit Card", "UPI"]


# ==============================================================================
# 4. Plotly Visualization Smoke Tests
# ==============================================================================


def test_create_income_vs_expense_chart(mock_transaction_df: pd.DataFrame) -> None:
    """Smoke test for Income vs Expense chart."""
    fig = create_income_vs_expense_chart(mock_transaction_df)
    assert isinstance(fig, go.Figure)


def test_create_monthly_trends_chart(mock_transaction_df: pd.DataFrame) -> None:
    """Smoke test for Monthly Trends chart."""
    fig = create_monthly_trends_chart(mock_transaction_df)
    assert isinstance(fig, go.Figure)


def test_create_monthly_savings_chart(mock_transaction_df: pd.DataFrame) -> None:
    """Smoke test for Monthly Savings chart."""
    fig = create_monthly_savings_chart(mock_transaction_df)
    assert isinstance(fig, go.Figure)


def test_create_category_spending_bar_chart(mock_transaction_df: pd.DataFrame) -> None:
    """Smoke test for Category Spending Bar chart."""
    fig = create_category_spending_bar_chart(mock_transaction_df)
    assert isinstance(fig, go.Figure)


def test_create_category_spending_donut_chart(mock_transaction_df: pd.DataFrame) -> None:
    """Smoke test for Category Spending Donut chart."""
    fig = create_category_spending_donut_chart(mock_transaction_df)
    assert isinstance(fig, go.Figure)


def test_create_payment_method_chart(mock_transaction_df: pd.DataFrame) -> None:
    """Smoke test for Payment Method chart."""
    fig = create_payment_method_chart(mock_transaction_df)
    assert isinstance(fig, go.Figure)


def test_create_category_avg_median_chart(mock_transaction_df: pd.DataFrame) -> None:
    """Smoke test for Mean vs Median ticket size chart."""
    fig = create_category_avg_median_chart(mock_transaction_df)
    assert isinstance(fig, go.Figure)


def test_create_budget_vs_actual_chart(mock_transaction_df: pd.DataFrame) -> None:
    """Smoke test for Budget vs Actual chart."""
    budgets = {"Rent": 22000.0, "Groceries": 4000.0}
    variance_df = compute_budget_variance(mock_transaction_df, budgets=budgets, include_unbudgeted=True)
    fig = create_budget_vs_actual_chart(variance_df)
    assert isinstance(fig, go.Figure)


def test_chart_functions_handle_empty_data() -> None:
    """Verify all chart functions return a valid go.Figure even when passed empty data."""
    empty_df = pd.DataFrame(columns=["date", "type", "category", "amount", "payment_method"])
    empty_variance = pd.DataFrame(columns=["category", "budget_amount", "actual_amount", "is_over_budget"])

    assert isinstance(create_income_vs_expense_chart(empty_df), go.Figure)
    assert isinstance(create_monthly_trends_chart(empty_df), go.Figure)
    assert isinstance(create_monthly_savings_chart(empty_df), go.Figure)
    assert isinstance(create_category_spending_bar_chart(empty_df), go.Figure)
    assert isinstance(create_category_spending_donut_chart(empty_df), go.Figure)
    assert isinstance(create_payment_method_chart(empty_df), go.Figure)
    assert isinstance(create_category_avg_median_chart(empty_df), go.Figure)
    assert isinstance(create_budget_vs_actual_chart(empty_variance), go.Figure)
    assert isinstance(create_forecast_chart(pd.Series(dtype=float), pd.DataFrame()), go.Figure)


# ==============================================================================
# 5. Budget Alert Logic & Semantics Regression Tests
# ==============================================================================


def test_get_budget_utilization_alert_tiers() -> None:
    """Verify budget utilization alert messages and severity levels."""
    from dashboard.budgets import get_budget_utilization_alert

    # Nan / Undefined
    alert_nan = get_budget_utilization_alert(np.nan)
    assert alert_nan["level"] == "INFO"

    # Exceeded / Over Budget
    alert_crit = get_budget_utilization_alert(115.5)
    assert alert_crit["level"] == "CRITICAL"
    assert "exceeded" in alert_crit["message"]

    # Approaching limit
    alert_warn = get_budget_utilization_alert(94.2)
    assert alert_warn["level"] == "WARNING"
    assert "near limit" in alert_warn["message"]

    # Healthy
    alert_ok = get_budget_utilization_alert(68.0)
    assert alert_ok["level"] == "OPTIMAL"
    assert "within limits" in alert_ok["message"]


def test_budget_semantics_zero_budget_with_positive_spending() -> None:
    """Regression Test 1: Category with explicit budget of ₹0 and positive spending is Over Budget."""
    from expense_tracker.analytics.budget_analysis import compute_budget_summary, compute_budget_variance

    spending_df = pd.DataFrame({
        "type": ["Expense"],
        "category": ["Dining"],
        "amount": [1500.0],
    })
    budgets = {"Dining": 0.0}

    var_df = compute_budget_variance(spending_df, budgets=budgets, include_unbudgeted=True)
    assert len(var_df) == 1
    row = var_df.iloc[0]
    assert row["category"] == "Dining"
    assert row["budget_amount"] == 0.0
    assert row["actual_amount"] == 1500.0
    assert row["budget_variance"] == 1500.0
    assert row["remaining_budget"] == -1500.0
    assert row["is_over_budget"] is True or row["is_over_budget"] == True

    summary = compute_budget_summary(spending_df, budgets=budgets, include_unbudgeted=True)
    assert summary["over_budget_category_count"] == 1
    assert summary["under_budget_category_count"] == 0
    assert summary["unbudgeted_category_count"] == 0


def test_budget_semantics_zero_budget_with_zero_spending() -> None:
    """Regression Test 2: Category with explicit budget of ₹0 and zero spending is Within Budget (0% util)."""
    from expense_tracker.analytics.budget_analysis import compute_budget_summary, compute_budget_variance

    spending_df = pd.DataFrame({
        "type": ["Expense"],
        "category": ["Rent"],
        "amount": [20000.0],
    })
    # Dining has an explicit ₹0 budget and zero spending in spending_df
    budgets = {"Rent": 25000.0, "Dining": 0.0}

    var_df = compute_budget_variance(spending_df, budgets=budgets, include_unbudgeted=True)
    dining_row = var_df[var_df["category"] == "Dining"].iloc[0]
    assert dining_row["budget_amount"] == 0.0
    assert dining_row["actual_amount"] == 0.0
    assert dining_row["budget_variance"] == 0.0
    assert dining_row["remaining_budget"] == 0.0
    assert dining_row["utilization_pct"] == 0.0
    assert dining_row["is_over_budget"] is False or dining_row["is_over_budget"] == False

    summary = compute_budget_summary(spending_df, budgets=budgets, include_unbudgeted=True)
    # Both Rent (20k / 25k) and Dining (0 / 0) are within budget
    assert summary["under_budget_category_count"] == 2
    assert summary["over_budget_category_count"] == 0
    assert summary["unbudgeted_category_count"] == 0


def test_budget_semantics_missing_budget_with_positive_spending() -> None:
    """Regression Test 3: Category absent from budget with positive spending is Unbudgeted (pd.NA)."""
    from expense_tracker.analytics.budget_analysis import compute_budget_summary, compute_budget_variance

    spending_df = pd.DataFrame({
        "type": ["Expense"],
        "category": ["Travel"],
        "amount": [8000.0],
    })
    # Budgets contains only Groceries; Travel is absent/unbudgeted
    budgets = {"Groceries": 5000.0}

    var_df = compute_budget_variance(spending_df, budgets=budgets, include_unbudgeted=True)
    travel_row = var_df[var_df["category"] == "Travel"].iloc[0]
    assert pd.isna(travel_row["budget_amount"])
    assert travel_row["actual_amount"] == 8000.0
    assert pd.isna(travel_row["budget_variance"])
    assert pd.isna(travel_row["remaining_budget"])
    assert pd.isna(travel_row["utilization_pct"])
    assert pd.isna(travel_row["is_over_budget"])

    summary = compute_budget_summary(spending_df, budgets=budgets, include_unbudgeted=True)
    assert summary["unbudgeted_category_count"] == 1
    assert summary["over_budget_category_count"] == 0
    assert summary["under_budget_category_count"] == 1  # Groceries (0 spent of 5000)


def test_budget_semantics_missing_budget_with_zero_spending() -> None:
    """Regression Test 4: Category absent from budget with zero spending is not assessed and not over budget."""
    from expense_tracker.analytics.budget_analysis import compute_budget_summary, compute_budget_variance

    spending_df = pd.DataFrame({
        "type": ["Expense"],
        "category": ["Rent"],
        "amount": [20000.0],
    })
    # Healthcare is absent from budgets and has 0 spending in spending_df
    budgets = {"Rent": 25000.0}

    var_df = compute_budget_variance(spending_df, budgets=budgets, include_unbudgeted=True)
    # Healthcare has no budget and 0 spend, so it is not in variance_df
    assert "Healthcare" not in var_df["category"].values

    summary = compute_budget_summary(spending_df, budgets=budgets, include_unbudgeted=True)
    assert summary["over_budget_category_count"] == 0
    assert summary["under_budget_category_count"] == 1  # Rent
    assert summary["unbudgeted_category_count"] == 0


def test_budget_semantics_summary_counts_and_chart_labels_all_cases() -> None:
    """Regression Test 5: Verify summary counts and Plotly chart labels for all 4 budget cases."""
    from expense_tracker.analytics.budget_analysis import compute_budget_summary, compute_budget_variance
    from dashboard.charts import COLOR_EXPENSE, COLOR_INCOME, COLOR_UNBUDGETED, create_budget_vs_actual_chart

    # Create dataset with all 4 scenarios:
    # 1. Shopping: explicit budget 0.0, positive spend 1200.0 -> Over Budget
    # 2. Entertainment: explicit budget 0.0, zero spend 0.0 -> Within Budget
    # 3. Travel: missing from budget, positive spend 5000.0 -> Unbudgeted (pd.NA)
    # (Healthcare: missing from budget, zero spend -> omitted)
    spending_df = pd.DataFrame({
        "type": ["Expense", "Expense"],
        "category": ["Shopping", "Travel"],
        "amount": [1200.0, 5000.0],
    })
    budgets = {
        "Shopping": 0.0,
        "Entertainment": 0.0,
    }

    var_df = compute_budget_variance(spending_df, budgets=budgets, include_unbudgeted=True)
    assert len(var_df) == 3  # Shopping, Entertainment, Travel

    summary = compute_budget_summary(spending_df, budgets=budgets, include_unbudgeted=True)
    assert summary["over_budget_category_count"] == 1   # Shopping
    assert summary["under_budget_category_count"] == 1  # Entertainment
    assert summary["unbudgeted_category_count"] == 1    # Travel

    # Generate Chart
    fig = create_budget_vs_actual_chart(var_df)
    assert isinstance(fig, go.Figure)

    # Inspect traces: trace 0 is Planned Budget, trace 1 is Actual Expenditure
    planned_trace = fig.data[0]
    actual_trace = fig.data[1]

    planned_hovers = planned_trace.customdata
    actual_hovers = actual_trace.customdata
    actual_colors = actual_trace.marker.color

    # Map categories to index in var_df
    cat_to_idx = {cat: i for i, cat in enumerate(var_df["category"])}

    # Case 1: Shopping (explicit ₹0 budget, positive spend)
    shop_idx = cat_to_idx["Shopping"]
    assert "Planned Budget: ₹0.00" in planned_hovers[shop_idx]
    assert "🚨 Over Budget" in actual_hovers[shop_idx]
    assert actual_colors[shop_idx] == COLOR_EXPENSE

    # Case 2: Entertainment (explicit ₹0 budget, zero spend)
    ent_idx = cat_to_idx["Entertainment"]
    assert "Planned Budget: ₹0.00" in planned_hovers[ent_idx]
    assert "✅ Within Budget" in actual_hovers[ent_idx]
    assert actual_colors[ent_idx] == COLOR_INCOME

    # Case 3: Travel (missing budget, positive spend)
    trav_idx = cat_to_idx["Travel"]
    assert "Planned Budget: Unbudgeted / Not Assessed" in planned_hovers[trav_idx]
    assert "⚪ Unbudgeted / Not Assessed" in actual_hovers[trav_idx]
    assert actual_colors[trav_idx] == COLOR_UNBUDGETED


def test_benchmark_presets_semantics() -> None:
    """Verify benchmark presets distinguish explicit zero budgets from omitted unbudgeted categories."""
    from dashboard.budgets import BENCHMARK_PRESETS

    # Essential Core Preset omits discretionary categories
    essential = BENCHMARK_PRESETS["Essential Core Preset (Select Categories Budgeted)"]
    assert "Rent" in essential
    assert "Groceries" in essential
    assert "Dining" not in essential
    assert "Shopping" not in essential

    # Zero-Discretionary Allocation Preset explicitly allocates ₹0.0 to discretionary categories
    zero_disc = BENCHMARK_PRESETS["Zero-Discretionary Allocation Preset (Explicit ₹0 Budget)"]
    assert zero_disc["Dining"] == 0.0
    assert zero_disc["Shopping"] == 0.0
    assert zero_disc["Entertainment"] == 0.0


# ==============================================================================
# 8. Calendar Month Budgeting and Period Alignment Tests (Phase 8 Audit)
# ==============================================================================


def test_get_available_budget_months(sample_transactions_df: pd.DataFrame) -> None:
    """Verify get_available_budget_months extracts all complete calendar months with proper defaults."""
    from dashboard.budgets import get_available_budget_months

    months, default_idx = get_available_budget_months(sample_transactions_df)

    assert len(months) == 12
    # Chronological sequence from 2025-11 to 2026-10
    assert months[0]["key"] == "2025-11"
    assert months[0]["label"] == "November 2025"
    assert months[0]["start_date"] == "2025-11-01"
    assert months[0]["end_date"] == "2025-11-30"
    assert months[0]["is_complete"] is True

    assert months[-1]["key"] == "2026-10"
    assert months[-1]["label"] == "October 2026"
    assert months[-1]["start_date"] == "2026-10-01"
    assert months[-1]["end_date"] == "2026-10-31"
    assert months[-1]["is_complete"] is True

    # Default index must point to the latest complete month (October 2026, index 11)
    assert default_idx == 11
    assert months[default_idx]["key"] == "2026-10"


def test_get_available_budget_months_empty() -> None:
    """Verify get_available_budget_months gracefully handles empty DataFrames."""
    from dashboard.budgets import get_available_budget_months

    months, default_idx = get_available_budget_months(pd.DataFrame())
    assert months == []
    assert default_idx == 0


def test_filter_budget_actuals_by_month_inclusive(sample_transactions_df: pd.DataFrame) -> None:
    """Verify filter_budget_actuals_by_month includes both the 1st and last calendar day."""
    from dashboard.budgets import filter_budget_actuals_by_month

    filtered = filter_budget_actuals_by_month(
        sample_transactions_df,
        start_date="2025-11-01",
        end_date="2025-11-30",
    )
    # Check boundary dates are present
    assert "2025-11-01" in filtered["date"].values
    assert "2025-11-30" in filtered["date"].values
    # Check no dates outside November 2025 are present
    parsed = pd.to_datetime(filtered["date"])
    assert (parsed >= pd.to_datetime("2025-11-01")).all()
    assert (parsed <= pd.to_datetime("2025-11-30")).all()
    assert len(filtered) == 427  # All 427 transactions in Nov 2025


def test_november_2025_actual_expenses_verified(sample_transactions_df: pd.DataFrame) -> None:
    """Verify November 2025 expense transactions match exactly 391 records and ₹826,899.27."""
    from dashboard.budgets import filter_budget_actuals_by_month

    nov_df = filter_budget_actuals_by_month(
        sample_transactions_df,
        start_date="2025-11-01",
        end_date="2025-11-30",
    )
    nov_exp = nov_df[nov_df["type"] == "Expense"]
    assert len(nov_exp) == 391
    assert pytest.approx(nov_exp["amount"].sum(), abs=1e-2) == 826899.27


def test_monthly_budget_comparison_isolation(sample_transactions_df: pd.DataFrame) -> None:
    """Verify monthly budget amounts are compared strictly against single-month actuals, eliminating full-year mismatch."""
    from dashboard.budgets import BENCHMARK_PRESETS, filter_budget_actuals_by_month
    from expense_tracker.analytics.budget_analysis import compute_budget_summary

    preset = BENCHMARK_PRESETS["Balanced Illustrative Benchmark (Full Portfolio)"]
    planned_budget = sum(preset.values())
    assert planned_budget == 84500.0

    # November 2025
    nov_df = filter_budget_actuals_by_month(sample_transactions_df, "2025-11-01", "2025-11-30")
    nov_exp = nov_df[nov_df["type"] == "Expense"]
    nov_summary = compute_budget_summary(nov_exp, budgets=preset, include_unbudgeted=True)

    assert nov_summary["total_budget"] == 84500.0
    assert pytest.approx(nov_summary["total_actual_spend"], abs=1e-2) == 826899.27
    assert pytest.approx(nov_summary["overall_remaining"], abs=1e-2) == -742399.27
    assert pytest.approx(nov_summary["overall_utilization_pct"], abs=1e-2) == 978.58
    # Never compares against full-year ₹9,365,016.87 (11,082.86%)
    assert nov_summary["total_actual_spend"] < 1000000.0

    # October 2026
    oct_df = filter_budget_actuals_by_month(sample_transactions_df, "2026-10-01", "2026-10-31")
    oct_exp = oct_df[oct_df["type"] == "Expense"]
    oct_summary = compute_budget_summary(oct_exp, budgets=preset, include_unbudgeted=True)

    assert oct_summary["total_budget"] == 84500.0
    assert pytest.approx(oct_summary["total_actual_spend"], abs=1e-2) == 759530.13
    assert pytest.approx(oct_summary["overall_remaining"], abs=1e-2) == -675030.13
    assert pytest.approx(oct_summary["overall_utilization_pct"], abs=1e-2) == 898.85
    # Rent is within budget in October 2026 (Actual ₹24,724.86 <= Budget ₹25,000.00)
    assert oct_summary["under_budget_category_count"] == 1
    assert oct_summary["over_budget_category_count"] == 11


def test_budget_sidebar_date_filter_isolation(sample_transactions_df: pd.DataFrame) -> None:
    """Verify that using source_df / full_df protects against narrow sidebar date ranges truncating monthly budget actuals."""
    from dashboard.budgets import filter_budget_actuals_by_month

    # Simulate a narrow 3-day sidebar filter
    narrow_filtered_df = filter_transactions(
        sample_transactions_df,
        start_date="2025-11-05",
        end_date="2025-11-07",
    )
    assert len(narrow_filtered_df) < 50

    # In budgets page, evaluation uses full_df (sample_transactions_df) for the selected calendar month
    month_df = filter_budget_actuals_by_month(
        sample_transactions_df,
        start_date="2025-11-01",
        end_date="2025-11-30",
    )
    month_exp = month_df[month_df["type"] == "Expense"]
    # Full month of 391 transactions is evaluated, not the 3-day window
    assert len(month_exp) == 391
    assert pytest.approx(month_exp["amount"].sum(), abs=1e-2) == 826899.27


def test_budget_empty_month_handled_gracefully() -> None:
    """Verify empty months or months with zero expenses are handled gracefully without exceptions."""
    from dashboard.budgets import BENCHMARK_PRESETS
    from expense_tracker.analytics.budget_analysis import compute_budget_summary, compute_budget_variance

    empty_df = pd.DataFrame(columns=["date", "type", "category", "amount", "payment_method"])
    preset = BENCHMARK_PRESETS["Balanced Illustrative Benchmark (Full Portfolio)"]

    var_df = compute_budget_variance(empty_df, budgets=preset, include_unbudgeted=True)
    assert len(var_df) == 12
    assert (var_df["actual_amount"] == 0.0).all()
    assert (var_df["utilization_pct"] == 0.0).all()
    assert (var_df["is_over_budget"] == False).all()

    summary = compute_budget_summary(empty_df, budgets=preset, include_unbudgeted=True)
    assert summary["total_budget"] == 84500.0
    assert summary["total_actual_spend"] == 0.0
    assert summary["overall_utilization_pct"] == 0.0
    assert summary["under_budget_category_count"] == 12
    assert summary["over_budget_category_count"] == 0
    assert summary["is_overall_over_budget"] is False


def test_create_budget_vs_actual_chart_with_period_label() -> None:
    """Verify create_budget_vs_actual_chart includes the period label in the chart title."""
    sample_var_df = pd.DataFrame({
        "category": ["Rent", "Groceries"],
        "budget_amount": [25000.0, 12000.0],
        "actual_amount": [24000.0, 14000.0],
        "budget_variance": [1000.0, -2000.0],
        "remaining_budget": [1000.0, 0.0],
        "utilization_pct": [96.0, 116.67],
        "is_over_budget": [False, True],
    })

    fig = create_budget_vs_actual_chart(sample_var_df, period_label="November 2025")
    assert "November 2025" in fig.layout.title.text

    fig_no_label = create_budget_vs_actual_chart(sample_var_df)
    assert "November 2025" not in fig_no_label.layout.title.text


# ==============================================================================
# 9. App to Dashboard Integration & Runtime Regression Tests
# ==============================================================================


def test_render_budgets_page_signature_accepts_full_df_and_kwargs() -> None:
    """Verify render_budgets_page signature explicitly accepts full_df, categories, payment_methods, and kwargs."""
    import inspect
    from dashboard.budgets import render_budgets_page

    sig = inspect.signature(render_budgets_page)
    params = sig.parameters

    assert "df" in params
    assert "full_df" in params
    assert "categories" in params
    assert "payment_methods" in params
    assert any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    assert params["full_df"].default is None


def test_app_to_render_budgets_page_call_site_integration(sample_transactions_df: pd.DataFrame) -> None:
    """Verify the exact app.py call site invocation of render_budgets_page executes cleanly without TypeError."""
    from contextlib import ExitStack
    from unittest.mock import MagicMock, patch
    from dashboard.budgets import render_budgets_page

    raw_df = sample_transactions_df.copy()
    filtered_df = raw_df.head(100).copy()

    def mock_columns(spec, *args, **kwargs):
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        return [MagicMock() for _ in range(n)]

    editor_df = pd.DataFrame({
        "Category": ["Rent", "Groceries"],
        "Is Budgeted": [True, True],
        "Monthly Budget (₹)": [25000.0, 12000.0],
    })

    with ExitStack() as stack:
        stack.enter_context(patch("streamlit.header"))
        stack.enter_context(patch("streamlit.caption"))
        stack.enter_context(patch("streamlit.warning"))
        stack.enter_context(patch("streamlit.info"))
        stack.enter_context(patch("streamlit.error"))
        stack.enter_context(patch("streamlit.success"))
        stack.enter_context(patch("streamlit.columns", side_effect=mock_columns))
        stack.enter_context(patch("streamlit.selectbox", side_effect=lambda label, options, *a, **k: options[0] if options else None))
        stack.enter_context(patch("streamlit.checkbox", return_value=True))
        stack.enter_context(patch("streamlit.expander"))
        stack.enter_context(patch("streamlit.data_editor", return_value=editor_df))
        stack.enter_context(patch("streamlit.metric"))
        stack.enter_context(patch("streamlit.plotly_chart"))
        stack.enter_context(patch("streamlit.dataframe"))
        stack.enter_context(patch("streamlit.markdown"))

        # Exact call signature from app.py line 153
        render_budgets_page(
            filtered_df,
            full_df=raw_df,
            categories=None,
            payment_methods=None,
        )


def test_app_main_executes_all_four_pages_without_runtime_error(sample_transactions_df: pd.DataFrame) -> None:
    """Verify app.main() executes cleanly for all 4 navigation pages without TypeError or crash."""
    from contextlib import ExitStack
    from unittest.mock import MagicMock, patch
    import app

    raw_df = sample_transactions_df.copy()

    def mock_columns(spec, *args, **kwargs):
        n = len(spec) if isinstance(spec, (list, tuple)) else int(spec)
        return [MagicMock() for _ in range(n)]

    editor_df = pd.DataFrame({
        "Category": ["Rent", "Groceries"],
        "Is Budgeted": [True, True],
        "Monthly Budget (₹)": [25000.0, 12000.0],
    })

    pages = [
        "📊 Overview",
        "💳 Spending Analysis",
        "🎯 Budget Analysis",
        "📈 Forecasting & Anomalies",
    ]

    for target_page in pages:
        with ExitStack() as stack:
            stack.enter_context(patch("app.get_cached_dashboard_data", return_value=raw_df))
            stack.enter_context(patch("streamlit.set_page_config"))
            stack.enter_context(patch("streamlit.title"))
            stack.enter_context(patch("streamlit.caption"))
            stack.enter_context(patch("streamlit.header"))
            stack.enter_context(patch("streamlit.subheader"))
            stack.enter_context(patch("streamlit.markdown"))
            stack.enter_context(patch("streamlit.warning"))
            stack.enter_context(patch("streamlit.info"))
            stack.enter_context(patch("streamlit.error"))
            stack.enter_context(patch("streamlit.success"))
            stack.enter_context(patch("streamlit.columns", side_effect=mock_columns))
            stack.enter_context(patch("streamlit.selectbox", side_effect=lambda label, options, *a, **k: options[0] if options else None))
            stack.enter_context(patch("streamlit.checkbox", return_value=True))
            stack.enter_context(patch("streamlit.expander"))
            stack.enter_context(patch("streamlit.tabs", return_value=[MagicMock(), MagicMock(), MagicMock()]))
            stack.enter_context(patch("streamlit.slider", return_value=0.02))
            stack.enter_context(patch("streamlit.data_editor", return_value=editor_df))
            stack.enter_context(patch("streamlit.metric"))
            stack.enter_context(patch("streamlit.plotly_chart"))
            stack.enter_context(patch("streamlit.dataframe"))
            stack.enter_context(patch("streamlit.sidebar.selectbox", return_value="October 2026"))
            stack.enter_context(patch("streamlit.sidebar.radio", return_value=target_page))
            stack.enter_context(patch("streamlit.sidebar.date_input", return_value=("2025-11-01", "2026-10-31")))
            stack.enter_context(patch("streamlit.sidebar.multiselect", return_value=[]))
            stack.enter_context(patch("streamlit.sidebar.markdown"))
            stack.enter_context(patch("streamlit.sidebar.caption"))

            # Execute main application routing
            app.main()


def test_streamlit_config_dark_theme() -> None:
    """Verify .streamlit/config.toml defines the professional dark theme."""
    import tomllib
    from pathlib import Path

    config_path = Path(".streamlit/config.toml")
    assert config_path.exists(), "config.toml must exist"

    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    assert "theme" in cfg, "config.toml must contain [theme] section"
    theme = cfg["theme"]
    assert theme.get("base") == "dark", "Base theme must be dark"
    assert theme.get("backgroundColor") == "#111827", "Background must be dark charcoal #111827"
    assert theme.get("secondaryBackgroundColor") == "#1f2937", "Secondary background must be #1f2937"
    assert theme.get("textColor") == "#f9fafb", "Text color must be off-white #f9fafb"
    assert theme.get("primaryColor") == "#60a5fa", "Primary accent must be professional blue #60a5fa"


def test_charts_dark_theme_attributes(sample_transactions_df: pd.DataFrame) -> None:
    """Verify dashboard charts apply consistent dark theme properties."""
    from dashboard.charts import (
        BG_CARD,
        BG_PAPER,
        BG_PLOT,
        GRID_COLOR,
        TEXT_PRIMARY,
        create_category_avg_median_chart,
        create_category_spending_bar_chart,
        create_income_vs_expense_chart,
        create_monthly_savings_chart,
        create_monthly_trends_chart,
    )

    charts = [
        create_income_vs_expense_chart(sample_transactions_df),
        create_monthly_trends_chart(sample_transactions_df),
        create_monthly_savings_chart(sample_transactions_df),
        create_category_spending_bar_chart(sample_transactions_df),
        create_category_avg_median_chart(sample_transactions_df),
    ]

    for fig in charts:
        assert fig.layout.paper_bgcolor == BG_PAPER
        assert fig.layout.plot_bgcolor == BG_PLOT
        assert fig.layout.font.color == TEXT_PRIMARY
        assert fig.layout.hoverlabel.bgcolor == BG_CARD
        assert fig.layout.xaxis.gridcolor == GRID_COLOR
        assert fig.layout.yaxis.gridcolor == GRID_COLOR


def test_chart_empty_state_dark_theme() -> None:
    """Verify empty chart states apply dark theme and readable muted annotations."""
    from dashboard.charts import BG_PAPER, BG_PLOT, TEXT_MUTED, create_income_vs_expense_chart

    empty_df = pd.DataFrame(columns=["date", "amount", "type", "category", "payment_method"])
    fig = create_income_vs_expense_chart(empty_df)

    assert fig.layout.paper_bgcolor == BG_PAPER
    assert fig.layout.plot_bgcolor == BG_PLOT
    assert len(fig.layout.annotations) > 0
    assert fig.layout.annotations[0].font.color == TEXT_MUTED




