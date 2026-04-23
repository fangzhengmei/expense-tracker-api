from app.models.expense import Expense
from app.models.user import User
from sqlalchemy import func
from typing import Optional, Dict, Any
from decimal import Decimal

from app.core.constants import DEFAULT_CURRENCY
from app.services.exchange_rate_service import (
    get_rate,
    convert_amount,
    get_user_rates,
)


class ExpenseNotFoundError(Exception):
    pass


class UnauthorizedExpenseAccess(Exception):
    pass


def get_user_default_currency(db, user_id: int) -> str:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user.default_currency
    return DEFAULT_CURRENCY


def create_expense(db, amount, description, user_id, currency: Optional[str] = None):
    if currency is None:
        currency = get_user_default_currency(db, user_id)
    
    expense = Expense(
        amount=amount,
        currency=currency,
        description=description,
        user_id=user_id
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)

    return expense


def get_expenses_by_user(db, user_id):
    return db.query(Expense).filter(Expense.user_id == user_id).all()


def get_expense_by_user(db, expense_id, user_id):
    return db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user_id
    ).first()


def delete_expense_by_user(db, expense_id, user_id):
    expense = get_expense_by_user(db, expense_id, user_id)

    if not expense:
        raise ExpenseNotFoundError()

    db.delete(expense)
    db.commit()


def update_expense_by_user(db, expense_id, user_id, amount=None, currency=None, description=None):
    expense = get_expense_by_user(db, expense_id, user_id)

    if not expense:
        raise ExpenseNotFoundError()

    if amount is not None:
        expense.amount = amount

    if currency is not None:
        expense.currency = currency

    if description is not None:
        expense.description = description

    db.commit()
    db.refresh(expense)

    return expense


def get_monthly_expenses(db, user_id):
    db_url = str(db.bind.url)

    if "sqlite" in db_url:
        month_expr = func.strftime("%Y-%m", Expense.created_at)
    else:
        month_expr = func.to_char(Expense.created_at, "YYYY-MM")

    results = (
        db.query(
            month_expr.label("month"),
            Expense.currency,
            func.sum(Expense.amount).label("total")
        )
        .filter(Expense.user_id == user_id)
        .group_by("month", Expense.currency)
        .order_by("month", Expense.currency)
        .all()
    )

    monthly_data = {}
    for row in results:
        month = row.month
        currency = row.currency
        total = float(row.total or 0)
        
        if month not in monthly_data:
            monthly_data[month] = {"month": month, "totals": {}}
        monthly_data[month]["totals"][currency] = total

    return list(monthly_data.values())


def get_expenses_summary_by_currency(db, user_id):
    results = (
        db.query(
            Expense.currency,
            func.sum(Expense.amount).label("total"),
            func.count(Expense.id).label("count")
        )
        .filter(Expense.user_id == user_id)
        .group_by(Expense.currency)
        .all()
    )

    return [
        {
            "currency": row.currency,
            "total": float(row.total or 0),
            "count": row.count
        }
        for row in results
    ]


def get_monthly_expenses_converted(db, user_id, target_currency: Optional[str] = None):
    user = db.query(User).filter(User.id == user_id).first()
    if target_currency is None:
        target_currency = user.default_currency if user else DEFAULT_CURRENCY
    
    db_url = str(db.bind.url)

    if "sqlite" in db_url:
        month_expr = func.strftime("%Y-%m", Expense.created_at)
    else:
        month_expr = func.to_char(Expense.created_at, "YYYY-MM")

    results = (
        db.query(
            month_expr.label("month"),
            Expense.currency,
            func.sum(Expense.amount).label("total")
        )
        .filter(Expense.user_id == user_id)
        .group_by("month", Expense.currency)
        .order_by("month", Expense.currency)
        .all()
    )

    monthly_data = {}
    for row in results:
        month = row.month
        currency = row.currency
        total = Decimal(str(row.total or 0))
        
        converted_total = convert_amount(db, total, currency, target_currency, user_id)
        
        if month not in monthly_data:
            monthly_data[month] = {
                "month": month,
                "target_currency": target_currency,
                "total_converted": Decimal("0"),
                "totals_by_currency": {}
            }
        
        monthly_data[month]["totals_by_currency"][currency] = {
            "original_amount": float(total),
            "converted_amount": float(converted_total)
        }
        monthly_data[month]["total_converted"] += converted_total

    result_list = []
    for month in sorted(monthly_data.keys()):
        data = monthly_data[month]
        data["total_converted"] = float(data["total_converted"])
        result_list.append(data)

    return result_list


def get_expenses_summary_converted(db, user_id, target_currency: Optional[str] = None):
    user = db.query(User).filter(User.id == user_id).first()
    if target_currency is None:
        target_currency = user.default_currency if user else DEFAULT_CURRENCY
    
    results = (
        db.query(
            Expense.currency,
            func.sum(Expense.amount).label("total"),
            func.count(Expense.id).label("count")
        )
        .filter(Expense.user_id == user_id)
        .group_by(Expense.currency)
        .all()
    )

    total_converted = Decimal("0")
    breakdown = []
    
    for row in results:
        currency = row.currency
        original_amount = Decimal(str(row.total or 0))
        count = row.count
        
        converted_amount = convert_amount(db, original_amount, currency, target_currency, user_id)
        total_converted += converted_amount
        
        breakdown.append({
            "currency": currency,
            "original_amount": float(original_amount),
            "converted_amount": float(converted_amount),
            "count": count
        })

    return {
        "target_currency": target_currency,
        "total_converted": float(total_converted),
        "breakdown": breakdown
    }


def get_all_expenses_with_conversion(db, user_id, target_currency: Optional[str] = None):
    user = db.query(User).filter(User.id == user_id).first()
    if target_currency is None:
        target_currency = user.default_currency if user else DEFAULT_CURRENCY
    
    expenses = get_expenses_by_user(db, user_id)
    
    result = []
    for expense in expenses:
        converted_amount = convert_amount(
            db, 
            Decimal(str(expense.amount)), 
            expense.currency, 
            target_currency, 
            user_id
        )
        
        rate = get_rate(db, expense.currency, user_id)
        target_rate = get_rate(db, target_currency, user_id)
        exchange_rate = rate / target_rate if target_rate != 0 else Decimal("0")
        
        result.append({
            "id": expense.id,
            "original_amount": float(expense.amount),
            "original_currency": expense.currency,
            "converted_amount": float(converted_amount),
            "target_currency": target_currency,
            "exchange_rate": float(exchange_rate.quantize(Decimal("0.000001"))),
            "description": expense.description,
            "created_at": expense.created_at.isoformat() if expense.created_at else None
        })
    
    return result
    