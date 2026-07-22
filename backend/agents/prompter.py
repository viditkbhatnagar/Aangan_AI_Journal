"""Prompter: gently nudges a member to journal when it's been a while, with a
starter question. Tuned for elders — soft, never pushy, in their language."""
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models import JournalEntry, User

QUIET_AFTER = timedelta(days=2)

STARTERS = {
    "en": [
        "What made you smile today?",
        "What did you eat today — anything special?",
        "Who did you talk to today?",
        "Anything on your mind lately?",
    ],
    "hi": [
        "आज किस बात पर मुस्कान आई?",
        "आज खाने में क्या बना — कुछ खास?",
        "आज किससे बात हुई?",
        "इन दिनों मन में क्या चल रहा है?",
    ],
}


@dataclass
class Nudge:
    kind: str  # "journal" | "reach_out" | "upcoming_date"
    text: str


def nudges(db: Session, user: User, now: datetime | None = None) -> list[Nudge]:
    now = now or datetime.utcnow()
    last = (
        db.query(JournalEntry)
        .filter(JournalEntry.author_id == user.id)
        .order_by(JournalEntry.created_at.desc())
        .first()
    )
    if last is not None and now - last.created_at < QUIET_AFTER:
        return []

    starters = STARTERS.get((user.language or "en")[:2], STARTERS["en"])
    starter = starters[now.toordinal() % len(starters)]
    if last is None:
        text = f"Your courtyard is ready whenever you are. {starter}"
    else:
        text = f"It's been a little while — no rush at all. {starter}"
    return [Nudge(kind="journal", text=text)]
