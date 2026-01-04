from contextlib import contextmanager
from datetime import datetime
from typing import Any

from sqlalchemy import Engine, and_, desc, func, select
from sqlalchemy.orm import sessionmaker

from src.model.models import Asset, AssetValue, MonthlyTransaction
from src.utils.database import init_database


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

    def get_portfolio_summary(self, date: datetime | None = None) -> list[dict[str, Any]]:
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

    def get_portfolio_history(self) -> list[dict[str, Any]]:
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

    def get_asset_type_allocation(self, date: datetime | None = None) -> list[dict[str, Any]]:
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

    def get_best_worst_performers(self, date: datetime | None = None) -> dict[str, dict[str, Any]]:
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
