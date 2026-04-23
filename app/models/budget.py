from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime, func, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True)

    amount = Column(Numeric(10, 2), nullable=False)

    year = Column(Integer, nullable=False)

    month = Column(Integer, nullable=False)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
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

    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")

    __table_args__ = (
        UniqueConstraint("user_id", "category_id", "year", "month", name="uq_budget_per_category_per_month"),
        CheckConstraint("amount >= 0", name="check_budget_amount_positive"),
        CheckConstraint("year >= 2000 AND year <= 2100", name="check_budget_year_valid"),
        CheckConstraint("month >= 1 AND month <= 12", name="check_budget_month_valid"),
        Index("idx_budgets_user_id", "user_id"),
        Index("idx_budgets_category_id", "category_id"),
        Index("idx_budgets_year_month", "year", "month"),
    )
