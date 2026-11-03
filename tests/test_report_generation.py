"""
Unit Tests for Report Generation, Numerical Outputs, and Visual Assets

Author: Akash Das
Description: Validates existence, schema integrity, numerical consistency,
             and visual asset validity for all generated reports and figures.
"""

import json
from pathlib import Path
import pandas as pd
from PIL import Image
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "reports" / "results"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
IMAGES_DIR = PROJECT_ROOT / "images"
REPORT_MD = PROJECT_ROOT / "reports" / "analysis_report.md"


class TestNumericalResults:
    """Validate all 8 numerical result files in reports/results/."""

    def test_all_eight_result_files_exist(self) -> None:
        """Verify all 8 numerical result files exist on disk."""
        expected_files = [
            "financial_summary.csv",
            "category_analysis.csv",
            "monthly_trends.csv",
            "budget_analysis.csv",
            "anomaly_evaluation.json",
            "forecast_evaluation.csv",
            "forecast_predictions.csv",
            "insights_summary.json",
        ]
        for fname in expected_files:
            target = RESULTS_DIR / fname
            assert target.exists(), f"Missing required result file: {fname}"
            assert target.stat().st_size > 0, f"Result file is empty: {fname}"

    def test_financial_summary_metrics(self) -> None:
        """Verify financial_summary.csv contains expected metrics and values."""
        df = pd.read_csv(RESULTS_DIR / "financial_summary.csv")
        assert "metric" in df.columns
        assert "value" in df.columns
        metrics = dict(zip(df["metric"], df["value"]))

        assert float(metrics["Total Transactions"]) == 5000.0
        assert float(metrics["Income Transactions"]) == 303.0
        assert float(metrics["Expense Transactions"]) == 4697.0
        assert float(metrics["Total Income"]) == pytest.approx(6757596.88, rel=1e-3)
        assert float(metrics["Total Expenses"]) == pytest.approx(9365016.87, rel=1e-3)
        assert float(metrics["Net Savings"]) == pytest.approx(-2607419.99, rel=1e-3)
        assert float(metrics["Savings Rate"]) == pytest.approx(-38.59, rel=1e-2)

    def test_category_analysis_schema_and_totals(self) -> None:
        """Verify category_analysis.csv schema and percentage totals."""
        df = pd.read_csv(RESULTS_DIR / "category_analysis.csv")
        expected_cols = [
            "category",
            "total_spend_inr",
            "percentage_of_total_pct",
            "transaction_count",
            "mean_amount_inr",
            "median_amount_inr",
        ]
        for col in expected_cols:
            assert col in df.columns

        assert len(df) == 12
        assert df["percentage_of_total_pct"].sum() == pytest.approx(100.0, rel=1e-2)
        assert df["total_spend_inr"].sum() == pytest.approx(9365016.87, rel=1e-3)

    def test_monthly_trends_length_and_fields(self) -> None:
        """Verify monthly_trends.csv covers 12 calendar months."""
        df = pd.read_csv(RESULTS_DIR / "monthly_trends.csv")
        assert len(df) == 12
        assert "income" in df.columns
        assert "expense" in df.columns
        assert "net_savings" in df.columns
        assert "savings_rate_pct" in df.columns
        assert df["income"].sum() == pytest.approx(6757596.88, rel=1e-3)
        assert df["expense"].sum() == pytest.approx(9365016.87, rel=1e-3)

    def test_budget_analysis_october_benchmark(self) -> None:
        """Verify budget_analysis.csv contains 12 categories plus PORTFOLIO TOTAL."""
        df = pd.read_csv(RESULTS_DIR / "budget_analysis.csv")
        assert len(df) == 13  # 12 categories + 1 total row
        total_row = df[df["category"] == "PORTFOLIO TOTAL"].iloc[0]
        assert total_row["monthly_budget_target_inr"] == 84500.0
        assert total_row["actual_spend_inr"] == pytest.approx(759530.13, rel=1e-3)
        assert bool(total_row["over_budget_flag"]) is True

    def test_anomaly_evaluation_json_structure(self) -> None:
        """Verify anomaly_evaluation.json contains valid evaluation payloads."""
        with open(RESULTS_DIR / "anomaly_evaluation.json", encoding="utf-8") as f:
            data = json.load(f)

        assert "model_name" in data
        assert data["contamination_parameter"] == 0.02
        assert data["total_anomalies_detected"] == 100
        assert "inductive_out_of_sample_evaluation" in data
        ind = data["inductive_out_of_sample_evaluation"]
        assert ind["recall"] == 1.0
        assert ind["test_ground_truth_count"] == 1

    def test_forecast_evaluation_models(self) -> None:
        """Verify forecast_evaluation.csv contains both holdout and walk-forward models."""
        df = pd.read_csv(RESULTS_DIR / "forecast_evaluation.csv")
        assert len(df) >= 7
        models = df["model_name"].tolist()
        assert "7-Day Rolling Mean Baseline" in models
        assert "ARIMA(1, 1, 1) Benchmark" in models

        prod = df[(df["model_name"] == "7-Day Rolling Mean Baseline") & (df["split_type"].str.contains("Holdout"))].iloc[0]
        assert prod["mae_inr"] == pytest.approx(9179.72, rel=1e-2)
        assert bool(prod["is_selected_production_model"]) is True

    def test_forecast_predictions_coverage(self) -> None:
        """Verify forecast_predictions.csv covers 365 historical days and 30 forecast days."""
        df = pd.read_csv(RESULTS_DIR / "forecast_predictions.csv")
        assert len(df) == 395  # 365 historical + 30 future
        assert "actual_daily_spend_inr" in df.columns
        assert "rolling_mean_forecast_inr" in df.columns
        assert "arima_forecast_inr" in df.columns
        forecast_period = df[df["period_type"] == "30-Day Forward Forecast"]
        assert len(forecast_period) == 30
        assert forecast_period["rolling_mean_forecast_inr"].notnull().all()

    def test_insights_summary_count(self) -> None:
        """Verify insights_summary.json contains 6 structured findings."""
        with open(RESULTS_DIR / "insights_summary.json", encoding="utf-8") as f:
            insights = json.load(f)
        assert len(insights) == 6
        for item in insights:
            assert "insight_id" in item
            assert "title" in item
            assert "severity" in item
            assert "observation" in item
            assert "recommendation" in item


