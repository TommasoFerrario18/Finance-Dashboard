from typing import Any

import pandas as pd
import streamlit as st

from src.Factory.chart_factory import ChartFactory
from src.service.finance_service import FinanceService

MIN_HISTORY_LEN = 2


class DashboardPage:
    """
    Main dashboard with comprehensive overview and tabs.
    """

    def __init__(self, service: FinanceService):
        self.service = service
        self.chart_factory = ChartFactory()

    def render(self) -> None:
        """Render the dashboard page with tabs."""
        st.header("📊 Financial Dashboard")

        # Get data
        summary = self.service.get_portfolio_summary()
        history = self.service.get_portfolio_history()
        allocation = self.service.get_asset_type_allocation()
        transactions = self.service.get_monthly_transactions()

        if not summary:
            st.warning("No portfolio data available yet.")
            return

        # Key metrics at the top
        self._render_key_metrics(summary, history)

        # Create tabs
        tabs = st.tabs(["📈 Net Worth", "🥧 Allocation", "💰 Performance", "💵 Cash Flow", "📊 Analysis"])

        with tabs[0]:
            self._render_net_worth_tab(history)

        with tabs[1]:
            self._render_allocation_tab(allocation)

        with tabs[2]:
            self._render_performance_tab(summary)

        with tabs[3]:
            self._render_cash_flow_tab(transactions)

        with tabs[4]:
            self._render_analysis_tab(summary)

    def _render_key_metrics(self, summary: list[dict[str, Any]], history: list[dict[str, Any]]) -> None:
        """Render key performance metrics."""
        total_invested = sum(item["amount_invested"] for item in summary)
        total_value = sum(item["countervalue"] for item in summary)
        total_profit = total_value - total_invested
        total_return = (total_profit / total_invested * 100) if total_invested > 0 else 0

        # Get month-over-month change if available
        mom_change = 0
        mom_change_pct = 0
        if len(history) >= MIN_HISTORY_LEN:
            prev_value = history[-2]["total_value"]
            curr_value = history[-1]["total_value"]
            mom_change = curr_value - prev_value
            mom_change_pct = (mom_change / prev_value * 100) if prev_value > 0 else 0

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Invested", f"€{total_invested:,.0f}", help="Total amount invested across all assets")

        with col2:
            st.metric(
                "Net Worth",
                f"€{total_value:,.0f}",
                delta=f"€{mom_change:,.0f} ({mom_change_pct:+.1f}%)" if len(history) >= MIN_HISTORY_LEN else None,
                help="Current total value of all assets",
            )

        with col3:
            st.metric(
                "Total Profit/Loss",
                f"€{total_profit:,.0f}",
                delta=f"{total_return:+.2f}%",
                help="Unrealized gains/losses",
            )

        with col4:
            # Get cash from latest transaction
            cash = 0
            trans = self.service.get_monthly_transactions()
            if trans:
                cash = trans[-1].cash

            st.metric("Cash Balance", f"€{cash:,.0f}", help="Available cash")

    def _render_net_worth_tab(self, history: list[dict[str, Any]]) -> None:
        """Render net worth analysis tab."""
        st.subheader("Net Worth Over Time")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Main net worth chart
            fig = self.chart_factory.create_net_worth_chart(history)
            st.plotly_chart(fig, width='stretch')

        with col2:
            # Statistics
            st.markdown("#### Statistics")

            df = pd.DataFrame(history)

            current_value = df["total_value"].iloc[-1] if len(df) > 0 else 0
            initial_value = df["total_invested"].iloc[0] if len(df) > 0 else 0
            total_return = current_value - initial_value
            total_return_pct = (total_return / initial_value * 100) if initial_value > 0 else 0

            st.metric("Current Net Worth", f"€{current_value:,.2f}")
            st.metric("Initial Investment", f"€{initial_value:,.2f}")
            st.metric("Total Return", f"€{total_return:,.2f}", delta=f"{total_return_pct:.2f}%")

            if len(df) > 1:
                avg_monthly_growth = df["profit_loss"].mean()
                st.metric("Avg Monthly Growth", f"€{avg_monthly_growth:,.2f}")

        # Profit/Loss chart
        st.markdown("---")
        fig = self.chart_factory.create_profit_loss_chart(history)
        st.plotly_chart(fig, width='stretch')

    def _render_allocation_tab(self, allocation: list[dict[str, Any]]) -> None:
        """Render asset allocation tab."""
        st.subheader("Asset Allocation")

        col1, col2 = st.columns(2)

        with col1:
            # Pie chart
            fig = self.chart_factory.create_allocation_pie_chart(allocation)
            st.plotly_chart(fig, width='stretch')

        with col2:
            # Bar chart
            fig = self.chart_factory.create_allocation_bar_chart(allocation)
            st.plotly_chart(fig, width='stretch')

        # Detailed breakdown
        st.markdown("---")
        st.markdown("#### Detailed Breakdown")

        df = pd.DataFrame(allocation)
        df = df.rename(
            columns={
                "asset_type": "Asset Type",
                "num_assets": "Assets",
                "total_invested": "Invested",
                "total_value": "Current Value",
                "profit_loss": "Profit/Loss",
                "percentage": "Allocation %",
            }
        )

        # Format columns
        df["Invested"] = df["Invested"].apply(lambda x: f"€{x:,.2f}")
        df["Current Value"] = df["Current Value"].apply(lambda x: f"€{x:,.2f}")
        df["Profit/Loss"] = df["Profit/Loss"].apply(lambda x: f"€{x:,.2f}")
        df["Allocation %"] = df["Allocation %"].apply(lambda x: f"{x:.1f}%")

        st.dataframe(
            df[["Asset Type", "Assets", "Invested", "Current Value", "Profit/Loss", "Allocation %"]],
            width='stretch',
            hide_index=True,
        )

    def _render_performance_tab(self, summary: list[dict[str, Any]]) -> None:
        """Render performance comparison tab."""
        st.subheader("Asset Performance")

        # Invested vs Current Value
        fig = self.chart_factory.create_performance_comparison_chart(summary)
        st.plotly_chart(fig, width='stretch')

        st.markdown("---")

        # Returns heatmap
        fig = self.chart_factory.create_returns_heatmap(summary)
        st.plotly_chart(fig, width='stretch')

        # Performance table
        st.markdown("---")
        st.markdown("#### Performance Details")

        df = pd.DataFrame(summary)
        df = df.sort_values("return_percentage", ascending=False)
        df = df.rename(
            columns={
                "name": "Asset",
                "asset_type": "Type",
                "amount_invested": "Invested",
                "countervalue": "Current Value",
                "profit_loss": "Profit/Loss",
                "return_percentage": "Return %",
            }
        )

        # Format and add rank
        df.insert(0, "Rank", range(1, len(df) + 1))
        df["Invested"] = df["Invested"].apply(lambda x: f"€{x:,.2f}")
        df["Current Value"] = df["Current Value"].apply(lambda x: f"€{x:,.2f}")
        df["Profit/Loss"] = df["Profit/Loss"].apply(lambda x: f"€{x:,.2f}")
        df["Return %"] = df["Return %"].apply(lambda x: f"{x:.2f}%")

        st.dataframe(
            df[["Rank", "Asset", "Type", "Invested", "Current Value", "Profit/Loss", "Return %"]],
            width='stretch',
            hide_index=True,
        )

    def _render_cash_flow_tab(self, transactions: list) -> None:
        """Render cash flow analysis tab."""
        st.subheader("Cash Flow Analysis")

        if not transactions:
            st.warning("No transaction data available.")
            return

        # Income vs Expenses chart
        fig = self.chart_factory.create_income_expense_chart(transactions)
        st.plotly_chart(fig, width='stretch')

        col1, col2 = st.columns(2)

        with col1:
            # Waterfall chart
            fig = self.chart_factory.create_cash_flow_waterfall(transactions, period="total")
            st.plotly_chart(fig, width='stretch')

        with col2:
            # Savings rate chart
            fig = self.chart_factory.create_savings_rate_chart(transactions)
            st.plotly_chart(fig, width='stretch')

        # Summary statistics
        st.markdown("---")
        st.markdown("#### Summary Statistics")

        total_income = sum(t.income for t in transactions)
        total_expenses = sum(t.expenses for t in transactions)
        net_savings = total_income - total_expenses
        avg_income = total_income / len(transactions) if transactions else 0
        avg_expenses = total_expenses / len(transactions) if transactions else 0
        avg_savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Income", f"€{total_income:,.2f}")
            st.caption(f"Avg: €{avg_income:,.2f}/month")

        with col2:
            st.metric("Total Expenses", f"€{total_expenses:,.2f}")
            st.caption(f"Avg: €{avg_expenses:,.2f}/month")

        with col3:
            st.metric("Net Savings", f"€{net_savings:,.2f}")
            st.caption(f"Over {len(transactions)} months")

        with col4:
            st.metric("Savings Rate", f"{avg_savings_rate:.1f}%")
            st.caption("Average across all months")

    def _render_analysis_tab(self, summary: list[dict[str, Any]]) -> None:
        """Render detailed analysis tab."""
        st.subheader("Detailed Analysis")

        # Asset selector for detailed history
        asset_names = [item["name"] for item in summary]
        selected_asset = st.selectbox(
            "Select asset for detailed analysis:", options=asset_names, key="analysis_asset_selector"
        )

        if selected_asset:
            fig = self.chart_factory.create_asset_history_chart(self.service, selected_asset)
            st.plotly_chart(fig, width='stretch')

        # Correlation analysis (if multiple assets)
        if len(summary) > 1:
            st.markdown("---")
            st.markdown("#### Portfolio Insights")

            col1, col2 = st.columns(2)

            with col1:
                # Best performers
                performers = self.service.get_best_worst_performers()
                if performers["best"]:
                    st.success("🏆 **Best Performer**")
                    best = performers["best"]
                    st.write(f"**{best['name']}**")
                    st.write(f"Return: {best['return_percentage']:.2f}%")
                    st.write(f"Profit: €{best['profit_loss']:,.2f}")

            with col2:
                if performers["worst"]:
                    st.error("📉 **Needs Attention**")
                    worst = performers["worst"]
                    st.write(f"**{worst['name']}**")
                    st.write(f"Return: {worst['return_percentage']:.2f}%")
                    st.write(f"Change: €{worst['profit_loss']:,.2f}")
