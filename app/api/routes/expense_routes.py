from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

from app.schemas.expense_schema import ExpenseCreate, ExpenseUpdate
from app.db.database import get_db

from app.services.expense_service import (
    create_expense,
    get_expenses_by_user,
    delete_expense_by_user,
    update_expense_by_user,
    get_monthly_expenses,
    export_expenses_to_csv,
    ExpenseNotFoundError
)

from app.api.deps import get_current_user


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
        description=expense.description,
        user_id=user.id
    )


@router.get("/")
def list_expenses(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
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


@router.get("/export/csv")
def export_expenses_csv(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    csv_content = export_expenses_to_csv(db, user.id)
    
    filename = f"expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    csv_with_bom = '\ufeff' + csv_content.getvalue()
    csv_bytes = csv_with_bom.encode('utf-8')
    
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )
