from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, func,
    UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)

    name = Column(String(50), nullable=False)

    color = Column(String(7), default="#6366f1", nullable=False)

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

    user = relationship("User", back_populates="tags")
    expenses = relationship(
        "Expense",
        secondary="expense_tags",
        back_populates="tags"
    )

    __table_args__ = (
        UniqueConstraint("name", "user_id", name="uq_tag_name_per_user"),
        Index("idx_tags_user_id", "user_id"),
    )
