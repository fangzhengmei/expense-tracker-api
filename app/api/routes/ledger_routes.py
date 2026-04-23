from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas.ledger_schema import (
    LedgerCreate,
    LedgerUpdate,
    LedgerOut,
    LedgerMemberOut,
    MemberRoleUpdate,
    InvitationCreate,
    InvitationOut,
    JoinLedger
)
from app.schemas.expense_schema import ExpenseWithUserOut, ExpenseCreate, ExpenseUpdate
from app.schemas.category_schema import (
    CategoryCreate,
    CategoryUpdate,
    CategoryOut,
    CategoryStats
)
from app.db.database import get_db
from app.api.deps import get_current_user

from app.services.ledger_service import (
    create_ledger,
    get_user_ledgers,
    get_ledger_details,
    update_ledger,
    deactivate_ledger,
    get_ledger_members,
    update_member_role,
    remove_member,
    create_invitation,
    get_ledger_invitations,
    deactivate_invitation,
    join_ledger_by_code,
    get_or_create_personal_ledger,
    LedgerError,
    LedgerNotFoundError,
    NotMemberError,
    InsufficientPermissionsError,
    InvitationNotFoundError,
    InvitationExpiredError,
    InvitationUsedUpError,
    AlreadyMemberError,
    CannotRemoveOwnerError
)

from app.services.expense_service import (
    create_expense as create_expense_service,
    get_expenses_by_ledger,
    get_ledger_expense_summary,
    get_monthly_expenses_by_ledger,
    get_expense_with_details,
    delete_expense,
    update_expense,
    ExpenseNotFoundError,
    UnauthorizedExpenseAccess
)

from app.services.category_service import (
    get_ledger_categories,
    get_category_by_id,
    create_category as create_category_service,
    update_category as update_category_service,
    deactivate_category,
    get_category_stats_with_percentage,
    get_monthly_category_stats,
    CategoryError,
    CategoryNotFoundError,
    CannotModifyDefaultCategoryError
)

from app.models.ledger import LedgerType
from app.models.category import CategoryType


router = APIRouter()


def handle_ledger_error(e: LedgerError) -> HTTPException:
    if isinstance(e, LedgerNotFoundError):
        return HTTPException(status_code=404, detail="账本不存在")
    elif isinstance(e, NotMemberError):
        return HTTPException(status_code=403, detail="你不是该账本的成员")
    elif isinstance(e, InsufficientPermissionsError):
        return HTTPException(status_code=403, detail="权限不足")
    elif isinstance(e, InvitationNotFoundError):
        return HTTPException(status_code=404, detail="邀请码无效或已过期")
    elif isinstance(e, InvitationExpiredError):
        return HTTPException(status_code=400, detail="邀请码已过期")
    elif isinstance(e, InvitationUsedUpError):
        return HTTPException(status_code=400, detail="邀请码使用次数已达上限")
    elif isinstance(e, AlreadyMemberError):
        return HTTPException(status_code=400, detail="你已经是该账本的成员")
    elif isinstance(e, CannotRemoveOwnerError):
        return HTTPException(status_code=400, detail="无法移除账本所有者或需要至少一个所有者")
    else:
        return HTTPException(status_code=500, detail=str(e))


def handle_category_error(e: CategoryError) -> HTTPException:
    if isinstance(e, CategoryNotFoundError):
        return HTTPException(status_code=404, detail="分类不存在")
    elif isinstance(e, CannotModifyDefaultCategoryError):
        return HTTPException(status_code=400, detail="无法修改或删除默认分类")
    else:
        return HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=LedgerOut)
