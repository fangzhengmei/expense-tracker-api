from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional

from app.schemas.exchange_rate_schema import (
    ExchangeRateCreate,
    ExchangeRateUpdate,
    ExchangeRateOut,
    ExchangeRateBatchCreate,
    ExchangeRateBatchOut,
    ConvertedAmount,
)
from app.db.database import get_db
from app.api.deps import get_current_user

from app.services.exchange_rate_service import (
    set_exchange_rate,
    set_multiple_rates,
    get_user_exchange_rates,
    delete_user_exchange_rate,
    convert_amount,
    get_rate,
    get_default_rate,
    get_user_rates,
    ExchangeRateNotFoundError,
    DEFAULT_EXCHANGE_RATES,
)
from app.core.constants import DEFAULT_CURRENCY, SUPPORTED_CURRENCIES, CURRENCY_SYMBOLS


router = APIRouter()


@router.get("/")
def list_exchange_rates(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_rates = get_user_exchange_rates(db, user.id)
    user_rates_dict = {r.currency: r for r in user_rates}
    
    all_rates = []
    for currency in SUPPORTED_CURRENCIES:
        if currency in user_rates_dict:
            all_rates.append(ExchangeRateOut(
                id=user_rates_dict[currency].id,
                currency=currency,
                rate_to_cny=user_rates_dict[currency].rate_to_cny,
                is_default=0
            ))
        else:
            all_rates.append(ExchangeRateOut(
                id=0,
                currency=currency,
                rate_to_cny=get_default_rate(currency),
                is_default=1
            ))
    
    return {
        "default_currency": DEFAULT_CURRENCY,
        "user_default_currency": user.default_currency,
        "rates": all_rates
    }


@router.post("/")
def set_rate(
    rate_data: ExchangeRateCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rate = set_exchange_rate(
        db,
        currency=rate_data.currency,
        rate_to_cny=rate_data.rate_to_cny,
        user_id=user.id
    )
    return ExchangeRateOut.model_validate(rate)


@router.post("/batch")
def set_rates_batch(
    batch_data: ExchangeRateBatchCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rates = set_multiple_rates(db, batch_data.rates, user_id=user.id)
    return [ExchangeRateOut.model_validate(r) for r in rates]


@router.delete("/{currency}")
def delete_rate(
    currency: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        delete_user_exchange_rate(db, user.id, currency)
        return {"message": f"Exchange rate for {currency.upper()} deleted, reverting to default"}
    except ExchangeRateNotFoundError:
        raise HTTPException(status_code=404, detail="Exchange rate not found")


@router.get("/convert")
def convert(
    amount: Decimal,
    from_currency: str,
    to_currency: Optional[str] = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if to_currency is None:
        to_currency = user.default_currency
    
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    if from_currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {from_currency}")
    if to_currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"Unsupported currency: {to_currency}")
    
    from_rate = get_rate(db, from_currency, user.id)
    to_rate = get_rate(db, to_currency, user.id)
    
    converted = convert_amount(db, amount, from_currency, to_currency, user.id)
    
    exchange_rate_used = from_rate / to_rate if to_rate != 0 else Decimal("0")
    
    return ConvertedAmount(
        original_amount=amount,
        original_currency=from_currency,
        converted_amount=converted,
        target_currency=to_currency,
        exchange_rate=exchange_rate_used.quantize(Decimal("0.000001"))
    )


@router.get("/defaults")
def get_default_rates():
    return {
        "default_currency": DEFAULT_CURRENCY,
        "default_rates": {k: float(v) for k, v in DEFAULT_EXCHANGE_RATES.items()},
        "supported_currencies": SUPPORTED_CURRENCIES,
        "currency_symbols": CURRENCY_SYMBOLS
    }
