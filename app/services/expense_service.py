from app.models.expense import Expense
from app.models.enums import ExpenseStatus
from sqlalchemy import func


class ExpenseNotFoundError(Exception):
    pass


class UnauthorizedExpenseAccess(Exception):
    pass


class ExpenseAlreadyApprovedError(Exception):
    pass


def create_expense(db, amount, description, user_id):
    expense = Expense(
        amount=amount,
        description=description,
        user_id=user_id,
        status=ExpenseStatus.PENDING
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)

    return expense


def get_expenses_by_user(db, user_id, status: ExpenseStatus | None = None):
    query = db.query(Expense).filter(Expense.user_id == user_id)
    if status:
        query = query.filter(Expense.status == status)
    return query.order_by(Expense.created_at.desc()).all()


def get_expense_by_user(db, expense_id, user_id):
    return db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user_id
    ).first()


def delete_expense_by_user(db, expense_id, user_id):
    expense = get_expense_by_user(db, expense_id, user_id)

    if not expense:
        raise ExpenseNotFoundError()

    if expense.status != ExpenseStatus.PENDING:
        raise ExpenseAlreadyApprovedError("已审批的支出无法删除")

    db.delete(expense)
    db.commit()


def update_expense_by_user(db, expense_id, user_id, amount=None, description=None):
    expense = get_expense_by_user(db, expense_id, user_id)

    if not expense:
        raise ExpenseNotFoundError()

    if expense.status != ExpenseStatus.PENDING:
        raise ExpenseAlreadyApprovedError("已审批的支出无法修改")

    if amount is not None:
        expense.amount = amount

    if description is not None:
        expense.description = description

    db.commit()
    db.refresh(expense)

    return expense


def get_monthly_expenses(db, user_id, status: ExpenseStatus | None = None):
    db_url = str(db.bind.url)

    if "sqlite" in db_url:
        month_expr = func.strftime("%Y-%m", Expense.created_at)
    else:
        month_expr = func.to_char(Expense.created_at, "YYYY-MM")

    query = (
        db.query(
            month_expr.label("month"),
            func.sum(Expense.amount).label("total")
        )
        .filter(Expense.user_id == user_id)
    )
    
    if status:
        query = query.filter(Expense.status == status)

    results = query.group_by("month").order_by("month").all()

    return [
        {
            "month": row.month,
            "total": float(row.total or 0)
        }
        for row in results
    ]
