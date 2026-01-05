from datetime import datetime
import json

from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, Time, TypeDecorator, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.orm import relationship, validates

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

class JSONEncodedList(TypeDecorator):
    """Custom type for storing lists as JSON strings."""
    
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert list to JSON string when saving."""
        if value is not None:
            return json.dumps(value)
        return None

    def process_result_value(self, value, dialect):
        """Convert JSON string back to list when loading."""
        if value is not None:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []
        return []


class ExpenseCategory(Base):
    """Expense category model."""
    
    __tablename__ = 'expense_categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    icon = Column(String(10), nullable=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), default='#FF6B6B')  # Hex color code
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to expenses
    expenses = relationship('Expense', back_populates='category_obj', lazy='dynamic')

    def __repr__(self):
        return f"<ExpenseCategory(id={self.id}, name='{self.name}')>"

    @validates('color')
    def validate_color(self, key, color):
        """Validate hex color format."""
        if color and not color.startswith('#'):
            return f'#{color}'
        return color

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'icon': self.icon,
            'description': self.description,
            'color': self.color,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Expense(Base):
    """Individual expense record model."""
    
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    time = Column(Time, nullable=True)
    amount = Column(Float, nullable=False)
    category = Column(String(100), ForeignKey('expense_categories.name'), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    merchant = Column(String(200), nullable=True, index=True)
    location = Column(String(200), nullable=True)
    payment_method = Column(String(50), default='Cash', nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSONEncodedList, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to category
    category_obj = relationship('ExpenseCategory', back_populates='expenses')

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_date_category', 'date', 'category'),
        Index('idx_date_amount', 'date', 'amount'),
    )

    def __repr__(self):
        return f"<Expense(id={self.id}, date={self.date}, amount={self.amount}, category='{self.category}')>"

    @validates('amount')
    def validate_amount(self, key, amount):
        """Validate amount is positive."""
        if amount < 0:
            raise ValueError("Expense amount must be positive")
        return amount

    @validates('payment_method')
    def validate_payment_method(self, key, method):
        """Validate payment method."""
        valid_methods = [
            'Cash', 'Credit Card', 'Debit Card', 
            'Mobile Payment', 'Bank Transfer', 'Other'
        ]
        if method not in valid_methods:
            return 'Other'
        return method

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'time': self.time.isoformat() if self.time else None,
            'amount': self.amount,
            'category': self.category,
            'subcategory': self.subcategory,
            'merchant': self.merchant,
            'location': self.location,
            'payment_method': self.payment_method,
            'description': self.description,
            'tags': self.tags or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
class FinancialRecord(Base):
    """Monthly financial record model."""
    
    __tablename__ = 'financial_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    income = Column(Float, default=0.0)
    salary = Column(Float, default=0.0)
    other_income = Column(Float, default=0.0)
    expenses = Column(Float, default=0.0)
    cash = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to expense details
    expense_details = relationship(
        'ExpenseDetail', 
        back_populates='financial_record',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    def __repr__(self):
        return f"<FinancialRecord(id={self.id}, date={self.date}, income={self.income}, expenses={self.expenses})>"

    @property
    def net_income(self):
        """Calculate net income."""
        return self.income - self.expenses

    @property
    def savings_rate(self):
        """Calculate savings rate percentage."""
        if self.income > 0:
            return (self.net_income / self.income) * 100
        return 0.0

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'income': self.income,
            'salary': self.salary,
            'other_income': self.other_income,
            'expenses': self.expenses,
            'cash': self.cash,
            'notes': self.notes,
            'net_income': self.net_income,
            'savings_rate': self.savings_rate
        }

class ExpenseDetail(Base):
    """Detailed expense breakdown for financial records."""
    
    __tablename__ = 'expense_details'

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(Integer, ForeignKey('financial_records.id', ondelete='CASCADE'), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to financial record
    financial_record = relationship('FinancialRecord', back_populates='expense_details')

    __table_args__ = (
        Index('idx_expense_details_record', 'record_id'),
    )

    def __repr__(self):
        return f"<ExpenseDetail(id={self.id}, record_id={self.record_id}, category='{self.category}', amount={self.amount})>"

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'record_id': self.record_id,
            'category': self.category,
            'amount': self.amount
        }