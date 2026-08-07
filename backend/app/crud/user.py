from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.auth.hashing import hash_password


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate):

    hashed_password = hash_password(user.password)

    db_user = User(
        full_name=user.full_name,
        email=user.email,
        password=hashed_password,
        role="owner"
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

from app.auth.hashing import verify_password

def authenticate_user(db: Session, email: str, password: str):

    user = get_user_by_email(db, email)

    if not user:
        return None

    if not verify_password(password, user.password):
        return None

    return user