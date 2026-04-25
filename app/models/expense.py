from sqlalchemy import (
    Column, Integer, String, Numeric, CheckConstraint,
    ForeignKey, DateTime, func, Index, Table
)
from sqlalchemy.orm import relationship

from app.db.database import Base


expense_tag = Table(
    "expense_tags",
    Base.metadata,
    Column(
        "expense_id",
        Integer,
        ForeignKey("expenses.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "tag_id",
        Integer,
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True
    )
)


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)

    amount = Column(Numeric(10, 2), nullable=False)

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
    tags = relationship(
        "Tag",
        secondary=expense_tag,
        back_populates="expenses"
    )

    __table_args__ = (
        CheckConstraint("amount >= 0", name="check_amount_positive"),
        CheckConstraint("length(trim(description)) > 0", name="check_description_not_empty"),
        Index("idx_expenses_user_id", "user_id"),
        Index("idx_expenses_created_at", "created_at"),
    )