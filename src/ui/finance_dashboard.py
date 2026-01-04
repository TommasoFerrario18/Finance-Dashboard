import logging
import streamlit as st
from typing import Optional

from omegaconf import DictConfig

from src.registry.page_registry import load_pages_from_config
from src.service.finance_service import FinanceService
from src.utils.config import load_hydra_config, setup_logging

logger = logging.getLogger(__name__)


class FinanceDashboard:
    """Main dashboard application class with enhanced features."""

    def __init__(self):
        """Initialize the dashboard."""
        self.cfg: Optional[DictConfig] = None
        self.service: Optional[FinanceService] = None
        self.data_loaded: bool = False

        self.setup()

    def setup(self) -> None:
        """Setup configuration and services."""
        # Load configuration
        self.cfg = load_hydra_config()
        setup_logging(self.cfg)

        # Load pages from config
        self.PAGES = load_pages_from_config(self.cfg)

        logger.info(f"Dashboard initialized - {self.cfg.app.name} v{self.cfg.app.version}")

    def render_header(self) -> None:
        """Render the main header with branding."""
        col1, col2 = st.columns([3, 1])

        with col1:
            st.title(f"{self.cfg.app.settings.page_icon} {self.cfg.app.settings.page_title}")
            st.caption("Track, analyze, and optimize your financial portfolio")

        with col2:
            # App info in an expander
            with st.expander("ℹ️ About"):
                st.markdown(f"""
                **Version:** {self.cfg.app.version}
                
                **Features:**
                - 📊 Multi-tab dashboard
                - 📈 Interactive charts
                - 💰 Asset tracking
                - 💵 Cash flow analysis
                - 🔍 Advanced analytics
                """)

    def render_sidebar(self) -> tuple:
        """Render the sidebar with navigation and settings."""
        with st.sidebar:
            st.header("⚙️ Settings")

            # File upload section
            uploaded_file = st.file_uploader(
                "Upload your finance CSV file", type=["csv"], help="Upload your financial tracking CSV file"
            )

            if uploaded_file:
                st.success("✓ File uploaded successfully!")
                st.caption(f"📄 {uploaded_file.name}")
                st.caption(f"📊 {uploaded_file.size:,} bytes")

            st.markdown("---")

            # Navigation section
            st.markdown("### 📑 Navigation")

            # Create navigation buttons
            page_options = list(self.PAGES.keys())

            selected_page = st.radio(
                "Select Page",
                options=page_options,
                format_func=lambda x: f"{self.PAGES[x]['icon']} {x}",
                label_visibility="collapsed",
                key="page_selector",
            )

            # Show page description
            if selected_page:
                st.caption(self.PAGES[selected_page]["description"])

            st.markdown("---")

            # Additional info
            with st.expander("📋 Help"):
                st.markdown("""
                **How to use:**
                1. Upload your CSV file
                2. Select a date (optional)
                3. Navigate between pages
                4. Explore interactive charts
                
                **CSV Format:**
                - Date, Income, Expenses, Cash
                - Asset columns: [Name] Invested, [Name] Countervalue
                
                **Date Filter:**
                - View historical snapshots
                - Compare time periods
                - Track portfolio evolution
                """)

        return uploaded_file, selected_page
    
    def render_page(self, page_name: str, selected_date=None) -> None:
        """
        Render the selected page.
        
        Args:
            page_name: Name of the page to render
            selected_date: Optional date filter
        """
        page_config = self.PAGES.get(page_name)
        
        if page_config:
            try:
                page_class = page_config['class']
                page = page_class(self.service)
                
                # Render page with date filter
                if hasattr(page, 'render_with_date'):
                    page.render_with_date(selected_date)
                else:
                    page.render()
                    
            except Exception as e:
                st.error(f"Error rendering page: {e}")
                logger.error(f"Page render error: {e}", exc_info=True)
                
                with st.expander("📋 Error Details"):
                    st.exception(e)
        else:
            st.error(f"Unknown page: {page_name}")
    
    def render_footer(self) -> None:
        """Render footer with additional info."""
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.caption("💡 **Tip:** Click on charts to interact")
        
        with col2:
            st.caption("📊 Data updates on file upload")
        
        with col3:
            st.caption(f"⚡ Powered by {self.cfg.app.name}")

    def run(self):
        """Run the main dashboard application."""
        # Render header
        self.render_header()

        # Handle sidebar and file upload
        _, selected_page = self.render_sidebar()

        self.render_page(selected_page)
        self.render_footer()
