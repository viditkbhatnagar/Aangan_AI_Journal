from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import entitlements
from auth import get_current_user, get_user_circle_id
from db import get_db
from models import FamilyCircle, User
from services.events import record_event

router = APIRouter(tags=["plus"])


@router.get("/plus")
def plan_info(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    circle_id = get_user_circle_id(db, user)
    circle = db.get(FamilyCircle, circle_id) if circle_id else None
    plan = circle.plan if circle else "free"
    return {"plan": plan, "caps": entitlements.caps_for(plan)}


@router.post("/plus/interest")
def plus_interest(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fake-door willingness-to-pay signal — the pilot's conversion evidence."""
    record_event(user.id, "plus_interest", {})
    return {"ok": True, "message": "You're on the list — we'll tell you the moment Plus opens. ✨"}
