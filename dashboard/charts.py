"""
Dashboard Plotly Visualizations Module

Author: Akash Das
Description: Interactive, accessible Plotly visualizations for the Expense Tracker dashboard
             using Indian Rupee (₹ / INR) formatting, professional dark themes, and dynamic coloring.
"""

from typing import Optional
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from expense_tracker.analytics.spending_analysis import (
    get_income_vs_expense_breakdown,
    get_spending_by_category,
    get_spending_by_payment_method,
)
from expense_tracker.analytics.trend_analysis import compute_monthly_trends

# Standard Professional Dark Theme Color Palette
COLOR_INCOME = "#10b981"      # Emerald Green (Surplus / Positive / Within Budget)
COLOR_EXPENSE = "#ef4444"     # Crimson Coral (Deficit / Outflow / Over Budget)
COLOR_SURPLUS = "#10b981"     # Emerald Green
COLOR_DEFICIT = "#ef4444"     # Rose / Crimson
COLOR_ACCENT = "#60a5fa"      # Professional Blue
COLOR_UNBUDGETED = "#94a3b8"  # Slate Grey (Unbudgeted / Neutral)
COLOR_WARNING = "#f59e0b"     # Amber

# Typography and Background Palette for Dark Theme
BG_PAPER = "rgba(0,0,0,0)"     # Transparent container integration
BG_PLOT = "rgba(0,0,0,0)"      # Transparent plot canvas
BG_CARD = "#1f2937"            # Tooltip card background (Dark Charcoal)
TEXT_PRIMARY = "#f9fafb"       # High-contrast off-white primary text
TEXT_SECONDARY = "#d1d5db"     # Light grey axis and legend text
TEXT_MUTED = "#9ca3af"         # Muted annotation text
GRID_COLOR = "#374151"         # Subtle slate gridlines
ZERO_LINE_COLOR = "#4b5563"    # Baseline zero line
TEMPLATE_THEME = "plotly_dark"


def apply_chart_theme(fig: go.Figure) -> go.Figure:
    """Apply consistent, accessible professional dark theme to a Plotly figure."""
    fig.update_layout(
        template=TEMPLATE_THEME,
        paper_bgcolor=BG_PAPER,
        plot_bgcolor=BG_PLOT,
        font=dict(color=TEXT_PRIMARY, family="sans-serif"),
        title_font=dict(color=TEXT_PRIMARY, size=15),
        legend=dict(
            font=dict(color=TEXT_SECONDARY),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(
            bgcolor=BG_CARD,
            bordercolor=GRID_COLOR,
            font=dict(color=TEXT_PRIMARY, size=13),
        ),
    )
    fig.update_xaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=ZERO_LINE_COLOR,
        tickfont=dict(color=TEXT_SECONDARY),
        title_font=dict(color=TEXT_SECONDARY),
    )
    fig.update_yaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=ZERO_LINE_COLOR,
        tickfont=dict(color=TEXT_SECONDARY),
        title_font=dict(color=TEXT_SECONDARY),
    )
    return fig


def create_income_vs_expense_chart(df: pd.DataFrame) -> go.Figure:
    """Create comparison bar chart between total income and total expense volume."""
    breakdown = get_income_vs_expense_breakdown(df)

    if breakdown.empty or breakdown["total_amount"].sum() == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No transaction data available for selected filters.",
            showarrow=False,
            font=dict(size=14, color=TEXT_MUTED),
        )
        fig.update_layout(height=350)
        return apply_chart_theme(fig)

    colors = [COLOR_INCOME if t == "Income" else COLOR_EXPENSE for t in breakdown["type"]]

    fig = go.Figure(
        data=[
            go.Bar(
                x=breakdown["type"],
                y=breakdown["total_amount"],
                marker_color=colors,
                text=[f"₹{amt:,.2f}" for amt in breakdown["total_amount"]],
                textposition="auto",
                hovertemplate="<b>%{x}</b><br>Total: ₹%{y:,.2f}<br>Share: %{customdata[0]:.1f}%<br>Transactions: %{customdata[1]:,}<extra></extra>",
                customdata=np.stack(
                    (breakdown["percentage_of_total_volume"], breakdown["transaction_count"]),
                    axis=-1,
                ),
            )
        ]
    )

    fig.update_layout(
        title="<b>Cash Flow Comparison: Income vs. Expenses</b>",
        yaxis_title="Amount (₹ INR)",
        xaxis_title=None,
        height=380,
        margin=dict(l=40, r=40, t=50, b=40),
    )
    return apply_chart_theme(fig)


