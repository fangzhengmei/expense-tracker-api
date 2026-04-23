import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    Enum as SQLEnum, Boolean, func
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class CategoryType(str, enum.Enum):
    EXPENSE = "expense"
    INCOME = "income"


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    type = Column(SQLEnum(CategoryType), nullable=False, default=CategoryType.EXPENSE)
    color = Column(String(7), nullable=False, default="#6366F1")
    icon = Column(String(50), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    ledger_id = Column(
        Integer,
        ForeignKey("ledgers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
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

    ledger = relationship("Ledger", back_populates="categories")
    expenses = relationship("Expense", back_populates="category")

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


DEFAULT_EXPENSE_CATEGORIES = [
    {"name": "餐饮", "color": "#EF4444", "icon": "food"},
    {"name": "交通", "color": "#F59E0B", "icon": "car"},
    {"name": "购物", "color": "#8B5CF6", "icon": "shopping"},
    {"name": "娱乐", "color": "#EC4899", "icon": "game"},
    {"name": "居住", "color": "#06B6D4", "icon": "home"},
    {"name": "通讯", "color": "#10B981", "icon": "phone"},
    {"name": "医疗", "color": "#DC2626", "icon": "heart"},
    {"name": "教育", "color": "#4F46E5", "icon": "book"},
    {"name": "人情", "color": "#F97316", "icon": "gift"},
    {"name": "其他", "color": "#6B7280", "icon": "other"},
]

DEFAULT_INCOME_CATEGORIES = [
    {"name": "工资", "color": "#10B981", "icon": "salary"},
    {"name": "奖金", "color": "#F59E0B", "icon": "bonus"},
    {"name": "投资", "color": "#8B5CF6", "icon": "invest"},
    {"name": "兼职", "color": "#06B6D4", "icon": "parttime"},
    {"name": "其他", "color": "#6B7280", "icon": "other"},
]
