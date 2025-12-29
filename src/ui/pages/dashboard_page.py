import streamlit as st

from src.service.finance_service import FinanceService


class DashboardPage:
    """
    Main dashboard with comprehensive overview and tabs.
    """

    def __init__(self, service: FinanceService):
        self.service = service

    def render(self) -> None:
        """Render the dashboard page with tabs."""
        st.header("📊 Financial Dashboard")

        # Create tabs
        tabs = st.tabs(["📈 Net Worth", "🥧 Allocation", "💰 Performance", "💵 Cash Flow", "📊 Analysis"])
