from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import (
    create_mfa_challenge_token,
    create_token,
    decode_mfa_challenge_token,
    get_current_user,
    hash_password,
    verify_password,
)
from db import get_db
from models import User
from schemas import (
    LoginIn,
    LoginOut,
    MfaCodeIn,
    MfaSetupOut,
    MfaVerifyIn,
    RegisterIn,
    TokenOut,
    UserOut,
)

router = APIRouter(tags=["auth"])

# Two-factor code attempts allowed per ACCOUNT per window (see mfa_verify).
MFA_ATTEMPTS_PER_WINDOW = 5
MFA_ATTEMPT_WINDOW_SEC = 300


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


@router.post("/auth/login", response_model=LoginOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    from services import audit

    user = db.query(User).filter(User.email == body.email.strip().lower()).first()
    if user is None or not verify_password(body.password, user.password_hash):
        audit.record(None, "login_failed", "user", user.id if user else None)
        raise HTTPException(status_code=401, detail="That email or password didn't match.")
    if user.mfa_enabled and user.totp_secret:
        audit.record(user.id, "mfa_challenged", "user", user.id)
        return LoginOut(mfa_required=True, mfa_token=create_mfa_challenge_token(user))
    audit.record(user.id, "login_ok", "user", user.id)
    return LoginOut(access_token=create_token(user))


@router.post("/auth/mfa/verify", response_model=TokenOut)
def mfa_verify(body: MfaVerifyIn, db: Session = Depends(get_db)):
    """Trade a challenge token + authenticator code for a full session.
    Wrong code is 403 (not 401 — the frontend treats 401 as logout)."""
    import pyotp

    from services import audit

    from services import ratelimit

    user_id = decode_mfa_challenge_token(body.mfa_token)
    user = db.get(User, user_id) if user_id is not None else None
    if user is None or not user.mfa_enabled or not user.totp_secret:
        raise HTTPException(status_code=403, detail="Please log in again to get a fresh code prompt.")
    # PER-ACCOUNT throttle: the /auth/* middleware limit is per IP, so a
    # distributed attacker holding the password could otherwise brute-force
    # a 6-digit code. Keyed by user, so extra IPs buy nothing.
    if not ratelimit.allow(
        f"user:{user.id}", "mfa", MFA_ATTEMPTS_PER_WINDOW, MFA_ATTEMPT_WINDOW_SEC
    ):
        audit.record(user.id, "mfa_throttled", "user", user.id)
        raise HTTPException(
            status_code=429,
            detail="Too many code attempts. Wait a few minutes, then log in again. 🌿",
        )
    if not pyotp.TOTP(user.totp_secret).verify(body.code.strip(), valid_window=1):
        audit.record(user.id, "mfa_failed", "user", user.id)
        raise HTTPException(status_code=403, detail="That code didn't match — try the next one from your app.")
    audit.record(user.id, "login_ok", "user", user.id, {"mfa": True})
    return TokenOut(access_token=create_token(user))


@router.post("/auth/mfa/setup", response_model=MfaSetupOut)
def mfa_setup(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mint a fresh secret (MFA stays OFF until /auth/mfa/enable confirms a code)."""
    import pyotp
    import qrcode
    import qrcode.image.svg

    if user.mfa_enabled:
        raise HTTPException(status_code=409, detail="Two-factor is already on for this account.")
    secret = pyotp.random_base32()
    user.totp_secret = secret
    db.commit()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="Aangan")
    svg = qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage).to_string().decode()
    return MfaSetupOut(secret=secret, otpauth_uri=uri, qr_svg=svg)


@router.post("/auth/mfa/enable")
def mfa_enable(
    body: MfaCodeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    import pyotp

    from services import audit

    if not user.totp_secret:
        raise HTTPException(status_code=400, detail="Scan the setup code first.")
    if not pyotp.TOTP(user.totp_secret).verify(body.code.strip(), valid_window=1):
        raise HTTPException(status_code=403, detail="That code didn't match — try the next one from your app.")
    user.mfa_enabled = True
    db.commit()
    audit.record(user.id, "mfa_enabled", "user", user.id)
    return {"ok": True, "message": "Two-factor is on. Your courtyard gate has a second latch now. 🔐"}


@router.post("/auth/mfa/disable")
def mfa_disable(
    body: MfaCodeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    import pyotp

    from services import audit

    if not user.mfa_enabled or not user.totp_secret:
        raise HTTPException(status_code=400, detail="Two-factor isn't on for this account.")
    if not pyotp.TOTP(user.totp_secret).verify(body.code.strip(), valid_window=1):
        raise HTTPException(status_code=403, detail="That code didn't match — try the next one from your app.")
    user.mfa_enabled = False
    user.totp_secret = None
    db.commit()
    audit.record(user.id, "mfa_disabled", "user", user.id)
    return {"ok": True, "message": "Two-factor is off."}


@router.post("/auth/reset", response_model=LoginOut)
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
    # a reset must not be an MFA bypass: two-factor accounts still owe a code
    if user.mfa_enabled and user.totp_secret:
        return LoginOut(mfa_required=True, mfa_token=create_mfa_challenge_token(user))
    return LoginOut(access_token=create_token(user))


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
    from auth import get_user_circle_ids
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
    circle_ids = get_user_circle_ids(db, user)

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

    for circle_id in circle_ids:
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
