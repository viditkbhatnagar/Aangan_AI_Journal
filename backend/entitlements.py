"""Central plan entitlements. Costly AI usage on the free tier is capped —
the caps are the single source of truth for both enforcement and the
business plan's freemium table. Payments plug in later; the plan column and
these checks make the tiering real today."""
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import AskRecord, FamilyCircle, JournalEntry

CAPS: dict[str, dict] = {
    # None = unlimited
    "free": {
        "asks_per_month": 100,
        "voice_minutes_per_month": 60,
        "memory_days": 90,
    },
    "plus": {
        "asks_per_month": None,
        "voice_minutes_per_month": None,
        "memory_days": None,
    },
}

UPGRADE_MESSAGES = {
    "asks": (
        "You've reached this month's Companion questions on the free plan. "
        "Aangan Plus lifts the limit — or the counter resets next month. 🪔"
    ),
    "voice": (
        "You've used this month's voice minutes on the free plan — typed entries "
        "are always unlimited. Aangan Plus lifts the limit. 🪔"
    ),
}


class CapExceeded(Exception):
    def __init__(self, kind: str):
        self.kind = kind
        super().__init__(UPGRADE_MESSAGES[kind])


def caps_for(plan: str) -> dict:
    return CAPS.get(plan, CAPS["free"])


def _month_start(now: datetime) -> datetime:
    return datetime(now.year, now.month, 1)


def check_ask_allowed(db: Session, circle: FamilyCircle, now: datetime | None = None) -> None:
    cap = caps_for(circle.plan)["asks_per_month"]
    if cap is None:
        return
    now = now or datetime.utcnow()
    used = (
        db.query(AskRecord)
        .filter(AskRecord.circle_id == circle.id, AskRecord.created_at >= _month_start(now))
        .count()
    )
    if used >= cap:
        raise CapExceeded("asks")


def check_voice_allowed(db: Session, circle: FamilyCircle, now: datetime | None = None) -> None:
    """Checked before transcribing a new recording. The current entry may
    overshoot slightly; the next one is blocked — good enough for cost control."""
    cap_minutes = caps_for(circle.plan)["voice_minutes_per_month"]
    if cap_minutes is None:
        return
    now = now or datetime.utcnow()
    used_seconds = (
        db.query(func.coalesce(func.sum(JournalEntry.duration_sec), 0))
        .filter(
            JournalEntry.circle_id == circle.id,
            JournalEntry.created_at >= _month_start(now),
        )
        .scalar()
    )
    if (used_seconds or 0) >= cap_minutes * 60:
        raise CapExceeded("voice")
