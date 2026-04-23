from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.user_schema import UserCreate, UserLogin, UserOut
from app.db.database import get_db
from app.services.user_service import create_user, get_user_by_email
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token
from app.api.deps import get_current_user
from app.models.user import User


router = APIRouter()


@router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    password_hash = hash_password(user.password)

    new_user = create_user(
        db,
        email=user.email,
        password_hash=password_hash,
        role=user.role
    )

    if not new_user:
        raise HTTPException(status_code=400, detail="用户已存在")

    return new_user


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)

    if not db_user:
        raise HTTPException(status_code=401, detail="凭证不正确")

    if not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="凭证不正确")

    token = create_access_token(db_user.id)

    return {
        "access_token": token,
        "user_id": db_user.id,
        "role": db_user.role
    }


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user
