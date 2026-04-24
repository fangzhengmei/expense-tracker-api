from app.models.expense import Expense
from app.models.category import Category
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload


class ExpenseNotFoundError(Exception):
    pass


class UnauthorizedExpenseAccess(Exception):
    pass


class InvalidCategoryError(Exception):
    pass


def create_expense(db, amount, description, user_id, category_id=None):
    if category_id is not None:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise InvalidCategoryError()
        if not category.is_default and category.user_id != user_id:
            raise InvalidCategoryError()

    expense = Expense(
        amount=amount,
        description=description,
        user_id=user_id,
        category_id=category_id
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)

    expense = db.query(Expense).options(
        joinedload(Expense.category)
    ).filter(Expense.id == expense.id).first()

    return expense


def get_expenses_by_user(db, user_id, category_id=None, start_date=None, end_date=None):
    query = db.query(Expense).options(
        joinedload(Expense.category)
    ).filter(Expense.user_id == user_id)

    if category_id is not None:
        query = query.filter(Expense.category_id == category_id)

    if start_date is not None:
        query = query.filter(Expense.created_at >= start_date)

    if end_date is not None:
        query = query.filter(Expense.created_at <= end_date)

    return query.order_by(Expense.created_at.desc()).all()


def get_expense_by_user(db, expense_id, user_id):
    return db.query(Expense).options(
        joinedload(Expense.category)
    ).filter(
        Expense.id == expense_id,
        Expense.user_id == user_id
    ).first()


def delete_expense_by_user(db, expense_id, user_id):
    expense = get_expense_by_user(db, expense_id, user_id)

    if not expense:
        raise ExpenseNotFoundError()

    db.delete(expense)
    db.commit()


def update_expense_by_user(db, expense_id, user_id, amount=None, description=None, category_id=None):
    expense = get_expense_by_user(db, expense_id, user_id)

    if not expense:
        raise ExpenseNotFoundError()

    if category_id is not None:
        if category_id == 0:
            expense.category_id = None
        else:
            category = db.query(Category).filter(Category.id == category_id).first()
            if not category:
                raise InvalidCategoryError()
            if not category.is_default and category.user_id != user_id:
                raise InvalidCategoryError()
            expense.category_id = category_id

    if amount is not None:
        expense.amount = amount

    if description is not None:
        expense.description = description

    db.commit()
    db.refresh(expense)

    expense = db.query(Expense).options(
        joinedload(Expense.category)
    ).filter(Expense.id == expense.id).first()

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
    