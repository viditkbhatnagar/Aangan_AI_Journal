import json as jsonlib
import os
import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from agents import conductor, transcriber
from agents.transcriber import TranscriptionUnavailable
from auth import get_current_user
from config import settings
from db import get_db
from models import User
from schemas import AskOut, SnippetOut

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskOut)
async def ask(
    request: Request,
    audio: UploadFile | None = File(default=None),
    question: str | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ask the Companion. Accepts JSON {"question": ...} or multipart with a
    recorded question (transcribed first)."""
    if audio is None and question is None and "application/json" in (
        request.headers.get("content-type") or ""
    ):
        try:
            body = jsonlib.loads(await request.body())
            question = body.get("question")
        except (ValueError, AttributeError):
            question = None

    audio_seconds = 0
    if audio is not None:
        os.makedirs(settings.audio_dir, exist_ok=True)
        path = os.path.join(settings.audio_dir, f"ask-{user.id}-{int(time.time() * 1000)}.webm")
        with open(path, "wb") as f:
            f.write(await audio.read())
        try:
            transcription = transcriber.transcribe(path)
            question = transcription.text
            audio_seconds = transcription.duration_sec
        except TranscriptionUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        finally:
            if os.path.exists(path):
                os.remove(path)  # questions are not journal entries; keep nothing

    if not question or not question.strip():
        raise HTTPException(status_code=422, detail="Ask me something first. 🙂")

    result = conductor.handle_ask(db, user, question.strip())

    # metering: the countable freemium unit + funnel event
    from auth import get_user_circle_id
    from models import AskRecord
    from services import metering
    from services.events import record_event

    circle_id = get_user_circle_id(db, user)
    if circle_id is not None:
        db.add(AskRecord(
            user_id=user.id,
            circle_id=circle_id,
            answered_by="llm" if metering.last_provenance.get("provider") != "fallback" else "fallback",
            snippet_count=len(result.snippets),
            audio_seconds=audio_seconds,
        ))
        db.commit()
    record_event(user.id, "ask", {"snippets": len(result.snippets)})

    return AskOut(
        answer=result.answer,
        language=result.language,
        snippets=[
            SnippetOut(
                text=s.text,
                author_id=s.author_id,
                author_name=s.author_name,
                created_at=s.created_at,
                source=s.source,
            )
            for s in result.snippets
        ],
    )
