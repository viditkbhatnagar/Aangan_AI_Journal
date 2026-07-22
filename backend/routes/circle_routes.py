import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user, get_user_circle_id, require_circle_id
from db import get_db
from models import FamilyCircle, Membership, Relationship, User
from schemas import CircleCreateIn, CircleJoinIn, CircleOut, MemberOut

router = APIRouter(tags=["circles"])


@router.post("/circles", response_model=CircleOut)
def create_circle(
    body: CircleCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if get_user_circle_id(db, user) is not None:
        raise HTTPException(status_code=409, detail="You are already in a family circle.")
    circle = FamilyCircle(
        name=body.name.strip(),
        invite_code=secrets.token_urlsafe(6),
        created_by=user.id,
    )
    db.add(circle)
    db.flush()
    db.add(Membership(circle_id=circle.id, user_id=user.id, role="admin"))
    db.commit()
    return circle


@router.post("/circles/join", response_model=CircleOut)
def join_circle(
    body: CircleJoinIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    circle = (
        db.query(FamilyCircle)
        .filter(FamilyCircle.invite_code == body.invite_code.strip())
        .first()
    )
    if circle is None:
        raise HTTPException(status_code=404, detail="No circle found for that invite code.")
    if get_user_circle_id(db, user) is not None:
        raise HTTPException(status_code=409, detail="You are already in a family circle.")
    db.add(Membership(circle_id=circle.id, user_id=user.id, role="member"))
    db.commit()
    return circle


@router.get("/circles/members", response_model=list[MemberOut])
def members(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    circle_id = require_circle_id(db, user)
    rows = (
        db.query(User, Relationship.label)
        .join(Membership, Membership.user_id == User.id)
        .outerjoin(
            Relationship,
            (Relationship.circle_id == circle_id)
            & (Relationship.from_user_id == user.id)
            & (Relationship.to_user_id == User.id),
        )
        .filter(Membership.circle_id == circle_id)
        .all()
    )
    return [
        MemberOut(id=member.id, name=member.name, language=member.language, relationship_label=label)
        for member, label in rows
    ]
