"""Pilot metrics report — the honest numbers for business-plan Sections 11/15/20.

Usage, from backend/:
    .venv/bin/python scripts/metrics.py
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def compute(db) -> dict:
    from sqlalchemy import func

    from models import AskRecord, JournalEntry, LlmCall, ProductEvent, User

    now = datetime.utcnow()
    users = db.query(User).all()
    entries = db.query(JournalEntry).all()

    # activation: first journal entry within 7 days of signup
    first_entry_at: dict[int, datetime] = {}
    for entry in entries:
        prev = first_entry_at.get(entry.author_id)
        if prev is None or entry.created_at < prev:
            first_entry_at[entry.author_id] = entry.created_at
    activated = sum(
        1 for u in users
        if u.id in first_entry_at
        and first_entry_at[u.id] - u.created_at <= timedelta(days=7)
    )

    wau = sum(
        1 for u in users
        if u.last_seen_at and now - u.last_seen_at <= timedelta(days=7)
    )

    voice_seconds = db.query(func.coalesce(func.sum(JournalEntry.duration_sec), 0)).scalar()
    asks_total = db.query(AskRecord).count()
    asks_llm = db.query(AskRecord).filter(AskRecord.answered_by == "llm").count()

    llm_calls = db.query(LlmCall).count()
    llm_served = db.query(LlmCall).filter(LlmCall.provider != "fallback").count()
    tokens_in = db.query(func.coalesce(func.sum(LlmCall.prompt_tokens), 0)).scalar()
    tokens_out = db.query(func.coalesce(func.sum(LlmCall.completion_tokens), 0)).scalar()

    funnel = dict(
        db.query(ProductEvent.name, func.count(ProductEvent.id))
        .group_by(ProductEvent.name)
        .all()
    )

    return {
        "users": len(users),
        "activated_7d": activated,
        "activation_rate": round(activated / len(users), 2) if users else 0.0,
        "wau": wau,
        "entries": len(entries),
        "voice_minutes_total": round((voice_seconds or 0) / 60, 1),
        "asks_total": asks_total,
        "asks_llm_share": round(asks_llm / asks_total, 2) if asks_total else 0.0,
        "llm_calls": llm_calls,
        "llm_served_rate": round(llm_served / llm_calls, 2) if llm_calls else 0.0,
        "tokens_prompt": int(tokens_in or 0),
        "tokens_completion": int(tokens_out or 0),
        "funnel_events": funnel,
    }


def main() -> None:
    from db import SessionLocal

    db = SessionLocal()
    try:
        report = compute(db)
    finally:
        db.close()
    print("\n=== Aangan pilot metrics ===")
    for key, value in report.items():
        print(f"  {key:22} {value}")


if __name__ == "__main__":
    main()
