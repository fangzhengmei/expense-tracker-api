from pydantic import BaseModel, Field, ConfigDict, field_validator
from decimal import Decimal
from typing import Optional, Dict

from app.core.constants import SUPPORTED_CURRENCIES, DEFAULT_CURRENCY


def validate_currency(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = v.upper()
    if v not in SUPPORTED_CURRENCIES:
        raise ValueError(f"Unsupported currency: {v}. Supported currencies: {SUPPORTED_CURRENCIES}")
    return v


class ExchangeRateCreate(BaseModel):
    currency: str = Field(..., min_length=3, max_length=3)
    rate_to_cny: Decimal = Field(..., gt=0)

    @field_validator('currency')
    def check_currency(cls, v):
        return validate_currency(v)


class ExchangeRateUpdate(BaseModel):
    rate_to_cny: Optional[Decimal] = Field(None, gt=0)


class ExchangeRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    currency: str
    rate_to_cny: Decimal
    is_default: int


class ExchangeRateBatchCreate(BaseModel):
    rates: Dict[str, Decimal]

    @field_validator('rates')
    def check_rates(cls, v):
        for currency, rate in v.items():
            currency = currency.upper()
            if currency not in SUPPORTED_CURRENCIES:
                raise ValueError(f"Unsupported currency: {currency}")
            if rate <= 0:
                raise ValueError(f"Rate must be positive: {currency}")
        return v


class ExchangeRateBatchOut(BaseModel):
    currency: str
    rate_to_cny: Decimal


class ConvertedAmount(BaseModel):
    original_amount: Decimal
    original_currency: str
    converted_amount: Decimal
    target_currency: str
    exchange_rate: Decimal
