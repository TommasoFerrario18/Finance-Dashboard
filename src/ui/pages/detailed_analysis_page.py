from typing import Any

import pandas as pd
import streamlit as st

from src.Factory.chart_factory import ChartFactory
from src.service.finance_service import FinanceService

MIN_HISTORY_LEN = 2


class DetailedAnalysisPage:
    """Advanced analysis and insights page."""

    def __init__(self, service: FinanceService):
        self.service = service
        self.chart_factory = ChartFactory()

    def render(self) -> None:
        """Render the detailed analysis page."""
        st.header("🔍 Advanced Analysis")

        history = self.service.get_portfolio_history()

        if not history:
            st.warning("No historical data available yet.")
            return

        # Tabs for different analyses
        tabs = st.tabs(["📈 Growth Trends", "📊 Comparative Analysis", "🎯 Projections", "📉 Risk Metrics"])

        with tabs[0]:
            self._render_growth_trends(history)

        with tabs[1]:
            self._render_comparative_analysis()

        with tabs[2]:
            self._render_projections(history)

        with tabs[3]:
            self._render_risk_metrics()

    def _render_growth_trends(self, history: list[dict[str, Any]]) -> None:
        """Render growth trend analysis."""
        st.subheader("Portfolio Growth Trends")

        fig = self.chart_factory.create_net_worth_chart(history)
        st.plotly_chart(fig, use_container_width=True)

        # Growth statistics
        df = pd.DataFrame(history)
        if len(df) > 1:
            initial_value = df["total_invested"].iloc[0]
            current_value = df["total_value"].iloc[-1]
            total_growth = current_value - initial_value
            months = len(df)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Growth", f"€{total_growth:,.2f}")

            with col2:
                monthly_avg = total_growth / months if months > 0 else 0
                st.metric("Avg Monthly Growth", f"€{monthly_avg:,.2f}")

            with col3:
                cagr = (
                    (((current_value / initial_value) ** (12 / months)) - 1) * 100
                    if initial_value > 0 and months > 0
                    else 0
                )
                st.metric("Annualized Return", f"{cagr:.2f}%")

    def _render_comparative_analysis(self) -> None:
        """Render comparative analysis between asset types."""
        st.subheader("Asset Type Comparison")

        allocation = self.service.get_asset_type_allocation()

        if allocation:
            # Create comparison chart
            df = pd.DataFrame(allocation)

            fig = self.chart_factory.create_allocation_bar_chart(allocation)
            st.plotly_chart(fig, use_container_width=True)

            # Performance comparison table
            st.markdown("#### Performance by Asset Type")

            df = df.sort_values("profit_loss", ascending=False)
            df["Return %"] = (df["profit_loss"] / df["total_invested"] * 100).apply(lambda x: f"{x:.2f}%")
            df["Invested"] = df["total_invested"].apply(lambda x: f"€{x:,.2f}")
            df["Value"] = df["total_value"].apply(lambda x: f"€{x:,.2f}")
            df["P/L"] = df["profit_loss"].apply(lambda x: f"€{x:,.2f}")

            st.dataframe(
                df[["asset_type", "num_assets", "Invested", "Value", "P/L", "Return %"]],
                use_container_width=True,
                hide_index=True,
            )

    def _render_projections(self, history: list[dict[str, Any]]) -> None:
        """Render future projections."""
        st.subheader("Future Projections")

        st.info("💡 Projections based on historical growth rates")

        if len(history) < MIN_HISTORY_LEN:
            st.warning("Need at least 2 months of data for projections")
            return

        # Calculate average growth rate
        df = pd.DataFrame(history)
        df["month_growth"] = df["profit_loss"].diff()
        avg_monthly_growth = df["month_growth"].mean()

        current_value = df["total_value"].iloc[-1]

        # Project 6 months ahead
        projections = []
        for i in range(1, 7):
            projected_value = current_value + (avg_monthly_growth * i)
            projections.append({"months_ahead": i, "projected_value": projected_value})

        pd.DataFrame(projections)

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Current Value", f"€{current_value:,.2f}")
            st.metric("Avg Monthly Growth", f"€{avg_monthly_growth:,.2f}")

        with col2:
            st.metric("Projected Value (3 months)", f"€{projections[2]['projected_value']:,.2f}")
            st.metric("Projected Value (6 months)", f"€{projections[5]['projected_value']:,.2f}")

    def _render_risk_metrics(self) -> None:
        """Render risk and volatility metrics."""
        st.subheader("Risk Analysis")

        summary = self.service.get_portfolio_summary()
        allocation = self.service.get_asset_type_allocation()

        if not summary:
            return

        # Concentration risk
        st.markdown("#### Portfolio Concentration")

        df = pd.DataFrame(allocation)
        max_allocation = df["percentage"].max() if len(df) > 0 else 0

        if max_allocation > 50:
            st.warning(f"⚠️ High concentration risk: {max_allocation:.1f}% in single asset type")
        elif max_allocation > 30:
            st.info(f"ℹ️ Moderate concentration: {max_allocation:.1f}% in single asset type")
        else:
            st.success(f"✅ Well diversified: Max {max_allocation:.1f}% in single asset type")

        # Diversification score
        num_assets = len(summary)
        num_types = len(allocation)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Assets", num_assets)

        with col2:
            st.metric("Asset Types", num_types)

        with col3:
            diversification_score = min(100, (num_assets * 10 + num_types * 20))
            st.metric("Diversification Score", f"{diversification_score}/100")
