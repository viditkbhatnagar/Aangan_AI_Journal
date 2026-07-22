from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents import prompter, relationship_radar
from auth import get_current_user
from db import get_db
from models import User

router = APIRouter(tags=["nudges"])


class NudgeOut(BaseModel):
    kind: str
    text: str


@router.get("/nudges", response_model=list[NudgeOut])
def get_nudges(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = prompter.nudges(db, user) + relationship_radar.radar(db, user)
    return [NudgeOut(kind=n.kind, text=n.text) for n in items]
