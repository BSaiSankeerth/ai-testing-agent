from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
#
from app.api.deps import get_current_user
from app.core.security import (
    DUMMY_HASH,
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    # Always verify against some hash so timing doesn't reveal which emails exist.
    ok = verify_password(password, user.hashed_password if user else DUMMY_HASH)
    if not user or not ok or not user.is_active:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return user


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email is already registered")
    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = _authenticate(db, payload.email, payload.password)
    return TokenOut(access_token=create_access_token(user.id))


@router.post("/token", response_model=TokenOut, include_in_schema=True)
def token_for_docs(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Form-based login used by the Authorize button on /docs."""
    user = _authenticate(db, form.username, form.password)
    return TokenOut(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user