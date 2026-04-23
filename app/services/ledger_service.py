import random
import string
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.ledger import Ledger, LedgerMember, Invitation, LedgerType, MemberRole
from app.models.user import User


class LedgerError(Exception):
    pass


class LedgerNotFoundError(LedgerError):
    pass


class NotMemberError(LedgerError):
    pass


class InsufficientPermissionsError(LedgerError):
    pass


class InvitationNotFoundError(LedgerError):
    pass


class InvitationExpiredError(LedgerError):
    pass


class InvitationUsedUpError(LedgerError):
    pass


class AlreadyMemberError(LedgerError):
    pass


class CannotRemoveOwnerError(LedgerError):
    pass


def generate_invitation_code(length: int = 8) -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def create_personal_ledger(db: Session, user_id: int) -> Ledger:
    ledger = Ledger(
        name="我的账本",
        type=LedgerType.PERSONAL,
        description="个人日常记账",
        created_by=user_id,
        is_active=True
    )
    db.add(ledger)
    db.flush()

    member = LedgerMember(
        ledger_id=ledger.id,
        user_id=user_id,
        role=MemberRole.OWNER
    )
    db.add(member)
    db.commit()
    db.refresh(ledger)

    return ledger


def create_ledger(
    db: Session,
    user_id: int,
    name: str,
    ledger_type: LedgerType = LedgerType.SHARED,
    description: Optional[str] = None
) -> Ledger:
    ledger = Ledger(
        name=name,
        type=ledger_type,
        description=description,
        created_by=user_id,
        is_active=True
    )
    db.add(ledger)
    db.flush()

    member = LedgerMember(
        ledger_id=ledger.id,
        user_id=user_id,
        role=MemberRole.OWNER
    )
    db.add(member)
    db.commit()
    db.refresh(ledger)

    return ledger


def get_user_ledgers(db: Session, user_id: int) -> List[Tuple[Ledger, MemberRole, int]]:
    results = (
        db.query(Ledger, LedgerMember.role, func.count(LedgerMember.id).label("member_count"))
        .join(LedgerMember, Ledger.id == LedgerMember.ledger_id)
        .filter(LedgerMember.user_id == user_id)
        .filter(Ledger.is_active == True)
        .group_by(Ledger.id, LedgerMember.role)
        .order_by(Ledger.created_at.desc())
        .all()
    )
    return results


def get_ledger_by_id(db: Session, ledger_id: int) -> Optional[Ledger]:
    return db.query(Ledger).filter(Ledger.id == ledger_id).first()


def get_member(db: Session, ledger_id: int, user_id: int) -> Optional[LedgerMember]:
    return (
        db.query(LedgerMember)
        .filter(LedgerMember.ledger_id == ledger_id)
        .filter(LedgerMember.user_id == user_id)
        .first()
    )


def get_member_role(db: Session, ledger_id: int, user_id: int) -> Optional[MemberRole]:
    member = get_member(db, ledger_id, user_id)
    return member.role if member else None


def is_owner(db: Session, ledger_id: int, user_id: int) -> bool:
    role = get_member_role(db, ledger_id, user_id)
    return role == MemberRole.OWNER


def is_admin_or_higher(db: Session, ledger_id: int, user_id: int) -> bool:
    role = get_member_role(db, ledger_id, user_id)
    return role in (MemberRole.OWNER, MemberRole.ADMIN)


def is_member(db: Session, ledger_id: int, user_id: int) -> bool:
    return get_member(db, ledger_id, user_id) is not None


def check_member_access(db: Session, ledger_id: int, user_id: int) -> None:
    if not is_member(db, ledger_id, user_id):
        raise NotMemberError()


def check_admin_access(db: Session, ledger_id: int, user_id: int) -> None:
    if not is_admin_or_higher(db, ledger_id, user_id):
        raise InsufficientPermissionsError()


def check_owner_access(db: Session, ledger_id: int, user_id: int) -> None:
    if not is_owner(db, ledger_id, user_id):
        raise InsufficientPermissionsError()


def get_ledger_details(
    db: Session,
    ledger_id: int,
    user_id: int
) -> Tuple[Ledger, MemberRole, int]:
    ledger = get_ledger_by_id(db, ledger_id)
    if not ledger or not ledger.is_active:
        raise LedgerNotFoundError()

    member = get_member(db, ledger_id, user_id)
    if not member:
        raise NotMemberError()

    member_count = (
        db.query(func.count(LedgerMember.id))
        .filter(LedgerMember.ledger_id == ledger_id)
        .scalar()
    )

    return ledger, member.role, member_count


