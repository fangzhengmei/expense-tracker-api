from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.category_schema import CategoryCreate, CategoryUpdate, CategoryOut
from app.db.database import get_db

from app.services.category_service import (
    create_category,
    get_categories_by_user,
    get_category_by_user,
    update_category_by_user,
    delete_category_by_user,
    CategoryNotFoundError,
    CategoryAlreadyExistsError
)

from app.api.deps import get_current_user


router = APIRouter()


@router.post("/", response_model=CategoryOut)
def create_category_endpoint(
    category: CategoryCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return create_category(
            db,
            user_id=user.id,
            name=category.name,
            icon=category.icon,
            color=category.color
        )
    except CategoryAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[CategoryOut])
def list_categories(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_categories_by_user(db, user.id)


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(
    category_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = get_category_by_user(db, category_id, user.id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    return category


@router.put("/{category_id}", response_model=CategoryOut)
def update_category_endpoint(
    category_id: int,
    category: CategoryUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return update_category_by_user(
            db,
            category_id=category_id,
            user_id=user.id,
            name=category.name,
            icon=category.icon,
            color=category.color
        )
    except CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="分类不存在")
    except CategoryAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{category_id}")
def delete_category_endpoint(
    category_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        delete_category_by_user(db, category_id, user.id)
        return {"message": "分类已删除"}
    except CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="分类不存在")
