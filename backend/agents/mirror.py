"""Mirror: a member's own private reflection — mood and themes over time.
Reads ONLY the owner's rows; the route guarantees the owner is the asker."""
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models import Fact, JournalEntry, User

POSITIVE = {
    "happy", "love", "loved", "beautiful", "excited", "wonderful", "proud",
    "great", "enjoyed", "smile", "laughed", "peaceful", "grateful",
    "खुश", "अच्छा", "सुंदर", "मज़ा", "शुक्र",
}
NEGATIVE = {
    "sad", "tired", "pain", "paining", "hurts", "worried", "anxious", "angry",
    "lonely", "sick", "unwell", "rough", "stressed",
    "दर्द", "थकान", "उदास", "चिंता", "बीमार",
}


@dataclass
class MoodPoint:
    date: str
    score: float  # -1 .. 1
    summary: str


@dataclass
class MirrorView:
    mood_series: list[MoodPoint] = field(default_factory=list)
    themes: list[dict] = field(default_factory=list)
    streak_days: int = 0
    total_entries: int = 0


def _mood_score(text: str) -> float:
    words = text.lower()
    pos = sum(words.count(w) for w in POSITIVE)
    neg = sum(words.count(w) for w in NEGATIVE)
    if pos == neg == 0:
        return 0.0
    return round((pos - neg) / (pos + neg), 2)


def reflect(db: Session, user: User, now: datetime | None = None) -> MirrorView:
    now = now or datetime.utcnow()
    entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.author_id == user.id)
        .order_by(JournalEntry.created_at.asc())
        .all()
    )
    mood_series = [
        MoodPoint(
            date=e.created_at.strftime("%Y-%m-%d"),
            score=_mood_score(e.transcript or e.summary or ""),
            summary=(e.summary or e.transcript or "")[:120],
        )
        for e in entries
    ]

    facts = db.query(Fact).filter(Fact.author_id == user.id).all()
    theme_counts = Counter(f.type for f in facts)
    topic_counts = Counter(
        (f.structured or {}).get("topic")
        for f in facts
        if (f.structured or {}).get("topic")
    )
    themes = [{"name": k, "count": v} for k, v in theme_counts.most_common(6)]
    themes += [{"name": f"topic: {k}", "count": v} for k, v in topic_counts.most_common(4)]

    # streak: consecutive days with an entry, counting back from today
    days_with_entries = {e.created_at.date() for e in entries}
    streak = 0
    cursor = now.date()
    while cursor in days_with_entries:
        streak += 1
        cursor -= timedelta(days=1)

    return MirrorView(
        mood_series=mood_series,
        themes=themes,
        streak_days=streak,
        total_entries=len(entries),
    )
