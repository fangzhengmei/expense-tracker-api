from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.user_schema import UserCreate, UserLogin
from app.db.database import get_db
from app.services.user_service import create_user, get_user_by_email
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token
from app.api.deps import get_current_user


router = APIRouter()


@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    password_hash = hash_password(user.password)

    new_user = create_user(
        db,
        email=user.email,
        password_hash=password_hash
    )

    if not new_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    return {"email": new_user.email}


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)

    if not db_user:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token = create_access_token(db_user.id)

    return {"access_token": token}


@router.get("/me")
def get_me(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email}
