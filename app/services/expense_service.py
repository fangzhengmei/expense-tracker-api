from app.models.expense import Expense
from app.models.category import Category
from app.services import budget_service
from sqlalchemy import func
from typing import Optional


class ExpenseNotFoundError(Exception):
    pass


class UnauthorizedExpenseAccess(Exception):
    pass


class InvalidCategoryError(Exception):
    pass


def create_expense(db, amount, description, user_id, category_id: Optional[int] = None):
    if category_id is not None:
        category = db.query(Category).filter(
            Category.id == category_id,
            Category.user_id == user_id
        ).first()
        if not category:
            raise InvalidCategoryError(f"分类 ID {category_id} 不存在或不属于当前用户")
    
    expense = Expense(
        amount=amount,
        description=description,
        user_id=user_id,
        category_id=category_id
    )
    
    db.add(expense)
    db.commit()
    db.refresh(expense)
    
    return expense


def create_expense_with_budget_check(db, amount, description, user_id, category_id: Optional[int] = None):
    budget_info = None
    
    if category_id is not None:
        budget_info = budget_service.check_budget_availability(
            db, user_id, category_id, amount
        )
    
    expense = create_expense(db, amount, description, user_id, category_id)
    
    if category_id is not None and budget_info and budget_info["has_budget"]:
        budget_info = budget_service.check_budget_availability(
            db, user_id, category_id, 0
        )
    
    return expense, budget_info


def get_expenses_by_user(db, user_id):
    return db.query(Expense).filter(Expense.user_id == user_id).all()


def get_expenses_by_user_with_category(db, user_id):
    expenses = db.query(Expense).filter(Expense.user_id == user_id).all()
    
    result = []
    for expense in expenses:
        category_name = None
        if expense.category_id:
            category = db.query(Category).filter(Category.id == expense.category_id).first()
            category_name = category.name if category else None
        
        result.append({
            "id": expense.id,
            "amount": expense.amount,
            "description": expense.description,
            "category_id": expense.category_id,
            "category_name": category_name,
            "created_at": expense.created_at
        })
    
    return result


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


def update_expense_by_user(db, expense_id, user_id, amount=None, description=None, category_id=None):
    expense = get_expense_by_user(db, expense_id, user_id)
    
    if not expense:
        raise ExpenseNotFoundError()
    
    if category_id is not None:
        if category_id == 0:
            expense.category_id = None
        else:
            category = db.query(Category).filter(
                Category.id == category_id,
                Category.user_id == user_id
            ).first()
            if not category:
                raise InvalidCategoryError(f"分类 ID {category_id} 不存在或不属于当前用户")
            expense.category_id = category_id
    
    if amount is not None:
        expense.amount = amount
    
    if description is not None:
        expense.description = description
    
    db.commit()
    db.refresh(expense)
    
    return expense


def update_expense_with_budget_check(db, expense_id, user_id, amount=None, description=None, category_id=None):
    old_expense = get_expense_by_user(db, expense_id, user_id)
    
    if not old_expense:
        raise ExpenseNotFoundError()
    
    old_amount = old_expense.amount
    old_category_id = old_expense.category_id
    
    new_amount = amount if amount is not None else old_amount
    new_category_id = category_id if category_id is not None else old_category_id
    
    budget_info = None
    
    if new_category_id is not None:
        amount_diff = new_amount - old_amount
        if old_category_id != new_category_id:
            check_amount = new_amount
        else:
            check_amount = amount_diff if amount_diff > 0 else 0
        
        if check_amount > 0:
            budget_info = budget_service.check_budget_availability(
                db, user_id, new_category_id, check_amount
            )
    
    expense = update_expense_by_user(db, expense_id, user_id, amount, description, category_id)
    
    if new_category_id is not None and budget_info and budget_info["has_budget"]:
        budget_info = budget_service.check_budget_availability(
            db, user_id, new_category_id, 0
        )
    
    return expense, budget_info


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


def get_expenses_by_category(db, user_id, category_id):
    return db.query(Expense).filter(
        Expense.user_id == user_id,
        Expense.category_id == category_id
    ).all()
