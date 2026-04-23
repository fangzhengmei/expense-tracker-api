from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from typing import Optional
from datetime import datetime


class ExpenseCreate(BaseModel):
    amount: Decimal = Field(..., ge=0)
    description: str = Field(..., min_length=1, max_length=255)
    category_id: Optional[int] = Field(None, gt=0)


class ExpenseUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    category_id: Optional[int] = Field(None, gt=0)


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    description: str
    category_id: Optional[int]
    created_at: datetime


class ExpenseWithCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    description: str
    category_id: Optional[int]
    category_name: Optional[str]
    created_at: datetime


class ExpenseWithBudgetOut(BaseModel):
    expense: ExpenseOut
    budget_info: Optional[dict] = None
