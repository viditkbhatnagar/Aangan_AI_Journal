import os
import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from agents import consent_guardian, librarian
from agents.transcriber import TranscriptionUnavailable
from auth import get_current_user, require_circle_id
from config import settings
from db import get_db
from models import Alert, Fact, JournalEntry, ShareTarget, User, Visibility
from services import activity
from schemas import ActionOut, CaptureOut, EntryOut, ShareIn, ShareSuggestionOut
from services import capture

router = APIRouter(tags=["entries"])

AUDIO_EXTENSIONS = {"audio/webm": "webm", "audio/mp4": "m4a", "audio/mpeg": "mp3", "audio/wav": "wav", "audio/ogg": "ogg"}


@router.post("/entries", response_model=CaptureOut)
async def create_entry(
    audio: UploadFile | None = File(default=None),
    transcript: str | None = Form(default=None),
    language: str | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    circle_id = require_circle_id(db, user)
    if audio is None and not (transcript and transcript.strip()):
        raise HTTPException(status_code=422, detail="Record something or type your entry.")

    audio_path = None
    if audio is not None:
        # freemium cap on costly voice minutes (typed entries are always free)
        import entitlements
        from models import FamilyCircle

        try:
            entitlements.check_voice_allowed(db, db.get(FamilyCircle, circle_id))
        except entitlements.CapExceeded as exc:
            raise HTTPException(status_code=402, detail=str(exc))
        ext = AUDIO_EXTENSIONS.get((audio.content_type or "").split(";")[0], "webm")
        os.makedirs(settings.audio_dir, exist_ok=True)
        audio_path = os.path.join(settings.audio_dir, f"{user.id}-{int(time.time() * 1000)}.{ext}")
        with open(audio_path, "wb") as f:
            f.write(await audio.read())

    try:
        result = capture.run_capture(
            db, user, circle_id,
            audio_path=audio_path,
            transcript=transcript.strip() if transcript else None,
            language=language,
        )
    except TranscriptionUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    db.refresh(result.entry)
    return CaptureOut(
        entry=EntryOut.model_validate(result.entry),
        share_suggestions=[
            ShareSuggestionOut(kind=s.kind, fact_id=s.fact_id, text=s.text, reason=s.reason)
            for s in result.share_suggestions
        ],
        applied_rules=result.applied_rules,
        suggested_action=(
            ActionOut.model_validate(result.suggested_action)
            if result.suggested_action
            else None
        ),
    )


@router.get("/entries", response_model=list[EntryOut])
def list_entries(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The current user's OWN entries only — never anyone else's."""
    rows = (
        db.query(JournalEntry)
        .filter(JournalEntry.author_id == user.id)
        .order_by(JournalEntry.created_at.desc())
        .limit(100)
        .all()
    )
    return rows


@router.get("/entries/{entry_id}", response_model=EntryOut)
def get_entry(entry_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    entry = db.get(JournalEntry, entry_id)
    # 404 (not 403) so we don't leak that another member's entry exists
    if entry is None or entry.author_id != user.id:
        raise HTTPException(status_code=404, detail="No such entry.")
    return entry


@router.delete("/entries/{entry_id}")
def delete_entry(entry_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The author (and only the author) can un-record a moment entirely:
    entry, facts, share grants, alerts it caused, vectors, and the audio."""
    entry = db.get(JournalEntry, entry_id)
    if entry is None or entry.author_id != user.id:
        raise HTTPException(status_code=404, detail="No such entry.")

    fact_ids = [fact.id for fact in entry.facts]
    librarian.remove_entry(db, entry)  # vector store first, while ids are known

    db.query(Alert).filter(Alert.source_entry_id == entry_id).delete()
    share_filter = ShareTarget.entry_id == entry_id
    if fact_ids:
        share_filter = share_filter | ShareTarget.fact_id.in_(fact_ids)
    db.query(ShareTarget).filter(share_filter).delete(synchronize_session=False)
    db.query(Fact).filter(Fact.entry_id == entry_id).delete()

    audio_path = entry.audio_path
    db.delete(entry)
    db.commit()
    if audio_path and os.path.exists(audio_path):
        os.remove(audio_path)

    activity.emit(user.id, "Librarian", "Erased that moment everywhere — as if it was never said.")
    return {"ok": True}


@router.post("/entries/{entry_id}/share", response_model=EntryOut)
def share_entry(
    entry_id: int,
    body: ShareIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        visibility = Visibility(body.visibility)
    except ValueError:
        raise HTTPException(status_code=422, detail="visibility must be private, circle, or custom")
    try:
        consent_guardian.set_visibility(
            db,
            user,
            entry_id=None if body.fact_id else entry_id,
            fact_id=body.fact_id,
            visibility=visibility,
            viewer_ids=body.viewer_ids,
        )
    except consent_guardian.NotYourContent:
        raise HTTPException(status_code=403, detail="Only the author can change what is shared.")
    except LookupError:
        raise HTTPException(status_code=404, detail="No such entry or fact.")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    entry = db.get(JournalEntry, entry_id)
    if entry is None or entry.author_id != user.id:
        raise HTTPException(status_code=404, detail="No such entry.")
    db.refresh(entry)
    from services.events import record_event

    record_event(user.id, "share", {
        "entry_id": entry_id,
        "fact_id": body.fact_id,
        "visibility": body.visibility,
    })
    return entry
