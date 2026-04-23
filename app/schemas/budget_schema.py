from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal
from datetime import datetime


class BudgetCreate(BaseModel):
    amount: Decimal = Field(..., ge=0)
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    category_id: int = Field(..., gt=0)


class BudgetUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, ge=0)


class BudgetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    year: int
    month: int
    category_id: int


class BudgetWithUsageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    year: int
    month: int
    category_id: int
    category_name: str
    spent: Decimal
    remaining: Decimal
    percentage: float


class MonthlyBudgetSummary(BaseModel):
    year: int
    month: int
    total_budget: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    budgets: list[BudgetWithUsageOut]
