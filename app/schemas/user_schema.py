from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional

from app.core.constants import SUPPORTED_CURRENCIES, DEFAULT_CURRENCY


def validate_currency(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = v.upper()
    if v not in SUPPORTED_CURRENCIES:
        raise ValueError(f"Unsupported currency: {v}. Supported currencies: {SUPPORTED_CURRENCIES}")
    return v


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    default_currency: Optional[str] = Field(default=DEFAULT_CURRENCY, min_length=3, max_length=3)

    @field_validator('default_currency')
    def check_currency(cls, v):
        return validate_currency(v) or DEFAULT_CURRENCY


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    default_currency: Optional[str] = Field(None, min_length=3, max_length=3)

    @field_validator('default_currency')
    def check_currency(cls, v):
        return validate_currency(v)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    default_currency: str