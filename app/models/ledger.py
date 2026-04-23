import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    Enum as SQLEnum, Boolean, func
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class LedgerType(str, enum.Enum):
    PERSONAL = "personal"
    SHARED = "shared"


class MemberRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Ledger(Base):
    __tablename__ = "ledgers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(SQLEnum(LedgerType), nullable=False, default=LedgerType.PERSONAL)
    description = Column(String(255), nullable=True)
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)

    members = relationship("LedgerMember", back_populates="ledger", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="ledger")
    invitations = relationship("Invitation", back_populates="ledger", cascade="all, delete-orphan")


class LedgerMember(Base):
    __tablename__ = "ledger_members"

    id = Column(Integer, primary_key=True)
    ledger_id = Column(
        Integer,
        ForeignKey("ledgers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(SQLEnum(MemberRole), nullable=False, default=MemberRole.MEMBER)
    joined_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    invited_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    ledger = relationship("Ledger", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True)
    ledger_id = Column(
        Integer,
        ForeignKey("ledgers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    code = Column(String(20), unique=True, nullable=False, index=True)
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True
    )
    max_uses = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    ledger = relationship("Ledger", back_populates="invitations")
    creator = relationship("User")
