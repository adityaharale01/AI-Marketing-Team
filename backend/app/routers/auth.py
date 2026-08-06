from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.user import UserCreate, UserResponse

from app.crud.user import create_user, get_user_by_email
from app.auth.oauth2 import create_access_token
from app.crud.user import authenticate_user
from app.schemas.user import UserLogin, Token
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)



@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):

    existing = get_user_by_email(db, user.email)

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    return create_user(db, user)

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):

    db_user = authenticate_user(
        db,
        user.email,
        user.password
    )

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        {
            "user_id": db_user.id,
            "email": db_user.email,
            "role": db_user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }