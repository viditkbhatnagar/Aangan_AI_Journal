"""Keepsake: curates SHARED moments into a memory book, with 'on this day'
resurfacing. Never private content — visibility-checked row by row."""
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from agents import librarian
from auth import get_user_circle_id
from models import JournalEntry, User, Visibility


@dataclass
class Moment:
    entry_id: int
    author_id: int
    author_name: str
    text: str
    created_at: datetime


@dataclass
class KeepsakeView:
    moments: list[Moment] = field(default_factory=list)
    on_this_day: list[Moment] = field(default_factory=list)


def _visible_shared_entries(db: Session, user: User, circle_id: int) -> list[JournalEntry]:
    candidates = (
        db.query(JournalEntry)
        .filter(
            JournalEntry.circle_id == circle_id,
            JournalEntry.visibility != Visibility.private,  # shared only, ever
        )
        .order_by(JournalEntry.created_at.desc())
        .limit(200)
        .all()
    )
    return [e for e in candidates if librarian.is_visible(db, user, entry_id=e.id)]


def _to_moment(db: Session, entry: JournalEntry) -> Moment:
    author = db.get(User, entry.author_id)
    return Moment(
        entry_id=entry.id,
        author_id=entry.author_id,
        author_name=author.name if author else "someone",
        text=entry.summary or entry.transcript or "",
        created_at=entry.created_at,
    )


def memory_book(db: Session, user: User, today: datetime | None = None) -> KeepsakeView:
    today = today or datetime.utcnow()
    circle_id = get_user_circle_id(db, user)
    if circle_id is None:
        return KeepsakeView()

    entries = _visible_shared_entries(db, user, circle_id)
    moments = [_to_moment(db, e) for e in entries[:40]]
    on_this_day = [
        _to_moment(db, e)
        for e in entries
        if e.created_at.month == today.month
        and e.created_at.day == today.day
        and e.created_at.year < today.year
    ]
    return KeepsakeView(moments=moments, on_this_day=on_this_day)
