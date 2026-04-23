from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.core.constants import DEFAULT_CURRENCY


def create_user(db, email: str, password_hash: str, default_currency: str = DEFAULT_CURRENCY):
    user = User(
        email=email,
        password_hash=password_hash,
        default_currency=default_currency
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


def update_user_default_currency(db, user_id: int, default_currency: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    user.default_currency = default_currency
    db.commit()
    db.refresh(user)
    return user