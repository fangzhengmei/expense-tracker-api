import csv
from io import StringIO
from datetime import datetime

from app.models.expense import Expense
from sqlalchemy import func


class ExpenseNotFoundError(Exception):
    pass


class UnauthorizedExpenseAccess(Exception):
    pass


def create_expense(db, amount, description, user_id):
    expense = Expense(
        amount=amount,
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


def update_expense_by_user(db, expense_id, user_id, amount=None, description=None):
    expense = get_expense_by_user(db, expense_id, user_id)

    if not expense:
        raise ExpenseNotFoundError()

    if amount is not None:
        expense.amount = amount

    if description is not None:
        expense.description = description

    db.commit()
    db.refresh(expense)

    return expense


def get_monthly_expenses(db, user_id):
    # Detectar tipo de base de datos
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


def export_expenses_to_csv(db, user_id):
    expenses = get_expenses_by_user(db, user_id)

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["ID", "金额", "描述", "创建时间", "更新时间"])

    for expense in expenses:
        created_at = expense.created_at.strftime("%Y-%m-%d %H:%M:%S") if expense.created_at else ""
        updated_at = expense.updated_at.strftime("%Y-%m-%d %H:%M:%S") if expense.updated_at else ""

        writer.writerow([
            expense.id,
            str(expense.amount),
            expense.description,
            created_at,
            updated_at
        ])

    output.seek(0)
    return output
    