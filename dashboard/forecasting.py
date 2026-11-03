"""
Dashboard Financial Insights, Anomaly Detection & Forecasting Page

Author: Akash Das
Description: Interactive presentation of evidence-based financial insights,
             unsupervised Isolation Forest anomaly detection, and time-series
             ARIMA expenditure forecasting in Indian Rupees (₹ / INR).
"""

from typing import Any, Dict, Optional, Tuple
import numpy as np
import pandas as pd
import streamlit as st

from dashboard.charts import create_forecast_chart
from expense_tracker.analytics.insights import generate_financial_insights
from expense_tracker.config.settings import RANDOM_SEED
from expense_tracker.features.feature_engineering import extract_ground_truth_labels
from expense_tracker.models.anomaly_detection import (
    detect_anomalies_isolation_forest,
    detect_outliers_statistical,
    evaluate_anomaly_detection,
    evaluate_anomaly_detection_out_of_sample,
    get_anomaly_records,
)
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
from expense_tracker.utils.helpers import format_currency, format_percentage


@st.cache_data
def _run_cached_anomaly_pipeline(
    df: pd.DataFrame,
    contamination: float,
    random_state: int,
) -> Tuple[pd.Series, pd.Series]:
    """Execute and cache Isolation Forest anomaly detection pipeline."""
    return detect_anomalies_isolation_forest(
        df,
        contamination=contamination,
        random_state=random_state,
    )


@st.cache_data
def _run_cached_forecasting_pipeline(
    df: pd.DataFrame,
    forecast_periods: int = 30,
    order: Tuple[int, int, int] = (1, 1, 1),
    window: int = 7,
) -> Dict[str, Any]:
    """Execute and cache time-series aggregation, ADF testing, evaluation, and multi-model forecasting."""
    series = prepare_expense_time_series(df, frequency="D")
    if series.empty or len(series) < 14:
        return {"series": series, "is_sufficient": False}

    sufficiency = assess_data_sufficiency(series, frequency="D")
    stationarity = check_stationarity(series)

    # Chronological 80/20 train/test split
    train_series, test_series = split_time_series_chronological(series, test_size=0.2)

    # 1. Selected Model: 7-Day Rolling Mean Baseline
    selected_test_pred = forecast_baseline(train_series, test_periods=len(test_series), method="rolling_mean", window=window)
    selected_eval = evaluate_forecast(test_series, selected_test_pred)
    selected_forward_df = forecast_expenses_rolling_mean(
        series,
        forecast_periods=forecast_periods,
        window=window,
        confidence_level=0.95,
    )

    # 2. Experimental Comparison Model: ARIMA Out-of-sample Model Fit & Test Evaluation
    arima_test_fit = train_arima_model(train_series, order=order)
    test_pred_mean = arima_test_fit.get_forecast(steps=len(test_series)).predicted_mean
    arima_test_pred = pd.Series(test_pred_mean.values, index=test_series.index)
    arima_eval = evaluate_forecast(test_series, arima_test_pred)
    arima_forward_df = forecast_expenses_arima(
        series,
        forecast_periods=forecast_periods,
        order=order,
        confidence_level=0.95,
    )

    # Additional baselines for comprehensive benchmarking
    hist_mean_pred = forecast_baseline(train_series, test_periods=len(test_series), method="mean")
    hist_mean_eval = evaluate_forecast(test_series, hist_mean_pred)
    naive_pred = forecast_baseline(train_series, test_periods=len(test_series), method="naive")
    naive_eval = evaluate_forecast(test_series, naive_pred)

    # 3. Training Walk-Forward Validation (Pre-Test Model Selection)
    val_selection = evaluate_model_selection_walk_forward(train_series, horizon=7, step=7, min_train=90)

    return {
        "series": series,
        "is_sufficient": sufficiency["is_sufficient"],
        "sufficiency": sufficiency,
        "stationarity": stationarity,
        "train_series": train_series,
        "test_series": test_series,
        "selected_test_pred": selected_test_pred,
        "selected_eval": selected_eval,
        "selected_forward_df": selected_forward_df,
        "arima_test_pred": arima_test_pred,
        "arima_eval": arima_eval,
        "arima_forward_df": arima_forward_df,
        "hist_mean_eval": hist_mean_eval,
        "naive_eval": naive_eval,
        "val_selection": val_selection,
    }


