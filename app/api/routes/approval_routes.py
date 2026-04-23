from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.api.deps import get_current_user, get_current_manager
from app.models.user import User
from app.models.enums import ExpenseStatus

from app.schemas.expense_schema import ApprovalCreate, ApprovalOut, ExpenseOut
from app.schemas.user_schema import UserOut, UserRoleUpdate

from app.services.approval_service import (
    create_approval,
    get_pending_expenses,
    get_approvals_by_approver,
    get_approval_statistics,
    get_expense_with_approvals,
    ExpenseAlreadyApprovedError,
    CannotApproveOwnExpenseError,
    InvalidApprovalStatusError,
    get_all_users,
    update_user_role
)


router = APIRouter()


@router.post("/approve", response_model=ApprovalOut)
def approve_expense(
    approval_data: ApprovalCreate,
    current_manager: User = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    try:
        approval = create_approval(
            db,
            expense_id=approval_data.expense_id,
            approver_id=current_manager.id,
            status=approval_data.status,
            comment=approval_data.comment
        )
        if not approval:
            raise HTTPException(status_code=404, detail="支出记录不存在")
        return approval
    except ExpenseAlreadyApprovedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CannotApproveOwnExpenseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidApprovalStatusError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pending", response_model=list[ExpenseOut])
def list_pending_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_manager: User = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    return get_pending_expenses(db, skip=skip, limit=limit)


@router.get("/my-approvals", response_model=list[ApprovalOut])
def list_my_approvals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_manager: User = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    return get_approvals_by_approver(db, approver_id=current_manager.id, skip=skip, limit=limit)


@router.get("/statistics")
def get_stats(
    current_manager: User = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    return get_approval_statistics(db)


@router.get("/expense/{expense_id}")
def get_expense_detail(
    expense_id: int,
    current_manager: User = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    expense = get_expense_with_approvals(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="支出记录不存在")
    return expense


@router.get("/users", response_model=list[UserOut])
def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_manager: User = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    return get_all_users(db, skip=skip, limit=limit)


@router.put("/users/{user_id}/role", response_model=UserOut)
def update_user_role_endpoint(
    user_id: int,
    role_data: UserRoleUpdate,
    current_manager: User = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    user = update_user_role(db, user_id=user_id, new_role=role_data.role)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user
