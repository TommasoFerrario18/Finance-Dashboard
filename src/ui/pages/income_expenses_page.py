import streamlit as st
from src.service.finance_service import FinanceService


class IncomeExpensesPage:
    """Income and expenses tracking page."""

    def __init__(self, service: FinanceService):
        self.service = service

    def render(self) -> None:
        """Render the income & expenses page."""
        st.header("💵 Income & Expenses")
