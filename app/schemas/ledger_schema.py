from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime
from typing import Optional
from app.models.ledger import LedgerType, MemberRole


class LedgerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: LedgerType = Field(default=LedgerType.PERSONAL)
    description: Optional[str] = Field(None, max_length=255)


class LedgerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)


class LedgerMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    user_email: str
    role: MemberRole
    joined_at: datetime


class LedgerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: LedgerType
    description: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    member_count: Optional[int] = None
    my_role: Optional[MemberRole] = None


class MemberRoleUpdate(BaseModel):
    role: MemberRole


class InvitationCreate(BaseModel):
    max_uses: Optional[int] = Field(None, ge=1, description="最大使用次数，None 表示无限制")
    expires_in_hours: Optional[int] = Field(None, ge=1, description="过期时间（小时），None 表示永不过期")


class InvitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ledger_id: int
    code: str
    created_by: int
    created_at: datetime
    expires_at: Optional[datetime]
    max_uses: Optional[int]
    used_count: int
    is_active: bool


class JoinLedger(BaseModel):
    code: str = Field(..., min_length=1, max_length=20)
