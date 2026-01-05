from contextlib import contextmanager
from datetime import date, datetime
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy import Engine, and_, desc, func, or_, select
from sqlalchemy.orm import sessionmaker

from src.model.models import Asset, AssetValue, Expense, ExpenseCategory, MonthlyTransaction
from src.utils.database import init_database

logger = logging.getLogger(__name__)

class FinanceService:
    """
    Service layer for finance database operations.
    Provides high-level methods for managing financial data.
    """

    def __init__(self, engine: Engine):
        """
        Initialize the finance service.

        Args:
            engine: SQLAlchemy engine instance
        """
        self.engine = engine
        self.SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    @contextmanager
    def get_session(self):
        """Context manager for database sessions."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_tables(self):
        """Create all database tables."""
        init_database(self.engine)

    # Asset operations

    def add_asset(self, name: str, asset_type: str, currency: str = "EUR", description: str | None = None) -> Asset:
        """
        Add a new asset or return existing one.

        Args:
            name: Asset name
            asset_type: Type of asset
            currency: Currency code
            description: Optional description

        Returns:
            Asset instance
        """
        with self.get_session() as session:
            # Check if asset exists
            stmt = select(Asset).where(Asset.name == name)
            existing_asset = session.scalars(stmt).first()

            if existing_asset:
                return existing_asset

            # Create new asset
            asset = Asset(name=name, asset_type=asset_type, currency=currency, description=description)
            session.add(asset)
            session.flush()
            session.refresh(asset)
            return asset

    def get_asset_by_name(self, name: str) -> Asset | None:
        """Get an asset by name."""
        with self.get_session() as session:
            stmt = select(Asset).where(Asset.name == name)
            return session.scalars(stmt).first()

    def get_all_assets(self) -> list[Asset]:
        """Get all assets."""
        with self.get_session() as session:
            stmt = select(Asset).order_by(Asset.asset_type, Asset.name)
            return list(session.scalars(stmt).all())

    def get_assets_by_type(self, asset_type: str) -> list[Asset]:
        """Get all assets of a specific type."""
        with self.get_session() as session:
            stmt = select(Asset).where(Asset.asset_type == asset_type)
            return list(session.scalars(stmt).all())

    # Asset value operations
    def add_asset_value(self, date: datetime, asset: Asset, amount_invested: float, countervalue: float) -> AssetValue:
        """
        Add or update an asset value.

        Args:
            date: Valuation date
            asset: Asset instance
            amount_invested: Amount invested
            countervalue: Current market value

        Returns:
            AssetValue instance
        """
        with self.get_session() as session:
            # Merge asset into this session
            asset = session.merge(asset)

            # Check if value exists
            stmt = select(AssetValue).where(and_(AssetValue.date == date, AssetValue.asset_id == asset.asset_id))
            existing = session.scalars(stmt).first()

            if existing:
                # Update existing
                existing.amount_invested = amount_invested
                existing.countervalue = countervalue
                session.flush()
                session.refresh(existing)
                return existing

            # Create new
            value = AssetValue(
                date=date, asset_id=asset.asset_id, amount_invested=amount_invested, countervalue=countervalue
            )
            session.add(value)
            session.flush()
            session.refresh(value)
            return value

    def get_asset_values(
        self, asset: Asset | None = None, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> list[AssetValue]:
        """Get asset values with optional filters."""
        with self.get_session() as session:
            stmt = select(AssetValue)

            if asset:
                asset = session.merge(asset)
                stmt = stmt.where(AssetValue.asset_id == asset.asset_id)
            if start_date:
                stmt = stmt.where(AssetValue.date >= start_date)
            if end_date:
                stmt = stmt.where(AssetValue.date <= end_date)

            stmt = stmt.order_by(AssetValue.date)
            return list(session.scalars(stmt).all())

    # MonthlyTransaction operations
    def add_monthly_transaction(
        self, date: datetime, income: float = 0.0, expenses: float = 0.0, cash: float = 0.0, notes: str | None = None
    ) -> MonthlyTransaction:
        """
        Add or update a monthly transaction.

        Args:
            date: Transaction date
            income: Monthly income
            expenses: Monthly expenses
            cash: Cash position
            notes: Optional notes

        Returns:
            MonthlyTransaction instance
        """
        with self.get_session() as session:
            # Check if transaction exists
            stmt = select(MonthlyTransaction).where(MonthlyTransaction.date == date)
            existing = session.scalars(stmt).first()

            if existing:
                # Update existing
                existing.income = income
                existing.expenses = expenses
                existing.cash = cash
                existing.notes = notes
                session.flush()
                session.refresh(existing)
                return existing

            # Create new
            transaction = MonthlyTransaction(date=date, income=income, expenses=expenses, cash=cash, notes=notes)
            session.add(transaction)
            session.flush()
            session.refresh(transaction)
            return transaction

    def get_monthly_transactions(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> list[MonthlyTransaction]:
        """Get monthly transactions within a date range."""
        with self.get_session() as session:
            stmt = select(MonthlyTransaction)

            if start_date:
                stmt = stmt.where(MonthlyTransaction.date >= start_date)
            if end_date:
                stmt = stmt.where(MonthlyTransaction.date <= end_date)

            stmt = stmt.order_by(MonthlyTransaction.date)
            return list(session.scalars(stmt).all())

    # Analytics methods

    def get_portfolio_summary(self, date: Optional[datetime] = None) -> list[dict[str, Any]]:
        """
        Get portfolio summary for a specific date.

        Args:
            date: Date for summary (defaults to latest)

        Returns:
            List of dictionaries with portfolio data
        """
        with self.get_session() as session:
            if date is None:
                # Get the portfolio situation at the current date
                stmt = select(func.max(AssetValue.date))
                date = session.scalar(stmt)

            if date is None:
                return []

            # Query asset values with asset info
            stmt = (
                select(
                    Asset.name, Asset.asset_type, Asset.currency, AssetValue.amount_invested, AssetValue.countervalue
                )
                .join(AssetValue.asset)
                .where(AssetValue.date == date)
                .order_by(Asset.asset_type, Asset.name)
            )

            results = session.execute(stmt).all()

            summary = []
            for row in results:
                profit_loss = row.countervalue - row.amount_invested
                return_pct = (profit_loss / row.amount_invested * 100) if row.amount_invested > 0 else 0.0

                summary.append(
                    {
                        "name": row.name,
                        "asset_type": row.asset_type,
                        "currency": row.currency,
                        "amount_invested": row.amount_invested,
                        "countervalue": row.countervalue,
                        "profit_loss": profit_loss,
                        "return_percentage": return_pct,
                    }
                )

            return summary

    def get_portfolio_history(self, date: Optional[datetime] = None) -> list[dict[str, Any]]:
        """Get portfolio value history over time."""
        with self.get_session() as session:
            # Aggregate by date
            stmt = (
                select(
                    AssetValue.date,
                    func.sum(AssetValue.amount_invested).label("total_invested"),
                    func.sum(AssetValue.countervalue).label("total_value"),
                )
                .group_by(AssetValue.date)
                .order_by(AssetValue.date)
            )

            results = session.execute(stmt).all()

            return [
                {
                    "date": row.date,
                    "total_invested": row.total_invested,
                    "total_value": row.total_value,
                    "profit_loss": row.total_value - row.total_invested,
                }
                for row in results
            ]

    def get_asset_type_allocation(self, date: Optional[datetime] = None) -> list[dict[str, Any]]:
        """Get portfolio allocation by asset type."""
        with self.get_session() as session:
            if date is None:
                # Get latest date
                stmt = select(func.max(AssetValue.date))
                date = session.scalar(stmt)

            if date is None:
                return []

            # Aggregate by asset type
            stmt = (
                select(
                    Asset.asset_type,
                    func.count(Asset.asset_id).label("num_assets"),
                    func.sum(AssetValue.amount_invested).label("total_invested"),
                    func.sum(AssetValue.countervalue).label("total_value"),
                )
                .join(AssetValue.asset)
                .where(AssetValue.date == date)
                .group_by(Asset.asset_type)
                .order_by(desc("total_value"))
            )

            results = session.execute(stmt).all()

            # Calculate total for percentages
            total_value = sum(row.total_value for row in results)

            return [
                {
                    "asset_type": row.asset_type,
                    "num_assets": row.num_assets,
                    "total_invested": row.total_invested,
                    "total_value": row.total_value,
                    "profit_loss": row.total_value - row.total_invested,
                    "percentage": (row.total_value / total_value * 100) if total_value > 0 else 0,
                }
                for row in results
            ]

    def get_best_worst_performers(self, date: Optional[datetime] = None) -> dict[str, dict[str, Any]]:
        """Get best and worst performing assets."""
        summary = self.get_portfolio_summary(date)

        if not summary:
            return {"best": None, "worst": None}

        # Filter out assets with no investment
        invested_assets = [s for s in summary if s["amount_invested"] > 0]

        if not invested_assets:
            return {"best": None, "worst": None}

        # Sort by return percentage
        sorted_assets = sorted(invested_assets, key=lambda x: x["return_percentage"], reverse=True)

        return {"best": sorted_assets[0], "worst": sorted_assets[-1]}

    # ==================== Expense Tracking Methods ====================

    def save_expense(
        self,
        date: date,
        time: Optional[datetime],
        amount: float,
        category: str,
        subcategory: Optional[str] = None,
        merchant: Optional[str] = None,
        location: Optional[str] = None,
        payment_method: str = "Cash",
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """
        Save a new expense entry.
        
        Args:
            date: Date of expense
            time: Time of expense
            amount: Amount spent
            category: Expense category
            subcategory: Optional subcategory
            merchant: Optional merchant/store name
            location: Optional location
            payment_method: Payment method used
            description: Optional description
            tags: Optional list of tags
            
        Returns:
            ID of the created expense
        """
        session = self.get_session()
        try:
            expense = Expense(
                date=date,
                time=time,
                amount=amount,
                category=category,
                subcategory=subcategory,
                merchant=merchant,
                location=location,
                payment_method=payment_method,
                description=description,
                tags=tags or []
            )
            
            session.add(expense)
            session.commit()
            
            expense_id = expense.id
            logger.info(f"Saved expense ID {expense_id}: ${amount} in {category}")
            
            return expense_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save expense: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def get_expenses(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        categories: Optional[List[str]] = None,
        payment_methods: Optional[List[str]] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        search_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get expenses with optional filters.
        
        Args:
            start_date: Filter from this date
            end_date: Filter to this date
            categories: Filter by categories
            payment_methods: Filter by payment methods
            min_amount: Minimum amount filter
            max_amount: Maximum amount filter
            search_text: Search in merchant, description, tags
            
        Returns:
            List of expense dictionaries
        """
        session = self.get_session()
        try:
            query = session.query(Expense)

            # Apply filters
            if start_date:
                query = query.filter(Expense.date >= start_date)

            if end_date:
                query = query.filter(Expense.date <= end_date)

            if categories:
                query = query.filter(Expense.category.in_(categories))

            if payment_methods:
                query = query.filter(Expense.payment_method.in_(payment_methods))

            if min_amount is not None:
                query = query.filter(Expense.amount >= min_amount)

            if max_amount is not None:
                query = query.filter(Expense.amount <= max_amount)

            if search_text:
                search_pattern = f"%{search_text}%"
                query = query.filter(
                    or_(
                        Expense.merchant.like(search_pattern),
                        Expense.description.like(search_pattern),
                        Expense.subcategory.like(search_pattern)
                    )
                )

            # Order by date and time descending
            query = query.order_by(desc(Expense.date), desc(Expense.time))

            # Execute query and convert to dictionaries
            expenses = query.all()
            return [expense.to_dict() for expense in expenses]
            
        except Exception as e:
            logger.error(f"Failed to get expenses: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def get_recent_expenses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent expenses.
        
        Args:
            limit: Maximum number of expenses to return
            
        Returns:
            List of expense dictionaries
        """
        session = self.get_session()
        try:
            expenses = session.query(Expense)\
                .order_by(desc(Expense.date), desc(Expense.time))\
                .limit(limit)\
                .all()
            
            return [expense.to_dict() for expense in expenses]
            
        except Exception as e:
            logger.error(f"Failed to get recent expenses: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def delete_expense(self, expense_id: int) -> None:
        """
        Delete an expense.
        
        Args:
            expense_id: ID of expense to delete
        """
        session = self.get_session()
        try:
            expense = session.query(Expense).filter(Expense.id == expense_id).first()
            
            if expense:
                session.delete(expense)
                session.commit()
                logger.info(f"Deleted expense ID: {expense_id}")
            else:
                logger.warning(f"Expense ID {expense_id} not found")
                
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete expense: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def update_expense(self, expense_id: int, **kwargs) -> None:
        """
        Update an expense.
        
        Args:
            expense_id: ID of expense to update
            **kwargs: Fields to update
        """
        session = self.get_session()
        try:
            expense = session.query(Expense).filter(Expense.id == expense_id).first()
            
            if not expense:
                raise ValueError(f"Expense ID {expense_id} not found")
            
            # Update allowed fields
            allowed_fields = [
                'date', 'time', 'amount', 'category', 'subcategory',
                'merchant', 'location', 'payment_method', 'description', 'tags'
            ]
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(expense, field, value)
            
            session.commit()
            logger.info(f"Updated expense ID: {expense_id}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update expense: {e}", exc_info=True)
            raise
        finally:
            session.close()

    # ==================== Category Management Methods ====================

    def get_expense_categories(self, active_only: bool = True) -> List[str]:
        """
        Get list of expense categories.
        
        Args:
            active_only: Only return active categories
            
        Returns:
            List of category names
        """
        session = self.get_session()
        try:
            query = session.query(ExpenseCategory.name).order_by(ExpenseCategory.name)
            
            if active_only:
                query = query.filter(ExpenseCategory.active == True)
            
            categories = query.all()
            return [cat[0] for cat in categories]
            
        except Exception as e:
            logger.error(f"Failed to get expense categories: {e}", exc_info=True)
            # Return default categories if query fails
            return [
                "Food & Dining", "Transportation", "Shopping", "Entertainment",
                "Bills & Utilities", "Healthcare", "Travel", "Education",
                "Personal Care", "Other"
            ]
        finally:
            session.close()

    def add_expense_category(
        self,
        name: str,
        icon: Optional[str] = None,
        description: Optional[str] = None,
        color: str = "#FF6B6B"
    ) -> None:
        """
        Add a new expense category.
        
        Args:
            name: Category name
            icon: Optional emoji icon
            description: Optional description
            color: Category color (hex)
        """
        session = self.get_session()
        try:
            category = ExpenseCategory(
                name=name,
                icon=icon,
                description=description,
                color=color,
                active=True
            )
            
            session.add(category)
            session.commit()
            logger.info(f"Added expense category: {name}")
            
        except IntegrityError:
            session.rollback()
            raise ValueError(f"Category '{name}' already exists")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to add expense category: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def delete_expense_category(self, category_name: str) -> None:
        """
        Delete (deactivate) an expense category.
        
        Args:
            category_name: Name of category to delete
        """
        session = self.get_session()
        try:
            # Check if any expenses use this category
            expense_count = session.query(Expense)\
                .filter(Expense.category == category_name)\
                .count()
            
            if expense_count > 0:
                raise ValueError(
                    f"Cannot delete category '{category_name}' - "
                    f"it has {expense_count} expenses. Reassign expenses first."
                )
            
            # Soft delete (set active = False)
            category = session.query(ExpenseCategory)\
                .filter(ExpenseCategory.name == category_name)\
                .first()
            
            if category:
                category.active = False
                session.commit()
                logger.info(f"Deleted expense category: {category_name}")
            else:
                logger.warning(f"Category '{category_name}' not found")
                
        except ValueError:
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete expense category: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def get_category_expense_count(self, category: str) -> int:
        """
        Get count of expenses in a category.
        
        Args:
            category: Category name
            
        Returns:
            Number of expenses in category
        """
        session = self.get_session()
        try:
            count = session.query(Expense)\
                .filter(Expense.category == category)\
                .count()
            return count
            
        except Exception as e:
            logger.error(f"Failed to get category count: {e}", exc_info=True)
            return 0
        finally:
            session.close()

    # ==================== Statistics Methods ====================

    def get_expense_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get expense statistics for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary with statistics
        """
        session = self.get_session()
        try:
            query = session.query(Expense)
            
            if start_date:
                query = query.filter(Expense.date >= start_date)
            
            if end_date:
                query = query.filter(Expense.date <= end_date)
            
            expenses = query.all()
            
            if not expenses:
                return {
                    'total': 0,
                    'count': 0,
                    'average': 0,
                    'min': 0,
                    'max': 0,
                    'by_category': {}
                }
            
            amounts = [e.amount for e in expenses]
            
            # Calculate by category
            by_category = {}
            for expense in expenses:
                cat = expense.category
                if cat not in by_category:
                    by_category[cat] = {'total': 0, 'count': 0}
                by_category[cat]['total'] += expense.amount
                by_category[cat]['count'] += 1
            
            return {
                'total': sum(amounts),
                'count': len(amounts),
                'average': sum(amounts) / len(amounts),
                'min': min(amounts),
                'max': max(amounts),
                'by_category': by_category
            }
            
        except Exception as e:
            logger.error(f"Failed to get expense statistics: {e}", exc_info=True)
            raise
        finally:
            session.close()
