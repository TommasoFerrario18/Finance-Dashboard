"""
Visualization utilities for creating charts and graphs.

This module provides reusable chart creation functions using Plotly.
"""

from datetime import datetime
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class ChartFactory:
    """Factory class for creating various chart types."""

    # Color schemes
    COLORS = {
        "primary": "#1f77b4",
        "success": "#2ecc71",
        "danger": "#e74c3c",
        "warning": "#f39c12",
        "info": "#3498db",
        "purple": "#9b59b6",
        "teal": "#1abc9c",
        "orange": "#e67e22",
    }

    ASSET_TYPE_COLORS = {
        "Mutual Fund": "#3498db",
        "ETF": "#2ecc71",
        "Stock": "#e74c3c",
        "Bond": "#f39c12",
        "Crypto": "#9b59b6",
        "Real Estate": "#1abc9c",
        "Cash": "#95a5a6",
        "Other": "#34495e",
    }

    @staticmethod
    def create_net_worth_chart(history: list[dict[str, Any]]) -> go.Figure:
        """
        Create a net worth over time chart.

        Args:
            history: List of portfolio history records

        Returns:
            Plotly figure
        """
        df = pd.DataFrame(history)
        df["date"] = pd.to_datetime(df["date"])

        fig = go.Figure()

        # Total Value line
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["total_value"],
                name="Net Worth",
                mode="lines+markers",
                line={"color": ChartFactory.COLORS["success"], "width": 3},
                marker={"size": 8},
                fill="tonexty",
                fillcolor="rgba(46, 204, 113, 0.1)",
            )
        )

        # Total Invested line
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["total_invested"],
                name="Total Invested",
                mode="lines",
                line={"color": ChartFactory.COLORS["info"], "width": 2, "dash": "dash"},
            )
        )

        fig.update_layout(
            title="Net Worth Over Time",
            xaxis_title="Date",
            yaxis_title="Value (€)",
            hovermode="x unified",
            template="plotly_white",
            height=500,
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        )

        return fig

    @staticmethod
    def create_profit_loss_chart(history: list[dict[str, Any]]) -> go.Figure:
        """
        Create a profit/loss over time chart.

        Args:
            history: List of portfolio history records

        Returns:
            Plotly figure
        """
        df = pd.DataFrame(history)
        df["date"] = pd.to_datetime(df["date"])

        # Color bars based on positive/negative
        colors = [
            ChartFactory.COLORS["success"] if val >= 0 else ChartFactory.COLORS["danger"] for val in df["profit_loss"]
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["profit_loss"],
                name="Profit/Loss",
                marker_color=colors,
                text=df["profit_loss"].apply(lambda x: f"€{x:,.0f}"),
                textposition="outside",
            )
        )

        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        fig.update_layout(
            title="Profit/Loss Over Time",
            xaxis_title="Date",
            yaxis_title="Profit/Loss (€)",
            template="plotly_white",
            height=400,
            showlegend=False,
        )

        return fig

    @staticmethod
    def create_allocation_pie_chart(allocation: list[dict[str, Any]]) -> go.Figure:
        """
        Create an asset allocation pie chart.

        Args:
            allocation: List of asset allocation records

        Returns:
            Plotly figure
        """
        df = pd.DataFrame(allocation)

        # Get colors for each asset type
        colors = [ChartFactory.ASSET_TYPE_COLORS.get(at, ChartFactory.COLORS["primary"]) for at in df["asset_type"]]

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=df["asset_type"],
                    values=df["total_value"],
                    hole=0.4,
                    marker={"colors": colors},
                    textinfo="label+percent",
                    textposition="outside",
                    hovertemplate="<b>%{label}</b><br>"
                    + "Value: €%{value:,.2f}<br>"
                    + "Percentage: %{percent}<br>"
                    + "<extra></extra>",
                )
            ]
        )

        fig.update_layout(
            title="Asset Allocation",
            template="plotly_white",
            height=450,
            annotations=[{"text": "Portfolio", "x": 0.5, "y": 0.5, "font_size": 20, "showarrow": False}],
        )

        return fig

    @staticmethod
    def create_allocation_bar_chart(allocation: list[dict[str, Any]]) -> go.Figure:
        """
        Create an asset allocation horizontal bar chart.

        Args:
            allocation: List of asset allocation records

        Returns:
            Plotly figure
        """
        df = pd.DataFrame(allocation)
        df = df.sort_values("total_value", ascending=True)

        colors = [ChartFactory.ASSET_TYPE_COLORS.get(at, ChartFactory.COLORS["primary"]) for at in df["asset_type"]]

        fig = go.Figure(
            go.Bar(
                x=df["total_value"],
                y=df["asset_type"],
                orientation="h",
                marker_color=colors,
                text=df["total_value"].apply(lambda x: f"€{x:,.0f}"),
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Value: €%{x:,.2f}<extra></extra>",
            )
        )

        fig.update_layout(
            title="Asset Allocation by Value",
            xaxis_title="Value (€)",
            yaxis_title="",
            template="plotly_white",
            height=max(300, len(df) * 60),
            showlegend=False,
        )

        return fig

    @staticmethod
    def create_performance_comparison_chart(summary: list[dict[str, Any]]) -> go.Figure:
        """
        Create invested vs countervalue comparison chart.

        Args:
            summary: List of portfolio summary records

        Returns:
            Plotly figure
        """
        df = pd.DataFrame(summary)
        df = df.sort_values("return_percentage", ascending=True)

        fig = go.Figure()

        # Invested amounts
        fig.add_trace(
            go.Bar(
                name="Invested",
                y=df["name"],
                x=df["amount_invested"],
                orientation="h",
                marker_color=ChartFactory.COLORS["info"],
                text=df["amount_invested"].apply(lambda x: f"€{x:,.0f}"),
                textposition="inside",
            )
        )

        # Current values
        fig.add_trace(
            go.Bar(
                name="Current Value",
                y=df["name"],
                x=df["countervalue"],
                orientation="h",
                marker_color=ChartFactory.COLORS["success"],
                text=df["countervalue"].apply(lambda x: f"€{x:,.0f}"),
                textposition="inside",
            )
        )

        fig.update_layout(
            title="Invested vs Current Value by Asset",
            xaxis_title="Value (€)",
            yaxis_title="",
            template="plotly_white",
            height=max(400, len(df) * 50),
            barmode="group",
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        )

        return fig

    @staticmethod
    def create_returns_heatmap(summary: list[dict[str, Any]]) -> go.Figure:
        """
        Create a returns heatmap by asset.

        Args:
            summary: List of portfolio summary records

        Returns:
            Plotly figure
        """
        df = pd.DataFrame(summary)
        df = df.sort_values("return_percentage", ascending=False)

        # Color scale: red for negative, green for positive
        df["return_percentage"].apply(
            lambda x: ChartFactory.COLORS["danger"] if x < 0 else ChartFactory.COLORS["success"]
        )

        fig = go.Figure(
            go.Bar(
                x=df["return_percentage"],
                y=df["name"],
                orientation="h",
                marker={
                    "color": df["return_percentage"],
                    "colorscale": [[0, "#e74c3c"], [0.5, "#f39c12"], [1, "#2ecc71"]],
                    "showscale": True,
                    "colorbar": {"title": "Return %"},
                },
                text=df["return_percentage"].apply(lambda x: f"{x:.1f}%"),
                textposition="outside",
            )
        )

        fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)

        fig.update_layout(
            title="Return Performance by Asset",
            xaxis_title="Return (%)",
            yaxis_title="",
            template="plotly_white",
            height=max(400, len(df) * 50),
            showlegend=False,
        )

        return fig

    @staticmethod
    def create_income_expense_chart(transactions: list) -> go.Figure:
        """
        Create income vs expenses trend chart.

        Args:
            transactions: List of monthly transactions

        Returns:
            Plotly figure
        """
        data = [
            {"date": t.date, "income": t.income, "expenses": t.expenses, "net": t.net_cashflow} for t in transactions
        ]

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])

        fig = go.Figure()

        # Income bars
        fig.add_trace(
            go.Bar(
                name="Income",
                x=df["date"],
                y=df["income"],
                marker_color=ChartFactory.COLORS["success"],
            )
        )

        # Expenses bars
        fig.add_trace(
            go.Bar(
                name="Expenses",
                x=df["date"],
                y=df["expenses"],
                marker_color=ChartFactory.COLORS["danger"],
            )
        )

        # Net cashflow line
        fig.add_trace(
            go.Scatter(
                name="Net Cashflow",
                x=df["date"],
                y=df["net"],
                mode="lines+markers",
                line={"color": ChartFactory.COLORS["purple"], "width": 3},
                marker={"size": 8},
                yaxis="y2",
            )
        )

        fig.update_layout(
            title="Income vs Expenses Over Time",
            xaxis_title="Date",
            yaxis_title="Amount (€)",
            yaxis2={"title": "Net Cashflow (€)", "overlaying": "y", "side": "right"},
            template="plotly_white",
            height=500,
            barmode="group",
            hovermode="x unified",
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        )

        return fig

    @staticmethod
    def create_savings_rate_chart(transactions: list) -> go.Figure:
        """
        Create savings rate chart.

        Args:
            transactions: List of monthly transactions

        Returns:
            Plotly figure
        """
        data = []
        for t in transactions:
            if t.income > 0:
                savings_rate = (t.net_cashflow / t.income) * 100
                data.append({"date": t.date, "savings_rate": savings_rate})

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])

        # Color based on positive/negative
        colors = [
            ChartFactory.COLORS["success"] if val >= 0 else ChartFactory.COLORS["danger"] for val in df["savings_rate"]
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["savings_rate"],
                mode="lines+markers",
                fill="tozeroy",
                line={"color": ChartFactory.COLORS["info"], "width": 2},
                marker={"size": 8, "color": colors},
                text=df["savings_rate"].apply(lambda x: f"{x:.1f}%"),
                textposition="top center",
            )
        )

        # Add target line (e.g., 20% savings rate)
        fig.add_hline(
            y=20, line_dash="dash", line_color="green", annotation_text="Target: 20%", annotation_position="right"
        )
        fig.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.3)

        fig.update_layout(
            title="Savings Rate Over Time",
            xaxis_title="Date",
            yaxis_title="Savings Rate (%)",
            template="plotly_white",
            height=400,
            hovermode="x unified",
        )

        return fig

    @staticmethod
    def create_cash_flow_waterfall(transactions: list, period: str = "total") -> go.Figure:
        """
        Create a waterfall chart showing cash flow breakdown.

        Args:
            transactions: List of monthly transactions
            period: 'total' or 'monthly'

        Returns:
            Plotly figure
        """
        if period == "total":
            total_income = sum(t.income for t in transactions)
            total_expenses = sum(t.expenses for t in transactions)
            net = total_income - total_expenses

            fig = go.Figure(
                go.Waterfall(
                    name="Cash Flow",
                    orientation="v",
                    measure=["relative", "relative", "total"],
                    x=["Income", "Expenses", "Net Savings"],
                    y=[total_income, -total_expenses, net],
                    text=[f"€{total_income:,.0f}", f"€{total_expenses:,.0f}", f"€{net:,.0f}"],
                    textposition="outside",
                    connector={"line": {"color": "rgb(63, 63, 63)"}},
                )
            )
        else:
            # Last month
            last = transactions[-1]
            fig = go.Figure(
                go.Waterfall(
                    name="Cash Flow",
                    orientation="v",
                    measure=["relative", "relative", "total"],
                    x=["Income", "Expenses", "Net Savings"],
                    y=[last.income, -last.expenses, last.net_cashflow],
                    text=[f"€{last.income:,.0f}", f"€{last.expenses:,.0f}", f"€{last.net_cashflow:,.0f}"],
                    textposition="outside",
                )
            )

        fig.update_layout(
            title=f"Cash Flow Breakdown ({period.title()})",
            yaxis_title="Amount (€)",
            template="plotly_white",
            height=400,
            showlegend=False,
        )

        return fig

    @staticmethod
    def create_asset_history_chart(
        service, asset_name: str, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> go.Figure:
        """
        Create asset value history chart.

        Args:
            service: FinanceService instance
            asset_name: Name of the asset
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Plotly figure
        """
        asset = service.get_asset_by_name(asset_name)
        if not asset:
            return go.Figure()

        values = service.get_asset_values(asset, start_date, end_date)

        data = [
            {"date": v.date, "invested": v.amount_invested, "value": v.countervalue, "return_pct": v.return_percentage}
            for v in values
        ]

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])

        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=(f"{asset_name} - Value Over Time", "Return %"),
            vertical_spacing=0.12,
            row_heights=[0.7, 0.3],
        )

        # Value chart
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["value"],
                name="Current Value",
                line={"color": ChartFactory.COLORS["success"], "width": 2},
                fill="tonexty",
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["invested"],
                name="Invested",
                line={"color": ChartFactory.COLORS["info"], "width": 2, "dash": "dash"},
            ),
            row=1,
            col=1,
        )

        # Return % chart
        colors = [
            ChartFactory.COLORS["success"] if val >= 0 else ChartFactory.COLORS["danger"] for val in df["return_pct"]
        ]

        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["return_pct"],
                name="Return %",
                marker_color=colors,
                showlegend=False,
            ),
            row=2,
            col=1,
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Value (€)", row=1, col=1)
        fig.update_yaxes(title_text="Return %", row=2, col=1)

        fig.update_layout(
            height=600,
            template="plotly_white",
            hovermode="x unified",
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        )

        return fig


# Convenience functions for quick chart creation


def plot_net_worth(history: list[dict[str, Any]]) -> go.Figure:
    """Quick function to plot net worth."""
    return ChartFactory.create_net_worth_chart(history)


def plot_allocation(allocation: list[dict[str, Any]], chart_type: str = "pie") -> go.Figure:
    """Quick function to plot allocation."""
    if chart_type == "pie":
        return ChartFactory.create_allocation_pie_chart(allocation)
    return ChartFactory.create_allocation_bar_chart(allocation)


def plot_performance(summary: list[dict[str, Any]]) -> go.Figure:
    """Quick function to plot performance comparison."""
    return ChartFactory.create_performance_comparison_chart(summary)


def plot_income_expenses(transactions: list) -> go.Figure:
    """Quick function to plot income vs expenses."""
    return ChartFactory.create_income_expense_chart(transactions)
