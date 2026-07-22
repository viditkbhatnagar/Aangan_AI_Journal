from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents import keepsake, mirror
from auth import get_current_user
from db import get_db
from models import User

router = APIRouter(tags=["keepsake", "mirror"])


class MomentOut(BaseModel):
    entry_id: int
    author_id: int
    author_name: str
    text: str
    created_at: datetime


class KeepsakeOut(BaseModel):
    moments: list[MomentOut]
    on_this_day: list[MomentOut]


class MoodPointOut(BaseModel):
    date: str
    score: float
    summary: str


class MirrorOut(BaseModel):
    mood_series: list[MoodPointOut]
    themes: list[dict]
    streak_days: int
    total_entries: int


@router.get("/keepsake", response_model=KeepsakeOut)
def get_keepsake(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    view = keepsake.memory_book(db, user)
    return KeepsakeOut(
        moments=[MomentOut(**m.__dict__) for m in view.moments],
        on_this_day=[MomentOut(**m.__dict__) for m in view.on_this_day],
    )


@router.get("/mirror", response_model=MirrorOut)
def get_mirror(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The Mirror is private: it reflects only the current user's own journal,
    and there is no way to ask for anyone else's."""
    view = mirror.reflect(db, user)
    return MirrorOut(
        mood_series=[MoodPointOut(**p.__dict__) for p in view.mood_series],
        themes=view.themes,
        streak_days=view.streak_days,
        total_entries=view.total_entries,
    )
