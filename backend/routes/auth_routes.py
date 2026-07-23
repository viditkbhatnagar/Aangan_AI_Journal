from datetime import datetime

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
    from services.events import record_event

    record_event(user.id, "registered", {"language": user.language, "source": body.source})
    return TokenOut(access_token=create_token(user))


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    from services import audit

    user = db.query(User).filter(User.email == body.email.strip().lower()).first()
    if user is None or not verify_password(body.password, user.password_hash):
        audit.record(None, "login_failed", "user", user.id if user else None)
        raise HTTPException(status_code=401, detail="That email or password didn't match.")
    audit.record(user.id, "login_ok", "user", user.id)
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


@router.get("/me/export")
def export_my_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Data portability: everything the requesting member authored, as JSON."""
    from models import AlertTrigger, Fact, JournalEntry, ShareRule

    entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.author_id == user.id)
        .order_by(JournalEntry.created_at.asc())
        .all()
    )
    facts = db.query(Fact).filter(Fact.author_id == user.id).all()
    facts_by_entry: dict[int, list] = {}
    for fact in facts:
        facts_by_entry.setdefault(fact.entry_id, []).append(fact)
    return {
        "exported_at": datetime.utcnow().isoformat(),
        "profile": {
            "name": user.name, "email": user.email, "language": user.language,
            "joined": user.created_at.isoformat(),
        },
        "entries": [
            {
                "created_at": e.created_at.isoformat(),
                "language": e.language,
                "transcript": e.transcript,
                "summary": e.summary,
                "visibility": e.visibility.value,
                "audio_file": e.audio_path,
                "facts": [
                    {
                        "type": f.type, "content": f.content,
                        "structured": f.structured,
                        "visibility": f.visibility.value,
                    }
                    for f in facts_by_entry.get(e.id, [])
                ],
            }
            for e in entries
        ],
        "sharing_rules": [
            {"description": r.description, "match": r.match, "audience": r.audience, "active": r.active}
            for r in db.query(ShareRule).filter(ShareRule.user_id == user.id)
        ],
        "alert_triggers": [
            {"description": t.description, "match": t.match, "audience": t.audience, "active": t.active}
            for t in db.query(AlertTrigger).filter(AlertTrigger.author_id == user.id)
        ],
    }


@router.delete("/me")
def delete_my_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Full erasure: every entry, fact, vector, audio file, grant, and the
    account itself. The circle survives if others remain."""
    import os

    from agents import librarian
    from auth import get_user_circle_id
    from models import (
        Action,
        Alert,
        AlertTrigger,
        AskRecord,
        Fact,
        Feedback,
        JournalEntry,
        LlmCall,
        PasswordReset,
        ProductEvent,
        ShareRule,
        ShareTarget,
    )
    from services import audit
    from services.membership import detach_user_from_circle

    user_id = user.id
    circle_id = get_user_circle_id(db, user)

    entries = db.query(JournalEntry).filter(JournalEntry.author_id == user_id).all()
    for entry in entries:
        fact_ids = [f.id for f in entry.facts]
        librarian.remove_entry(db, entry)
        db.query(Alert).filter(Alert.source_entry_id == entry.id).delete()
        share_filter = ShareTarget.entry_id == entry.id
        if fact_ids:
            share_filter = share_filter | ShareTarget.fact_id.in_(fact_ids)
        db.query(ShareTarget).filter(share_filter).delete(synchronize_session=False)
        db.query(Fact).filter(Fact.entry_id == entry.id).delete()
        if entry.audio_path and os.path.exists(entry.audio_path):
            os.remove(entry.audio_path)
        db.delete(entry)
    db.commit()

    for model, column in (
        (Alert, Alert.recipient_id), (Alert, Alert.author_id),
        (ShareRule, ShareRule.user_id), (AlertTrigger, AlertTrigger.author_id),
        (Action, Action.created_by), (AskRecord, AskRecord.user_id),
        (LlmCall, LlmCall.user_id), (ProductEvent, ProductEvent.user_id),
        (Feedback, Feedback.user_id), (PasswordReset, PasswordReset.user_id),
    ):
        db.query(model).filter(column == user_id).delete(synchronize_session=False)
    db.commit()

    if circle_id is not None:
        detach_user_from_circle(db, user_id, circle_id)

    db.delete(db.get(User, user_id))
    db.commit()
    audit.record(user_id, "account_deleted", "user", user_id)
    return {"ok": True, "message": "Everything you recorded is gone. Take care. 🪔"}


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
