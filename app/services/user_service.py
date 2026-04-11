from sqlalchemy.exc import IntegrityError

from app.models.user import User


def create_user(db, email: str, password_hash: str):
    user = User(
        email=email,
        password_hash=password_hash
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