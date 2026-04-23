from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas.expense_schema import ExpenseCreate, ExpenseUpdate
from app.db.database import get_db

from app.services.expense_service import (
    create_expense,
    get_expenses_by_user,
    delete_expense_by_user,
    update_expense_by_user,
    get_monthly_expenses,
    get_expenses_summary_by_currency,
    get_expense_by_user,
    get_monthly_expenses_converted,
    get_expenses_summary_converted,
    get_all_expenses_with_conversion,
    ExpenseNotFoundError
)

from app.api.deps import get_current_user
from app.core.constants import SUPPORTED_CURRENCIES


router = APIRouter()


@router.post("/")
def create_expense_endpoint(
    expense: ExpenseCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return create_expense(
        db,
        amount=expense.amount,
        currency=expense.currency,
        description=expense.description,
        user_id=user.id
    )


@router.get("/")
def list_expenses(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_expenses_by_user(db, user.id)


@router.get("/{id}")
def get_expense(
    id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expense = get_expense_by_user(db, id, user.id)
    if not expense:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    return expense


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
            currency=expense.currency,
            description=expense.description
        )
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")


@router.get("/analytics/monthly")
def get_monthly_analytics(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_monthly_expenses(db, user.id)


@router.get("/analytics/currency")
def get_currency_analytics(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_expenses_summary_by_currency(db, user.id)


@router.get("/analytics/monthly/converted")
def get_monthly_analytics_converted(
    target_currency: Optional[str] = Query(
        None, 
        description="目标货币代码，不指定则使用用户默认货币"
    ),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if target_currency is not None:
        target_currency = target_currency.upper()
        if target_currency not in SUPPORTED_CURRENCIES:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported currency: {target_currency}. Supported: {SUPPORTED_CURRENCIES}"
            )
    return get_monthly_expenses_converted(db, user.id, target_currency)


@router.get("/analytics/summary/converted")
def get_summary_analytics_converted(
    target_currency: Optional[str] = Query(
        None, 
        description="目标货币代码，不指定则使用用户默认货币"
    ),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if target_currency is not None:
        target_currency = target_currency.upper()
        if target_currency not in SUPPORTED_CURRENCIES:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported currency: {target_currency}. Supported: {SUPPORTED_CURRENCIES}"
            )
    return get_expenses_summary_converted(db, user.id, target_currency)


@router.get("/with-conversion")
def list_expenses_with_conversion(
    target_currency: Optional[str] = Query(
        None, 
        description="目标货币代码，不指定则使用用户默认货币"
    ),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if target_currency is not None:
        target_currency = target_currency.upper()
        if target_currency not in SUPPORTED_CURRENCIES:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported currency: {target_currency}. Supported: {SUPPORTED_CURRENCIES}"
            )
    return get_all_expenses_with_conversion(db, user.id, target_currency)
