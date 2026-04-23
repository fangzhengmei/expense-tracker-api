from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.expense_schema import (
    ExpenseCreate, 
    ExpenseUpdate, 
    ExpenseOut,
    ExpenseWithCategoryOut,
    ExpenseWithBudgetOut
)
from app.db.database import get_db

from app.services.expense_service import (
    create_expense_with_budget_check,
    get_expenses_by_user,
    get_expenses_by_user_with_category,
    delete_expense_by_user,
    update_expense_with_budget_check,
    get_monthly_expenses,
    ExpenseNotFoundError,
    InvalidCategoryError
)

from app.api.deps import get_current_user


router = APIRouter()


@router.post("/", response_model=ExpenseWithBudgetOut)
def create_expense_endpoint(
    expense: ExpenseCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        new_expense, budget_info = create_expense_with_budget_check(
            db,
            amount=expense.amount,
            description=expense.description,
            user_id=user.id,
            category_id=expense.category_id
        )
        return {
            "expense": new_expense,
            "budget_info": budget_info
        }
    except InvalidCategoryError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[ExpenseWithCategoryOut])
def list_expenses(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_expenses_by_user_with_category(db, user.id)


@router.get("/{id}", response_model=ExpenseWithCategoryOut)
def get_expense(
    id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expenses = get_expenses_by_user_with_category(db, user.id)
    for exp in expenses:
        if exp["id"] == id:
            return exp
    raise HTTPException(status_code=404, detail="支出记录不存在")


@router.delete("/{id}")
def delete_expense_endpoint(
    id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        delete_expense_by_user(db, id, user.id)
        return {"message": "支出记录已删除"}
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="支出记录不存在")


@router.put("/{id}", response_model=ExpenseWithBudgetOut)
def update_expense_endpoint(
    id: int,
    expense: ExpenseUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        updated_expense, budget_info = update_expense_with_budget_check(
            db,
            expense_id=id,
            user_id=user.id,
            amount=expense.amount,
            description=expense.description,
            category_id=expense.category_id
        )
        return {
            "expense": updated_expense,
            "budget_info": budget_info
        }
    except ExpenseNotFoundError:
        raise HTTPException(status_code=404, detail="支出记录不存在")
    except InvalidCategoryError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/analytics/monthly")
def get_monthly_analytics(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_monthly_expenses(db, user.id)
