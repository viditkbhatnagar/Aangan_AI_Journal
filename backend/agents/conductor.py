"""Conductor: routes a request to the right agents so it all feels like one
helper. For an ask: Librarian (visibility-scoped retrieval) → Companion
(grounded, warm answer) — the Interpreter sits inside both via language hints.
For a baithak turn: the SAME spine, re-run fresh on every single turn."""
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from agents import companion, librarian
from auth import get_user_circle_id
from models import Conversation, ConversationTurn, Relationship, User


@dataclass
class AskResult:
    answer: str
    language: str
    snippets: list[librarian.Snippet] = field(default_factory=list)


def relationship_labels(db: Session, user: User) -> dict[int, str]:
    """How this user refers to each member ('spouse', 'mother', ...)."""
    circle_id = get_user_circle_id(db, user)
    if circle_id is None:
        return {}
    rows = (
        db.query(Relationship)
        .filter(Relationship.circle_id == circle_id, Relationship.from_user_id == user.id)
        .all()
    )
    return {r.to_user_id: r.label for r in rows}

def handle_ask(db: Session, user: User, question: str) -> AskResult:
    from services import activity, metering

    with metering.context(user_id=user.id, db=db):
        return _handle_ask_metered(db, user, question, activity)


def _handle_ask_metered(db: Session, user: User, question: str, activity) -> AskResult:
    activity.emit(user.id, "Conductor", "Routing your question through the agents…")
    snippets = librarian.search(db, user, question)
    activity.emit(
        user.id, "Librarian",
        f"Found {len(snippets)} snippet(s) you're allowed to see — private ones stayed sealed.",
    )
    relationships = relationship_labels(db, user)
    answer = companion.compose_answer(user, question, snippets, relationships)
    from agents import llm

    voice = llm._openai_model or ("claude" if llm.llm_available() else "local warmth")
    activity.emit(user.id, "Companion", f"Answered with love (voice: {voice}).")
    return AskResult(answer=answer, language=user.language or "en", snippets=snippets)


@dataclass
class ConverseResult:
    conversation_id: int
    reply: str
    language: str
    snippets: list[librarian.Snippet] = field(default_factory=list)


HISTORY_TURNS = 8
# a very short message ("what else?", "और?") has no topic of its own — give
# retrieval the previous user turn as context
_FOLLOWUP_MAX_WORDS = 4


def handle_converse(
    db: Session, user: User, conversation_id: int | None, message: str
) -> ConverseResult:
    from services import activity, metering

    with metering.context(user_id=user.id, db=db):
        return _handle_converse_metered(db, user, conversation_id, message, activity)


def _handle_converse_metered(
    db: Session, user: User, conversation_id: int | None, message: str, activity
) -> ConverseResult:
    """One baithak turn. The privacy spine runs FRESH here every time:
    librarian.search on this turn's query, snippets never cached across turns,
    so a re-share or un-share takes effect on the very next turn."""
    now = datetime.utcnow()
    if conversation_id is None:
        circle_id = get_user_circle_id(db, user)
        conversation = Conversation(user_id=user.id, circle_id=circle_id, started_at=now, last_at=now)
        db.add(conversation)
        db.flush()
    else:
        # ownership was verified by the route (owner-only, 404 otherwise)
        conversation = db.get(Conversation, conversation_id)

    history_rows = (
        db.query(ConversationTurn)
        .filter(ConversationTurn.conversation_id == conversation.id)
        .order_by(ConversationTurn.id.desc())
        .limit(HISTORY_TURNS)
        .all()
    )
    history = [(t.role, t.text) for t in reversed(history_rows)]

    search_query = message
    if len(message.split()) <= _FOLLOWUP_MAX_WORDS:
        last_user_text = next((t for r, t in reversed(history) if r == "user"), None)
        if last_user_text:
            search_query = f"{last_user_text} {message}"

    activity.emit(user.id, "Conductor", "A baithak turn — running the full privacy check again…")
    snippets = librarian.search(db, user, search_query)
    activity.emit(
        user.id, "Librarian",
        f"Found {len(snippets)} snippet(s) you're allowed to see right now — checked fresh this turn.",
    )
    relationships = relationship_labels(db, user)
    reply = companion.compose_reply(user, message, history, snippets, relationships)

    db.add(ConversationTurn(
        conversation_id=conversation.id, role="user", text=message,
        snippet_count=0, created_at=now,
    ))
    db.add(ConversationTurn(
        conversation_id=conversation.id, role="companion", text=reply,
        snippet_count=len(snippets), created_at=now,
    ))
    conversation.last_at = now
    db.commit()

    activity.emit(user.id, "Companion", "Replied in the baithak — talk answered with talk.")
    return ConverseResult(
        conversation_id=conversation.id,
        reply=reply,
        language=user.language or "en",
        snippets=snippets,
    )
