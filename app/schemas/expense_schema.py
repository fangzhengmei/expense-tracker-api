from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from app.schemas.category_schema import CategoryOut


class ExpenseCreate(BaseModel):
    amount: Decimal = Field(..., ge=0)
    description: str = Field(..., min_length=1, max_length=255)
    category_id: int | None = Field(None)


class ExpenseUpdate(BaseModel):
    amount: Decimal | None = Field(None, ge=0)
    description: str | None = Field(None, min_length=1, max_length=255)
    category_id: int | None = Field(None)


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    description: str
    category_id: int | None
    category: CategoryOut | None