def create_ledger_endpoint(
    ledger: LedgerCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_ledger = create_ledger(
        db,
        user_id=user.id,
        name=ledger.name,
        ledger_type=ledger.type,
        description=ledger.description
    )

    return LedgerOut(
        id=new_ledger.id,
        name=new_ledger.name,
        type=new_ledger.type,
        description=new_ledger.description,
        created_by=new_ledger.created_by,
        created_at=new_ledger.created_at,
        updated_at=new_ledger.updated_at,
        is_active=new_ledger.is_active,
        member_count=1,
        my_role="owner"
    )


@router.get("/", response_model=list[LedgerOut])
def list_ledgers(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    personal_ledger = get_or_create_personal_ledger(db, user.id)

    ledgers = get_user_ledgers(db, user.id)

    result = []
    for ledger, role, member_count in ledgers:
        result.append(LedgerOut(
            id=ledger.id,
            name=ledger.name,
            type=ledger.type,
            description=ledger.description,
            created_by=ledger.created_by,
            created_at=ledger.created_at,
            updated_at=ledger.updated_at,
            is_active=ledger.is_active,
            member_count=member_count,
            my_role=role
        ))

    return result


@router.get("/personal", response_model=LedgerOut)
def get_personal_ledger(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ledger = get_or_create_personal_ledger(db, user.id)

    try:
        ledger, role, member_count = get_ledger_details(db, ledger.id, user.id)
        return LedgerOut(
            id=ledger.id,
            name=ledger.name,
            type=ledger.type,
            description=ledger.description,
            created_by=ledger.created_by,
            created_at=ledger.created_at,
            updated_at=ledger.updated_at,
            is_active=ledger.is_active,
            member_count=member_count,
            my_role=role
        )
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.get("/{ledger_id}", response_model=LedgerOut)
def get_ledger(
    ledger_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        ledger, role, member_count = get_ledger_details(db, ledger_id, user.id)
        return LedgerOut(
            id=ledger.id,
            name=ledger.name,
            type=ledger.type,
            description=ledger.description,
            created_by=ledger.created_by,
            created_at=ledger.created_at,
            updated_at=ledger.updated_at,
            is_active=ledger.is_active,
            member_count=member_count,
            my_role=role
        )
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.put("/{ledger_id}", response_model=LedgerOut)
def update_ledger_endpoint(
    ledger_id: int,
    ledger_update: LedgerUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        ledger = update_ledger(
            db,
            ledger_id=ledger_id,
            user_id=user.id,
            name=ledger_update.name,
            description=ledger_update.description
        )

        _, role, member_count = get_ledger_details(db, ledger_id, user.id)

        return LedgerOut(
            id=ledger.id,
            name=ledger.name,
            type=ledger.type,
            description=ledger.description,
            created_by=ledger.created_by,
            created_at=ledger.created_at,
            updated_at=ledger.updated_at,
            is_active=ledger.is_active,
            member_count=member_count,
            my_role=role
        )
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.delete("/{ledger_id}")
def delete_ledger_endpoint(
    ledger_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        deactivate_ledger(db, ledger_id, user.id)
        return {"message": "账本已删除"}
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.get("/{ledger_id}/members", response_model=list[LedgerMemberOut])
def list_ledger_members(
    ledger_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from app.services.ledger_service import check_member_access
        check_member_access(db, ledger_id, user.id)

        members = get_ledger_members(db, ledger_id)

        result = []
        for member, email in members:
            result.append(LedgerMemberOut(
                user_id=member.user_id,
                user_email=email,
                role=member.role,
                joined_at=member.joined_at
            ))

        return result
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.put("/{ledger_id}/members/{user_id}/role", response_model=LedgerMemberOut)
def update_member_role_endpoint(
    ledger_id: int,
    user_id: int,
    role_update: MemberRoleUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        member = update_member_role(
            db,
            ledger_id=ledger_id,
            target_user_id=user_id,
            new_role=role_update.role,
            actor_user_id=current_user.id
        )

        from app.models.user import User
        user = db.query(User).filter(User.id == user_id).first()

        return LedgerMemberOut(
            user_id=member.user_id,
            user_email=user.email if user else "",
            role=member.role,
            joined_at=member.joined_at
        )
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.delete("/{ledger_id}/members/{user_id}")
def remove_member_endpoint(
    ledger_id: int,
    user_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        remove_member(db, ledger_id, user_id, current_user.id)
        return {"message": "成员已移除"}
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.post("/{ledger_id}/invitations", response_model=InvitationOut)
def create_invitation_endpoint(
    ledger_id: int,
    invitation: InvitationCreate = InvitationCreate(),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        new_invitation = create_invitation(
            db,
            ledger_id=ledger_id,
            user_id=user.id,
            max_uses=invitation.max_uses,
            expires_in_hours=invitation.expires_in_hours
        )

        return InvitationOut(
            id=new_invitation.id,
            ledger_id=new_invitation.ledger_id,
            code=new_invitation.code,
            created_by=new_invitation.created_by,
            created_at=new_invitation.created_at,
            expires_at=new_invitation.expires_at,
            max_uses=new_invitation.max_uses,
            used_count=new_invitation.used_count,
            is_active=new_invitation.is_active
        )
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.get("/{ledger_id}/invitations", response_model=list[InvitationOut])
def list_invitations(
    ledger_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        invitations = get_ledger_invitations(db, ledger_id, user.id)
        return [
            InvitationOut(
                id=inv.id,
                ledger_id=inv.ledger_id,
                code=inv.code,
                created_by=inv.created_by,
                created_at=inv.created_at,
                expires_at=inv.expires_at,
                max_uses=inv.max_uses,
                used_count=inv.used_count,
                is_active=inv.is_active
            )
            for inv in invitations
        ]
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.delete("/{ledger_id}/invitations/{invitation_id}")
def deactivate_invitation_endpoint(
    ledger_id: int,
    invitation_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        deactivate_invitation(db, ledger_id, invitation_id, user.id)
        return {"message": "邀请码已失效"}
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.post("/join", response_model=LedgerOut)
def join_ledger_endpoint(
    join_data: JoinLedger,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        ledger = join_ledger_by_code(db, join_data.code, user.id)

        _, role, member_count = get_ledger_details(db, ledger.id, user.id)

        return LedgerOut(
            id=ledger.id,
            name=ledger.name,
            type=ledger.type,
            description=ledger.description,
            created_by=ledger.created_by,
            created_at=ledger.created_at,
            updated_at=ledger.updated_at,
            is_active=ledger.is_active,
            member_count=member_count,
            my_role=role
        )
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.get("/{ledger_id}/categories", response_model=list[CategoryOut])
def list_ledger_categories(
    ledger_id: int,
    category_type: Optional[CategoryType] = Query(None, description="分类类型：expense 支出，income 收入"),
    include_inactive: bool = Query(False, description="是否包含已禁用的分类"),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from app.services.ledger_service import check_member_access
        check_member_access(db, ledger_id, user.id)

        categories = get_ledger_categories(db, ledger_id, category_type, include_inactive)

        return [
            CategoryOut(
                id=cat.id,
                name=cat.name,
                type=cat.type,
                color=cat.color,
                icon=cat.icon,
                sort_order=cat.sort_order,
                is_default=cat.is_default,
                is_active=cat.is_active,
                ledger_id=cat.ledger_id,
                created_at=cat.created_at,
                updated_at=cat.updated_at
            )
            for cat in categories
        ]
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.post("/{ledger_id}/categories", response_model=CategoryOut)
def create_category_endpoint(
    ledger_id: int,
    category: CategoryCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from app.services.ledger_service import check_admin_access
        check_admin_access(db, ledger_id, user.id)

        new_category = create_category_service(
            db,
            ledger_id=ledger_id,
            name=category.name,
            category_type=category.type,
            color=category.color,
            icon=category.icon,
            sort_order=category.sort_order
        )

        return CategoryOut(
            id=new_category.id,
            name=new_category.name,
            type=new_category.type,
            color=new_category.color,
            icon=new_category.icon,
            sort_order=new_category.sort_order,
            is_default=new_category.is_default,
            is_active=new_category.is_active,
            ledger_id=new_category.ledger_id,
            created_at=new_category.created_at,
            updated_at=new_category.updated_at
        )
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.put("/{ledger_id}/categories/{category_id}", response_model=CategoryOut)
def update_category_endpoint(
    ledger_id: int,
    category_id: int,
    category: CategoryUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from app.services.ledger_service import check_admin_access
        check_admin_access(db, ledger_id, user.id)

        updated_category = update_category_service(
            db,
            category_id=category_id,
            name=category.name,
            color=category.color,
            icon=category.icon,
            sort_order=category.sort_order,
            is_active=category.is_active
        )

        return CategoryOut(
            id=updated_category.id,
            name=updated_category.name,
            type=updated_category.type,
            color=updated_category.color,
            icon=updated_category.icon,
            sort_order=updated_category.sort_order,
            is_default=updated_category.is_default,
            is_active=updated_category.is_active,
            ledger_id=updated_category.ledger_id,
            created_at=updated_category.created_at,
            updated_at=updated_category.updated_at
        )
    except LedgerError as e:
        raise handle_ledger_error(e)
    except CategoryError as e:
        raise handle_category_error(e)


@router.delete("/{ledger_id}/categories/{category_id}")
def delete_category_endpoint(
    ledger_id: int,
    category_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from app.services.ledger_service import check_admin_access
        check_admin_access(db, ledger_id, user.id)

        deactivate_category(db, category_id)
        return {"message": "分类已删除"}
    except LedgerError as e:
        raise handle_ledger_error(e)
    except CategoryError as e:
        raise handle_category_error(e)


@router.get("/{ledger_id}/categories/stats", response_model=list[CategoryStats])
def get_category_stats(
    ledger_id: int,
    category_type: CategoryType = Query(CategoryType.EXPENSE, description="分类类型：expense 支出，income 收入"),
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from app.services.ledger_service import check_member_access
        check_member_access(db, ledger_id, user.id)

        total_amount, stats = get_category_stats_with_percentage(
            db, ledger_id, category_type, start_date, end_date
        )

        return [
            CategoryStats(
                category_id=stat["category_id"],
                category_name=stat["category_name"],
                category_color=stat["category_color"],
                category_icon=stat["category_icon"],
                total_amount=stat["total_amount"],
                count=stat["count"],
                percentage=stat["percentage"]
            )
            for stat in stats
        ]
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.get("/{ledger_id}/categories/stats/monthly")
def get_monthly_category_stats_endpoint(
    ledger_id: int,
    category_type: CategoryType = Query(CategoryType.EXPENSE, description="分类类型：expense 支出，income 收入"),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from app.services.ledger_service import check_member_access
        check_member_access(db, ledger_id, user.id)

        return get_monthly_category_stats(db, ledger_id, category_type)
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.post("/{ledger_id}/expenses", response_model=ExpenseWithUserOut)
def create_expense_in_ledger(
    ledger_id: int,
    expense: ExpenseCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if expense.ledger_id is not None and expense.ledger_id != ledger_id:
        raise HTTPException(status_code=400, detail="ledger_id 不匹配")

    try:
        new_expense = create_expense_service(
            db,
            amount=expense.amount,
            description=expense.description,
            user_id=user.id,
            ledger_id=ledger_id,
            category_id=expense.category_id
        )

        expense_details = get_expense_with_details(db, new_expense.id)
        if expense_details:
            exp, email, category_name, category_color = expense_details
            return ExpenseWithUserOut(
                id=exp.id,
                amount=exp.amount,
                description=exp.description,
                user_id=exp.user_id,
                user_email=email,
                ledger_id=exp.ledger_id,
                category_id=exp.category_id,
                category_name=category_name,
                category_color=category_color,
                created_at=exp.created_at,
                updated_at=exp.updated_at
            )

        return ExpenseWithUserOut(
            id=new_expense.id,
            amount=new_expense.amount,
            description=new_expense.description,
            user_id=new_expense.user_id,
            user_email=user.email,
            ledger_id=new_expense.ledger_id,
            category_id=new_expense.category_id,
            created_at=new_expense.created_at,
            updated_at=new_expense.updated_at
        )
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.get("/{ledger_id}/expenses", response_model=list[ExpenseWithUserOut])
def list_ledger_expenses(
    ledger_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        expenses = get_expenses_by_ledger(db, ledger_id, user.id, limit, offset)

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
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.get("/{ledger_id}/expenses/analytics")
def get_ledger_analytics(
    ledger_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return get_ledger_expense_summary(db, ledger_id, user.id)
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.get("/{ledger_id}/expenses/analytics/monthly")
def get_ledger_monthly_analytics(
    ledger_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return get_monthly_expenses_by_ledger(db, ledger_id, user.id)
    except LedgerError as e:
        raise handle_ledger_error(e)


@router.put("/{ledger_id}/expenses/{expense_id}", response_model=ExpenseWithUserOut)
def update_expense_in_ledger(
    ledger_id: int,
    expense_id: int,
    expense: ExpenseUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from app.services.ledger_service import check_member_access
        check_member_access(db, ledger_id, user.id)

        updated_expense = update_expense(
            db,
            expense_id=expense_id,
            user_id=user.id,
            amount=expense.amount,
            description=expense.description,
            category_id=expense.category_id
        )

        expense_details = get_expense_with_details(db, updated_expense.id)
        if expense_details:
            exp, email, category_name, category_color = expense_details
            return ExpenseWithUserOut(
                id=exp.id,
                amount=exp.amount,
                description=exp.description,
                user_id=exp.user_id,
                user_email=email,
                ledger_id=exp.ledger_id,
                category_id=exp.category_id,
                category_name=category_name,
                category_color=category_color,
                created_at=exp.created_at,
                updated_at=exp.updated_at
            )

        from app.models.user import User
        expense_user = db.query(User).filter(User.id == updated_expense.user_id).first()

        return ExpenseWithUserOut(
            id=updated_expense.id,
            amount=updated_expense.amount,
            description=updated_expense.description,
            user_id=updated_expense.user_id,
            user_email=expense_user.email if expense_user else "",
            ledger_id=updated_expense.ledger_id,
            category_id=updated_expense.category_id,
            created_at=updated_expense.created_at,
            updated_at=updated_expense.updated_at
        )
    except LedgerError as e:
        raise handle_ledger_error(e)
    except (ExpenseNotFoundError, UnauthorizedExpenseAccess):
        raise HTTPException(status_code=404, detail="支出记录不存在")


@router.delete("/{ledger_id}/expenses/{expense_id}")
def delete_expense_in_ledger(
    ledger_id: int,
    expense_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from app.services.ledger_service import check_member_access
        check_member_access(db, ledger_id, user.id)

        delete_expense(db, expense_id, user.id)
        return {"message": "支出记录已删除"}
    except LedgerError as e:
        raise handle_ledger_error(e)
    except (ExpenseNotFoundError, UnauthorizedExpenseAccess):
        raise HTTPException(status_code=404, detail="支出记录不存在")
