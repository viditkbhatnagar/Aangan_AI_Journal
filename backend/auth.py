"""Login, JWT, current-user dependency. Every data route resolves the current
user from the token and enforces visibility with that identity."""
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import settings
from db import get_db
from models import Membership, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except Exception:  # corrupt/unknown hash must never 500 a login
        return False


def create_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expiry_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


MFA_CHALLENGE_MINUTES = 5


def create_mfa_challenge_token(user: User) -> str:
    """Short-lived token proving password success only. get_current_user
    rejects it — it can never act as a session."""
    payload = {
        "sub": str(user.id),
        "scope": "mfa",
        "exp": datetime.utcnow() + timedelta(minutes=MFA_CHALLENGE_MINUTES),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_mfa_challenge_token(token: str) -> int | None:
    """Return the user id if this is a valid, unexpired challenge token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("scope") != "mfa":
            return None
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in again."
    )
    if credentials is None:
        raise unauthorized
    try:
        payload = jwt.decode(
            credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        if payload.get("scope") == "mfa":  # challenge tokens are not sessions
            raise unauthorized
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise unauthorized
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    # retention ground truth: throttled last-seen update (max once per 5 min)
    now = datetime.utcnow()
    if user.last_seen_at is None or (now - user.last_seen_at) > timedelta(minutes=5):
        user.last_seen_at = now
        db.commit()
    return user


def get_user_circle_id(db: Session, user: User) -> int | None:
    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    return membership.circle_id if membership else None


def require_circle_id(db: Session, user: User) -> int:
    circle_id = get_user_circle_id(db, user)
    if circle_id is None:
        raise HTTPException(status_code=400, detail="Join or create a family circle first.")
    return circle_id
