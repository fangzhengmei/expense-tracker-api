from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas.expense_schema import ExpenseCreate, ExpenseUpdate, ExpenseOut
from app.models.enums import ExpenseStatus
from app.db.database import get_db

from app.services.expense_service import (
    create_expense,
    get_expenses_by_user,
    get_expense_by_user,
    delete_expense_by_user,
    update_expense_by_user,
    get_monthly_expenses,
    ExpenseNotFoundError,
    ExpenseAlreadyApprovedError
)

from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter()


@router.post("/", response_model=ExpenseOut)
def create_expense_endpoint(
    expense: ExpenseCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return create_expense(
        db,
        amount=expense.amount,
        description=expense.description,
        user_id=user.id
    )


@router.get("/", response_model=list[ExpenseOut])
def list_expenses(
    status: Optional[ExpenseStatus] = Query(None, description="按状态过滤"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_expenses_by_user(db, user.id, status=status)


@router.get("/{id}", response_model=ExpenseOut)
def get_expense_detail(
    id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expense = get_expense_by_user(db, id, user.id)
    if not expense:
        raise HTTPException(status_code=404, detail="支出记录不存在")
    return expense


@router.delete("/{id}")
def delete_expense_endpoint(
    id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        delete_expense_by_user(db, id, user.id)
        return {"message": "支出已删除"}
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="支出记录不存在")
    except ExpenseAlreadyApprovedError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id}", response_model=ExpenseOut)
def update_expense_endpoint(
    id: int,
    expense: ExpenseUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return update_expense_by_user(
            db,
            expense_id=id,
            user_id=user.id,
            amount=expense.amount,
            description=expense.description
        )
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="支出记录不存在")
    except ExpenseAlreadyApprovedError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/monthly")
def get_monthly_analytics(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_monthly_expenses(db, user.id)
