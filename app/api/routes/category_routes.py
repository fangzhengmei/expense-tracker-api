from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import Optional

from app.schemas.category_schema import CategoryCreate, CategoryUpdate, CategoryOut, CategoryStats
from app.db.database import get_db

from app.services.category_service import (
    get_available_categories,
    create_user_category,
    update_user_category,
    delete_user_category,
    get_category_stats,
    CategoryNotFoundError,
    UnauthorizedCategoryAccess,
    CannotDeleteDefaultCategory,
    CategoryNameAlreadyExistsError
)

from app.api.deps import get_current_user


router = APIRouter()


@router.get("/", response_model=list[CategoryOut])
def list_categories(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_available_categories(db, user.id)


@router.post("/", response_model=CategoryOut)
def create_category(
    category: CategoryCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return create_user_category(
            db,
            name=category.name,
            icon=category.icon,
            color=category.color,
            user_id=user.id
        )
    except CategoryNameAlreadyExistsError:
        raise HTTPException(status_code=400, detail="分类名称已存在")
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="分类名称已存在")


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    category: CategoryUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return update_user_category(
            db,
            category_id=category_id,
            user_id=user.id,
            name=category.name,
            icon=category.icon,
            color=category.color
        )
    except CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="分类不存在")
    except UnauthorizedCategoryAccess:
        raise HTTPException(status_code=403, detail="无权修改此分类")
    except CategoryNameAlreadyExistsError:
        raise HTTPException(status_code=400, detail="分类名称已存在")
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="分类名称已存在")


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        delete_user_category(db, category_id, user.id)
        return {"message": "分类删除成功"}
    except CategoryNotFoundError:
        raise HTTPException(status_code=404, detail="分类不存在")
    except CannotDeleteDefaultCategory:
        raise HTTPException(status_code=400, detail="不能删除系统默认分类")
    except UnauthorizedCategoryAccess:
        raise HTTPException(status_code=403, detail="无权删除此分类")


@router.get("/analytics/stats", response_model=list[CategoryStats])
def get_category_analytics(
    category_id: Optional[int] = Query(None, description="按分类筛选，不填则返回所有分类统计"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_category_stats(
        db,
        user_id=user.id,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date
    )
