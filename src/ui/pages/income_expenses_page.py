import pandas as pd
import streamlit as st

from src.Factory.chart_factory import ChartFactory
from src.service.finance_service import FinanceService


class IncomeExpensesPage:
    """Income and expenses tracking page."""

    def __init__(self, service: FinanceService):
        self.service = service
        self.chart_factory = ChartFactory()

    def render(self) -> None:
        """Render the income & expenses page."""
        st.header("💵 Income & Expenses")

        transactions = self.service.get_monthly_transactions()

        if not transactions:
            st.warning("No transaction data available yet.")
            return

        # Summary metrics
        self._render_summary_metrics(transactions)

        st.markdown("---")

        # Main chart
        fig = self.chart_factory.create_income_expense_chart(transactions)
        st.plotly_chart(fig, width='stretch')

        col1, col2 = st.columns(2)

        with col1:
            # Savings rate
            fig = self.chart_factory.create_savings_rate_chart(transactions)
            st.plotly_chart(fig, width='stretch')

        with col2:
            # Waterfall
            fig = self.chart_factory.create_cash_flow_waterfall(transactions[-1:], period="monthly")
            st.plotly_chart(fig, width='stretch')

        # Transaction table
        st.markdown("---")
        self._render_transactions_table(transactions)

    def _render_summary_metrics(self, transactions: list) -> None:
        """Render summary metrics."""
        total_income = sum(t.income for t in transactions)
        total_expenses = sum(t.expenses for t in transactions)
        net_savings = total_income - total_expenses
        savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Income", f"€{total_income:,.2f}")

        with col2:
            st.metric("Total Expenses", f"€{total_expenses:,.2f}")

        with col3:
            st.metric("Net Savings", f"€{net_savings:,.2f}")

        with col4:
            st.metric("Savings Rate", f"{savings_rate:.1f}%")

    def _render_transactions_table(self, transactions: list) -> None:
        """Render transactions table."""
        st.subheader("Transaction History")

        data = [
            {
                "Date": t.date.strftime("%Y-%m"),
                "Income": f"€{t.income:,.2f}",
                "Expenses": f"€{t.expenses:,.2f}",
                "Net": f"€{t.net_cashflow:,.2f}",
                "Cash": f"€{t.cash:,.2f}",
                "Savings Rate": f"{(t.net_cashflow / t.income * 100):.1f}%" if t.income > 0 else "N/A",
            }
            for t in transactions[-12:]
        ]  # Last 12 months

        df = pd.DataFrame(data)
        st.dataframe(df, width='stretch', hide_index=True)
