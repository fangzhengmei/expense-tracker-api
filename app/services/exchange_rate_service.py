from decimal import Decimal
from typing import Optional, Dict, List
from sqlalchemy.exc import IntegrityError

from app.models.exchange_rate import ExchangeRate
from app.models.user import User
from app.core.constants import DEFAULT_CURRENCY, SUPPORTED_CURRENCIES


DEFAULT_EXCHANGE_RATES = {
    "CNY": Decimal("1.0"),
    "USD": Decimal("7.25"),
    "EUR": Decimal("7.80"),
    "JPY": Decimal("0.048"),
    "GBP": Decimal("9.10"),
    "HKD": Decimal("0.93"),
    "AUD": Decimal("4.75"),
    "CAD": Decimal("5.35"),
    "SGD": Decimal("5.35"),
    "CHF": Decimal("8.25"),
}


class ExchangeRateNotFoundError(Exception):
    pass


class UnsupportedCurrencyError(Exception):
    def __init__(self, currency: str):
        self.currency = currency
        super().__init__(f"Unsupported currency: {currency}")


def is_supported_currency(currency: str) -> bool:
    return currency.upper() in SUPPORTED_CURRENCIES


def get_default_rate(currency: str) -> Decimal:
    currency_upper = currency.upper()
    if currency_upper not in DEFAULT_EXCHANGE_RATES:
        raise UnsupportedCurrencyError(currency)
    return DEFAULT_EXCHANGE_RATES[currency_upper]


def get_user_rates(db, user_id: int) -> Dict[str, Decimal]:
    user_rates = db.query(ExchangeRate).filter(
        ExchangeRate.user_id == user_id
    ).all()
    
    rates = {}
    for rate in user_rates:
        rates[rate.currency] = rate.rate_to_cny
    
    for currency in SUPPORTED_CURRENCIES:
        if currency not in rates:
            rates[currency] = get_default_rate(currency)
    
    return rates


def get_rate(db, currency: str, user_id: Optional[int] = None) -> Decimal:
    currency = currency.upper()
    
    if not is_supported_currency(currency):
        raise UnsupportedCurrencyError(currency)
    
    if currency == DEFAULT_CURRENCY:
        return Decimal("1.0")
    
    if user_id is not None:
        user_rate = db.query(ExchangeRate).filter(
            ExchangeRate.currency == currency,
            ExchangeRate.user_id == user_id
        ).first()
        if user_rate:
            if user_rate.rate_to_cny <= Decimal("0"):
                raise ValueError(f"Invalid exchange rate for {currency}: rate must be positive")
            return user_rate.rate_to_cny
    
    default_rate = db.query(ExchangeRate).filter(
        ExchangeRate.currency == currency,
        ExchangeRate.is_default == 1
    ).first()
    if default_rate:
        if default_rate.rate_to_cny <= Decimal("0"):
            raise ValueError(f"Invalid exchange rate for {currency}: rate must be positive")
        return default_rate.rate_to_cny
    
    return get_default_rate(currency)


def convert_amount(
    db,
    amount: Decimal,
    from_currency: str,
    to_currency: str,
    user_id: Optional[int] = None
) -> Decimal:
    if amount < Decimal("0"):
        raise ValueError("Amount cannot be negative")
    
    if from_currency == to_currency:
        return amount.quantize(Decimal("0.01"))
    
    from_rate = get_rate(db, from_currency, user_id)
    to_rate = get_rate(db, to_currency, user_id)
    
    if to_rate <= Decimal("0"):
        raise ValueError(f"Invalid exchange rate for {to_currency}: rate must be positive")
    
    amount_in_cny = amount * from_rate
    converted_amount = amount_in_cny / to_rate
    
    return converted_amount.quantize(Decimal("0.01"))


def set_exchange_rate(
    db,
    currency: str,
    rate_to_cny: Decimal,
    user_id: Optional[int] = None,
    is_default: bool = False
) -> ExchangeRate:
    currency = currency.upper()
    
    if not is_supported_currency(currency):
        raise UnsupportedCurrencyError(currency)
    
    if rate_to_cny <= Decimal("0"):
        raise ValueError("Exchange rate must be positive")
    
    existing = db.query(ExchangeRate).filter(
        ExchangeRate.currency == currency,
        ExchangeRate.user_id == user_id
    ).first()
    
    if existing:
        existing.rate_to_cny = rate_to_cny
        existing.is_default = 1 if is_default else 0
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_rate = ExchangeRate(
            currency=currency,
            rate_to_cny=rate_to_cny,
            user_id=user_id,
            is_default=1 if is_default else 0
        )
        db.add(new_rate)
        db.commit()
        db.refresh(new_rate)
        return new_rate


def set_multiple_rates(
    db,
    rates: Dict[str, Decimal],
    user_id: Optional[int] = None
) -> List[ExchangeRate]:
    result = []
    for currency, rate in rates.items():
        result.append(set_exchange_rate(db, currency, rate, user_id))
    return result


def get_user_exchange_rates(db, user_id: int) -> List[ExchangeRate]:
    return db.query(ExchangeRate).filter(
        ExchangeRate.user_id == user_id
    ).all()


def delete_user_exchange_rate(db, user_id: int, currency: str) -> bool:
    currency = currency.upper()
    rate = db.query(ExchangeRate).filter(
        ExchangeRate.user_id == user_id,
        ExchangeRate.currency == currency
    ).first()
    
    if not rate:
        raise ExchangeRateNotFoundError()
    
    db.delete(rate)
    db.commit()
    return True
