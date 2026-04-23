from app.models.expense import Expense
from app.models.user import User
from sqlalchemy import func
from typing import Optional

from app.core.constants import DEFAULT_CURRENCY


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
    