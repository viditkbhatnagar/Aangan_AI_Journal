from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth import get_current_user, require_circle_id
from db import get_db
from models import ShareRule, User
from schemas import ShareRuleIn, ShareRuleOut

router = APIRouter(tags=["share-rules"])


@router.post("/share-rules", response_model=ShareRuleOut)
def create_share_rule(
    body: ShareRuleIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    circle_id = require_circle_id(db, user)
    rule = ShareRule(
        user_id=user.id,
        circle_id=circle_id,
        description=body.description.strip(),
        match=body.match,
        audience=body.audience,
    )
    db.add(rule)
    db.commit()
    return rule


@router.get("/share-rules", response_model=list[ShareRuleOut])
def list_share_rules(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(ShareRule)
        .filter(ShareRule.user_id == user.id)
        .order_by(ShareRule.created_at.desc())
        .all()
    )
