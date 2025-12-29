from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from sqlalchemy import CheckConstraint, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Asset(Base):
    """
    Represents a financial asset (mutual fund, crypto, ETF, etc.).

    Attributes:
        asset_id: Primary key
        name: Unique name of the asset
        asset_type: Type of asset (Mutual Fund, Crypto, Bond, ETF, etc.)
        currency: Currency denomination (default: EUR)
        description: Optional description
        created_at: When the asset was added
        values: Relationship to AssetValue records
    """

    __tablename__ = "assets"

    asset_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(), nullable=False)

    # Relationships
    values: Mapped[list["AssetValue"]] = relationship(back_populates="asset", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Asset(id={self.asset_id}, name='{self.name}', type='{self.asset_type}')>"


class AssetValue(Base):
    """
    Represents the value of an asset at a specific point in time.

    Attributes:
        value_id: Primary key
        date: Date of valuation
        asset_id: Foreign key to Asset
        amount_invested: Total amount invested in this asset
        countervalue: Current market value
        asset: Relationship to Asset
    """

    __tablename__ = "asset_values"

    value_id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(nullable=False)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.asset_id", ondelete="CASCADE"), nullable=False)
    amount_invested: Mapped[float] = mapped_column(Float, nullable=False)
    countervalue: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    asset: Mapped["Asset"] = relationship(back_populates="values")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("date", "asset_id", name="uq_date_asset"),
        Index("idx_asset_values_date", "date"),
        Index("idx_asset_values_asset_id", "asset_id"),
        CheckConstraint("amount_invested >= 0", name="check_invested_positive"),
        CheckConstraint("countervalue >= 0", name="check_countervalue_positive"),
    )

    @property
    def profit_loss(self) -> float:
        """Calculate profit/loss."""
        return self.countervalue - self.amount_invested

    @property
    def return_percentage(self) -> float:
        """Calculate return percentage."""
        if self.amount_invested == 0:
            return 0.0
        return (self.profit_loss / self.amount_invested) * 100

    def __repr__(self) -> str:
        return f"<AssetValue(date='{self.date}', asset_id={self.asset_id}, value={self.countervalue})>"


class MonthlyTransaction(Base):
    """
    Represents monthly income, expenses, and cash position.

    Attributes:
        transaction_id: Primary key
        date: Month date (first day of month)
        income: Monthly income
        expenses: Monthly expenses
        cash: Cash position at end of month
        notes: Optional notes
    """

    __tablename__ = "monthly_transactions"

    transaction_id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(nullable=False, unique=True)
    income: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expenses: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cash: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500))

    # Add check constraints
    __table_args__ = (
        CheckConstraint("income >= 0", name="check_income_positive"),
        CheckConstraint("expenses >= 0", name="check_expenses_positive"),
        Index("idx_monthly_transactions_date", "date"),
    )

    @property
    def net_cashflow(self) -> float:
        """Calculate net cashflow (income - expenses)."""
        return self.income - self.expenses

    def __repr__(self) -> str:
        return f"<MonthlyTransaction(date='{self.date}', income={self.income}, expenses={self.expenses})>"
