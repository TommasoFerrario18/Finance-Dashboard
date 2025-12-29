import logging
import streamlit as st

from src.ui.finance_dashboard import FinanceDashboard

logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the Streamlit app."""
    try:
        dashboard = FinanceDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.error(f"Application error: {e}", exc_info=True)

        with st.expander("📋 Error Details"):
            st.exception(e)
            st.markdown("""
            **Troubleshooting:**
            - Check your CSV file format
            - Ensure database is accessible
            - Check logs for details
            - Try reloading the page
            """)


if __name__ == "__main__":
    main()
