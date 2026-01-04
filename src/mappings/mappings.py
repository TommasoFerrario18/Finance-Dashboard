# Page configuration
from src.ui.pages.dashboard_page import DashboardPage
from src.ui.pages.detailed_analysis_page import DetailedAnalysisPage
from src.ui.pages.income_expenses_page import IncomeExpensesPage
from src.ui.pages.investments_page import InvestmentsPage

MAP_PAGES = {
    "Dashboard": DashboardPage,
    "Investments": InvestmentsPage,
    "Income & Expenses": IncomeExpensesPage,
    "Advanced Analysis": DetailedAnalysisPage,
}
