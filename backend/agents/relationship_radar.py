"""Relationship Radar: 'not in touch' and upcoming-date nudges. It suggests a
human connection — it never acts. Uses only content the asker may see."""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from agents import librarian
from agents.prompter import Nudge
from auth import get_user_circle_id
from models import Fact, JournalEntry, Membership, User, Visibility

OUT_OF_TOUCH_AFTER = timedelta(days=5)
DATE_HORIZON = timedelta(days=14)


def radar(db: Session, user: User, now: datetime | None = None) -> list[Nudge]:
    now = now or datetime.utcnow()
    circle_id = get_user_circle_id(db, user)
    if circle_id is None:
        return []

    nudges: list[Nudge] = []

    # 1) upcoming dates — only date-facts this user is allowed to see
    date_facts = (
        db.query(Fact)
        .filter(Fact.circle_id == circle_id, Fact.type == "date")
        .order_by(Fact.created_at.desc())
        .limit(50)
        .all()
    )
    for fact in date_facts:
        if not librarian.is_visible(db, user, fact_id=fact.id):
            continue
        raw = (fact.structured or {}).get("date")
        if not raw:
            continue
        try:
            when = datetime.fromisoformat(raw)
        except ValueError:
            continue
        # compare month/day so yearly dates (birthdays) recur
        this_year = when.replace(year=now.year)
        if this_year < now - timedelta(days=1):
            this_year = this_year.replace(year=now.year + 1)
        days_away = (this_year - now).days
        if 0 <= days_away <= DATE_HORIZON.days:
            author = db.get(User, fact.author_id)
            who = author.name if author and author.id != user.id else "You"
            date_str = this_year.strftime("%d %b")
            nudges.append(
                Nudge(
                    kind="upcoming_date",
                    text=f"📅 Coming up on {date_str}: {fact.content} ({who}). A little planning goes a long way.",
                )
            )

    # 2) not in touch — a member whose shared voice has gone quiet for you
    members = (
        db.query(User)
        .join(Membership, Membership.user_id == User.id)
        .filter(Membership.circle_id == circle_id, User.id != user.id)
        .all()
    )
    for member in members:
        latest_shared = (
            db.query(JournalEntry)
            .filter(
                JournalEntry.author_id == member.id,
                JournalEntry.circle_id == circle_id,
                JournalEntry.visibility == Visibility.circle,
            )
            .order_by(JournalEntry.created_at.desc())
            .first()
        )
        if latest_shared is None:
            continue  # nothing ever shared — nothing to go quiet from
        if now - latest_shared.created_at > OUT_OF_TOUCH_AFTER:
            nudges.append(
                Nudge(
                    kind="reach_out",
                    text=f"🤍 It's been a while since you heard from {member.name} here — a call might be lovely.",
                )
            )

    return nudges[:4]
