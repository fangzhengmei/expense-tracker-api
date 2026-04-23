from sqlalchemy import (
    Column, Integer, String, Numeric, CheckConstraint,
    ForeignKey, DateTime, func, Index
)
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.core.constants import DEFAULT_CURRENCY, SUPPORTED_CURRENCIES



class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)

    amount = Column(Numeric(10, 2), nullable=False)

    currency = Column(String(3), nullable=False, default=DEFAULT_CURRENCY)

    description = Column(String(255), nullable=False)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    user = relationship("User", back_populates="expenses")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="check_amount_positive"),
        CheckConstraint("length(trim(description)) > 0", name="check_description_not_empty"),
        Index("idx_expenses_user_id", "user_id"),
        Index("idx_expenses_created_at", "created_at"),
    )