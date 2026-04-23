from app.models.category import Category
from sqlalchemy.exc import IntegrityError


class CategoryNotFoundError(Exception):
    pass


class CategoryAlreadyExistsError(Exception):
    pass


class UnauthorizedCategoryAccess(Exception):
    pass


def create_category(db, user_id, name, icon=None, color=None):
    try:
        category = Category(
            name=name,
            icon=icon,
            color=color,
            user_id=user_id
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except IntegrityError:
        db.rollback()
        raise CategoryAlreadyExistsError(f"分类 '{name}' 已存在")


def get_categories_by_user(db, user_id):
    return db.query(Category).filter(Category.user_id == user_id).all()


def get_category_by_user(db, category_id, user_id):
    return db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == user_id
    ).first()


def get_category_by_id(db, category_id):
    return db.query(Category).filter(Category.id == category_id).first()


def update_category_by_user(db, category_id, user_id, name=None, icon=None, color=None):
    category = get_category_by_user(db, category_id, user_id)
    
    if not category:
        raise CategoryNotFoundError()
    
    try:
        if name is not None:
            category.name = name
        if icon is not None:
            category.icon = icon
        if color is not None:
            category.color = color
        
        db.commit()
        db.refresh(category)
        return category
    except IntegrityError:
        db.rollback()
        raise CategoryAlreadyExistsError(f"分类 '{name}' 已存在")


def delete_category_by_user(db, category_id, user_id):
    category = get_category_by_user(db, category_id, user_id)
    
    if not category:
        raise CategoryNotFoundError()
    
    db.delete(category)
    db.commit()
