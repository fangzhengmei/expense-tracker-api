from typing import List, Optional, Tuple
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.category import (
    Category,
    CategoryType,
    DEFAULT_EXPENSE_CATEGORIES,
    DEFAULT_INCOME_CATEGORIES
)
from app.models.expense import Expense
from app.models.ledger import Ledger


class CategoryError(Exception):
    pass


class CategoryNotFoundError(CategoryError):
    pass


class CannotModifyDefaultCategoryError(CategoryError):
    pass


def create_default_categories(db: Session, ledger_id: int) -> None:
    sort_order = 0
    for cat in DEFAULT_EXPENSE_CATEGORIES:
        category = Category(
            name=cat["name"],
            type=CategoryType.EXPENSE,
            color=cat["color"],
            icon=cat["icon"],
            sort_order=sort_order,
            is_default=True,
            is_active=True,
            ledger_id=ledger_id
        )
        db.add(category)
        sort_order += 1

    for cat in DEFAULT_INCOME_CATEGORIES:
        category = Category(
            name=cat["name"],
            type=CategoryType.INCOME,
            color=cat["color"],
            icon=cat["icon"],
            sort_order=sort_order,
            is_default=True,
            is_active=True,
            ledger_id=ledger_id
        )
        db.add(category)
        sort_order += 1

    db.commit()


def get_ledger_categories(
    db: Session,
    ledger_id: int,
    category_type: Optional[CategoryType] = None,
    include_inactive: bool = False
) -> List[Category]:
    query = db.query(Category).filter(Category.ledger_id == ledger_id)

    if category_type:
        query = query.filter(Category.type == category_type)

    if not include_inactive:
        query = query.filter(Category.is_active == True)

    query = query.order_by(Category.sort_order, Category.id)

    return query.all()


def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    return db.query(Category).filter(Category.id == category_id).first()


def create_category(
    db: Session,
    ledger_id: int,
    name: str,
    category_type: CategoryType = CategoryType.EXPENSE,
    color: str = "#6366F1",
    icon: Optional[str] = None,
    sort_order: int = 0
) -> Category:
    category = Category(
        name=name,
        type=category_type,
        color=color,
        icon=icon,
        sort_order=sort_order,
        is_default=False,
        is_active=True,
        ledger_id=ledger_id
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return category


def update_category(
    db: Session,
    category_id: int,
    name: Optional[str] = None,
    color: Optional[str] = None,
    icon: Optional[str] = None,
    sort_order: Optional[int] = None,
    is_active: Optional[bool] = None
) -> Category:
    category = get_category_by_id(db, category_id)
    if not category:
        raise CategoryNotFoundError()

    if name is not None:
        category.name = name
    if color is not None:
        category.color = color
    if icon is not None:
        category.icon = icon
    if sort_order is not None:
        category.sort_order = sort_order
    if is_active is not None:
        if category.is_default and not is_active:
            raise CannotModifyDefaultCategoryError()
        category.is_active = is_active

    db.commit()
    db.refresh(category)

    return category


def deactivate_category(db: Session, category_id: int) -> None:
    category = get_category_by_id(db, category_id)
    if not category:
        raise CategoryNotFoundError()

    if category.is_default:
        raise CannotModifyDefaultCategoryError()

    category.is_active = False
    db.commit()


def get_category_stats_by_ledger(
    db: Session,
    ledger_id: int,
    category_type: CategoryType = CategoryType.EXPENSE,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Tuple[Category, Decimal, int]]:
    query = (
        db.query(
            Category,
            func.coalesce(func.sum(Expense.amount), Decimal("0")).label("total_amount"),
            func.count(Expense.id).label("count")
        )
        .outerjoin(Expense, Category.id == Expense.category_id)
        .filter(Category.ledger_id == ledger_id)
        .filter(Category.type == category_type)
        .filter(Category.is_active == True)
    )

    if start_date:
        query = query.filter(Expense.created_at >= start_date)
    if end_date:
        query = query.filter(Expense.created_at <= end_date)

    query = query.group_by(Category.id).order_by(Category.sort_order, Category.id)

    return query.all()


def get_category_stats_with_percentage(
    db: Session,
    ledger_id: int,
    category_type: CategoryType = CategoryType.EXPENSE,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Tuple[Decimal, List[dict]]:
    stats = get_category_stats_by_ledger(db, ledger_id, category_type, start_date, end_date)

    total_amount = Decimal("0")
    for category, amount, count in stats:
        total_amount += amount

    result = []
    for category, amount, count in stats:
        percentage = 0.0
        if total_amount > 0:
            percentage = float(amount) / float(total_amount) * 100

        result.append({
            "category_id": category.id,
            "category_name": category.name,
            "category_color": category.color,
            "category_icon": category.icon,
            "total_amount": float(amount),
            "count": count,
            "percentage": round(percentage, 2)
        })

    return total_amount, result


def get_monthly_category_stats(
    db: Session,
    ledger_id: int,
    category_type: CategoryType = CategoryType.EXPENSE
) -> List[dict]:
    db_url = str(db.bind.url)

    if "sqlite" in db_url:
        month_expr = func.strftime("%Y-%m", Expense.created_at)
    else:
        month_expr = func.to_char(Expense.created_at, "YYYY-MM")

    results = (
        db.query(
            month_expr.label("month"),
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            Category.color.label("category_color"),
            Category.icon.label("category_icon"),
            func.coalesce(func.sum(Expense.amount), Decimal("0")).label("total_amount"),
            func.count(Expense.id).label("count")
        )
        .join(Category, Expense.category_id == Category.id)
        .filter(Expense.ledger_id == ledger_id)
        .filter(Category.type == category_type)
        .group_by("month", Category.id)
        .order_by("month", Category.sort_order)
        .all()
    )

    monthly_data = {}
    for row in results:
        month = row.month
        if month not in monthly_data:
            monthly_data[month] = {
                "month": month,
                "total": 0,
                "categories": []
            }

        category_data = {
            "category_id": row.category_id,
            "category_name": row.category_name,
            "category_color": row.category_color,
            "category_icon": row.category_icon,
            "total_amount": float(row.total_amount or 0),
            "count": row.count or 0
        }

        monthly_data[month]["categories"].append(category_data)
        monthly_data[month]["total"] += float(row.total_amount or 0)

    return list(monthly_data.values())
