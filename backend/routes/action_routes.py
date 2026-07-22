from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from auth import get_current_user
from db import get_db
from models import Action, User
from schemas import ActionIn, ActionOut
from services import actions as actions_service

router = APIRouter(tags=["actions"])


@router.post("/actions", response_model=ActionOut)
def create_action(
    body: ActionIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not body.intent.strip():
        raise HTTPException(status_code=422, detail="Tell me what you'd like to do.")
    try:
        return actions_service.create_action(
            db, user, body.intent, body.related_alert_id, body.plan_hint
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="No such alert.")


@router.get("/actions", response_model=list[ActionOut])
def list_actions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Action)
        .filter(Action.created_by == user.id)
        .order_by(Action.created_at.desc())
        .limit(100)
        .all()
    )


@router.post("/actions/{action_id}/approve", response_model=ActionOut)
async def approve_action(
    action_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # sync Playwright must not run on the event loop thread
        action = await run_in_threadpool(
            actions_service.approve_and_complete, db, user, action_id
        )
    except actions_service.NotYourAction:
        raise HTTPException(status_code=404, detail="No such action.")
    except actions_service.WrongState as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    db.refresh(action)
    return action


@router.post("/actions/{action_id}/cancel", response_model=ActionOut)
def cancel_action(
    action_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return actions_service.cancel(db, user, action_id)
    except actions_service.NotYourAction:
        raise HTTPException(status_code=404, detail="No such action.")
    except actions_service.WrongState as exc:
        raise HTTPException(status_code=409, detail=str(exc))
