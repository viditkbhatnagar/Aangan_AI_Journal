"""Action lifecycle. The approval gate lives HERE: nothing completes unless
the creating human explicitly approves it first."""
from datetime import datetime

from sqlalchemy.orm import Session

from agents import doer
from models import Action, Alert, User


class NotYourAction(PermissionError):
    pass


class WrongState(ValueError):
    pass


def create_action(
    db: Session,
    user: User,
    intent: str,
    related_alert_id: int | None = None,
    plan_hint: dict | None = None,
) -> Action:
    if related_alert_id is not None:
        alert = db.get(Alert, related_alert_id)
        if alert is None or alert.recipient_id != user.id:
            raise LookupError("No such alert.")
    action = Action(created_by=user.id, intent=intent.strip(), related_alert_id=related_alert_id)
    db.add(action)
    db.flush()
    plan = doer.prepare(db, action, plan_hint)  # -> awaiting_approval
    from services import activity

    activity.emit(
        user.id, "Doer",
        f"Drafted a {plan.get('type', 'plan')} — nothing happens until you approve.",
    )
    return action


def approve_and_complete(db: Session, user: User, action_id: int) -> Action:
    action = db.get(Action, action_id)
    if action is None or action.created_by != user.id:
        raise NotYourAction("Only the person who created an action can approve it.")
    if action.status != "awaiting_approval":
        raise WrongState(f"This action is {action.status}, not awaiting approval.")
    action.status = "approved"
    db.commit()
    from services import activity

    activity.emit(user.id, "Doer", "Approved — working up to the safe handoff (never paying, never sending)…")
    result = doer.complete_action(db, action, user)  # -> completed, stops at safe handoff
    note = result.get("note", "")
    activity.emit(user.id, "Doer", f"Done: {note[:110]}" if note else "Done — over to you.")
    from services.events import record_event

    record_event(user.id, "action_approved", {
        "action_id": action.id,
        "kind": (action.plan or {}).get("type"),
        "result": result.get("status"),
    })
    from services import audit

    audit.record(user.id, "action_approved", "action", action.id, {
        "kind": (action.plan or {}).get("type"), "result": result.get("status"),
    })
    return action


def cancel(db: Session, user: User, action_id: int) -> Action:
    action = db.get(Action, action_id)
    if action is None or action.created_by != user.id:
        raise NotYourAction("Only the person who created an action can cancel it.")
    if action.status in {"completed", "cancelled"}:
        raise WrongState(f"This action is already {action.status}.")
    action.status = "cancelled"
    action.completed_at = datetime.utcnow()
    db.commit()
    return action