class TestAnalyticalFigures:
    """Validate all 10 analytical figures in reports/figures/."""

    @pytest.mark.parametrize("filename", [
        "transaction_type_distribution.png",
        "expense_category_distribution.png",
        "monthly_income_expense.png",
        "payment_method_distribution.png",
        "expense_amount_distribution.png",
        "category_spending.png",
        "monthly_financial_trends.png",
        "budget_vs_actual.png",
        "anomaly_detection.png",
        "expense_forecast.png",
    ])
    def test_figure_exists_and_is_valid_image(self, filename: str) -> None:
        """Verify each analytical figure exists and is a valid PNG."""
        target = FIGURES_DIR / filename
        assert target.exists(), f"Figure missing: {filename}"
        assert target.stat().st_size > 10_000, f"Figure too small: {filename}"

        with Image.open(target) as img:
            assert img.format == "PNG"
            assert img.size[0] >= 1000
            assert img.size[1] >= 600


class TestDashboardScreenshotsAndArchitecture:
    """Validate 6 actual dashboard screenshots and architecture diagram in images/."""

    @pytest.mark.parametrize("filename", [
        "dashboard_overview.png",
        "spending_analysis.png",
        "budget_analysis.png",
        "financial_insights.png",
        "anomaly_detection.png",
        "expense_forecasting.png",
    ])
    def test_dashboard_screenshots_valid(self, filename: str) -> None:
        """Verify dashboard screenshots exist, are high resolution, and non-empty."""
        target = IMAGES_DIR / filename
        assert target.exists(), f"Screenshot missing: {filename}"
        assert target.stat().st_size > 50_000, f"Screenshot too small: {filename}"

        with Image.open(target) as img:
            assert img.format == "PNG"
            assert img.size[0] >= 1200
            assert img.size[1] >= 800

    def test_architecture_diagram_valid(self) -> None:
        """Verify architecture diagram exists and is high resolution."""
        target = IMAGES_DIR / "architecture.png"
        assert target.exists(), "Architecture diagram missing"
        assert target.stat().st_size > 50_000, "Architecture diagram too small"

        with Image.open(target) as img:
            assert img.format == "PNG"
            assert img.size[0] >= 2000
            assert img.size[1] >= 1000


class TestReportDocumentation:
    """Validate reports/analysis_report.md formatting and references."""

    def test_analysis_report_exists_and_comprehensive(self) -> None:
        """Verify analysis_report.md exists, is substantial, and contains required sections."""
        assert REPORT_MD.exists()
        text = REPORT_MD.read_text(encoding="utf-8")
        assert len(text) > 5000

        # Required sections
        assert "## 1. Executive Summary" in text
        assert "## 2. Dataset Profile" in text
        assert "## 3. Portfolio Financial Health" in text
        assert "## 4. Category Expenditure" in text
        assert "## 5. 12-Month Cash Flow" in text
        assert "## 6. Calendar Month Budget Variance Ledger" in text
        assert "## 7. Unsupervised Anomaly Detection" in text
        assert "## 8. Time-Series Expenditure Forecasting" in text
        assert "## 9. Synthesized Financial Insights" in text
        assert "## 10. Methodology Limitations" in text
        assert "## 11. Artifact Index" in text

        # Style checks: zero emojis and zero em dashes
        assert "—" not in text, "Found em dash in analysis_report.md"
        assert not any(ord(c) > 0x1F000 for c in text), "Found emoji in analysis_report.md"
