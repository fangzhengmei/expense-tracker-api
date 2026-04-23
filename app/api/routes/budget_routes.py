from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.schemas.budget_schema import (
    BudgetCreate, 
    BudgetUpdate, 
    BudgetOut, 
    BudgetWithUsageOut,
    MonthlyBudgetSummary
)
from app.db.database import get_db

from app.services.budget_service import (
    create_budget,
    get_budgets_by_user,
    get_budgets_by_user_and_month,
    get_budget_by_user,
    update_budget_by_user,
    delete_budget_by_user,
    get_budget_with_usage,
    get_monthly_budget_summary,
    BudgetNotFoundError,
    BudgetAlreadyExistsError
)

from app.services.category_service import get_category_by_user

from app.api.deps import get_current_user


router = APIRouter()


@router.post("/", response_model=BudgetOut)
def create_budget_endpoint(
    budget: BudgetCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = get_category_by_user(db, budget.category_id, user.id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    try:
        return create_budget(
            db,
            user_id=user.id,
            amount=budget.amount,
            year=budget.year,
            month=budget.month,
            category_id=budget.category_id
        )
    except BudgetAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[BudgetOut])
def list_budgets(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_budgets_by_user(db, user.id)


@router.get("/monthly", response_model=list[BudgetWithUsageOut])
def list_budgets_with_usage(
    year: Optional[int] = Query(None, ge=2000, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if year is None or month is None:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
    
    budgets = get_budgets_by_user_and_month(db, user.id, year, month)
    
    result = []
    for budget in budgets:
        budget_usage = get_budget_with_usage(db, budget)
        result.append(budget_usage)
    
    return result


@router.get("/summary", response_model=MonthlyBudgetSummary)
def get_budget_summary(
    year: Optional[int] = Query(None, ge=2000, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if year is None or month is None:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
    
    return get_monthly_budget_summary(db, user.id, year, month)


@router.get("/{budget_id}", response_model=BudgetWithUsageOut)
def get_budget(
    budget_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    budget = get_budget_by_user(db, budget_id, user.id)
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")
    
    return get_budget_with_usage(db, budget)


@router.put("/{budget_id}", response_model=BudgetOut)
def update_budget_endpoint(
    budget_id: int,
    budget: BudgetUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return update_budget_by_user(
            db,
            budget_id=budget_id,
            user_id=user.id,
            amount=budget.amount
        )
    except BudgetNotFoundError:
        raise HTTPException(status_code=404, detail="预算不存在")


@router.delete("/{budget_id}")
def delete_budget_endpoint(
    budget_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        delete_budget_by_user(db, budget_id, user.id)
        return {"message": "预算已删除"}
    except BudgetNotFoundError:
        raise HTTPException(status_code=404, detail="预算不存在")
