from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.schemas.expense_schema import ExpenseCreate, ExpenseUpdate
from app.db.database import get_db

from app.services.expense_service import (
    create_expense,
    get_expenses_by_user,
    delete_expense_by_user,
    update_expense_by_user,
    get_monthly_expenses,
    ExpenseNotFoundError,
    InvalidCategoryError
)

from app.api.deps import get_current_user


router = APIRouter()


@router.post("/")
def create_expense_endpoint(
    expense: ExpenseCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return create_expense(
            db,
            amount=expense.amount,
            description=expense.description,
            user_id=user.id,
            category_id=expense.category_id
        )
    except InvalidCategoryError:
        raise HTTPException(status_code=400, detail="分类无效或无权限访问")


@router.get("/")
def list_expenses(
    category_id: Optional[int] = Query(None, description="按分类筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_expenses_by_user(
        db,
        user.id,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date
    )


@router.delete("/{id}")
def delete_expense_endpoint(
    id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        delete_expense_by_user(db, id, user.id)
        return {"message": "支出删除成功"}
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="支出不存在")


@router.put("/{id}")
def update_expense_endpoint(
    id: int,
    expense: ExpenseUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return update_expense_by_user(
            db,
            expense_id=id,
            user_id=user.id,
            amount=expense.amount,
            description=expense.description,
            category_id=expense.category_id
        )
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="支出不存在")
    except InvalidCategoryError:
        raise HTTPException(status_code=400, detail="分类无效或无权限访问")


@router.get("/analytics/monthly")
def get_monthly_analytics(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_monthly_expenses(db, user.id)
