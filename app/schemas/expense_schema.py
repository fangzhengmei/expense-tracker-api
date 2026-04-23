from pydantic import BaseModel, Field, ConfigDict, field_validator
from decimal import Decimal
from typing import Optional

from app.core.constants import SUPPORTED_CURRENCIES, DEFAULT_CURRENCY


def validate_currency(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = v.upper()
    if v not in SUPPORTED_CURRENCIES:
        raise ValueError(f"Unsupported currency: {v}. Supported currencies: {SUPPORTED_CURRENCIES}")
    return v


class ExpenseCreate(BaseModel):
    amount: Decimal = Field(..., ge=0)
    currency: Optional[str] = Field(default=DEFAULT_CURRENCY, min_length=3, max_length=3)
    description: str = Field(..., min_length=1, max_length=255)

    @field_validator('currency')
    def check_currency(cls, v):
        return validate_currency(v) or DEFAULT_CURRENCY


class ExpenseUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    description: Optional[str] = Field(None, min_length=1, max_length=255)

    @field_validator('currency')
    def check_currency(cls, v):
        return validate_currency(v)


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    currency: str
    description: str