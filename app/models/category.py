from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)

    name = Column(String(50), nullable=False)

    icon = Column(String(50), nullable=True)

    color = Column(String(20), nullable=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
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

    user = relationship("User", back_populates="categories")
    expenses = relationship("Expense", back_populates="category")
    budgets = relationship("Budget", back_populates="category")

    __table_args__ = (
        UniqueConstraint("name", "user_id", name="uq_category_name_per_user"),
        Index("idx_categories_user_id", "user_id"),
    )
