"""Membership lifecycle: leaving or being removed from a circle must also purge
every grant that pointed at the departing member — share targets, rule and
trigger audiences — and re-index affected entries so the vector store's
custom-viewer metadata converges. Otherwise a member who later rejoins could
inherit stale grants."""
from sqlalchemy.orm import Session

from agents import librarian
from models import (
    AlertTrigger,
    FamilyCircle,
    JournalEntry,
    Membership,
    Relationship,
    ShareRule,
    ShareTarget,
    User,
)


def detach_user_from_circle(db: Session, user_id: int, circle_id: int) -> None:
    # 1) share targets naming the departing user -> collect affected entries
    targets = (
        db.query(ShareTarget)
        .filter(ShareTarget.user_id == user_id)
        .all()
    )
    affected_entry_ids: set[int] = set()
    for target in targets:
        if target.entry_id:
            affected_entry_ids.add(target.entry_id)
        elif target.fact_id:
            from models import Fact

            fact = db.get(Fact, target.fact_id)
            if fact:
                affected_entry_ids.add(fact.entry_id)
        db.delete(target)

    # 2) remove from rule/trigger audiences in this circle
    for rule in db.query(ShareRule).filter(ShareRule.circle_id == circle_id).all():
        if isinstance(rule.audience, list) and user_id in rule.audience:
            rule.audience = [u for u in rule.audience if u != user_id]
    for trigger in db.query(AlertTrigger).filter(AlertTrigger.circle_id == circle_id).all():
        if isinstance(trigger.audience, list) and user_id in trigger.audience:
            trigger.audience = [u for u in trigger.audience if u != user_id]

    # 3) relationship labels involving the user in this circle
    db.query(Relationship).filter(
        Relationship.circle_id == circle_id,
        (Relationship.from_user_id == user_id) | (Relationship.to_user_id == user_id),
    ).delete(synchronize_session=False)

    # 4) the membership itself
    db.query(Membership).filter(
        Membership.circle_id == circle_id, Membership.user_id == user_id
    ).delete(synchronize_session=False)
    db.commit()

    # 5) converge vector metadata for entries whose viewer set changed
    for entry_id in affected_entry_ids:
        entry = db.get(JournalEntry, entry_id)
        if entry is not None:
            librarian.upsert_entry(db, entry)

    from services import audit

    audit.record(user_id, "left_or_removed_from_circle", "circle", circle_id)

    # 6) circle housekeeping: promote an admin, or delete an empty circle
    remaining = (
        db.query(Membership).filter(Membership.circle_id == circle_id).all()
    )
    if not remaining:
        circle = db.get(FamilyCircle, circle_id)
        if circle:
            db.delete(circle)
        db.commit()
        return
    if not any(m.role == "admin" for m in remaining):
        remaining[0].role = "admin"
        db.commit()
