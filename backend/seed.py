"""Seed the sample family (spec Section 20). Run from backend/:

    python seed.py

Wipes aangan.db and the vector store for a deterministic demo, then creates
the circle "Ghar" with four members, relationships, Deepa's gift-ideas rule,
Mumma's knee trigger, and entries that make the app demo on first login —
all without needing any API keys.
"""
from datetime import datetime, timedelta

from auth import hash_password
from config import settings
from db import Base, SessionLocal, engine
from memory import store
from models import (
    FamilyCircle,
    Membership,
    Relationship,
    ShareRule,
    User,
    Visibility,
)
from services.capture import run_capture

PASSWORD = "aangan123"

MEMBERS = [
    # name, email, language
    ("Aditya", "aditya@ghar.family", "en"),
    ("Deepa", "deepa@ghar.family", "en"),
    ("Mumma", "mumma@ghar.family", "hi"),
    ("Abhishek", "abhishek@ghar.family", "en"),
]

# how FROM refers to TO
RELATIONSHIPS = [
    ("Aditya", "Deepa", "wife"),
    ("Aditya", "Mumma", "mother"),
    ("Aditya", "Abhishek", "brother"),
    ("Deepa", "Aditya", "husband"),
    ("Deepa", "Mumma", "mother-in-law"),
    ("Deepa", "Abhishek", "brother-in-law"),
    ("Mumma", "Aditya", "son"),
    ("Mumma", "Deepa", "daughter-in-law"),
    ("Mumma", "Abhishek", "son"),
    ("Abhishek", "Aditya", "brother"),
    ("Abhishek", "Deepa", "sister-in-law"),
    ("Abhishek", "Mumma", "mother"),
]


def reset_stores():
    print("Resetting aangan.db and the vector store for a clean demo…")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    try:
        collection = store.get_collection()
        existing = collection.get()
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass


def backdate(db, entry, facts, when: datetime):
    from agents import librarian

    entry.created_at = when
    for fact in facts:
        fact.created_at = when
    db.commit()
    librarian.upsert_entry(db, entry, facts)  # refresh vector metadata dates


def main():
    reset_stores()
    db = SessionLocal()
    now = datetime.utcnow()

    users = {}
    for name, email, lang in MEMBERS:
        user = User(
            name=name, email=email,
            password_hash=hash_password(PASSWORD), language=lang,
        )
        db.add(user)
        users[name] = user
    db.flush()

    circle = FamilyCircle(name="Ghar", invite_code="GHAR-2026", created_by=users["Aditya"].id)
    db.add(circle)
    db.flush()
    for user in users.values():
        role = "admin" if user.name == "Aditya" else "member"
        db.add(Membership(circle_id=circle.id, user_id=user.id, role=role))
    for frm, to, label in RELATIONSHIPS:
        db.add(Relationship(
            circle_id=circle.id,
            from_user_id=users[frm].id,
            to_user_id=users[to].id,
            label=label,
        ))
    db.commit()
    print(f"Circle '{circle.name}' created (invite code {circle.invite_code}).")

    # Deepa's standing rule — her own choice, applied automatically on capture
    db.add(ShareRule(
        user_id=users["Deepa"].id,
        circle_id=circle.id,
        description="share my gift ideas with the family",
        match={"type": "preference", "tag": "gift"},
        audience="all",
    ))
    db.commit()

    # Mumma's trigger about herself: knee pain -> tell the sons
    from models import AlertTrigger
    db.add(AlertTrigger(
        author_id=users["Mumma"].id,
        circle_id=circle.id,
        description="अगर मैं कहूँ कि घुटने में दर्द है, तो मेरे बेटों को बता देना",
        match={"type": "state", "topic": "health"},
        audience=[users["Aditya"].id, users["Abhishek"].id],
        severity_hint="notable",
    ))
    db.commit()
    print("Deepa's gift rule and Mumma's knee trigger are in place.")

    print("Indexing entries (first run downloads the local embedding model)…")

    # 1) Deepa, a few months ago, shared: the black dress moment
    result = run_capture(
        db, users["Deepa"], circle.id,
        transcript="Saw a beautiful black dress at H&M today, I could not stop thinking about it.",
        language="en",
    )
    from agents import consent_guardian
    consent_guardian.set_visibility(
        db, users["Deepa"], entry_id=result.entry.id, visibility=Visibility.circle,
    )
    backdate(db, result.entry, result.facts, now - timedelta(days=96))
    print("  • Deepa's black-dress moment (shared with the circle, ~3 months ago)")

    # 2) Deepa, recent, private — proves the ask layer excludes it
    result = run_capture(
        db, users["Deepa"], circle.id,
        transcript=(
            "A normal day really. Work was long, I made poha for breakfast and "
            "read a few pages before sleeping. Keeping this one just for me."
        ),
        language="en",
    )
    backdate(db, result.entry, result.facts, now - timedelta(days=1, hours=3))
    print("  • Deepa's private everyday entry (stays private)")

    # 3) Mumma, recent, in Hindi — fires the knee trigger for her sons
    result = run_capture(
        db, users["Mumma"], circle.id,
        transcript="आज मेरे घुटने में थोड़ा दर्द है। बाकी सब ठीक है, सुबह पूजा की और आँगन में धूप सेकी।",
        language="hi",
    )
    backdate(db, result.entry, result.facts, now - timedelta(hours=6))
    print("  • Mumma's knee entry (Hindi) — alert created for Aditya and Abhishek")

    # 4) Aditya, private reflection — feeds his Mirror, invisible to others
    result = run_capture(
        db, users["Aditya"], circle.id,
        transcript=(
            "Feeling a bit stretched between work and home lately, but tonight's "
            "dinner together made me really happy and grateful. I want to plan "
            "something special for Deepa's birthday next month."
        ),
        language="en",
    )
    backdate(db, result.entry, result.facts, now - timedelta(hours=20))
    print("  • Aditya's private reflection (Mirror only)")

    from models import Alert
    alert_count = db.query(Alert).count()
    db.close()

    print(
        f"""
Done. {len(MEMBERS)} members, {alert_count} alert(s) waiting.

Log in at the Vite URL with any of:
  aditya@ghar.family    / {PASSWORD}
  deepa@ghar.family     / {PASSWORD}
  mumma@ghar.family     / {PASSWORD}   (हिन्दी)
  abhishek@ghar.family  / {PASSWORD}

Try asking as Aditya: “What would Deepa want for her birthday?”
"""
    )


if __name__ == "__main__":
    main()
