from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import create_token, get_current_user, hash_password, verify_password
from db import get_db
from models import User
from schemas import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=TokenOut)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    from datetime import datetime

    from routes.legal_routes import POLICY_VERSION

    if not body.accept_terms:
        raise HTTPException(
            status_code=422,
            detail="Please read and accept the privacy policy and terms first.",
        )
    email = body.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="That email is already registered.")
    user = User(
        name=body.name.strip(),
        email=email,
        password_hash=hash_password(body.password),
        language=body.language,
        accepted_policy_version=POLICY_VERSION,
        accepted_at=datetime.utcnow(),
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


@router.post("/auth/reset", response_model=TokenOut)
def reset_password(body: dict, db: Session = Depends(get_db)):
    """Consume a one-time reset token (minted via backend/scripts/reset_link.py)."""
    from datetime import datetime

    from models import PasswordReset

    token = (body.get("token") or "").strip()
    new_password = body.get("new_password") or ""
    if len(new_password) < 8:
        raise HTTPException(status_code=422, detail="Pick a password of at least 8 characters.")
    reset = db.query(PasswordReset).filter(PasswordReset.token == token).first()
    if reset is None or reset.used or reset.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="That reset link isn't valid any more.")
    user = db.get(User, reset.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="That reset link isn't valid any more.")
    user.password_hash = hash_password(new_password)
    reset.used = True
    db.commit()
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
