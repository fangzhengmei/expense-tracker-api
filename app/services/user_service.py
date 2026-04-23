from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.enums import UserRole


def create_user(db, email: str, password_hash: str, role: UserRole = UserRole.EMPLOYEE):
    user = User(
        email=email,
        password_hash=password_hash,
        role=role
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        return None


def get_user_by_email(db, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db, user_id: int):
    return db.query(User).filter(User.id == user_id).first()