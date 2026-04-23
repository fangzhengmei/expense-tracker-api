from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.expense import Expense, Approval
from app.models.enums import ExpenseStatus, UserRole
from app.models.user import User


class ExpenseAlreadyApprovedError(Exception):
    pass


class CannotApproveOwnExpenseError(Exception):
    pass


class InvalidApprovalStatusError(Exception):
    pass


def create_approval(
    db: Session,
    expense_id: int,
    approver_id: int,
    status: ExpenseStatus,
    comment: str | None = None
):
    if status not in [ExpenseStatus.APPROVED, ExpenseStatus.REJECTED]:
        raise InvalidApprovalStatusError("审批状态只能是 approved 或 rejected")

    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        return None

    if expense.status != ExpenseStatus.PENDING:
        raise ExpenseAlreadyApprovedError("该支出已被审批，无法重复操作")

    if expense.user_id == approver_id:
        raise CannotApproveOwnExpenseError("不能审批自己提交的支出")

    old_status = expense.status
    expense.status = status

    approval = Approval(
        expense_id=expense_id,
        approver_id=approver_id,
        status=status,
        comment=comment
    )
    db.add(approval)
    db.commit()
    db.refresh(expense)
    db.refresh(approval)

    return approval


def get_pending_expenses(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(Expense)
        .filter(Expense.status == ExpenseStatus.PENDING)
        .order_by(Expense.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_approvals_by_expense(db: Session, expense_id: int):
    return (
        db.query(Approval)
        .filter(Approval.expense_id == expense_id)
        .order_by(Approval.created_at.desc())
        .all()
    )


def get_approvals_by_approver(db: Session, approver_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(Approval)
        .filter(Approval.approver_id == approver_id)
        .order_by(Approval.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_approval_statistics(db: Session, manager_id: int | None = None):
    base_query = db.query(Expense.status, func.count(Expense.id).label("count")).group_by(Expense.status)
    
    if manager_id:
        results = (
            db.query(
                Expense.status,
                func.count(Expense.id).label("total_count")
            )
            .join(Approval, Approval.expense_id == Expense.id)
            .filter(Approval.approver_id == manager_id)
            .group_by(Expense.status)
            .all()
        )
    else:
        results = base_query.all()

    stats = {
        ExpenseStatus.PENDING: 0,
        ExpenseStatus.APPROVED: 0,
        ExpenseStatus.REJECTED: 0
    }
    
    for row in results:
        if hasattr(row, 'status') and hasattr(row, 'count'):
            stats[row.status] = row.count
        elif hasattr(row, 'status') and hasattr(row, 'total_count'):
            stats[row.status] = row.total_count
            
    return stats


def get_expense_with_approvals(db: Session, expense_id: int):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        return None
    
    approvals = get_approvals_by_expense(db, expense_id)
    expense.approvals = approvals
    return expense


def can_user_modify_expense(db: Session, expense_id: int, user_id: int) -> bool:
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        return False
    
    if expense.user_id != user_id:
        return False
    
    if expense.status != ExpenseStatus.PENDING:
        return False
    
    return True


def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(User)
        .order_by(User.id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_user_role(db: Session, user_id: int, new_role: UserRole):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user
