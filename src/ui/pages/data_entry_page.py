"""Data Entry page for manual input of financial data."""

import logging
from datetime import date

import streamlit as st

from src.service.finance_service import FinanceService

logger = logging.getLogger(__name__)


class DataEntryPage:
    """Page for entering financial data manually."""

    def __init__(self, service: FinanceService):
        """Initialize the data entry page."""
        self.service = service

    def render(self) -> None:
        """Render the data entry page with tabs."""
        st.header("✍️ Data Entry")
        st.markdown("Manually enter and manage your financial data")

        # Create tabs
        tab1, tab2, tab3 = st.tabs([
            "📊 Update Asset Values",
            "➕ Add New Asset Type",
            "💰 Income & Expenses"
        ])

        with tab1:
            self._render_asset_values_tab()

        with tab2:
            self._render_new_asset_tab()

        with tab3:
            self._render_income_expenses_tab()

    def _render_asset_values_tab(self) -> None:
        """Render tab for updating monthly asset values."""
        st.subheader("Update Asset Values")
        st.markdown("Enter the current values for your assets")

        # Get existing assets
        try:
            assets = self._get_existing_assets()
            
            if not assets:
                st.info("No assets found. Add a new asset type first in the 'Add New Asset Type' tab.")
                return

            # Date selector
            col1, col2 = st.columns([2, 1])
            with col1:
                entry_date = st.date_input(
                    "Date",
                    value=date.today(),
                    help="Select the date for this asset valuation"
                )
            
            with col2:
                st.metric("Assets to update", len(assets))

            st.markdown("---")

            # Create form for asset values
            with st.form("asset_values_form"):
                st.markdown("### Asset Values")
                
                asset_values = {}
                
                # Create input fields for each asset
                cols = st.columns(2)
                for idx, asset_name in enumerate(assets):
                    col = cols[idx % 2]
                    with col:
                        st.markdown(f"**{asset_name}**")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            invested = st.number_input(
                                f"Invested",
                                min_value=0.0,
                                value=0.0,
                                step=100.0,
                                key=f"invested_{asset_name}",
                                help=f"Amount invested in {asset_name}"
                            )
                        
                        with col_b:
                            countervalue = st.number_input(
                                f"Current Value",
                                min_value=0.0,
                                value=0.0,
                                step=100.0,
                                key=f"countervalue_{asset_name}",
                                help=f"Current market value of {asset_name}"
                            )
                        
                        asset_values[asset_name] = {
                            'invested': invested,
                            'countervalue': countervalue
                        }
                        
                        st.markdown("")  # Spacing

                # Submit button
                submitted = st.form_submit_button("💾 Save Asset Values", use_container_width=True)
                
                if submitted:
                    try:
                        self._save_asset_values(entry_date, asset_values)
                        st.success(f"✅ Asset values saved successfully for {entry_date}")
                        
                        # Show summary
                        total_invested = sum(v['invested'] for v in asset_values.values())
                        total_value = sum(v['countervalue'] for v in asset_values.values())
                        gain_loss = total_value - total_invested
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Total Invested", f"${total_invested:,.2f}")
                        col2.metric("Total Value", f"${total_value:,.2f}")
                        col3.metric("Gain/Loss", f"${gain_loss:,.2f}", 
                                  delta=f"{(gain_loss/total_invested*100) if total_invested > 0 else 0:.2f}%")
                        
                    except Exception as e:
                        st.error(f"Error saving asset values: {str(e)}")
                        logger.error(f"Error saving asset values: {e}", exc_info=True)

        except Exception as e:
            st.error(f"Error loading assets: {str(e)}")
            logger.error(f"Error loading assets: {e}", exc_info=True)

    def _render_new_asset_tab(self) -> None:
        """Render tab for adding new asset types."""
        st.subheader("Add New Asset Type")
        st.markdown("Create a new asset category to track (e.g., Stocks, Bonds, Real Estate)")

        # Show existing assets
        try:
            existing_assets = self._get_existing_assets()
            
            if existing_assets:
                st.markdown("### Existing Assets")
                cols = st.columns(min(4, len(existing_assets)))
                for idx, asset in enumerate(existing_assets):
                    cols[idx % len(cols)].info(f"📊 {asset}")
                st.markdown("---")

        except Exception as e:
            logger.error(f"Error loading existing assets: {e}")

        # Form for new asset
        with st.form("new_asset_form"):
            st.markdown("### New Asset Details")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                asset_name = st.text_input(
                    "Asset Name",
                    placeholder="e.g., Bonds, Real Estate, Cryptocurrency",
                    help="Enter a unique name for this asset type"
                )
            
            with col2:
                asset_category = st.selectbox(
                    "Category",
                    options=["Equity", "Fixed Income", "Real Estate", "Commodities", "Cash", "Alternative", "Other"],
                    help="Select the asset category"
                )

            asset_description = st.text_area(
                "Description (Optional)",
                placeholder="Add notes about this asset type...",
                help="Optional description or notes"
            )

            col1, col2 = st.columns(2)
            with col1:
                initial_invested = st.number_input(
                    "Initial Amount Invested",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    help="Initial investment amount"
                )
            
            with col2:
                initial_value = st.number_input(
                    "Initial Current Value",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    help="Current market value"
                )

            # Submit button
            submitted = st.form_submit_button("➕ Add Asset Type", use_container_width=True)
            
            if submitted:
                if not asset_name:
                    st.error("Please enter an asset name")
                elif asset_name in existing_assets:
                    st.error(f"Asset '{asset_name}' already exists. Please use a different name.")
                else:
                    try:
                        self._save_new_asset(
                            asset_name, 
                            asset_category, 
                            asset_description,
                            initial_invested,
                            initial_value
                        )
                        st.success(f"✅ New asset type '{asset_name}' added successfully!")
                        st.balloons()
                        
                        # Show what was added
                        st.info(f"""
                        **Asset Created:**
                        - Name: {asset_name}
                        - Category: {asset_category}
                        - Initial Investment: ${initial_invested:,.2f}
                        - Initial Value: ${initial_value:,.2f}
                        """)
                        
                    except Exception as e:
                        st.error(f"Error adding new asset: {str(e)}")
                        logger.error(f"Error adding new asset: {e}", exc_info=True)

    def _render_income_expenses_tab(self) -> None:
        """Render tab for recording income and expenses."""
        st.subheader("Income & Expenses")
        st.markdown("Record your monthly income and expenses")

        # Date selector
        entry_date = st.date_input(
            "Date",
            value=date.today(),
            help="Select the date for this entry"
        )

        st.markdown("---")

        # Create form
        with st.form("income_expenses_form"):
            
            # Income section
            st.markdown("### 💰 Income")
            col1, col2 = st.columns(2)
            
            with col1:
                salary = st.number_input(
                    "Salary/Wages",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    help="Regular salary or wages"
                )
            
            with col2:
                other_income = st.number_input(
                    "Other Income",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    help="Dividends, interest, side income, etc."
                )
            
            total_income = salary + other_income
            st.metric("Total Income", f"${total_income:,.2f}")

            st.markdown("---")

            # Expenses section
            st.markdown("### 💸 Expenses")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Fixed Expenses**")
                rent_mortgage = st.number_input("Rent/Mortgage", min_value=0.0, value=0.0, step=100.0)
                utilities = st.number_input("Utilities", min_value=0.0, value=0.0, step=50.0)
                insurance = st.number_input("Insurance", min_value=0.0, value=0.0, step=50.0)
            
            with col2:
                st.markdown("**Variable Expenses**")
                groceries = st.number_input("Groceries", min_value=0.0, value=0.0, step=50.0)
                transportation = st.number_input("Transportation", min_value=0.0, value=0.0, step=50.0)
                entertainment = st.number_input("Entertainment", min_value=0.0, value=0.0, step=50.0)
            
            other_expenses = st.number_input(
                "Other Expenses",
                min_value=0.0,
                value=0.0,
                step=50.0,
                help="Any other expenses not listed above"
            )
            
            total_expenses = (rent_mortgage + utilities + insurance + 
                            groceries + transportation + entertainment + other_expenses)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Expenses", f"${total_expenses:,.2f}")
            col2.metric("Net Income", f"${total_income - total_expenses:,.2f}")
            col3.metric("Savings Rate", f"{(total_income - total_expenses) / total_income * 100 if total_income > 0 else 0:.1f}%")

            st.markdown("---")

            # Cash balance
            st.markdown("### 💵 Cash Balance")
            cash_balance = st.number_input(
                "Current Cash Balance",
                min_value=0.0,
                value=0.0,
                step=100.0,
                help="Total cash in bank accounts"
            )

            # Notes
            notes = st.text_area(
                "Notes (Optional)",
                placeholder="Add any additional notes about this period...",
                help="Optional notes"
            )

            # Submit button
            submitted = st.form_submit_button("💾 Save Income & Expenses", use_container_width=True)
            
            if submitted:
                try:
                    expense_breakdown = {
                        'rent_mortgage': rent_mortgage,
                        'utilities': utilities,
                        'insurance': insurance,
                        'groceries': groceries,
                        'transportation': transportation,
                        'entertainment': entertainment,
                        'other': other_expenses
                    }
                    
                    self._save_income_expenses(
                        entry_date,
                        salary,
                        other_income,
                        total_expenses,
                        expense_breakdown,
                        cash_balance,
                        notes
                    )
                    
                    st.success(f"✅ Income and expenses saved successfully for {entry_date}")
                    
                    # Show summary
                    st.info(f"""
                    **Summary:**
                    - Total Income: ${total_income:,.2f}
                    - Total Expenses: ${total_expenses:,.2f}
                    - Net Income: ${total_income - total_expenses:,.2f}
                    - Cash Balance: ${cash_balance:,.2f}
                    """)
                    
                except Exception as e:
                    st.error(f"Error saving data: {str(e)}")
                    logger.error(f"Error saving income/expenses: {e}", exc_info=True)

    def _get_existing_assets(self) -> list:
        """
        Get list of existing asset types.
        
        Returns:
            List of asset names
        """
        try:
            # Query the database for existing assets
            # This is a placeholder - implement based on your service layer
            query = "SELECT DISTINCT asset_name FROM assets ORDER BY asset_name"
            result = self.service.execute_query(query)
            return [row['asset_name'] for row in result] if result else []
        except Exception as e:
            logger.error(f"Error fetching assets: {e}")
            return []

    def _save_asset_values(self, entry_date: date, asset_values: dict) -> None:
        """
        Save asset values to database.
        
        Args:
            entry_date: Date of the entry
            asset_values: Dictionary of asset names and their values
        """
        # Placeholder - implement based on your service layer
        for asset_name, values in asset_values.items():
            self.service.save_asset_value(
                date=entry_date,
                asset_name=asset_name,
                invested=values['invested'],
                countervalue=values['countervalue']
            )
        logger.info(f"Saved asset values for {len(asset_values)} assets on {entry_date}")

    def _save_new_asset(
        self, 
        asset_name: str, 
        asset_category: str, 
        description: str,
        initial_invested: float,
        initial_value: float
    ) -> None:
        """
        Save new asset type to database.
        
        Args:
            asset_name: Name of the asset
            asset_category: Category of the asset
            description: Optional description
            initial_invested: Initial investment amount
            initial_value: Initial market value
        """
        # Placeholder - implement based on your service layer
        self.service.create_asset_type(
            name=asset_name,
            category=asset_category,
            description=description
        )
        
        # Save initial values if provided
        if initial_invested > 0 or initial_value > 0:
            self.service.save_asset_value(
                date=date.today(),
                asset_name=asset_name,
                invested=initial_invested,
                countervalue=initial_value
            )
        
        logger.info(f"Created new asset type: {asset_name}")

    def _save_income_expenses(
        self,
        entry_date: date,
        salary: float,
        other_income: float,
        total_expenses: float,
        expense_breakdown: dict,
        cash_balance: float,
        notes: str
    ) -> None:
        """
        Save income and expenses to database.
        
        Args:
            entry_date: Date of the entry
            salary: Salary/wages income
            other_income: Other income sources
            total_expenses: Total expenses amount
            expense_breakdown: Dictionary of expense categories
            cash_balance: Current cash balance
            notes: Optional notes
        """
        # Placeholder - implement based on your service layer
        self.service.save_financial_record(
            date=entry_date,
            income=salary + other_income,
            salary=salary,
            other_income=other_income,
            expenses=total_expenses,
            expense_breakdown=expense_breakdown,
            cash=cash_balance,
            notes=notes
        )
        logger.info(f"Saved income/expenses record for {entry_date}")