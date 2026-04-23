from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime
from typing import Optional

from app.models.category import CategoryType


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    type: CategoryType = Field(default=CategoryType.EXPENSE)
    color: str = Field(default="#6366F1", min_length=7, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)
    sort_order: int = Field(default=0, ge=0)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, min_length=7, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: CategoryType
    color: str
    icon: Optional[str]
    sort_order: int
    is_default: bool
    is_active: bool
    ledger_id: int
    created_at: datetime
    updated_at: datetime


class CategoryWithStatsOut(CategoryOut):
    total_amount: Decimal = Decimal("0.00")
    count: int = 0
    percentage: float = 0.0


class CategoryStats(BaseModel):
    category_id: int
    category_name: str
    category_color: str
    category_icon: Optional[str]
    total_amount: Decimal
    count: int
    percentage: float