def create_monthly_trends_chart(df: pd.DataFrame) -> go.Figure:
    """Create chronological dual-line/bar monthly income and expense trend chart."""
    trends = compute_monthly_trends(df)

    if trends.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No monthly trend records available for selected date range.",
            showarrow=False,
            font=dict(size=14, color=TEXT_MUTED),
        )
        fig.update_layout(height=400)
        return apply_chart_theme(fig)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=trends["month"],
            y=trends["income"],
            name="Income",
            marker_color=COLOR_INCOME,
            hovertemplate="<b>%{x}</b><br>Income: ₹%{y:,.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            x=trends["month"],
            y=trends["expense"],
            name="Expense",
            marker_color=COLOR_EXPENSE,
            hovertemplate="<b>%{x}</b><br>Expense: ₹%{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="<b>Monthly Trajectory: Income vs. Expenditure</b>",
        barmode="group",
        yaxis_title="Amount (₹ INR)",
        xaxis_title="Calendar Month",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return apply_chart_theme(fig)


def create_monthly_savings_chart(df: pd.DataFrame) -> go.Figure:
    """Create monthly net savings bar chart with surplus/deficit dynamic colors and zero baseline."""
    trends = compute_monthly_trends(df)

    if trends.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No monthly savings trend records available.",
            showarrow=False,
            font=dict(size=14, color=TEXT_MUTED),
        )
        fig.update_layout(height=380)
        return apply_chart_theme(fig)

    colors = [COLOR_SURPLUS if s >= 0 else COLOR_DEFICIT for s in trends["net_savings"]]

    hover_texts = []
    for _, row in trends.iterrows():
        status = "Surplus" if row["net_savings"] >= 0 else "Deficit"
        rate_str = f"{row['savings_rate_pct']:.2f}%" if not pd.isna(row["savings_rate_pct"]) else "N/A"
        hover_texts.append(
            f"<b>{row['month']} ({status})</b><br>"
            f"Net Savings: ₹{row['net_savings']:,.2f}<br>"
            f"Savings Rate: {rate_str}<extra></extra>"
        )

    fig = go.Figure(
        data=[
            go.Bar(
                x=trends["month"],
                y=trends["net_savings"],
                marker_color=colors,
                hovertemplate="%{customdata}",
                customdata=hover_texts,
                text=[f"₹{s:,.0f}" for s in trends["net_savings"]],
                textposition="outside",
            )
        ]
    )

    # Add reference zero horizontal line
    fig.add_hline(y=0, line_dash="dash", line_color=ZERO_LINE_COLOR, line_width=1.5)

    fig.update_layout(
        title="<b>Monthly Net Savings (Green = Capital Surplus | Red = Net Deficit)</b>",
        yaxis_title="Net Savings (₹ INR)",
        xaxis_title="Calendar Month",
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return apply_chart_theme(fig)


def create_category_spending_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create horizontal bar chart of expenses broken down by category, sorted descending."""
    cat_df = get_spending_by_category(df)

    if cat_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No expense transactions matching current filters.",
            showarrow=False,
            font=dict(size=14, color=TEXT_MUTED),
        )
        fig.update_layout(height=450)
        return apply_chart_theme(fig)

    # Sort ascending for horizontal bar chart so highest appears at top
    cat_df_sorted = cat_df.sort_values(by="total_amount", ascending=True)

    fig = go.Figure(
        data=[
            go.Bar(
                x=cat_df_sorted["total_amount"],
                y=cat_df_sorted["category"],
                orientation="h",
                marker_color="#818cf8",  # Vibrant Indigo
                text=[f"₹{a:,.2f} ({p:.1f}%)" for a, p in zip(cat_df_sorted["total_amount"], cat_df_sorted["percentage"])],
                textposition="auto",
                hovertemplate="<b>%{y}</b><br>Total Spend: ₹%{x:,.2f}<br>Share: %{customdata[0]:.2f}%<br>Count: %{customdata[1]:,}<extra></extra>",
                customdata=np.stack(
                    (cat_df_sorted["percentage"], cat_df_sorted["transaction_count"]),
                    axis=-1,
                ),
            )
        ]
    )

    fig.update_layout(
        title="<b>Expenditure by Expense Category (Descending)</b>",
        xaxis_title="Total Expenditure (₹ INR)",
        yaxis_title=None,
        height=max(400, len(cat_df) * 35),
        margin=dict(l=100, r=40, t=50, b=40),
    )
    return apply_chart_theme(fig)


def create_category_spending_donut_chart(df: pd.DataFrame) -> go.Figure:
    """Create donut chart showing percentage share of expense categories."""
    cat_df = get_spending_by_category(df)

    if cat_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No expense data available for percentage breakdown.",
            showarrow=False,
            font=dict(size=14, color=TEXT_MUTED),
        )
        fig.update_layout(height=400)
        return apply_chart_theme(fig)

    fig = px.pie(
        cat_df,
        values="total_amount",
        names="category",
        hole=0.45,
        title="<b>Expense Category Allocation (%)</b>",
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Amount: ₹%{value:,.2f}<br>Share: %{percent}<extra></extra>",
    )
    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05),
    )
    return apply_chart_theme(fig)


def create_payment_method_chart(df: pd.DataFrame) -> go.Figure:
    """Create payment method distribution chart for expenses."""
    pm_df = get_spending_by_payment_method(df, expense_only=True)

    if pm_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No payment channel records available.",
            showarrow=False,
            font=dict(size=14, color=TEXT_MUTED),
        )
        fig.update_layout(height=380)
        return apply_chart_theme(fig)

    fig = px.pie(
        pm_df,
        values="total_amount",
        names="payment_method",
        hole=0.4,
        title="<b>Expenditure by Payment Channel</b>",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Spend: ₹%{value:,.2f}<br>Share: %{percent}<br>Count: %{customdata:,}<extra></extra>",
        customdata=pm_df["transaction_count"],
    )
    fig.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return apply_chart_theme(fig)


def create_category_avg_median_chart(df: pd.DataFrame) -> go.Figure:
    """Create grouped bar chart comparing mean ticket size against median ticket size per category."""
    cat_df = get_spending_by_category(df)

    if cat_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No expense data available for ticket size comparison.",
            showarrow=False,
            font=dict(size=14, color=TEXT_MUTED),
        )
        fig.update_layout(height=400)
        return apply_chart_theme(fig)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=cat_df["category"],
            y=cat_df["average_amount"],
            name="Mean Ticket Size",
            marker_color="#38bdf8",  # Sky Blue
            hovertemplate="<b>%{x}</b><br>Mean Ticket: ₹%{y:,.2f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            x=cat_df["category"],
            y=cat_df["median_amount"],
            name="Median Ticket Size",
            marker_color="#fbbf24",  # Amber Gold
            hovertemplate="<b>%{x}</b><br>Median Ticket: ₹%{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="<b>Ticket Size Distribution: Mean vs. Median by Category</b>",
        barmode="group",
        yaxis_title="Ticket Size (₹ INR)",
        xaxis_title=None,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420,
        margin=dict(l=40, r=40, t=60, b=60),
    )
    return apply_chart_theme(fig)


def create_budget_vs_actual_chart(
    variance_df: pd.DataFrame,
    period_label: Optional[str] = None,
) -> go.Figure:
    """Create grouped bar chart comparing planned category budget against actual spend.

    Args:
        variance_df: DataFrame containing category, budget_amount, actual_amount, etc.
        period_label: Optional label for the evaluated calendar month (e.g. 'October 2026').

    Returns:
        Plotly Figure object representing category budget vs. actual expenditure.
    """
    if variance_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No budget allocations or expenditures available.",
            showarrow=False,
            font=dict(size=14, color=TEXT_MUTED),
        )
        fig.update_layout(height=420)
        return apply_chart_theme(fig)

    # Filter out or separate unbudgeted categories
    budget_col = variance_df["budget_amount"].fillna(0.0)
    actual_col = variance_df["actual_amount"].fillna(0.0)

    budget_hovers = []
    actual_hovers = []
    actual_colors = []

    for _, row in variance_df.iterrows():
        b_amt = row["budget_amount"]
        a_amt = row["actual_amount"]
        is_over = row["is_over_budget"]

        # Planned Budget bar hover: clearly distinguish explicit ₹0 budget from Unbudgeted
        if pd.isna(b_amt):
            b_label = "Unbudgeted / Not Assessed"
        else:
            b_label = f"₹{b_amt:,.2f}"
        budget_hovers.append(f"<b>{row['category']}</b><br>Planned Budget: {b_label}<extra></extra>")

        # Actual bar color and hover
        if pd.isna(is_over):
            actual_colors.append(COLOR_UNBUDGETED)
            actual_hovers.append(
                f"<b>{row['category']}</b><br>"
                f"Actual Spend: ₹{a_amt:,.2f}<br>"
                f"Status: ⚪ Unbudgeted / Not Assessed<extra></extra>"
            )
        elif is_over is True:
            actual_colors.append(COLOR_EXPENSE)
            overrun = row["budget_variance"]
            actual_hovers.append(
                f"<b>{row['category']}</b><br>"
                f"Actual Spend: ₹{a_amt:,.2f}<br>"
                f"Planned Budget: {b_label}<br>"
                f"Status: 🚨 Over Budget (+₹{overrun:,.2f})<extra></extra>"
            )
        else:
            actual_colors.append(COLOR_INCOME)
            rem = row["remaining_budget"]
            actual_hovers.append(
                f"<b>{row['category']}</b><br>"
                f"Actual Spend: ₹{a_amt:,.2f}<br>"
                f"Planned Budget: {b_label}<br>"
                f"Status: ✅ Within Budget (Remaining: ₹{rem:,.2f})<extra></extra>"
            )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=variance_df["category"],
            y=budget_col,
            name="Planned Budget",
            marker_color=COLOR_ACCENT,
            hovertemplate="%{customdata}",
            customdata=budget_hovers,
        )
    )

    fig.add_trace(
        go.Bar(
            x=variance_df["category"],
            y=actual_col,
            name="Actual Expenditure",
            marker_color=actual_colors,
            hovertemplate="%{customdata}",
            customdata=actual_hovers,
        )
    )

    title_suffix = f" ({period_label})" if period_label else ""
    fig.update_layout(
        title=f"<b>Category Budget vs. Actual Expenditure{title_suffix} (Red = Over Budget | Green = Within Budget | Grey = Unbudgeted)</b>",
        barmode="group",
        yaxis_title="Amount (₹ INR)",
        xaxis_title=None,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=450,
        margin=dict(l=40, r=40, t=60, b=60),
    )
    return apply_chart_theme(fig)


def create_forecast_chart(
    historical_series: pd.Series,
    forecast_df: pd.DataFrame,
    test_series: Optional[pd.Series] = None,
    test_forecast: Optional[pd.Series] = None,
    model_name: str = "Selected Model (7-Day Rolling Mean)",
    experimental_forecast_df: Optional[pd.DataFrame] = None,
    experimental_test_forecast: Optional[pd.Series] = None,
) -> go.Figure:
    """Create interactive time-series expenditure forecast chart with 95% confidence intervals.

    Distinguishes the selected forecast model (7-day rolling mean baseline) from experimental
    comparisons (ARIMA).

    Args:
        historical_series: Historical expenditure time series.
        forecast_df: Forward forecast DataFrame with ['forecast', 'lower_bound', 'upper_bound'].
        test_series: Optional hold-out test set actuals for visual comparison.
        test_forecast: Optional hold-out selected model predictions for visual comparison.
        model_name: Human-readable label for the selected model.
        experimental_forecast_df: Optional forward forecast from experimental ARIMA model.
        experimental_test_forecast: Optional hold-out test predictions from experimental ARIMA model.

    Returns:
        go.Figure: Interactive Plotly line chart with shaded confidence interval ribbon.
    """
    if historical_series.empty and forecast_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No historical expenditure records available for forecasting.",
            showarrow=False,
            font=dict(size=14, color=TEXT_MUTED),
        )
        fig.update_layout(height=450)
        return apply_chart_theme(fig)

    fig = go.Figure()

    # 1. Historical Actuals (display recent historical window for visual clarity if long)
    hist_to_plot = historical_series if len(historical_series) <= 90 else historical_series.iloc[-90:]
    fig.add_trace(
        go.Scatter(
            x=hist_to_plot.index,
            y=hist_to_plot.values,
            name="Historical Actual Spend",
            mode="lines+markers",
            line=dict(color="#94a3b8", width=1.8),
            marker=dict(size=4),
            hovertemplate="<b>Date: %{x|%Y-%m-%d}</b><br>Actual: ₹%{y:,.2f}<extra></extra>",
        )
    )

    # 2. Out-of-sample Test Actuals (Hold-Out Test Window)
    if test_series is not None and not test_series.empty:
        fig.add_trace(
            go.Scatter(
                x=test_series.index,
                y=test_series.values,
                name="Hold-Out Actual (Test)",
                mode="lines+markers",
                line=dict(color="#fbbf24", width=2.0),
                marker=dict(size=5, symbol="diamond"),
                hovertemplate="<b>Hold-Out Date: %{x|%Y-%m-%d}</b><br>Actual: ₹%{y:,.2f}<extra></extra>",
            )
        )

    # 3. Hold-out Test Predictions for Selected Model
    if test_forecast is not None and not test_forecast.empty:
        fig.add_trace(
            go.Scatter(
                x=test_forecast.index,
                y=test_forecast.values,
                name=f"Hold-Out Test ({model_name})",
                mode="lines",
                line=dict(color="#34d399", width=2.0, dash="dash"),
                hovertemplate=f"<b>Test Forecast: %{{x|%Y-%m-%d}}</b><br>{model_name}: ₹%{{y:,.2f}}<extra></extra>",
            )
        )

    # 4. Hold-out Test Predictions for Experimental ARIMA Model (if provided)
    if experimental_test_forecast is not None and not experimental_test_forecast.empty:
        fig.add_trace(
            go.Scatter(
                x=experimental_test_forecast.index,
                y=experimental_test_forecast.values,
                name="Hold-Out Test (Experimental ARIMA)",
                mode="lines",
                line=dict(color="#f87171", width=1.8, dash="dot"),
                hovertemplate="<b>Test Forecast: %{x|%Y-%m-%d}</b><br>ARIMA: ₹%{y:,.2f}<extra></extra>",
            )
        )

    # 5. Forward Projections and Confidence Interval Ribbon for Selected Model
    if not forecast_df.empty:
        # Lower bound boundary (invisible)
        fig.add_trace(
            go.Scatter(
                x=forecast_df.index,
                y=forecast_df["lower_bound"],
                name="95% CI Lower Bound",
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            )
        )

        # Upper bound boundary with shaded fill down to lower bound
        fig.add_trace(
            go.Scatter(
                x=forecast_df.index,
                y=forecast_df["upper_bound"],
                name="95% Display Interval (Clipped >= ₹0)",
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(52, 211, 153, 0.20)",  # Translucent Mint Green
                hovertemplate="<b>Date: %{x|%Y-%m-%d}</b><br>95% Display Interval: ₹%{customdata[0]:,.2f} to ₹%{y:,.2f}<extra></extra>",
                customdata=np.stack((forecast_df["lower_bound"],), axis=-1),
            )
        )

        # Central Selected Forecast Mean
        fig.add_trace(
            go.Scatter(
                x=forecast_df.index,
                y=forecast_df["forecast"],
                name=f"Forward Forecast ({model_name})",
                mode="lines+markers",
                line=dict(color="#34d399", width=2.5),
                marker=dict(size=5),
                hovertemplate=f"<b>Date: %{{x|%Y-%m-%d}}</b><br>{model_name}: ₹%{{y:,.2f}}<extra></extra>",
            )
        )

    # 6. Forward Projections for Experimental ARIMA Model (if provided)
    if experimental_forecast_df is not None and not experimental_forecast_df.empty:
        fig.add_trace(
            go.Scatter(
                x=experimental_forecast_df.index,
                y=experimental_forecast_df["forecast"],
                name="Forward Forecast (Experimental ARIMA)",
                mode="lines",
                line=dict(color="#a78bfa", width=2.0, dash="dashdot"),
                hovertemplate="<b>Date: %{x|%Y-%m-%d}</b><br>ARIMA: ₹%{y:,.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        title=f"<b>Expenditure Trajectory and 30-Day Forward Forecast ({model_name})</b>",
        xaxis_title="Timeline",
        yaxis_title="Expenditure (₹ INR)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=480,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return apply_chart_theme(fig)
