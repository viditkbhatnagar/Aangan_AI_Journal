"""Conductor: routes a request to the right agents so it all feels like one
helper. For an ask: Librarian (visibility-scoped retrieval) → Companion
(grounded, warm answer) — the Interpreter sits inside both via language hints."""
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from agents import companion, librarian
from auth import get_user_circle_id
from models import Relationship, User


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
