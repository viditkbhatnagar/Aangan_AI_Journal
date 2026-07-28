"""Baithak: a multi-turn conversation with the Companion. Talk replied with
talk — while the privacy spine re-checks visibility on EVERY turn (the
conductor re-runs librarian.search fresh; snippets are never cached across
turns). Each user turn counts as one ask, so freemium caps stay truthful."""
import json as jsonlib
import os
import time
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents import conductor, transcriber
from agents.transcriber import TranscriptionUnavailable
from auth import get_current_user, require_circle_id
from config import settings
from db import get_db
from models import Conversation, ConversationTurn, User
from schemas import SnippetOut

router = APIRouter(tags=["converse"])


class ConverseOut(BaseModel):
    conversation_id: int
    reply: str
    language: str
    snippets: list[SnippetOut] = []


class TurnOut(BaseModel):
    role: str
    text: str
    snippet_count: int
    created_at: datetime


class ConversationOut(BaseModel):
    id: int
    started_at: datetime
    last_at: datetime
    turns: list[TurnOut]


def _own_conversation(db: Session, user: User, conversation_id: int) -> Conversation:
    """Owner-only: anyone else's conversation id is a plain 404 — the id's
    very existence is not disclosed."""
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=404, detail="No such conversation.")
    return conversation


@router.post("/converse", response_model=ConverseOut)
async def converse(
    request: Request,
    audio: UploadFile | None = File(default=None),
    message: str | None = Form(default=None),
    conversation_id: int | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """One baithak turn. JSON {conversation_id?, message} or multipart with a
    recorded question (transcribed first, exactly like /ask)."""
    if audio is None and message is None and "application/json" in (
        request.headers.get("content-type") or ""
    ):
        try:
            body = jsonlib.loads(await request.body())
            message = body.get("message")
            conversation_id = body.get("conversation_id", conversation_id)
        except (ValueError, AttributeError):
            message = None

    audio_seconds = 0
    if audio is not None:
        os.makedirs(settings.audio_dir, exist_ok=True)
        path = os.path.join(settings.audio_dir, f"converse-{user.id}-{int(time.time() * 1000)}.webm")
        with open(path, "wb") as f:
            f.write(await audio.read())
        try:
            transcription = transcriber.transcribe(path)
            message = transcription.text
            audio_seconds = transcription.duration_sec
        except TranscriptionUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        finally:
            if os.path.exists(path):
                os.remove(path)  # baithak questions are not journal entries; keep nothing

    if not message or not message.strip():
        raise HTTPException(status_code=422, detail="Say something first. 🙂")

    if conversation_id is not None:
        _own_conversation(db, user, conversation_id)

    # freemium: EVERY user turn is one ask — same cap, same record as /ask
    import entitlements
    from models import AskRecord, FamilyCircle
    from services import metering
    from services.events import record_event

    circle_id = require_circle_id(db, user)
    try:
        entitlements.check_ask_allowed(db, db.get(FamilyCircle, circle_id))
    except entitlements.CapExceeded as exc:
        raise HTTPException(status_code=402, detail=str(exc))

    result = conductor.handle_converse(db, user, conversation_id, message.strip())
    db.add(AskRecord(
        user_id=user.id,
        circle_id=circle_id,
        answered_by="llm" if metering.last_provenance.get("provider") != "fallback" else "fallback",
        snippet_count=len(result.snippets),
        audio_seconds=audio_seconds,
    ))
    db.commit()
    record_event(user.id, "converse", {
        "conversation_id": result.conversation_id, "snippets": len(result.snippets),
    })

    return ConverseOut(
        conversation_id=result.conversation_id,
        reply=result.reply,
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


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = _own_conversation(db, user, conversation_id)
    turns = (
        db.query(ConversationTurn)
        .filter(ConversationTurn.conversation_id == conversation.id)
        .order_by(ConversationTurn.id.asc())
        .all()
    )
    return ConversationOut(
        id=conversation.id,
        started_at=conversation.started_at,
        last_at=conversation.last_at,
        turns=[
            TurnOut(role=t.role, text=t.text, snippet_count=t.snippet_count, created_at=t.created_at)
            for t in turns
        ],
    )
