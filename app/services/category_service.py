from sqlalchemy import or_
from app.models.category import Category
from app.models.expense import Expense
from sqlalchemy import func


class CategoryNotFoundError(Exception):
    pass


class UnauthorizedCategoryAccess(Exception):
    pass


class CannotDeleteDefaultCategory(Exception):
    pass


class CategoryNameAlreadyExistsError(Exception):
    pass


DEFAULT_CATEGORIES = [
    {"name": "餐饮", "icon": "🍜", "color": "#EF4444"},
    {"name": "交通", "icon": "🚗", "color": "#3B82F6"},
    {"name": "住房", "icon": "🏠", "color": "#10B981"},
    {"name": "购物", "icon": "🛒", "color": "#F59E0B"},
    {"name": "娱乐", "icon": "🎮", "color": "#8B5CF6"},
    {"name": "医疗", "icon": "💊", "color": "#EC4899"},
    {"name": "教育", "icon": "📚", "color": "#06B6D4"},
    {"name": "其他", "icon": "📝", "color": "#6B7280"},
]


def init_default_categories(db):
    existing = db.query(Category).filter(Category.is_default == True).first()
    if existing:
        return

    for cat in DEFAULT_CATEGORIES:
        category = Category(
            name=cat["name"],
            icon=cat["icon"],
            color=cat["color"],
            is_default=True,
            user_id=None
        )
        db.add(category)
    db.commit()


def get_available_categories(db, user_id):
    return db.query(Category).filter(
        or_(
            Category.is_default == True,
            Category.user_id == user_id
        )
    ).order_by(Category.is_default.desc(), Category.id).all()


def get_category_by_id(db, category_id):
    return db.query(Category).filter(Category.id == category_id).first()


def can_user_access_category(db, category_id, user_id):
    category = get_category_by_id(db, category_id)
    if not category:
        return False
    if category.is_default:
        return True
    return category.user_id == user_id


def is_category_name_taken(db, name, user_id, exclude_category_id=None):
    default_exists = db.query(Category).filter(
        Category.is_default == True,
        Category.name == name
    ).first()
    if default_exists:
        return True

    query = db.query(Category).filter(
        Category.is_default == False,
        Category.user_id == user_id,
        Category.name == name
    )

    if exclude_category_id is not None:
        query = query.filter(Category.id != exclude_category_id)

    custom_exists = query.first()
    if custom_exists:
        return True

    return False


def create_user_category(db, name, icon, color, user_id):
    if is_category_name_taken(db, name, user_id):
        raise CategoryNameAlreadyExistsError()

    category = Category(
        name=name,
        icon=icon or "📝",
        color=color or "#6B7280",
        is_default=False,
        user_id=user_id
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_user_category(db, category_id, user_id, name=None, icon=None, color=None):
    category = get_category_by_id(db, category_id)

    if not category:
        raise CategoryNotFoundError()

    if category.is_default:
        raise UnauthorizedCategoryAccess()

    if category.user_id != user_id:
        raise UnauthorizedCategoryAccess()

    if name is not None:
        if is_category_name_taken(db, name, user_id, exclude_category_id=category_id):
            raise CategoryNameAlreadyExistsError()
        category.name = name
    if icon is not None:
        category.icon = icon
    if color is not None:
        category.color = color

    db.commit()
    db.refresh(category)
    return category


def delete_user_category(db, category_id, user_id):
    category = get_category_by_id(db, category_id)

    if not category:
        raise CategoryNotFoundError()

    if category.is_default:
        raise CannotDeleteDefaultCategory()

    if category.user_id != user_id:
        raise UnauthorizedCategoryAccess()

    db.delete(category)
    db.commit()


def get_category_stats(db, user_id, category_id=None, start_date=None, end_date=None):
    query = db.query(
        Category.id,
        Category.name,
        Category.icon,
        Category.color,
        Category.is_default,
        Category.user_id,
        func.sum(Expense.amount).label("total_amount"),
        func.count(Expense.id).label("expense_count")
    ).join(
        Expense, Category.id == Expense.category_id, isouter=True
    ).filter(
        Expense.user_id == user_id
    )

    if category_id is not None:
        query = query.filter(Category.id == category_id)

    if start_date is not None:
        query = query.filter(Expense.created_at >= start_date)

    if end_date is not None:
        query = query.filter(Expense.created_at <= end_date)

    results = query.group_by(
        Category.id,
        Category.name,
        Category.icon,
        Category.color,
        Category.is_default,
        Category.user_id
    ).all()

    return [
        {
            "category": {
                "id": row.id,
                "name": row.name,
                "icon": row.icon,
                "color": row.color,
                "is_default": row.is_default,
                "user_id": row.user_id
            },
            "total_amount": float(row.total_amount or 0),
            "expense_count": row.expense_count or 0
        }
        for row in results
    ]
