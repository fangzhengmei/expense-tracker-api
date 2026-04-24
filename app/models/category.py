from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, DateTime, func, Index
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)

    name = Column(String(50), nullable=False)

    icon = Column(String(20), default="📝")

    color = Column(String(7), default="#6B7280")

    is_default = Column(Boolean, default=False, nullable=False)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
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

    __table_args__ = (
        Index("idx_categories_user_id", "user_id"),
        Index("idx_categories_is_default", "is_default"),
    )
