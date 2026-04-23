from app.models.budget import Budget
from app.models.expense import Expense
from app.models.category import Category
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from decimal import Decimal
from datetime import datetime


class BudgetNotFoundError(Exception):
    pass


class BudgetAlreadyExistsError(Exception):
    pass


class UnauthorizedBudgetAccess(Exception):
    pass


def create_budget(db, user_id, amount, year, month, category_id):
    try:
        budget = Budget(
            amount=amount,
            year=year,
            month=month,
            user_id=user_id,
            category_id=category_id
        )
        db.add(budget)
        db.commit()
        db.refresh(budget)
        return budget
    except IntegrityError:
        db.rollback()
        raise BudgetAlreadyExistsError("该分类该月份的预算已存在")


def get_budgets_by_user(db, user_id):
    return db.query(Budget).filter(Budget.user_id == user_id).all()


def get_budgets_by_user_and_month(db, user_id, year, month):
    return db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.year == year,
        Budget.month == month
    ).all()


def get_budget_by_user(db, budget_id, user_id):
    return db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user_id
    ).first()


def get_budget_by_category_and_month(db, user_id, category_id, year, month):
    return db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category_id == category_id,
        Budget.year == year,
        Budget.month == month
    ).first()


def update_budget_by_user(db, budget_id, user_id, amount=None):
    budget = get_budget_by_user(db, budget_id, user_id)
    
    if not budget:
        raise BudgetNotFoundError()
    
    if amount is not None:
        budget.amount = amount
    
    db.commit()
    db.refresh(budget)
    return budget


def delete_budget_by_user(db, budget_id, user_id):
    budget = get_budget_by_user(db, budget_id, user_id)
    
    if not budget:
        raise BudgetNotFoundError()
    
    db.delete(budget)
    db.commit()


def get_category_monthly_spent(db, user_id, category_id, year, month):
    db_url = str(db.bind.url)
    
    if "sqlite" in db_url:
        month_expr = func.strftime("%Y-%m", Expense.created_at)
        target_month = f"{year}-{month:02d}"
    else:
        month_expr = func.to_char(Expense.created_at, "YYYY-MM")
        target_month = f"{year}-{month:02d}"
    
    result = db.query(
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user_id,
        Expense.category_id == category_id,
        month_expr == target_month
    ).scalar()
    
    return Decimal(result or 0)


def get_budget_with_usage(db, budget):
    category = db.query(Category).filter(Category.id == budget.category_id).first()
    spent = get_category_monthly_spent(
        db, 
        budget.user_id, 
        budget.category_id, 
        budget.year, 
        budget.month
    )
    remaining = budget.amount - spent
    percentage = (float(spent) / float(budget.amount) * 100) if budget.amount > 0 else 0
    
    return {
        "id": budget.id,
        "amount": budget.amount,
        "year": budget.year,
        "month": budget.month,
        "category_id": budget.category_id,
        "category_name": category.name if category else None,
        "spent": spent,
        "remaining": remaining,
        "percentage": round(percentage, 2)
    }


def get_monthly_budget_summary(db, user_id, year, month):
    budgets = get_budgets_by_user_and_month(db, user_id, year, month)
    
    total_budget = Decimal(0)
    total_spent = Decimal(0)
    budgets_with_usage = []
    
    for budget in budgets:
        budget_usage = get_budget_with_usage(db, budget)
        budgets_with_usage.append(budget_usage)
        total_budget += budget.amount
        total_spent += budget_usage["spent"]
    
    total_remaining = total_budget - total_spent
    
    return {
        "year": year,
        "month": month,
        "total_budget": total_budget,
        "total_spent": total_spent,
        "total_remaining": total_remaining,
        "budgets": budgets_with_usage
    }


def check_budget_availability(db, user_id, category_id, amount, year=None, month=None):
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month
    
    budget = get_budget_by_category_and_month(db, user_id, category_id, year, month)
    
    if not budget:
        return {
            "has_budget": False,
            "budget_amount": None,
            "spent": None,
            "remaining": None,
            "will_exceed": False,
            "exceed_amount": None
        }
    
    spent = get_category_monthly_spent(db, user_id, category_id, year, month)
    remaining = budget.amount - spent
    will_exceed = (spent + amount) > budget.amount
    exceed_amount = (spent + amount) - budget.amount if will_exceed else Decimal(0)
    
    return {
        "has_budget": True,
        "budget_amount": budget.amount,
        "spent": spent,
        "remaining": remaining,
        "will_exceed": will_exceed,
        "exceed_amount": exceed_amount
    }
