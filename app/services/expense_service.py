from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.user import User
from app.services.ledger_service import (
    is_member,
    is_admin_or_higher,
    get_member_role,
    get_ledger_by_id,
    LedgerNotFoundError,
    NotMemberError
)


class ExpenseNotFoundError(Exception):
    pass


class UnauthorizedExpenseAccess(Exception):
    pass


def create_expense(
    db: Session,
    amount: float,
    description: str,
    user_id: int,
    ledger_id: int
) -> Expense:
    if not is_member(db, ledger_id, user_id):
        raise NotMemberError()

    ledger = get_ledger_by_id(db, ledger_id)
    if not ledger or not ledger.is_active:
        raise LedgerNotFoundError()

    expense = Expense(
        amount=amount,
        description=description,
        user_id=user_id,
        ledger_id=ledger_id
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)

    return expense


def get_expenses_by_ledger(
    db: Session,
    ledger_id: int,
    user_id: int,
    limit: int = 100,
    offset: int = 0
) -> List[tuple]:
    if not is_member(db, ledger_id, user_id):
        raise NotMemberError()

    results = (
        db.query(Expense, User.email)
        .join(User, Expense.user_id == User.id)
        .filter(Expense.ledger_id == ledger_id)
        .order_by(Expense.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return results


def get_expenses_by_user(db: Session, user_id: int) -> List[Expense]:
    return db.query(Expense).filter(Expense.user_id == user_id).all()


def get_expense_by_id(db: Session, expense_id: int) -> Optional[Expense]:
    return db.query(Expense).filter(Expense.id == expense_id).first()


def can_edit_expense(
    db: Session,
    expense: Expense,
    user_id: int
) -> bool:
    if expense.user_id == user_id:
        return True
    return is_admin_or_higher(db, expense.ledger_id, user_id)


def can_delete_expense(
    db: Session,
    expense: Expense,
    user_id: int
) -> bool:
    if expense.user_id == user_id:
        return True
    return is_admin_or_higher(db, expense.ledger_id, user_id)


def delete_expense(
    db: Session,
    expense_id: int,
    user_id: int
) -> None:
    expense = get_expense_by_id(db, expense_id)

    if not expense:
        raise ExpenseNotFoundError()

    if not can_delete_expense(db, expense, user_id):
        raise UnauthorizedExpenseAccess()

    db.delete(expense)
    db.commit()


def update_expense(
    db: Session,
    expense_id: int,
    user_id: int,
    amount: Optional[float] = None,
    description: Optional[str] = None
) -> Expense:
    expense = get_expense_by_id(db, expense_id)

    if not expense:
        raise ExpenseNotFoundError()

    if not can_edit_expense(db, expense, user_id):
        raise UnauthorizedExpenseAccess()

    if amount is not None:
        expense.amount = amount

    if description is not None:
        expense.description = description

    db.commit()
    db.refresh(expense)

    return expense


def get_monthly_expenses_by_ledger(
    db: Session,
    ledger_id: int,
    user_id: int
) -> List[dict]:
    if not is_member(db, ledger_id, user_id):
        raise NotMemberError()

    db_url = str(db.bind.url)

    if "sqlite" in db_url:
        month_expr = func.strftime("%Y-%m", Expense.created_at)
    else:
        month_expr = func.to_char(Expense.created_at, "YYYY-MM")

    results = (
        db.query(
            month_expr.label("month"),
            func.sum(Expense.amount).label("total"),
            func.count(Expense.id).label("count")
        )
        .filter(Expense.ledger_id == ledger_id)
        .group_by("month")
        .order_by("month")
        .all()
    )

    return [
        {
            "month": row.month,
            "total": float(row.total or 0),
            "count": row.count or 0
        }
        for row in results
    ]


def get_user_monthly_expenses(db: Session, user_id: int) -> List[dict]:
    db_url = str(db.bind.url)

    if "sqlite" in db_url:
        month_expr = func.strftime("%Y-%m", Expense.created_at)
    else:
        month_expr = func.to_char(Expense.created_at, "YYYY-MM")

    results = (
        db.query(
            month_expr.label("month"),
            func.sum(Expense.amount).label("total")
        )
        .filter(Expense.user_id == user_id)
        .group_by("month")
        .order_by("month")
        .all()
    )

    return [
        {
            "month": row.month,
            "total": float(row.total or 0)
        }
        for row in results
    ]


def get_ledger_expense_summary(
    db: Session,
    ledger_id: int,
    user_id: int
) -> dict:
    if not is_member(db, ledger_id, user_id):
        raise NotMemberError()

    total_expense = (
        db.query(func.sum(Expense.amount))
        .filter(Expense.ledger_id == ledger_id)
        .scalar()
    )

    expense_count = (
        db.query(func.count(Expense.id))
        .filter(Expense.ledger_id == ledger_id)
        .scalar()
    )

    db_url = str(db.bind.url)
    if "sqlite" in db_url:
        month_expr = func.strftime("%Y-%m", Expense.created_at)
    else:
        month_expr = func.to_char(Expense.created_at, "YYYY-MM")

    monthly = (
        db.query(
            month_expr.label("month"),
            func.sum(Expense.amount).label("total"),
            func.count(Expense.id).label("count")
        )
        .filter(Expense.ledger_id == ledger_id)
        .group_by("month")
        .order_by("month")
        .all()
    )

    by_user = (
        db.query(
            User.id.label("user_id"),
            User.email.label("user_email"),
            func.sum(Expense.amount).label("total"),
            func.count(Expense.id).label("count")
        )
        .join(User, Expense.user_id == User.id)
        .filter(Expense.ledger_id == ledger_id)
        .group_by(User.id, User.email)
        .all()
    )

    return {
        "total": float(total_expense or 0),
        "count": expense_count or 0,
        "monthly": [
            {
                "month": row.month,
                "total": float(row.total or 0),
                "count": row.count or 0
            }
            for row in monthly
        ],
        "by_user": [
            {
                "user_id": row.user_id,
                "user_email": row.user_email,
                "total": float(row.total or 0),
                "count": row.count or 0
            }
            for row in by_user
        ]
    }
