from pydantic import BaseModel, Field, ConfigDict, field_serializer
from decimal import Decimal
from typing import Optional, List
from app.schemas.tag_schema import TagOut


class ExpenseCreate(BaseModel):
    amount: Decimal = Field(..., ge=0)
    description: str = Field(..., min_length=1, max_length=255)
    tag_ids: Optional[List[int]] = Field(None, description="List of tag IDs to associate with this expense")


class ExpenseUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    tag_ids: Optional[List[int]] = Field(None, description="List of tag IDs to associate with this expense (replaces existing tags)")


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    description: str
    tags: Optional[List[TagOut]] = []

    @field_serializer('amount')
    def serialize_amount(self, v: Decimal) -> float:
        return float(v)