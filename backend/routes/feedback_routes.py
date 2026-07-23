from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import get_current_user
from db import get_db
from models import Feedback, User
from services.events import record_event

router = APIRouter(tags=["feedback"])


class FeedbackIn(BaseModel):
    kind: str = "feedback"  # feedback | report
    subject_kind: str | None = None  # answer | alert | fact | other
    subject_id: int | None = None
    message: str = Field(min_length=1, max_length=4000)


@router.post("/feedback")
def create_feedback(
    body: FeedbackIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.kind not in {"feedback", "report"}:
        raise HTTPException(status_code=422, detail="kind must be feedback or report")
    db.add(Feedback(
        user_id=user.id,
        kind=body.kind,
        subject_kind=body.subject_kind,
        subject_id=body.subject_id,
        message=body.message.strip(),
    ))
    db.commit()
    record_event(user.id, body.kind, {"subject": body.subject_kind})
    return {"ok": True, "message": "Thank you — a human will read this. 🙏"}
