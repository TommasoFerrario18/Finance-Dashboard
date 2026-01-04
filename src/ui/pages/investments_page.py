from typing import Any

import streamlit as st

from src.Factory.chart_factory import ChartFactory
from src.service.finance_service import FinanceService


class InvestmentsPage:
    """Detailed investments page with individual asset analysis."""

    def __init__(self, service: FinanceService):
        self.service = service
        self.chart_factory = ChartFactory()

    def render(self) -> None:
        """Render the investments page."""
        st.header("💰 Investment Portfolio")

        summary = self.service.get_portfolio_summary()

        if not summary:
            st.warning("No investment data available yet.")
            return

        # Portfolio overview
        self._render_portfolio_overview(summary)

        st.markdown("---")

        # Individual asset cards
        st.subheader("Individual Assets")
        self._render_asset_cards(summary)

    def _render_portfolio_overview(self, summary: list[dict[str, Any]]) -> None:
        """Render portfolio overview metrics."""
        total_invested = sum(item["amount_invested"] for item in summary)
        total_value = sum(item["countervalue"] for item in summary)
        total_profit = total_value - total_invested

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Portfolio Value", f"€{total_value:,.2f}")

        with col2:
            st.metric("Total Invested", f"€{total_invested:,.2f}")

        with col3:
            return_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0
            st.metric("Total Return", f"€{total_profit:,.2f}", delta=f"{return_pct:.2f}%")

    def _render_asset_cards(self, summary: list[dict[str, Any]]) -> None:
        """Render individual asset cards with expandable details."""
        for asset in summary:
            with st.expander(f"📊 {asset['name']} ({asset['asset_type']})"):
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Invested", f"€{asset['amount_invested']:,.2f}")

                with col2:
                    st.metric("Current Value", f"€{asset['countervalue']:,.2f}")

                with col3:
                    delta_color = "normal" if asset["profit_loss"] >= 0 else "inverse"
                    st.metric(
                        "Profit/Loss",
                        f"€{asset['profit_loss']:,.2f}",
                        delta=f"{asset['return_percentage']:.2f}%",
                        delta_color=delta_color,
                    )

                with col4:
                    allocation = self.service.get_asset_type_allocation()
                    total_value = sum(a["total_value"] for a in allocation)
                    weight = (asset["countervalue"] / total_value * 100) if total_value > 0 else 0
                    st.metric("Portfolio Weight", f"{weight:.1f}%")

                # Asset history chart
                fig = self.chart_factory.create_asset_history_chart(self.service, asset["name"])
                st.plotly_chart(fig, use_container_width=True)
