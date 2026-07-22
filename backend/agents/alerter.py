"""Alerter: fires only the triggers the author set, only to the permitted
audience. Nudges connect humans — the wording prompts a person to reach out
and must never sound like medical advice or a diagnosis. Rate limited so
family never drowns in pings."""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from agents.consent_guardian import _fact_matches
from agents.llm import complete
from config import settings
from models import Alert, AlertTrigger, Fact, JournalEntry, User

WORDING_SYSTEM = (
    "You write one short, warm alert message for a family app. Someone journaled "
    "something a family member asked to be told about. Write 1-2 gentle sentences "
    "prompting the recipient to reach out (call, visit, small treat). Plain words. "
    "NEVER give medical advice, never diagnose, never sound alarming or clinical. "
    "Write in the recipient's language if given."
)

FALLBACK_MESSAGES = {
    "health": "{author} mentioned not feeling their best today — a call or their favourite treat might brighten things up.",
    "default": "{author} shared something you asked to know about — a good moment to check in.",
}
FALLBACK_ACTION = "Give {author} a call and see how they're doing."


def _day_start(now: datetime) -> datetime:
    return datetime(now.year, now.month, now.day)


def _wording(author: User, recipient: User, fact: Fact, trigger: AlertTrigger) -> tuple[str, str]:
    topic = (fact.structured or {}).get("topic", "")
    template = FALLBACK_MESSAGES.get(topic, FALLBACK_MESSAGES["default"])

    def fallback() -> str:
        return template.format(author=author.name)

    message = complete(
        (
            f"Author: {author.name}. Recipient: {recipient.name} "
            f"(language '{recipient.language}').\n"
            f"The author's own trigger: \"{trigger.description}\".\n"
            f"What they journaled: \"{fact.source_quote or fact.content}\""
        ),
        system=WORDING_SYSTEM,
        fallback=fallback,
        max_tokens=200,
    )
    return message, FALLBACK_ACTION.format(author=author.name)


def evaluate(
    db: Session,
    entry: JournalEntry,
    facts: list[Fact],
    now: datetime | None = None,
) -> list[Alert]:
    now = now or datetime.utcnow()
    triggers = (
        db.query(AlertTrigger)
        .filter(
            AlertTrigger.author_id == entry.author_id,
            AlertTrigger.active.is_(True),
        )
        .all()
    )
    if not triggers:
        return []

    author = db.get(User, entry.author_id)
    created: list[Alert] = []

    for fact in facts:
        for trigger in triggers:
            if not _fact_matches(fact, trigger.match or {}):
                continue
            for recipient_id in trigger.audience or []:
                if recipient_id == entry.author_id:
                    continue
                # never two alerts about the same fact
                already = (
                    db.query(Alert)
                    .filter(Alert.source_fact_id == fact.id, Alert.recipient_id == recipient_id)
                    .first()
                )
                if already:
                    continue
                # collapse similar alerts: one per recipient per entry
                if any(
                    a.recipient_id == recipient_id and a.source_entry_id == entry.id
                    for a in created
                ):
                    continue
                # anti alert-fatigue: daily cap per recipient
                today_count = (
                    db.query(Alert)
                    .filter(
                        Alert.recipient_id == recipient_id,
                        Alert.created_at >= _day_start(now),
                        Alert.created_at < _day_start(now) + timedelta(days=1),
                    )
                    .count()
                )
                if today_count >= settings.alert_daily_cap:
                    continue

                recipient = db.get(User, recipient_id)
                if recipient is None:
                    continue
                message, suggested = _wording(author, recipient, fact, trigger)
                alert = Alert(
                    source_entry_id=entry.id,
                    source_fact_id=fact.id,
                    author_id=entry.author_id,
                    recipient_id=recipient_id,
                    circle_id=entry.circle_id,
                    severity=trigger.severity_hint or "gentle",
                    message=message,
                    suggested_action=suggested,
                    created_at=now,
                )
                db.add(alert)
                created.append(alert)

    if created:
        db.commit()
    return created
