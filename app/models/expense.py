from sqlalchemy import (
    Column, Integer, String, Numeric, CheckConstraint,
    ForeignKey, DateTime, func, Index, Text
)
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.models.enums import ExpenseStatus


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)

    amount = Column(Numeric(10, 2), nullable=False)

    description = Column(String(255), nullable=False)

    status = Column(String, default=ExpenseStatus.PENDING, nullable=False)

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
    approvals = relationship("Approval", back_populates="expense")

    __table_args__ = (
        CheckConstraint("amount >= 0", name="check_amount_positive"),
        CheckConstraint("length(trim(description)) > 0", name="check_description_not_empty"),
        Index("idx_expenses_user_id", "user_id"),
        Index("idx_expenses_created_at", "created_at"),
        Index("idx_expenses_status", "status"),
    )


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True)

    expense_id = Column(
        Integer,
        ForeignKey("expenses.id", ondelete="RESTRICT"),
        nullable=False
    )

    approver_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )

    status = Column(String, nullable=False)

    comment = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    expense = relationship("Expense", back_populates="approvals")
    approver = relationship("User", back_populates="approvals")

    __table_args__ = (
        Index("idx_approvals_expense_id", "expense_id"),
        Index("idx_approvals_approver_id", "approver_id"),
    )