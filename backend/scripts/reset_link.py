"""Mint a one-time password-reset link for a member (pilot account recovery).

Usage, from backend/:
    .venv/bin/python scripts/reset_link.py mumma@ghar.family
"""
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import Base, SessionLocal, engine  # noqa: E402
from models import PasswordReset, User  # noqa: E402


def mint(email: str) -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if user is None:
        print(f"No member with email {email}")
        raise SystemExit(1)
    token = secrets.token_urlsafe(24)
    db.add(PasswordReset(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    ))
    db.commit()
    db.close()
    print(f"Reset link for {user.name} (valid 24h):")
    print(f"  http://localhost:5173/reset?token={token}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(1)
    mint(sys.argv[1])