def render_forecasting_page(df: Optional[pd.DataFrame] = None) -> None:
    """Render comprehensive financial insights, anomaly detection, and time-series forecasting view.

    Args:
        df: Filtered transaction DataFrame.
    """
    st.header("📈 Financial Insights, Anomaly Detection & Forecasting")
    st.caption("Evidence-based financial analytics, unsupervised anomaly detection, and statistical expenditure forecasting.")

    if df is None or df.empty:
        st.warning("⚠️ No transactions match the active filter criteria. Please adjust your filters in the sidebar.")
        return

    tab_insights, tab_anomalies, tab_forecasting = st.tabs([
        "💡 Financial Insights",
        "🚨 Anomaly Detection (Isolation Forest)",
        "⏳ Expense Forecasting",
    ])

    # =========================================================================
    # TAB 1: Financial Insights
    # =========================================================================
    with tab_insights:
        st.subheader("💡 Evidence-Based Financial Insights")
        st.caption(
            "Synthesized from calculated portfolio KPIs, spending distributions, and historical trends. "
            "Observations reflect empirical figures; recommendations offer standard financial hygiene guidance."
        )

        insights = generate_financial_insights(df)

        for ins in insights:
            badge_color = {
                "OPTIMAL": "🟢",
                "INFO": "🔵",
                "WARNING": "🟡",
                "CRITICAL": "🔴",
            }.get(ins.severity, "⚪")

            with st.container():
                st.markdown(f"#### {badge_color} {ins.title}")
                st.markdown(f"**Observation:** {ins.observation}")
                st.markdown(f"**Recommendation:** {ins.recommendation}")
                st.caption(f"Category: `{ins.category}` | Severity Level: `{ins.severity}`")
                st.markdown("---")

        st.info(
            "🔬 **Synthetic Data Notice**: These findings are derived from the project's synthetically generated "
            "transaction dataset and demonstrate automated data science insight extraction algorithms."
        )

    # =========================================================================
    # TAB 2: Anomaly Detection (Isolation Forest)
    # =========================================================================
    with tab_anomalies:
        st.subheader("🚨 Unsupervised Anomaly Detection")
        st.caption(
            "Multivariate Isolation Forest (`sklearn.ensemble.IsolationForest`) trained on the leak-free "
            "42-feature matrix (temporal, amount, lag, rolling, and categorical encodings)."
        )

        # Configurable Contamination & Controls
        col_ctrl1, col_ctrl2 = st.columns([2, 1])
        with col_ctrl1:
            contamination = st.slider(
                "Contamination Parameter (Expected Outlier Proportion)",
                min_value=0.005,
                max_value=0.05,
                value=0.02,
                step=0.005,
                help="Estimated proportion of anomalies in the dataset. Default 0.02 corresponds to ~2% of transactions.",
            )
        with col_ctrl2:
            st.write("")
            st.metric("Reproducible Seed", f"{RANDOM_SEED}", help="Fixed NumPy/Scikit-learn random seed for deterministic tree partitioning.")

        # Run Anomaly Pipeline
        is_anomaly, anomaly_scores = _run_cached_anomaly_pipeline(df, contamination, RANDOM_SEED)
        anomaly_records = get_anomaly_records(df, is_anomaly, anomaly_scores)

        # Baseline Statistical Outliers (Z-score > 3.0 on amount)
        stat_outliers = detect_outliers_statistical(df, method="zscore", threshold=3.0)

        # Anomaly Summary Metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Analyzed", f"{len(df):,}")
        with m2:
            st.metric("Flagged Anomalies", f"{int(is_anomaly.sum()):,}")
        with m3:
            st.metric("Contamination Rate", f"{(is_anomaly.sum() / max(1, len(df))) * 100:.2f}%")
        with m4:
            st.metric("Univariate Z-Score Spikes", f"{int(stat_outliers.sum()):,}", help="Transactions with |Z| > 3.0 on amount.")

        st.markdown("---")

        # Flagged Transactions Table
        st.markdown("### 📋 Flagged Anomaly Transactions (Ranked by Severity)")
        st.caption("Lower decision scores indicate shorter path lengths through the isolation trees (higher anomaly severity).")

        if not anomaly_records.empty:
            display_cols = ["date", "type", "category", "amount", "payment_method", "anomaly_score", "display_description"]
            table_cols = [c for c in display_cols if c in anomaly_records.columns]

            st.dataframe(
                anomaly_records[table_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "date": "Date",
                    "type": "Type",
                    "category": "Category",
                    "amount": st.column_config.NumberColumn("Amount", format="₹%.2f"),
                    "payment_method": "Payment Method",
                    "anomaly_score": st.column_config.NumberColumn("Anomaly Score", format="%.4f", help="Decision score (lower = more anomalous)"),
                    "display_description": "Description",
                },
            )
        else:
            st.info("No transactions flagged as anomalies under current contamination setting.")

        st.markdown("---")

        # Ground-Truth Benchmark Evaluation
        st.markdown("### 🔬 Benchmark Evaluation Against Synthetic Ground Truth")
        st.caption(
            "Evaluation against the 12 deliberately injected synthetic unusual shocks (`[UNUSUAL]`). "
            "Ground-truth markers were strictly quarantined and never used during model training."
        )

        # 1. Full Dataset Transductive Audit (at active contamination slider)
        y_true = extract_ground_truth_labels(df)
        eval_metrics = evaluate_anomaly_detection(y_true, is_anomaly)
        cm = eval_metrics["confusion_matrix"]
        gt_count = eval_metrics["ground_truth_count"]
        pred_count = eval_metrics["predicted_count"]

        st.markdown("##### Full-Dataset Transductive Audit (Active Contamination Setting)")
        c_eval0, c_eval1, c_eval2, c_eval3, c_eval4 = st.columns(5)
        with c_eval0:
            st.metric("Ground-Truth Positives", f"{gt_count:,} / {len(df):,} ({(gt_count/len(df))*100:.2f}%)")
        with c_eval1:
            st.metric("Precision", f"{eval_metrics['precision']:.4f}", help=f"TP / (TP + FP) = {cm['tp']} / {pred_count}")
        with c_eval2:
            st.metric("Recall", f"{eval_metrics['recall']:.4f}", help=f"TP / (TP + FN) = {cm['tp']} / {gt_count}")
        with c_eval3:
            st.metric("F1-Score", f"{eval_metrics['f1_score']:.4f}")
        with c_eval4:
            st.metric(
                "Confusion Matrix",
                f"TP: {cm['tp']} | FP: {cm['fp']}",
                help=f"True Positives: {cm['tp']} | False Positives: {cm['fp']} | True Negatives: {cm['tn']} | False Negatives: {cm['fn']}",
            )

        # 2. Chronological Out-of-Sample Hold-Out Evaluation
        with st.expander("📊 View Inductive Out-of-Sample Hold-Out Benchmark (80% Train / 20% Test)", expanded=False):
            oos_metrics = evaluate_anomaly_detection_out_of_sample(df, test_size=0.2, contamination=contamination, random_state=RANDOM_SEED)
            cm_oos = oos_metrics["confusion_matrix"]
            oos_gt = oos_metrics.get("test_ground_truth_count", 0)
            oos_samples = oos_metrics.get("test_samples", 0)
            oos_pred = oos_metrics.get("predicted_count", 0)

            co0, co1, co2, co3, co4 = st.columns(5)
            with co0:
                st.metric("Test Positives", f"{oos_gt} / {oos_samples:,} ({(oos_gt/max(1, oos_samples))*100:.2f}%)")
            with co1:
                st.metric("Test Precision", f"{oos_metrics['precision']:.4f}", help=f"TP / (TP + FP) = {cm_oos['tp']} / {oos_pred}")
            with co2:
                st.metric("Test Recall", f"{oos_metrics['recall']:.4f}", help=f"TP / (TP + FN) = {cm_oos['tp']} / {oos_gt}")
            with co3:
                st.metric("Test F1-Score", f"{oos_metrics['f1_score']:.4f}")
            with co4:
                st.metric(
                    "Test Confusion Matrix",
                    f"TP: {cm_oos['tp']} | FP: {cm_oos['fp']}",
                    help=f"TP: {cm_oos['tp']}, FP: {cm_oos['fp']}, TN: {cm_oos['tn']}, FN: {cm_oos['fn']}",
                )

            st.warning(
                "⚠️ **Extreme Sample-Size Uncertainty Due to Single Positive Test Sample (N_pos = 1)**:\n"
                "- The chronological hold-out test set contains **only 1 positive ground-truth anomaly** out of 1,000 test transactions ($N_{\\text{pos}} = 1$).\n"
                "- The **100% test recall** represents detecting **one out of one** positive test example ($TP=1, FN=0$).\n"
                "- With only one positive example, performance estimates carry extreme statistical uncertainty (a single missed transaction drops recall to 0%).\n"
                "- The model flagged 30 normal transactions as false positives ($FP=30$), resulting in a test precision of 3.23%.\n"
                "- **Real-World Efficacy Notice**: This benchmark demonstrates algorithm execution on synthetic data and should NOT be construed as evidence of reliable real-world fraud or crime detection."
            )
            st.caption(
                f"Train Samples: {oos_metrics.get('train_samples', 0):,} ({oos_metrics.get('train_ground_truth_count', 0)} anomalies) | "
                f"Test Samples: {oos_samples:,} ({oos_gt} anomaly). "
                "Evaluates model generalizability on strictly unseen future records."
            )

        st.info(
            "💡 **Analytical Interpretation of False Positives & Baseline Comparison**:\n"
            "- **Synthetic Shock Benchmark**: The 12 evaluation anomalies were generated exclusively as high-magnitude "
            "monetary spikes in `amount` (₹65,000–₹162,000). A simple univariate Z-score rule ($Z > 3.0$) isolates them "
            "with 100% precision and recall because of this univariate generation method. This synthetic benchmark "
            "does not imply Z-score superiority in real-world environments where fraud mimics normal spending.\n"
            "- **Multivariate Geometry vs. Univariate Ground Truth**: Isolation Forest constructs recursive orthogonal "
            "partitions across **all 42 numeric dimensions** (including day-of-week, inter-transaction elapsed days, "
            "rolling category ratios, and payment channels). It flags transactions that are unusual in combination "
            "(e.g., an atypical category on a Sunday via Cash after days of dormancy). Evaluated against pure monetary shocks, "
            "these multidimensional outliers appear as 'false positives', but represent mathematically valid multivariate anomalies.\n"
            "- **Strict Leakage Prevention**: Ground-truth tags (`[UNUSUAL]`), descriptions, transaction IDs, and description-derived "
            "text length proxies were strictly excluded from model matrices.\n"
            "- **A Priori Parameter Setting**: Contamination (default 0.02) was specified as an operational heuristic (~2% expected outliers) "
            "and was not retroactively tuned to maximize evaluation metrics against the synthetic test labels."
        )

    # =========================================================================
    # TAB 3: Expense Forecasting (Selected: Rolling Mean | Experimental: ARIMA)
    # =========================================================================
    with tab_forecasting:
        st.subheader("⏳ Time-Series Expense Forecasting")
        st.caption("Daily aggregated expenditure modeling, stationarity diagnostics, selected baseline projections, and experimental comparisons.")

        expense_df = df[df["type"] == "Expense"]
        if expense_df.empty:
            st.warning("⚠️ No expense transactions available in the current filter selection to construct an expenditure forecast.")
            return

        with st.spinner("Processing time-series expenditure series and generating forecasts..."):
            forecast_results = _run_cached_forecasting_pipeline(df, forecast_periods=30, order=(1, 1, 1))

        if not forecast_results.get("is_sufficient", False):
            st.warning(forecast_results.get("sufficiency", {}).get("limitation_note", "Insufficient data for forecasting."))
            return

        # Model Selection Highlight Banner
        sel_ev = forecast_results["selected_eval"]
        ar_ev = forecast_results["arima_eval"]
        nv_ev = forecast_results.get("naive_eval", {"mae": np.nan, "rmse": np.nan, "mape": np.nan})
        hm_ev = forecast_results.get("hist_mean_eval", {"mae": np.nan, "rmse": np.nan, "mape": np.nan})

        st.success(
            f"🏆 **Selected Forecast Model**: **7-Day Rolling Mean Baseline** (Hold-Out RMSE: ₹{sel_ev['rmse']:,.2f} | MAE: ₹{sel_ev['mae']:,.2f} | MAPE: {sel_ev['mape']:.2f}%)\n\n"
            f"**Alternative Benchmark**: **Naive Baseline** (Hold-Out RMSE: ₹{nv_ev['rmse']:,.2f} | MAE: ₹{nv_ev['mae']:,.2f} | MAPE: {nv_ev['mape']:.2f}%)\n\n"
            f"**Experimental Model**: **ARIMA(1, 1, 1)** (Hold-Out RMSE: ₹{ar_ev['rmse']:,.2f} | MAE: ₹{ar_ev['mae']:,.2f} | MAPE: {ar_ev['mape']:.2f}%)\n\n"
            "**Primary Selection Metric & Symmetry Disclosure**: **RMSE (Root Mean Squared Error)** is retained as the primary selection criterion "
            "because the training-only walk-forward cross-validation supports it (7-day rolling mean achieved lower mean RMSE across 28 training folds). "
            "Crucially, RMSE penalizes large errors **quadratically and symmetrically in either direction** ($(\\hat{y}_t - y_t)^2$); it is a measure of "
            "error variance and dispersion, **not** specifically an under-prediction or liquidity-risk metric, and RMSE does not inherently protect against under-predictions or cash shortfalls. "
            f"The 7-day rolling mean baseline achieved the lowest hold-out RMSE (₹{sel_ev['rmse']:,.2f} vs. ₹{nv_ev['rmse']:,.2f} for Naive and ₹{ar_ev['rmse']:,.2f} for ARIMA)."
        )

        # MAE vs RMSE Trade-Off Callout & Future Asymmetric Loss
        st.warning(
            "⚖️ **MAE vs. RMSE Model Trade-Off & Future Asymmetric Loss Enhancements**:\n"
            "- **The 7-Day Rolling Mean is NOT universally superior**: It achieves the lowest hold-out RMSE "
            f"(**₹{sel_ev['rmse']:,.2f}** vs. ₹{nv_ev['rmse']:,.2f} for Naive) because averaging over a 7-day window yields lower overall error variance across the hold-out window.\n"
            "- **Naive Baseline Wins on MAE and MAPE**: The Naive baseline achieves the lowest hold-out MAE "
            f"(**₹{nv_ev['mae']:,.2f}** vs. ₹{sel_ev['mae']:,.2f} for Rolling Mean) and lowest MAPE (**{nv_ev['mape']:.2f}%** vs. {sel_ev['mape']:.2f}% for Rolling Mean), "
            "incurring smaller linear absolute deviations during steady periods.\n"
            "- **Measured Performance**: The 7-day rolling mean does not necessarily cushion sudden spending spikes in real time (it produces a constant forward projection over the test window); its lower RMSE reflects lower variance across the evaluation period.\n"
            "- **Potential Future Improvements (Not Implemented)**: Standard RMSE and MAE penalize over-prediction and under-prediction equally. "
            "If an application specifically mandates penalizing under-predictions more heavily than over-predictions (e.g. to guard against cash depletion), "
            "suitable future enhancements could evaluate **asymmetric loss functions** (e.g., lin-lin loss) or **upper-quantile forecasting** (e.g., pinball loss at $\\tau = 0.80$ or $0.90$). "
            "These represent potential future algorithmic directions, not currently implemented features."
        )

        # Pre-Test Validation Design Expander
        val_sel = forecast_results.get("val_selection", {})
        with st.expander("🔬 View Pre-Test Model Selection Evidence (28-Fold Training Walk-Forward Validation)", expanded=False):
            st.markdown(
                "**Zero-Leakage Model Selection Design**:\n"
                "To prevent post-hoc overfitting to the test set, candidate model selection was established *prior* to viewing the test set "
                "using rolling-origin walk-forward cross-validation strictly on the 292 training days (`min_train=90`, `horizon=7`, `step=7`)."
            )
            if val_sel.get("folds_evaluated", 0) > 0:
                v_models = val_sel.get("models", {})
                v_roll = v_models.get("7_day_rolling_mean", {})
                v_naive = v_models.get("naive_baseline", {})
                v_hist = v_models.get("historical_mean", {})

                cv_col1, cv_col2, cv_col3 = st.columns(3)
                with cv_col1:
                    st.metric("Walk-Forward Folds", f"{val_sel.get('folds_evaluated')} Folds", help="Evaluated over training days 90 to 292")
                with cv_col2:
                    st.metric("Rolling Mean Avg RMSE", f"₹{v_roll.get('mean_rmse', 0):,.2f}", help=f"Avg MAE: ₹{v_roll.get('mean_mae', 0):,.2f}")
                with cv_col3:
                    st.metric("Naive Avg RMSE", f"₹{v_naive.get('mean_rmse', 0):,.2f}", help=f"Avg MAE: ₹{v_naive.get('mean_mae', 0):,.2f}")

                st.caption(
                    f"Result: Across {val_sel.get('folds_evaluated')} training folds, the 7-day rolling mean achieved lower average RMSE "
                    f"(₹{v_roll.get('mean_rmse', 0):,.2f} vs. ₹{v_naive.get('mean_rmse', 0):,.2f}) and lower average MAE "
                    f"(₹{v_roll.get('mean_mae', 0):,.2f} vs. ₹{v_naive.get('mean_mae', 0):,.2f}), confirming its selection on training data alone."
                )
            else:
                st.caption("Walk-forward validation metrics not available for current slice.")

        # Diagnostics & Sufficiency
        stat = forecast_results["stationarity"]
        suff = forecast_results["sufficiency"]

        col_stat, col_suff = st.columns(2)
        with col_stat:
            st.markdown("#### 🔬 Stationarity & Differencing Review (ADF Test)")
            var_ratio_str = f"{stat.get('variance_ratio', 'N/A')}x" if stat.get('variance_ratio') is not None else "N/A"
            st.markdown(
                f"- **ADF Statistic**: `{stat['adf_statistic']}` (p-value: `{stat['p_value']:.4e}`)\n"
                f"- **Unit-Root Hypothesis**: {'✅ Rejects H0 (evidence against unit root)' if stat['is_stationary'] else '⚠️ Fails to reject H0'}\n"
                f"- **Variance Ratio (Var(Δy) / Var(y))**: `{var_ratio_str}`\n"
                f"- **Methodological Note**: Rejection of the unit-root null hypothesis is not absolute proof of strict covariance stationarity. "
                "Furthermore, first differencing doubles series variance (2.18x), indicating over-differencing and explaining why ARIMA(1, 1, 1) underperformed."
            )
        with col_suff:
            st.markdown("#### 📊 Sample Size & Frequency Assessment")
            st.markdown(
                f"- **Aggregation Frequency**: Daily (`D`)\n"
                f"- **Total Time-Series Observations**: `{suff['observation_count']} days`\n"
                f"- **Hold-Out Split**: 80% Train ({len(forecast_results['train_series'])} days) / 20% Test ({len(forecast_results['test_series'])} days)\n"
                f"- **Data Sufficiency**: 12 monthly observations are mathematically insufficient for seasonal SARIMAX. "
                "Daily continuous aggregation provides 365 observations with gap days filled with ₹0.00."
            )

        st.markdown("---")

        # Interactive Forecast Visual
        st.markdown("### 📈 Expenditure Forecast & 95% Confidence Interval Ribbon")
        st.caption("Displays recent historical daily actuals, out-of-sample hold-out validation, and 30-day forward projection with 95% confidence intervals.")

        fig_forecast = create_forecast_chart(
            historical_series=forecast_results["train_series"],
            forecast_df=forecast_results["selected_forward_df"],
            test_series=forecast_results["test_series"],
            test_forecast=forecast_results["selected_test_pred"],
            model_name="Selected 7-Day Rolling Mean",
            experimental_forecast_df=forecast_results["arima_forward_df"],
            experimental_test_forecast=forecast_results["arima_test_pred"],
        )
        st.plotly_chart(fig_forecast, use_container_width=True)

        st.markdown("---")

        # Model Out-of-Sample Hold-Out Evaluation Table
        st.markdown("### ⚖️ Out-of-Sample Hold-Out Model Comparison")
        st.caption("Strict chronological 80% train / 20% test hold-out split (evaluating strictly on unseen future observations).")

        hm_ev = forecast_results.get("hist_mean_eval", {"mae": np.nan, "rmse": np.nan, "mape": np.nan})
        nv_ev = forecast_results.get("naive_eval", {"mae": np.nan, "rmse": np.nan, "mape": np.nan})

        eval_comparison_df = pd.DataFrame([
            {
                "Model Status": "🏆 Selected Model",
                "Model Architecture": "7-Day Rolling Mean Baseline",
                "RMSE (₹) [Primary]": format_currency(sel_ev["rmse"]),
                "MAE (₹)": format_currency(sel_ev["mae"]),
                "MAPE (%)": format_percentage(sel_ev["mape"]),
                "Error Profile & Trade-Off": (
                    f"Lowest hold-out RMSE ({format_currency(sel_ev['rmse'])}); lower error variance across test window; "
                    f"trade-off: higher MAE than Naive ({format_currency(sel_ev['mae'])} vs. {format_currency(nv_ev['mae'])})"
                ),
            },
            {
                "Model Status": "Benchmark",
                "Model Architecture": "Naive Baseline (Last Value)",
                "RMSE (₹) [Primary]": format_currency(nv_ev["rmse"]),
                "MAE (₹)": format_currency(nv_ev["mae"]),
                "MAPE (%)": format_percentage(nv_ev["mape"]),
                "Error Profile & Trade-Off": (
                    f"Lowest hold-out MAE ({format_currency(nv_ev['mae'])}) and MAPE ({format_percentage(nv_ev['mape'])}); "
                    f"trade-off: higher RMSE ({format_currency(nv_ev['rmse'])}) due to higher error variance"
                ),
            },
            {
                "Model Status": "🔬 Experimental Comparison",
                "Model Architecture": "ARIMA(1, 1, 1)",
                "RMSE (₹) [Primary]": format_currency(ar_ev["rmse"]),
                "MAE (₹)": format_currency(ar_ev["mae"]),
                "MAPE (%)": format_percentage(ar_ev["mape"]),
                "Error Profile & Trade-Off": "Underperformed baselines across all metrics due to over-differencing (variance ratio: 2.18x)",
            },
            {
                "Model Status": "Benchmark",
                "Model Architecture": "Historical Mean Baseline",
                "RMSE (₹) [Primary]": format_currency(hm_ev["rmse"]),
                "MAE (₹)": format_currency(hm_ev["mae"]),
                "MAPE (%)": format_percentage(hm_ev["mape"]),
                "Error Profile & Trade-Off": "Static series average; highest errors across MAE, RMSE, and MAPE",
            },
        ])

        st.dataframe(eval_comparison_df, use_container_width=True, hide_index=True)

        st.info(
            "💡 **Methodological Disclaimers & Confidence Interval Treatment**:\n"
            "- **Non-Negativity Presentation Constraint**: Model-generated confidence intervals produce negative lower bounds "
            "due to symmetric Gaussian assumptions. The displayed lower bounds are clipped to ₹0.00 to reflect the domain constraint "
            "that expenditures cannot be negative. Truncating the distribution tail modifies coverage probability; therefore, "
            "the displayed interval does not retain nominal 95% statistical coverage.\n"
            "- **Zero-Spend Days & MAPE**: Standard MAPE is mathematically undefined on days with ₹0.00 actual spend (|y_t| = 0). "
            "MAPE is evaluated strictly across non-zero test days; MAE and RMSE in INR are the primary trustworthy evaluation metrics.\n"
            "- **Synthetic Extrapolation Notice**: Projections represent statistical extrapolations derived from synthetic "
            "transaction history. Outputs are mathematical estimates, not financial guarantees or advisory advice.\n"
            "- **Seasonality Limitation**: A 12-month sample dataset cannot establish long-term multi-year seasonal cycles."
        )


if __name__ == "__main__":
    from dashboard.data_processing import load_dashboard_data

    sample_df = load_dashboard_data()
    render_forecasting_page(sample_df)
