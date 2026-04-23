from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.expense_schema import ExpenseCreate, ExpenseUpdate, ExpenseOut, ExpenseWithUserOut
from app.db.database import get_db

from app.services.expense_service import (
    ExpenseNotFoundError,
    UnauthorizedExpenseAccess
)

from app.api.deps import get_current_user
from app.services.ledger_service import get_or_create_personal_ledger
from app.services.expense_service import (
    create_expense as create_expense_service,
    get_expenses_by_ledger,
    get_expense_with_details,
    delete_expense,
    update_expense,
    get_user_monthly_expenses
)


router = APIRouter()


@router.post("/", response_model=ExpenseOut)
def create_expense_endpoint(
    expense: ExpenseCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    personal_ledger = get_or_create_personal_ledger(db, user.id)

    new_expense = create_expense_service(
        db,
        amount=expense.amount,
        description=expense.description,
        user_id=user.id,
        ledger_id=personal_ledger.id,
        category_id=expense.category_id
    )

    expense_details = get_expense_with_details(db, new_expense.id)
    if expense_details:
        exp, email, category_name, category_color = expense_details
        return ExpenseOut(
            id=exp.id,
            amount=exp.amount,
            description=exp.description,
            user_id=exp.user_id,
            ledger_id=exp.ledger_id,
            category_id=exp.category_id,
            category_name=category_name,
            category_color=category_color,
            created_at=exp.created_at,
            updated_at=exp.updated_at
        )

    return ExpenseOut(
        id=new_expense.id,
        amount=new_expense.amount,
        description=new_expense.description,
        user_id=new_expense.user_id,
        ledger_id=new_expense.ledger_id,
        category_id=new_expense.category_id,
        created_at=new_expense.created_at,
        updated_at=new_expense.updated_at
    )


@router.get("/", response_model=list[ExpenseWithUserOut])
def list_expenses(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    personal_ledger = get_or_create_personal_ledger(db, user.id)

    expenses = get_expenses_by_ledger(db, personal_ledger.id, user.id)

    return [
        ExpenseWithUserOut(
            id=expense.id,
            amount=expense.amount,
            description=expense.description,
            user_id=expense.user_id,
            user_email=email,
            ledger_id=expense.ledger_id,
            category_id=expense.category_id,
            category_name=category_name,
            category_color=category_color,
            created_at=expense.created_at,
            updated_at=expense.updated_at
        )
        for expense, email, category_name, category_color in expenses
    ]


@router.delete("/{id}")
def delete_expense_endpoint(
    id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        delete_expense(db, id, user.id)
        return {"message": "支出记录已删除"}
    except (ExpenseNotFoundError, UnauthorizedExpenseAccess):
        raise HTTPException(status_code=404, detail="支出记录不存在")


@router.put("/{id}", response_model=ExpenseOut)
def update_expense_endpoint(
    id: int,
    expense: ExpenseUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        updated_expense = update_expense(
            db,
            expense_id=id,
            user_id=user.id,
            amount=expense.amount,
            description=expense.description,
            category_id=expense.category_id
        )

        expense_details = get_expense_with_details(db, updated_expense.id)
        if expense_details:
            exp, email, category_name, category_color = expense_details
            return ExpenseOut(
                id=exp.id,
                amount=exp.amount,
                description=exp.description,
                user_id=exp.user_id,
                ledger_id=exp.ledger_id,
                category_id=exp.category_id,
                category_name=category_name,
                category_color=category_color,
                created_at=exp.created_at,
                updated_at=exp.updated_at
            )

        return ExpenseOut(
            id=updated_expense.id,
            amount=updated_expense.amount,
            description=updated_expense.description,
            user_id=updated_expense.user_id,
            ledger_id=updated_expense.ledger_id,
            category_id=updated_expense.category_id,
            created_at=updated_expense.created_at,
            updated_at=updated_expense.updated_at
        )
    except (ExpenseNotFoundError, UnauthorizedExpenseAccess):
        raise HTTPException(status_code=404, detail="支出记录不存在")


@router.get("/analytics/monthly")
def get_monthly_analytics(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_user_monthly_expenses(db, user.id)
