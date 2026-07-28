"""My Thoughts: the personal dashboard. Everything here is the CURRENT USER'S
OWN writing — mirror, weekly reflection, open loops, upcoming dates. There is
no way to ask for anyone else's; every query filters on the author's id."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents import mirror, reflector
from auth import get_current_user
from db import get_db
from models import Fact, User
from routes.keepsake_routes import MirrorOut, MoodPointOut
from services import activity, metering

router = APIRouter(tags=["thoughts"])

OPEN_LOOP_WINDOW = timedelta(days=14)
UPCOMING_HORIZON = timedelta(days=14)


class OpenLoopOut(BaseModel):
    fact_id: int
    content: str
    source_quote: str | None
    age_days: int


class UpcomingOut(BaseModel):
    fact_id: int
    content: str
    date: str  # ISO date of the next occurrence
    days_away: int


class ThoughtsOut(BaseModel):
    mirror: MirrorOut
    reflection: str
    open_loops: list[OpenLoopOut]
    upcoming: list[UpcomingOut]


def _next_occurrence(raw: str, now: datetime) -> datetime | None:
    """Month/day recurrence, same style as relationship_radar: a yearly date
    (birthday) rolls forward to its next occurrence."""
    try:
        when = datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return None
    this_year = when.replace(year=now.year)
    if this_year < now - timedelta(days=1):
        this_year = this_year.replace(year=now.year + 1)
    return this_year


def open_loops(db: Session, user: User, now: datetime | None = None) -> list[OpenLoopOut]:
    """The author's recent plans that never got a date — 'plans you voiced'."""
    now = now or datetime.utcnow()
    plans = (
        db.query(Fact)
        .filter(
            Fact.author_id == user.id,
            Fact.type == "plan",
            Fact.created_at >= now - OPEN_LOOP_WINDOW,
        )
        .order_by(Fact.created_at.desc())
        .all()
    )
    return [
        OpenLoopOut(
            fact_id=f.id,
            content=f.content,
            source_quote=f.source_quote,
            age_days=max(0, (now - f.created_at).days),
        )
        for f in plans
        if not (f.structured or {}).get("date")
    ][:6]


def upcoming(db: Session, user: User, now: datetime | None = None) -> list[UpcomingOut]:
    """The author's own dated facts in the next 14 days. Includes plan facts
    that carry a structured.date so a dated plan shows as a 'coming up' chip."""
    now = now or datetime.utcnow()
    dated = (
        db.query(Fact)
        .filter(Fact.author_id == user.id, Fact.type.in_(["date", "plan"]))
        .order_by(Fact.created_at.desc())
        .limit(50)
        .all()
    )
    items: list[UpcomingOut] = []
    for fact in dated:
        raw = (fact.structured or {}).get("date")
        if not raw:
            continue
        occurrence = _next_occurrence(raw, now)
        if occurrence is None:
            continue
        days_away = (occurrence.date() - now.date()).days
        if 0 <= days_away <= UPCOMING_HORIZON.days:
            items.append(
                UpcomingOut(
                    fact_id=fact.id,
                    content=fact.content,
                    date=occurrence.strftime("%Y-%m-%d"),
                    days_away=days_away,
                )
            )
    items.sort(key=lambda i: i.days_away)
    return items[:6]


@router.get("/thoughts", response_model=ThoughtsOut)
def get_thoughts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    activity.emit(user.id, "Reflector", "Reading your week back to you…")
    view = mirror.reflect(db, user)
    with metering.context(user_id=user.id):  # Reflector LLM calls land in llm_calls
        reflection = reflector.weekly_reflection(db, user)
    return ThoughtsOut(
        mirror=MirrorOut(
            mood_series=[MoodPointOut(**p.__dict__) for p in view.mood_series],
            themes=view.themes,
            streak_days=view.streak_days,
            total_entries=view.total_entries,
        ),
        reflection=reflection,
        open_loops=open_loops(db, user),
        upcoming=upcoming(db, user),
    )