def update_ledger(
    db: Session,
    ledger_id: int,
    user_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Ledger:
    ledger = get_ledger_by_id(db, ledger_id)
    if not ledger or not ledger.is_active:
        raise LedgerNotFoundError()

    check_admin_access(db, ledger_id, user_id)

    if name is not None:
        ledger.name = name
    if description is not None:
        ledger.description = description

    db.commit()
    db.refresh(ledger)

    return ledger


def deactivate_ledger(db: Session, ledger_id: int, user_id: int) -> None:
    ledger = get_ledger_by_id(db, ledger_id)
    if not ledger or not ledger.is_active:
        raise LedgerNotFoundError()

    check_owner_access(db, ledger_id, user_id)

    ledger.is_active = False
    db.commit()


def get_ledger_members(db: Session, ledger_id: int) -> List[Tuple[LedgerMember, str]]:
    results = (
        db.query(LedgerMember, User.email)
        .join(User, LedgerMember.user_id == User.id)
        .filter(LedgerMember.ledger_id == ledger_id)
        .order_by(LedgerMember.joined_at)
        .all()
    )
    return results


def update_member_role(
    db: Session,
    ledger_id: int,
    target_user_id: int,
    new_role: MemberRole,
    actor_user_id: int
) -> LedgerMember:
    ledger = get_ledger_by_id(db, ledger_id)
    if not ledger or not ledger.is_active:
        raise LedgerNotFoundError()

    check_owner_access(db, ledger_id, actor_user_id)

    target_member = get_member(db, ledger_id, target_user_id)
    if not target_member:
        raise NotMemberError()

    if target_member.role == MemberRole.OWNER and new_role != MemberRole.OWNER:
        raise CannotRemoveOwnerError()

    target_member.role = new_role
    db.commit()
    db.refresh(target_member)

    return target_member


def remove_member(
    db: Session,
    ledger_id: int,
    target_user_id: int,
    actor_user_id: int
) -> None:
    ledger = get_ledger_by_id(db, ledger_id)
    if not ledger or not ledger.is_active:
        raise LedgerNotFoundError()

    if target_user_id == actor_user_id:
        pass
    else:
        check_admin_access(db, ledger_id, actor_user_id)

    target_member = get_member(db, ledger_id, target_user_id)
    if not target_member:
        raise NotMemberError()

    if target_member.role == MemberRole.OWNER:
        owner_count = (
            db.query(func.count(LedgerMember.id))
            .filter(LedgerMember.ledger_id == ledger_id)
            .filter(LedgerMember.role == MemberRole.OWNER)
            .scalar()
        )
        if owner_count <= 1:
            raise CannotRemoveOwnerError()

    db.delete(target_member)
    db.commit()


def create_invitation(
    db: Session,
    ledger_id: int,
    user_id: int,
    max_uses: Optional[int] = None,
    expires_in_hours: Optional[int] = None
) -> Invitation:
    ledger = get_ledger_by_id(db, ledger_id)
    if not ledger or not ledger.is_active:
        raise LedgerNotFoundError()

    check_admin_access(db, ledger_id, user_id)

    code = generate_invitation_code()
    while db.query(Invitation).filter(Invitation.code == code).first():
        code = generate_invitation_code()

    expires_at = None
    if expires_in_hours:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)

    invitation = Invitation(
        ledger_id=ledger_id,
        code=code,
        created_by=user_id,
        expires_at=expires_at,
        max_uses=max_uses,
        used_count=0,
        is_active=True
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    return invitation


def get_ledger_invitations(db: Session, ledger_id: int, user_id: int) -> List[Invitation]:
    ledger = get_ledger_by_id(db, ledger_id)
    if not ledger or not ledger.is_active:
        raise LedgerNotFoundError()

    check_admin_access(db, ledger_id, user_id)

    return (
        db.query(Invitation)
        .filter(Invitation.ledger_id == ledger_id)
        .order_by(Invitation.created_at.desc())
        .all()
    )


def deactivate_invitation(
    db: Session,
    ledger_id: int,
    invitation_id: int,
    user_id: int
) -> None:
    ledger = get_ledger_by_id(db, ledger_id)
    if not ledger or not ledger.is_active:
        raise LedgerNotFoundError()

    check_admin_access(db, ledger_id, user_id)

    invitation = (
        db.query(Invitation)
        .filter(Invitation.id == invitation_id)
        .filter(Invitation.ledger_id == ledger_id)
        .first()
    )

    if not invitation:
        raise InvitationNotFoundError()

    invitation.is_active = False
    db.commit()


def join_ledger_by_code(db: Session, code: str, user_id: int) -> Ledger:
    invitation = (
        db.query(Invitation)
        .filter(Invitation.code == code.upper())
        .filter(Invitation.is_active == True)
        .first()
    )

    if not invitation:
        raise InvitationNotFoundError()

    if invitation.expires_at and datetime.now(timezone.utc) > invitation.expires_at:
        raise InvitationExpiredError()

    if invitation.max_uses and invitation.used_count >= invitation.max_uses:
        raise InvitationUsedUpError()

    ledger = get_ledger_by_id(db, invitation.ledger_id)
    if not ledger or not ledger.is_active:
        raise LedgerNotFoundError()

    if is_member(db, ledger.id, user_id):
        raise AlreadyMemberError()

    member = LedgerMember(
        ledger_id=ledger.id,
        user_id=user_id,
        role=MemberRole.MEMBER,
        invited_by=invitation.created_by
    )
    db.add(member)

    invitation.used_count += 1
    if invitation.max_uses and invitation.used_count >= invitation.max_uses:
        invitation.is_active = False

    db.commit()
    db.refresh(ledger)

    return ledger


def get_or_create_personal_ledger(db: Session, user_id: int) -> Ledger:
    personal_membership = (
        db.query(LedgerMember)
        .join(Ledger, LedgerMember.ledger_id == Ledger.id)
        .filter(LedgerMember.user_id == user_id)
        .filter(Ledger.type == LedgerType.PERSONAL)
        .filter(Ledger.is_active == True)
        .first()
    )

    if personal_membership:
        return personal_membership.ledger

    return create_personal_ledger(db, user_id)
