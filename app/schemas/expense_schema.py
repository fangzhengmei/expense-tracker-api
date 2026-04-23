from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime
from app.models.enums import ExpenseStatus


class ExpenseCreate(BaseModel):
    amount: Decimal = Field(..., ge=0)
    description: str = Field(..., min_length=1, max_length=255)


class ExpenseUpdate(BaseModel):
    amount: Decimal | None = Field(None, ge=0)
    description: str | None = Field(None, min_length=1, max_length=255)


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    description: str
    status: ExpenseStatus
    user_id: int
    created_at: datetime
    updated_at: datetime


class ApprovalCreate(BaseModel):
    expense_id: int
    status: ExpenseStatus
    comment: str | None = Field(None, max_length=500)


class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    expense_id: int
    approver_id: int
    status: ExpenseStatus
    comment: str | None
    created_at: datetime


class ExpenseWithApprovalsOut(ExpenseOut):
    approvals: list[ApprovalOut] = []