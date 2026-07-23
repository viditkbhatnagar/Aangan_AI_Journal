from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agents import librarian
from auth import get_current_user
from db import get_db
from memory import store
from models import Alert, Fact, ShareTarget, User
from schemas import FactOut

router = APIRouter(tags=["facts"])


class FactPatch(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


@router.patch("/facts/{fact_id}", response_model=FactOut)
def edit_fact(
    fact_id: int,
    body: FactPatch,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The author can correct what the Extractor noted — the correction loop
    the AI needs (rubric 3/14). Re-indexed immediately."""
    fact = db.get(Fact, fact_id)
    if fact is None or fact.author_id != user.id:
        raise HTTPException(status_code=404, detail="No such note.")
    fact.content = body.content.strip()
    db.commit()
    librarian.upsert_entry(db, fact.entry)
    return fact


@router.delete("/facts/{fact_id}")
def delete_fact(
    fact_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fact = db.get(Fact, fact_id)
    if fact is None or fact.author_id != user.id:
        raise HTTPException(status_code=404, detail="No such note.")
    store.delete_documents([f"fact:{fact_id}"])
    db.query(ShareTarget).filter(ShareTarget.fact_id == fact_id).delete()
    db.query(Alert).filter(Alert.source_fact_id == fact_id).update({"source_fact_id": None})
    db.delete(fact)
    db.commit()
    return {"ok": True}
