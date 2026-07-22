from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import create_token, get_current_user, hash_password, verify_password
from db import get_db
from models import User
from schemas import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="That email is already registered.")
    user = User(
        name=body.name.strip(),
        email=email,
        password_hash=hash_password(body.password),
        language=body.language,
    )
    db.add(user)
    db.commit()
    return TokenOut(access_token=create_token(user))


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.strip().lower()).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="That email or password didn't match.")
    return TokenOut(access_token=create_token(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/me/settings", response_model=UserOut)
def update_settings(
    body: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    language = body.get("language")
    if language in {"en", "hi"}:
        user.language = language
    name = (body.get("name") or "").strip()
    if name:
        user.name = name
    db.add(user)
    db.commit()
    return user
