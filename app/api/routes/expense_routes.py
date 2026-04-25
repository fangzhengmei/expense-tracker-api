from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.schemas.expense_schema import ExpenseCreate, ExpenseUpdate, ExpenseOut
from app.db.database import get_db

from app.services.expense_service import (
    create_expense,
    get_expenses_by_user,
    delete_expense_by_user,
    update_expense_by_user,
    get_monthly_expenses,
    get_expenses_by_tag,
    get_expenses_by_tags,
    ExpenseNotFoundError
)

from app.api.deps import get_current_user


router = APIRouter()


@router.post("/", response_model=ExpenseOut)
def create_expense_endpoint(
    expense: ExpenseCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return create_expense(
        db,
        amount=expense.amount,
        description=expense.description,
        user_id=user.id,
        tag_ids=expense.tag_ids
    )


@router.get("/", response_model=list[ExpenseOut])
def list_expenses(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
    tag_ids: Optional[List[int]] = Query(None)
):
    if tag_ids:
        if len(tag_ids) == 1:
            return get_expenses_by_tag(db, user.id, tag_ids[0])
        return get_expenses_by_tags(db, user.id, tag_ids)
    return get_expenses_by_user(db, user.id)


@router.delete("/{id}")
def delete_expense_endpoint(
    id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        delete_expense_by_user(db, id, user.id)
        return {"message": "Gasto eliminado correctamente"}
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")


@router.put("/{id}", response_model=ExpenseOut)
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
            tag_ids=expense.tag_ids
        )
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")


@router.get("/analytics/monthly")
def get_monthly_analytics(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_monthly_expenses(db, user.id)
