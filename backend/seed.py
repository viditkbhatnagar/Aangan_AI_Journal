"""Seed the sample family (spec Section 20). Run from backend/:

    python seed.py

Wipes aangan.db and the vector store for a deterministic demo, then creates
the circle "Ghar" with four members, relationships, Deepa's gift-ideas rule,
Mumma's knee trigger, and entries that make the app demo on first login —
all without needing any API keys.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Windows consoles default to cp1252, which can't print the Hindi in the
# closing summary — never let a print() undo a successful seed.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from auth import hash_password
from config import settings
from db import Base, SessionLocal, engine
from memory import store
from models import (
    FamilyCircle,
    JournalEntry,
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
    _stamp_current_revision()
    try:
        # full drop: a fresh collection gets the current model's stamp and
        # dimension (deleting ids alone would keep both from the old model)
        store.reset_collection()
    except Exception:
        pass


def _stamp_current_revision():
    """A freshly seeded DB is already at head — record that for Alembic."""
    from alembic import command
    from alembic.config import Config

    backend_dir = Path(__file__).resolve().parent
    cfg = Config(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    command.stamp(cfg, "head", purge=True)


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

    # 5) Aditya, yesterday, private — a dated plan so the Personal Radar has
    # something to remember on first login (the founder's "important meeting"
    # example). The plan fact is added deterministically so the demo works
    # with or without LLM keys.
    meeting_day = (now + timedelta(days=2)).strftime("%A")
    result = run_capture(
        db, users["Aditya"], circle.id,
        transcript=(
            f"Busy day. I have an important presentation to the client on "
            f"{meeting_day} — I really want it to go well."
        ),
        language="en",
    )
    # keyless extraction can't resolve "Thursday" to a date, so guarantee ONE
    # dated plan fact; with LLM keys the extractor usually already made it
    extra_facts = []
    if not any(
        f.type in ("plan", "date") and (f.structured or {}).get("date")
        for f in result.facts
    ):
        from models import Fact
        radar_fact = Fact(
            entry_id=result.entry.id,
            author_id=users["Aditya"].id,
            circle_id=circle.id,
            type="plan",
            content=f"Important client presentation on {meeting_day}",
            structured={"date": (now + timedelta(days=2)).strftime("%Y-%m-%d")},
            source_quote=f"I have an important presentation to the client on {meeting_day}",
        )
        db.add(radar_fact)
        db.commit()
        extra_facts = [radar_fact]
    backdate(db, result.entry, result.facts + extra_facts, now - timedelta(days=1))
    print("  • Aditya's dated plan (personal nudge will greet him on login)")

    # ------------------------------------------------------------------
    # Rich demo data — so every dashboard looks full during a live demo.
    # Entries span ~8 weeks (mood strip, streak, themes fill in), several
    # are shared (memory book + Ask + Baithak), and a few prepared/completed
    # actions fill the Actions screen. Privacy spine untouched: the gift
    # surprise stays private; shared moments are each author's own choice.
    # ------------------------------------------------------------------
    from agents import consent_guardian
    from models import Action, AlertTrigger

    def cap(member, days_ago, shared, lang, text):
        res = run_capture(db, users[member], circle.id, transcript=text, language=lang)
        if shared:
            consent_guardian.set_visibility(
                db, users[member], entry_id=res.entry.id, visibility=Visibility.circle,
            )
        backdate(db, res.entry, res.facts, now - timedelta(days=days_ago))
        return res

    # Aditya's own care trigger — his "overworked" note can gently reach Deepa,
    # and his Me page now shows a trigger of his own.
    db.add(AlertTrigger(
        author_id=users["Aditya"].id, circle_id=circle.id,
        description="If I mention I'm feeling overworked, gently let Deepa know.",
        match={"type": "state", "topic": "wellbeing"},
        audience=[users["Deepa"].id], severity_hint="gentle",
    ))
    db.commit()

    RICH_ENTRIES = [
        # member, days_ago, shared?, lang, text
        ("Aditya", 56, True, "en", "Took Mumma to the temple this morning — she kept pointing out the marigolds. A quiet, good start to the week."),
        ("Aditya", 40, False, "en", "Heavy week at work and I'm feeling overworked, honestly. Trying to keep Sundays for family and leave the laptop shut."),
        ("Aditya", 33, False, "en", "Booked our family trip to Nainital for next month. I keep picturing Mumma by the lake."),
        ("Aditya", 20, True, "en", "Abhishek got his offer letter today — the whole house was loud and happy. So proud of my little brother."),
        ("Aditya", 12, False, "en", "Small win: made dinner for everyone tonight. Deepa laughed at my rotis but ate three of them."),
        ("Aditya", 4, False, "en", "Picked up reading again before bed — finished a whole book this week. A small thing, but it feels like me again."),
        ("Deepa", 49, True, "en", "The garden roses finally bloomed — the first thing I saw this morning. Called Mumma just to tell her."),
        ("Deepa", 10, False, "en", "A tired but content kind of day. Early night, a few pages of my book, done."),
        ("Deepa", 3, True, "en", "I've been wanting a good pair of running shoes for my morning walks in the park."),
        ("Deepa", 2, True, "en", "My birthday is coming up next month. Honestly I keep thinking about that beautiful black dress I saw at H&M — or maybe finally some good running shoes for my walks."),
        ("Mumma", 35, True, "hi", "आज सारा परिवार रविवार के खाने पर आया — घर भरा-भरा और खुशियों से भरा लगा।"),
        ("Mumma", 14, False, "hi", "सुबह आँगन में तुलसी को पानी दिया और थोड़ी देर धूप में बैठी। मन शांत था।"),
        ("Mumma", 8, True, "hi", "अभिषेक की नौकरी की खबर सुनकर दिल खुश हो गया। भगवान उसे हमेशा खुश रखे।"),
        ("Abhishek", 42, False, "en", "The job hunt is exhausting. Trying to stay hopeful and keep applying."),
        ("Abhishek", 20, True, "en", "Got the offer! Calling everyone tonight. Couldn't have done it without the family's patience."),
        ("Abhishek", 7, False, "en", "First week at the new job — nervous but genuinely excited."),
        ("Abhishek", 3, True, "en", "Fixed the old cycle in the courtyard with Aditya bhai — Mumma couldn't stop laughing at the two of us."),
    ]
    for member, days_ago, shared, lang, text in RICH_ENTRIES:
        cap(member, days_ago, shared, lang, text)
    print(f"  • {len(RICH_ENTRIES)} more entries across the family (many shared → memory book)")

    # A few prepared/completed actions so the Actions screen is never empty.
    def steps(*items):
        return [{"icon": i, "label": lbl, "detail": d} for (i, lbl, d) in items]

    def make_action(member, intent, status, plan, result, days_ago):
        created = now - timedelta(days=days_ago)
        db.add(Action(
            created_by=users[member].id, intent=intent, plan=plan, status=status,
            result=result, created_at=created,
            completed_at=(created + timedelta(minutes=4)) if status == "completed" else None,
        ))

    make_action(
        "Aditya", "order chocolates for Deepa", "completed",
        {"type": "purchase", "item": "assorted chocolates", "site": "https://www.amazon.in",
         "candidate": {"title": "Cadbury Celebrations Assorted Chocolate Gift Pack, 172.4g",
                       "price_text": "₹145", "reason": "Fits your ₹800 budget",
                       "url": "https://www.amazon.in/s?k=cadbury+celebrations"},
         "trace": steps(("📝", "Received your request", "order chocolates for Deepa"),
                        ("🧭", "Understood this as a purchase", "the wording sounds like shopping"),
                        ("🔎", "Worked out the item", "assorted chocolates"),
                        ("⭐", "Picked the best match", "Cadbury Celebrations — ₹145"))},
        {"status": "ready_for_human",
         "item": "Cadbury Celebrations Assorted Chocolate Gift Pack, 172.4g",
         "checkout_url": "https://www.amazon.in/gp/cart/view.html",
         "note": "The cart is ready — review the item, price and address, then pay yourself. I stop before any payment.",
         "trace": steps(("✅", "You approved", "completing up to the safe handoff"),
                        ("🛒", "Added it to the cart", "Cadbury Celebrations Assorted, 172.4g"),
                        ("🛡️", "No payment or credential field was touched", "the guards stayed green"),
                        ("✋", "Stopped at the safe handoff", "over to you to pay"))},
        days_ago=15,
    )
    make_action(
        "Aditya", "send Mumma a good-morning message", "completed",
        {"type": "message", "channel": "whatsapp", "to": "",
         "body": "Good morning Mumma! Hope you slept well. I'll call at lunch. ❤️",
         "trace": steps(("📝", "Received your request", "message Mumma"),
                        ("💬", "Draft ready", "a warm good-morning note"))},
        {"status": "ready_for_human",
         "body": "Good morning Mumma! Hope you slept well. I'll call at lunch. ❤️",
         "note": "Your message is drafted — read it once and press send yourself.",
         "trace": steps(("✅", "You approved", ""),
                        ("🔗", "Built a ready-to-send link", "I will NOT press send — that's yours"),
                        ("✋", "Stopped at the safe handoff", ""))},
        days_ago=6,
    )
    make_action(
        "Aditya", "send Abhishek a congratulations message", "awaiting_approval",
        {"type": "message", "channel": "whatsapp", "to": "",
         "body": "Abhishek!! So proud of you for the new job. Dinner's on me this weekend. 🎉",
         "trace": steps(("📝", "Received your request", "congratulate Abhishek"),
                        ("💬", "Draft ready", "a celebratory note"),
                        ("⏸️", "Plan ready — waiting for your approval", "nothing runs until you approve"))},
        None, days_ago=1,
    )
    make_action(
        "Deepa", "order a book for Aditya", "completed",
        {"type": "purchase", "item": "the alchemist paulo coelho", "site": "https://www.amazon.in",
         "candidate": {"title": "The Alchemist by Paulo Coelho (Paperback)",
                       "price_text": "₹199", "reason": "His favourite — a nicer copy",
                       "url": "https://www.amazon.in/s?k=the+alchemist"},
         "trace": steps(("📝", "Received your request", "order a book for Aditya"),
                        ("🔎", "Worked out the item", "The Alchemist"),
                        ("⭐", "Picked the best match", "Paperback — ₹199"))},
        {"status": "ready_for_human",
         "item": "The Alchemist by Paulo Coelho (Paperback)",
         "checkout_url": "https://www.amazon.in/gp/cart/view.html",
         "note": "The cart is ready — review and pay yourself. I stop before any payment.",
         "trace": steps(("✅", "You approved", ""), ("🛒", "Added it to the cart", "The Alchemist"),
                        ("✋", "Stopped at the safe handoff", ""))},
        days_ago=9,
    )
    make_action(
        "Mumma", "order laddoos for the family", "completed",
        {"type": "purchase", "item": "besan laddoo box", "site": "https://www.amazon.in",
         "candidate": {"title": "Haldiram's Besan Laddoo, 400g", "price_text": "₹185",
                       "reason": "Everyone's festival favourite",
                       "url": "https://www.amazon.in/s?k=besan+laddoo"},
         "trace": steps(("📝", "Received your request", "order laddoos"),
                        ("⭐", "Picked the best match", "Haldiram's — ₹185"))},
        {"status": "ready_for_human", "item": "Haldiram's Besan Laddoo, 400g",
         "checkout_url": "https://www.amazon.in/gp/cart/view.html",
         "note": "The cart is ready — review and pay yourself. I stop before any payment.",
         "trace": steps(("✅", "You approved", ""), ("🛒", "Added it to the cart", "Besan Laddoo"),
                        ("✋", "Stopped at the safe handoff", ""))},
        days_ago=11,
    )
    make_action(
        "Abhishek", "send Mumma a thank-you message", "completed",
        {"type": "message", "channel": "whatsapp", "to": "",
         "body": "Mumma, I got the job! Thank you for every prayer and every cup of chai. ❤️",
         "trace": steps(("📝", "Received your request", "message Mumma"),
                        ("💬", "Draft ready", "a heartfelt thank-you"))},
        {"status": "ready_for_human",
         "body": "Mumma, I got the job! Thank you for every prayer and every cup of chai. ❤️",
         "note": "Your message is drafted — read it once and press send yourself.",
         "trace": steps(("✅", "You approved", ""), ("🔗", "Built a ready-to-send link", ""),
                        ("✋", "Stopped at the safe handoff", ""))},
        days_ago=19,
    )
    db.commit()
    print("  • Prepared & completed actions seeded (all four members)")

    # A couple of gentle care alerts so Deepa's and Mumma's Alerts aren't empty
    # either. Each references a real entry (Alert requires a source).
    from models import Alert

    def make_alert(about, to, source_text, severity, message, suggested, days_ago):
        entry = db.query(JournalEntry).filter(
            JournalEntry.author_id == users[about].id,
            JournalEntry.transcript.like(f"%{source_text}%"),
        ).first()
        if entry is None:
            return
        db.add(Alert(
            source_entry_id=entry.id, author_id=users[about].id,
            recipient_id=users[to].id, circle_id=circle.id,
            severity=severity, message=message, suggested_action=suggested,
            created_at=now - timedelta(days=days_ago),
        ))

    make_alert(
        "Aditya", "Deepa", "overworked", "gentle",
        "Aditya has seemed a little stretched at work this week — a warm word might land nicely.",
        "Maybe ask how his big project is going.", days_ago=2,
    )
    make_alert(
        "Abhishek", "Mumma", "new job", "gentle",
        "Abhishek is settling into his new job — he would love to hear from you.",
        "Give Abhishek a call to tell him you're proud.", days_ago=1,
    )
    db.commit()
    print("  • Gentle care alerts for Deepa and Mumma")

    from models import Alert
    alert_count = db.query(Alert).count()
    entry_count = db.query(JournalEntry).count()
    action_count = db.query(Action).count()
    db.close()

    print(
        f"""
Done. {len(MEMBERS)} members · {entry_count} entries · {action_count} actions · {alert_count} alert(s) waiting.

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
