from src.Factory.chart_factory import ChartFactory
from src.service.finance_service import FinanceService
from src.ui.pages.dashboard_page import DashboardPage


class OverviewPage:
    """Simplified overview page redirecting to Dashboard."""

    def __init__(self, service: FinanceService):
        self.service = service
        self.chart_factory = ChartFactory()

    def render(self) -> None:
        """Render overview - now redirects to main dashboard."""
        dashboard = DashboardPage(self.service)
        dashboard.render()
