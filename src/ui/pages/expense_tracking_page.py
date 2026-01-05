"""Expense Tracking page for detailed daily expense management and analysis."""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.service.finance_service import FinanceService

logger = logging.getLogger(__name__)


class ExpenseTrackingPage:
    """Page for tracking daily expenses and analyzing spending patterns."""

    def __init__(self, service: FinanceService):
        """Initialize the expense tracking page."""
        self.service = service

    def render(self) -> None:
        """Render the expense tracking page with tabs."""
        st.header("💸 Expense Tracking & Analysis")
        st.markdown("Track daily expenses and analyze your spending patterns")

        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "➕ Add Expense",
            "📋 Expense History",
            "📊 Analytics",
            "⚙️ Manage Categories"
        ])

        with tab1:
            self._render_add_expense_tab()

        with tab2:
            self._render_expense_history_tab()

        with tab3:
            self._render_analytics_tab()

        with tab4:
            self._render_manage_categories_tab()

    def _render_add_expense_tab(self) -> None:
        """Render tab for adding individual expenses."""
        st.subheader("Add New Expense")
        st.markdown("Log each expense as you make it")

        # Quick stats
        col1, col2, col3 = st.columns(3)
        with col1:
            today_total = self._get_today_total()
            st.metric("Today's Expenses", f"${today_total:,.2f}")
        with col2:
            week_total = self._get_week_total()
            st.metric("This Week", f"${week_total:,.2f}")
        with col3:
            month_total = self._get_month_total()
            st.metric("This Month", f"${month_total:,.2f}")

        st.markdown("---")

        # Expense form
        with st.form("add_expense_form", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                expense_date = st.date_input(
                    "Date",
                    value=date.today(),
                    max_value=date.today(),
                    help="When did you make this expense?"
                )
                
                expense_time = st.time_input(
                    "Time",
                    value=datetime.now().time(),
                    help="What time did you make this expense?"
                )
            
            with col2:
                amount = st.number_input(
                    "Amount ($)",
                    min_value=0.01,
                    value=10.0,
                    step=1.0,
                    help="How much did you spend?"
                )
                
                payment_method = st.selectbox(
                    "Payment Method",
                    options=["Cash", "Credit Card", "Debit Card", "Mobile Payment", "Bank Transfer", "Other"],
                    help="How did you pay?"
                )

            # Category selection
            categories = self._get_expense_categories()
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                category = st.selectbox(
                    "Category",
                    options=categories,
                    help="What type of expense is this?"
                )
            
            with col2:
                subcategory = st.text_input(
                    "Subcategory (Optional)",
                    placeholder="e.g., Coffee, Gas, Netflix",
                    help="Optional: Add more detail"
                )

            # Description and merchant
            col1, col2 = st.columns(2)
            
            with col1:
                merchant = st.text_input(
                    "Merchant/Store (Optional)",
                    placeholder="e.g., Starbucks, Walmart",
                    help="Where did you spend?"
                )
            
            with col2:
                location = st.text_input(
                    "Location (Optional)",
                    placeholder="e.g., Downtown, Airport",
                    help="Where were you?"
                )

            description = st.text_area(
                "Notes (Optional)",
                placeholder="Add any notes about this expense...",
                help="Optional notes"
            )

            # Tags
            tags = st.text_input(
                "Tags (Optional)",
                placeholder="e.g., work, vacation, essential",
                help="Comma-separated tags for filtering"
            )

            # Submit button
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                submitted = st.form_submit_button("💾 Save Expense", use_container_width=True)
            
            with col2:
                quick_add = st.form_submit_button("⚡ Save & Add Another", use_container_width=True)

            if submitted or quick_add:
                try:
                    expense_datetime = datetime.combine(expense_date, expense_time)
                    tag_list = [tag.strip() for tag in tags.split(",")] if tags else []
                    
                    self._save_expense(
                        date=expense_date,
                        time=expense_time,
                        amount=amount,
                        category=category,
                        subcategory=subcategory if subcategory else None,
                        merchant=merchant if merchant else None,
                        location=location if location else None,
                        payment_method=payment_method,
                        description=description if description else None,
                        tags=tag_list
                    )
                    
                    st.success(f"✅ Expense of ${amount:.2f} saved successfully!")
                    
                    # Show quick summary
                    new_today_total = self._get_today_total()
                    st.info(f"📊 Today's total is now ${new_today_total:,.2f}")
                    
                    if quick_add:
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"Error saving expense: {str(e)}")
                    logger.error(f"Error saving expense: {e}", exc_info=True)

        # Recent expenses preview
        st.markdown("---")
        st.markdown("### Recent Expenses (Last 5)")
        recent_expenses = self._get_recent_expenses(limit=5)
        
        if recent_expenses:
            for expense in recent_expenses:
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.text(f"{expense['category']} - {expense.get('merchant', 'N/A')}")
                with col2:
                    st.text(f"${expense['amount']:.2f}")
                with col3:
                    st.text(expense['date'])
                with col4:
                    if st.button("🗑️", key=f"del_{expense['id']}"):
                        self._delete_expense(expense['id'])
                        st.rerun()
        else:
            st.info("No expenses recorded yet. Add your first expense above!")

    def _render_expense_history_tab(self) -> None:
        """Render tab showing expense history with filters."""
        st.subheader("Expense History")
        st.markdown("View and filter your expense records")

        # Filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=date.today() - timedelta(days=30),
                help="Filter from this date"
            )
        
        with col2:
            end_date = st.date_input(
                "End Date",
                value=date.today(),
                help="Filter to this date"
            )
        
        with col3:
            categories = self._get_expense_categories()
            category_filter = st.multiselect(
                "Categories",
                options=categories,
                help="Filter by category"
            )
        
        with col4:
            payment_filter = st.multiselect(
                "Payment Method",
                options=["Cash", "Credit Card", "Debit Card", "Mobile Payment", "Bank Transfer", "Other"],
                help="Filter by payment method"
            )

        # Additional filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_amount = st.number_input("Min Amount ($)", min_value=0.0, value=0.0)
        
        with col2:
            max_amount = st.number_input("Max Amount ($)", min_value=0.0, value=10000.0)
        
        with col3:
            search_text = st.text_input("Search", placeholder="Merchant, description, tags...")

        st.markdown("---")

        # Get filtered expenses
        expenses = self._get_expenses(
            start_date=start_date,
            end_date=end_date,
            categories=category_filter if category_filter else None,
            payment_methods=payment_filter if payment_filter else None,
            min_amount=min_amount,
            max_amount=max_amount,
            search_text=search_text if search_text else None
        )

        if expenses:
            # Summary metrics
            total_expenses = sum(e['amount'] for e in expenses)
            avg_expense = total_expenses / len(expenses)
            max_expense = max(e['amount'] for e in expenses)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Expenses", f"${total_expenses:,.2f}")
            col2.metric("# of Transactions", len(expenses))
            col3.metric("Average", f"${avg_expense:.2f}")
            col4.metric("Largest", f"${max_expense:.2f}")

            st.markdown("---")

            # Convert to DataFrame for display
            df = pd.DataFrame(expenses)
            
            # Format display
            display_df = df[[
                'date', 'time', 'category', 'subcategory', 'amount', 
                'merchant', 'payment_method', 'description'
            ]].copy()
            
            display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:.2f}")
            display_df.columns = [
                'Date', 'Time', 'Category', 'Subcategory', 'Amount', 
                'Merchant', 'Payment', 'Notes'
            ]
            
            # Display with sorting
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=400
            )

            # Export options
            col1, col2 = st.columns([3, 1])
            with col2:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Export to CSV",
                    data=csv,
                    file_name=f"expenses_{start_date}_to_{end_date}.csv",
                    mime="text/csv"
                )

        else:
            st.info("No expenses found for the selected filters.")

    def _render_analytics_tab(self) -> None:
        """Render tab with expense analytics and visualizations."""
        st.subheader("Expense Analytics")
        st.markdown("Analyze your spending patterns")

        # Date range selector
        col1, col2 = st.columns([3, 1])
        
        with col1:
            date_range = st.selectbox(
                "Time Period",
                options=[
                    "Last 7 Days",
                    "Last 30 Days",
                    "Last 90 Days",
                    "This Month",
                    "Last Month",
                    "This Year",
                    "Custom Range"
                ]
            )
        
        with col2:
            refresh = st.button("🔄 Refresh", use_container_width=True)

        # Handle custom range
        if date_range == "Custom Range":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
            with col2:
                end_date = st.date_input("End Date", value=date.today())
        else:
            start_date, end_date = self._get_date_range(date_range)

        st.markdown("---")

        # Get data for analytics
        expenses = self._get_expenses(start_date=start_date, end_date=end_date)

        if not expenses:
            st.info("No expense data available for this period.")
            return

        df = pd.DataFrame(expenses)
        df['amount'] = pd.to_numeric(df['amount'])
        df['date'] = pd.to_datetime(df['date'])

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total = df['amount'].sum()
        daily_avg = total / ((end_date - start_date).days + 1)
        largest = df['amount'].max()
        num_transactions = len(df)
        
        col1.metric("Total Spent", f"${total:,.2f}")
        col2.metric("Daily Average", f"${daily_avg:.2f}")
        col3.metric("Largest Expense", f"${largest:.2f}")
        col4.metric("Transactions", num_transactions)

        st.markdown("---")

        # Visualization 1: Spending by Category (Pie Chart)
        st.markdown("### 📊 Spending by Category")
        
        category_totals = df.groupby('category')['amount'].sum().sort_values(ascending=False)
        
        fig_pie = px.pie(
            values=category_totals.values,
            names=category_totals.index,
            title="",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>$%{value:.2f}<br>%{percent}<extra></extra>'
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        # Show category breakdown table
        with st.expander("📋 Category Breakdown"):
            category_df = pd.DataFrame({
                'Category': category_totals.index,
                'Amount': category_totals.values,
                'Percentage': (category_totals.values / total * 100).round(2),
                'Transactions': df.groupby('category').size()[category_totals.index].values
            })
            category_df['Amount'] = category_df['Amount'].apply(lambda x: f"${x:,.2f}")
            category_df['Percentage'] = category_df['Percentage'].apply(lambda x: f"{x}%")
            st.dataframe(category_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Visualization 2: Daily Spending Trend
        st.markdown("### 📈 Daily Spending Trend")
        
        daily_spending = df.groupby('date')['amount'].sum().reset_index()
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=daily_spending['date'],
            y=daily_spending['amount'],
            mode='lines+markers',
            name='Daily Total',
            line=dict(color='#FF6B6B', width=2),
            marker=dict(size=6),
            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>$%{y:.2f}<extra></extra>'
        ))
        
        # Add average line
        avg_line = daily_spending['amount'].mean()
        fig_line.add_hline(
            y=avg_line,
            line_dash="dash",
            line_color="green",
            annotation_text=f"Average: ${avg_line:.2f}",
            annotation_position="right"
        )
        
        fig_line.update_layout(
            xaxis_title="Date",
            yaxis_title="Amount ($)",
            hovermode='x unified',
            showlegend=True
        )
        st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("---")

        # Visualization 3: Category Comparison (Bar Chart)
        st.markdown("### 📊 Category Comparison")
        
        fig_bar = px.bar(
            category_totals.reset_index(),
            x='category',
            y='amount',
            title="",
            color='amount',
            color_continuous_scale='Reds',
            labels={'category': 'Category', 'amount': 'Amount ($)'}
        )
        fig_bar.update_traces(hovertemplate='<b>%{x}</b><br>$%{y:.2f}<extra></extra>')
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

        # Visualization 4: Payment Method Distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💳 Payment Methods")
            payment_totals = df.groupby('payment_method')['amount'].sum()
            
            fig_payment = px.bar(
                payment_totals.reset_index(),
                x='payment_method',
                y='amount',
                title="",
                color='payment_method',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_payment.update_layout(showlegend=False, xaxis_title="", yaxis_title="Amount ($)")
            st.plotly_chart(fig_payment, use_container_width=True)
        
        with col2:
            st.markdown("### 🏪 Top Merchants")
            merchant_totals = df[df['merchant'].notna()].groupby('merchant')['amount'].sum().nlargest(10)
            
            if not merchant_totals.empty:
                fig_merchant = px.bar(
                    merchant_totals.reset_index(),
                    y='merchant',
                    x='amount',
                    orientation='h',
                    title="",
                    color='amount',
                    color_continuous_scale='Blues'
                )
                fig_merchant.update_layout(showlegend=False, xaxis_title="Amount ($)", yaxis_title="")
                st.plotly_chart(fig_merchant, use_container_width=True)
            else:
                st.info("No merchant data available")

        st.markdown("---")

        # Visualization 5: Weekly Heatmap
        st.markdown("### 🗓️ Spending Heatmap")
        
        df['day_of_week'] = df['date'].dt.day_name()
        df['hour'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.hour
        
        # Create day/hour heatmap
        heatmap_data = df.groupby(['day_of_week', 'hour'])['amount'].sum().unstack(fill_value=0)
        
        # Reorder days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        heatmap_data = heatmap_data.reindex(day_order)
        
        fig_heatmap = px.imshow(
            heatmap_data,
            labels=dict(x="Hour of Day", y="Day of Week", color="Amount ($)"),
            x=[f"{h}:00" for h in heatmap_data.columns],
            y=heatmap_data.index,
            color_continuous_scale='YlOrRd',
            aspect='auto'
        )
        fig_heatmap.update_xaxes(side="bottom")
        st.plotly_chart(fig_heatmap, use_container_width=True)

        st.markdown("---")

        # Insights section
        st.markdown("### 💡 Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top spending day
            top_day = daily_spending.loc[daily_spending['amount'].idxmax()]
            st.info(f"**Highest spending day:** {top_day['date'].strftime('%Y-%m-%d')} (${top_day['amount']:.2f})")
            
            # Most frequent category
            top_category = df['category'].mode()[0]
            st.info(f"**Most frequent category:** {top_category} ({len(df[df['category'] == top_category])} transactions)")
        
        with col2:
            # Average transaction size
            avg_transaction = df['amount'].mean()
            st.info(f"**Average transaction:** ${avg_transaction:.2f}")
            
            # Most expensive category
            most_expensive_cat = category_totals.idxmax()
            st.info(f"**Highest spending category:** {most_expensive_cat} (${category_totals[most_expensive_cat]:,.2f})")

    def _render_manage_categories_tab(self) -> None:
        """Render tab for managing expense categories."""
        st.subheader("Manage Expense Categories")
        st.markdown("Customize your expense categories")

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Current Categories")
            
            categories = self._get_expense_categories()
            
            for category in categories:
                col_a, col_b, col_c = st.columns([3, 1, 1])
                with col_a:
                    st.text(f"📁 {category}")
                with col_b:
                    # Count expenses in this category
                    count = self._get_category_expense_count(category)
                    st.caption(f"{count} expenses")
                with col_c:
                    if st.button("🗑️", key=f"delete_cat_{category}"):
                        try:
                            self._delete_category(category)
                            st.success(f"Category '{category}' deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Cannot delete category: {str(e)}")
        
        with col2:
            st.markdown("### Add New Category")
            
            with st.form("add_category_form"):
                new_category = st.text_input(
                    "Category Name",
                    placeholder="e.g., Healthcare, Education",
                    help="Enter a unique category name"
                )
                
                category_icon = st.text_input(
                    "Icon (Optional)",
                    placeholder="🏥",
                    help="Optional emoji icon"
                )
                
                category_description = st.text_area(
                    "Description (Optional)",
                    placeholder="What expenses belong in this category?",
                    help="Optional description"
                )
                
                category_color = st.color_picker(
                    "Color",
                    value="#FF6B6B",
                    help="Choose a color for charts"
                )
                
                submitted = st.form_submit_button("➕ Add Category", use_container_width=True)
                
                if submitted:
                    if not new_category:
                        st.error("Please enter a category name")
                    elif new_category in categories:
                        st.error(f"Category '{new_category}' already exists")
                    else:
                        try:
                            self._add_category(
                                name=new_category,
                                icon=category_icon if category_icon else None,
                                description=category_description if category_description else None,
                                color=category_color
                            )
                            st.success(f"✅ Category '{new_category}' added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding category: {str(e)}")

        st.markdown("---")
        
        # Default categories suggestion
        with st.expander("💡 Suggested Categories"):
            st.markdown("""
            **Common expense categories:**
            - 🏠 Housing (Rent, Mortgage, Utilities)
            - 🍕 Food & Dining (Groceries, Restaurants)
            - 🚗 Transportation (Gas, Public Transit, Parking)
            - 🎉 Entertainment (Movies, Events, Hobbies)
            - 👕 Shopping (Clothing, Electronics, Home)
            - 🏥 Healthcare (Medical, Pharmacy, Insurance)
            - 📚 Education (Books, Courses, Supplies)
            - 💼 Work (Office, Business Travel)
            - ✈️ Travel (Flights, Hotels, Vacation)
            - 🎁 Gifts & Donations
            - 💰 Financial (Fees, Subscriptions)
            - 🐕 Pets
            - 🔧 Maintenance & Repairs
            - 📱 Communications (Phone, Internet)
            - 🏋️ Fitness & Wellness
            """)

    # Helper methods
    
    def _get_today_total(self) -> float:
        """Get total expenses for today."""
        try:
            expenses = self._get_expenses(start_date=date.today(), end_date=date.today())
            return sum(e['amount'] for e in expenses)
        except Exception as e:
            logger.error(f"Error getting today's total: {e}")
            return 0.0

    def _get_week_total(self) -> float:
        """Get total expenses for this week."""
        try:
            start = date.today() - timedelta(days=date.today().weekday())
            expenses = self._get_expenses(start_date=start, end_date=date.today())
            return sum(e['amount'] for e in expenses)
        except Exception as e:
            logger.error(f"Error getting week total: {e}")
            return 0.0

    def _get_month_total(self) -> float:
        """Get total expenses for this month."""
        try:
            start = date.today().replace(day=1)
            expenses = self._get_expenses(start_date=start, end_date=date.today())
            return sum(e['amount'] for e in expenses)
        except Exception as e:
            logger.error(f"Error getting month total: {e}")
            return 0.0

    def _get_date_range(self, range_name: str) -> tuple:
        """Convert range name to start and end dates."""
        today = date.today()
        
        if range_name == "Last 7 Days":
            return today - timedelta(days=7), today
        elif range_name == "Last 30 Days":
            return today - timedelta(days=30), today
        elif range_name == "Last 90 Days":
            return today - timedelta(days=90), today
        elif range_name == "This Month":
            return today.replace(day=1), today
        elif range_name == "Last Month":
            last_month = today.replace(day=1) - timedelta(days=1)
            return last_month.replace(day=1), last_month
        elif range_name == "This Year":
            return today.replace(month=1, day=1), today
        else:
            return today - timedelta(days=30), today

    def _save_expense(
        self,
        date: date,
        time: datetime.time,
        amount: float,
        category: str,
        subcategory: Optional[str],
        merchant: Optional[str],
        location: Optional[str],
        payment_method: str,
        description: Optional[str],
        tags: list
    ) -> None:
        """Save a new expense to the database."""
        # Placeholder - implement based on your service layer
        self.service.save_expense(
            date=date,
            time=time,
            amount=amount,
            category=category,
            subcategory=subcategory,
            merchant=merchant,
            location=location,
            payment_method=payment_method,
            description=description,
            tags=tags
        )
        logger.info(f"Saved expense: ${amount} in {category}")

    def _get_expenses(
        self,
        start_date: date,
        end_date: date,
        categories: Optional[list] = None,
        payment_methods: Optional[list] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        search_text: Optional[str] = None
    ) -> list:
        """Get filtered expenses from database."""
        # Placeholder - implement based on your service layer
        return self.service.get_expenses(
            start_date=start_date,
            end_date=end_date,
            categories=categories,
            payment_methods=payment_methods,
            min_amount=min_amount,
            max_amount=max_amount,
            search_text=search_text
        )

    def _get_recent_expenses(self, limit: int = 5) -> list:
        """Get most recent expenses."""
        # Placeholder - implement based on your service layer
        return self.service.get_recent_expenses(limit=limit)

    def _delete_expense(self, expense_id: int) -> None:
        """Delete an expense."""
        # Placeholder - implement based on your service layer
        self.service.delete_expense(expense_id)
        logger.info(f"Deleted expense ID: {expense_id}")

    def _get_expense_categories(self) -> list:
        """Get list of expense categories."""
        # Placeholder - implement based on your service layer
        return self.service.get_expense_categories()

    def _get_category_expense_count(self, category: str) -> int:
        """Get count of expenses in a category."""
        # Placeholder - implement based on your service layer
        return self.service.get_category_expense_count(category)

    def _delete_category(self, category: str) -> None:
        """Delete an expense category."""
        # Placeholder - implement based on your service layer
        self.service.delete_expense_category(category)

    def _add_category(
        self,
        name: str,
        icon: Optional[str],
        description: Optional[str],
        color: str
    ) -> None:
        """Add a new expense category."""
        # Placeholder - implement based on your service layer
        self.service.add_expense_category(
            name=name,
            icon=icon,
            description=description,
            color=color
        )
        logger.info(f"Added category: {name}")