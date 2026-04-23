from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime
from typing import Optional


class ExpenseCreate(BaseModel):
    amount: Decimal = Field(..., ge=0)
    description: str = Field(..., min_length=1, max_length=255)
    ledger_id: Optional[int] = Field(None, ge=1, description="账本ID，可选。如果不提供，将使用个人账本")


class ExpenseUpdate(BaseModel):
    amount: Decimal | None = Field(None, ge=0)
    description: str | None = Field(None, min_length=1, max_length=255)


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    description: str
    user_id: int
    ledger_id: int
    created_at: datetime
    updated_at: datetime


class ExpenseWithUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    description: str
    user_id: int
    user_email: str
    ledger_id: int
    created_at: datetime
    updated_at: datetime
