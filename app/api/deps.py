from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.jwt import decode_token
from app.db.database import get_db
from app.models.user import User
from app.models.enums import UserRole


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(User).filter(User.id == payload["user_id"]).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return user


def get_current_manager(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=403,
            detail="需要主管权限才能执行此操作"
        )
    return current_user
