import streamlit as st

from src.service.finance_service import FinanceService


class InvestmentsPage:
    """Detailed investments page with individual asset analysis."""

    def __init__(self, service: FinanceService):
        self.service = service

    def render(self) -> None:
        """Render the investments page."""
        st.header("💰 Investment Portfolio")

        st.markdown("---")

        # Individual asset cards
        st.subheader("Individual Assets")
