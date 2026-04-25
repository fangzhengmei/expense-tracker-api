from app.models.tag import Tag
from app.models.expense import Expense
from sqlalchemy import func
from sqlalchemy.orm import Session


class TagNotFoundError(Exception):
    pass


class TagAlreadyExistsError(Exception):
    pass


class UnauthorizedTagAccess(Exception):
    pass


def create_tag(db: Session, name: str, user_id: int, color: str = "#6366f1") -> Tag:
    existing_tag = db.query(Tag).filter(
        Tag.name == name,
        Tag.user_id == user_id
    ).first()
    
    if existing_tag:
        raise TagAlreadyExistsError(f"Tag '{name}' already exists")
    
    tag = Tag(
        name=name,
        color=color,
        user_id=user_id
    )
    
    db.add(tag)
    db.commit()
    db.refresh(tag)
    
    return tag


def get_tags_by_user(db: Session, user_id: int) -> list[Tag]:
    return db.query(Tag).filter(Tag.user_id == user_id).all()


def get_tag_by_user(db: Session, tag_id: int, user_id: int) -> Tag | None:
    return db.query(Tag).filter(
        Tag.id == tag_id,
        Tag.user_id == user_id
    ).first()


def update_tag_by_user(
    db: Session,
    tag_id: int,
    user_id: int,
    name: str | None = None,
    color: str | None = None
) -> Tag:
    tag = get_tag_by_user(db, tag_id, user_id)
    
    if not tag:
        raise TagNotFoundError()
    
    if name is not None:
        existing_tag = db.query(Tag).filter(
            Tag.name == name,
            Tag.user_id == user_id,
            Tag.id != tag_id
        ).first()
        
        if existing_tag:
            raise TagAlreadyExistsError(f"Tag '{name}' already exists")
        
        tag.name = name
    
    if color is not None:
        tag.color = color
    
    db.commit()
    db.refresh(tag)
    
    return tag


def delete_tag_by_user(db: Session, tag_id: int, user_id: int) -> None:
    tag = get_tag_by_user(db, tag_id, user_id)
    
    if not tag:
        raise TagNotFoundError()
    
    db.delete(tag)
    db.commit()


def get_tags_by_ids(db: Session, tag_ids: list[int], user_id: int) -> list[Tag]:
    return db.query(Tag).filter(
        Tag.id.in_(tag_ids),
        Tag.user_id == user_id
    ).all()


def get_tag_stats(db: Session, user_id: int, tag_id: int) -> dict:
    tag = get_tag_by_user(db, tag_id, user_id)
    
    if not tag:
        raise TagNotFoundError()
    
    count = db.query(func.count(Expense.id)).filter(
        Expense.user_id == user_id,
        Expense.tags.any(Tag.id == tag_id)
    ).scalar()
    
    total = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.tags.any(Tag.id == tag_id)
    ).scalar()
    
    return {
        "expense_count": count or 0,
        "total_amount": float(total or 0)
    }


def get_all_tag_stats(db: Session, user_id: int) -> list[dict]:
    tags = get_tags_by_user(db, user_id)
    
    results = []
    for tag in tags:
        stats = get_tag_stats(db, user_id, tag.id)
        results.append({
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "user_id": tag.user_id,
            "expense_count": stats["expense_count"],
            "total_amount": stats["total_amount"]
        })
    
    return results
