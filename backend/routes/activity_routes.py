from fastapi import APIRouter, Depends

from auth import get_current_user
from db import get_db
from models import User
from services import activity

router = APIRouter(tags=["activity"])


@router.get("/activity")
def get_activity(after: int = 0, user: User = Depends(get_current_user), db=Depends(get_db)):
    """The current user's own agent-activity timeline (what the agents did
    while handling THEIR requests)."""
    return {"events": activity.feed(user.id, after_id=after)}
