from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user, require_circle_id
from db import get_db
from models import Alert, AlertTrigger, User
from schemas import AlertOut, AlertStatusIn, AlertTriggerIn, AlertTriggerOut

router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Alert)
        .filter(Alert.recipient_id == user.id)
        .order_by(Alert.created_at.desc())
        .limit(100)
        .all()
    )


@router.post("/alerts/{alert_id}/status", response_model=AlertOut)
def set_alert_status(
    alert_id: int,
    body: AlertStatusIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.status not in {"seen", "acted", "dismissed"}:
        raise HTTPException(status_code=422, detail="status must be seen, acted, or dismissed")
    alert = db.get(Alert, alert_id)
    if alert is None or alert.recipient_id != user.id:
        raise HTTPException(status_code=404, detail="No such alert.")
    alert.status = body.status
    db.commit()
    return alert


@router.post("/alert-triggers", response_model=AlertTriggerOut)
def create_trigger(
    body: AlertTriggerIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """A trigger is always about ME — I choose who gets told, and how loudly."""
    circle_id = require_circle_id(db, user)
    if body.severity_hint not in {"gentle", "notable", "urgent"}:
        raise HTTPException(status_code=422, detail="severity_hint must be gentle, notable, or urgent")
    trigger = AlertTrigger(
        author_id=user.id,
        circle_id=circle_id,
        description=body.description.strip(),
        match=body.match,
        audience=body.audience,
        severity_hint=body.severity_hint,
    )
    db.add(trigger)
    db.commit()
    return trigger


@router.get("/alert-triggers", response_model=list[AlertTriggerOut])
def list_triggers(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(AlertTrigger)
        .filter(AlertTrigger.author_id == user.id)
        .order_by(AlertTrigger.created_at.desc())
        .all()
    )
