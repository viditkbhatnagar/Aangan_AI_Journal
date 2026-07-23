"""Consent Guardian: the ONLY code path that moves anything from private to
shared. The AI proposes (suggest_shares) — the author decides, either by an
explicit share action (set_visibility) or a standing rule the author created
themselves (apply_rules)."""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from agents import librarian
from models import Fact, JournalEntry, ShareRule, ShareTarget, User, Visibility


class NotYourContent(PermissionError):
    """Raised when anyone but the author tries to change visibility."""


@dataclass
class ShareSuggestion:
    kind: str  # "entry" | "fact"
    fact_id: int | None
    text: str
    reason: str


SHAREABLE_TYPES = {"preference", "plan", "event"}
HAPPY_WORDS = {
    "love", "loved", "beautiful", "happy", "excited", "wonderful", "proud",
    "great", "khush", "अच्छा", "खुश", "सुंदर",
}


def suggest_shares(entry: JournalEntry, facts: list[Fact]) -> list[ShareSuggestion]:
    """Proposals only — never writes. Shown to the author after recording."""
    suggestions = []
    for fact in facts:
        if fact.visibility != Visibility.private:
            continue  # already shared by a rule
        if fact.type in SHAREABLE_TYPES:
            reason = {
                "preference": "Sounds like a lovely gift hint — want your family to know?",
                "plan": "A plan your family might want to be part of — share it?",
                "event": "A moment worth sharing with the family?",
            }[fact.type]
            suggestions.append(
                ShareSuggestion(kind="fact", fact_id=fact.id, text=fact.content, reason=reason)
            )
    if not suggestions and entry.summary:
        text = (entry.transcript or "") + " " + (entry.summary or "")
        if any(w in text.lower() for w in HAPPY_WORDS):
            suggestions.append(
                ShareSuggestion(
                    kind="entry",
                    fact_id=None,
                    text=entry.summary,
                    reason="This sounds like a happy one — share the whole moment?",
                )
            )
    return suggestions[:3]


def _fact_matches(fact: Fact, match: dict) -> bool:
    if match.get("type") and fact.type != match["type"]:
        return False
    tag = match.get("tag")
    if tag:
        structured = fact.structured or {}
        tags = structured.get("tags", [])
        haystack = (fact.content + " " + " ".join(str(v) for v in structured.values())).lower()
        if tag.lower() not in [t.lower() for t in tags] and tag.lower() not in haystack:
            return False
    topic = match.get("topic")
    if topic:
        structured = fact.structured or {}
        if structured.get("topic", "").lower() != topic.lower() and topic.lower() not in fact.content.lower():
            return False
    return True


def apply_rules(db: Session, author: User, facts: list[Fact]) -> list[str]:
    """Apply the author's own standing share_rules to freshly extracted facts.
    Still the author's choice — they wrote the rule. Returns descriptions of
    the rules that fired (for the 'shared because of your rule' notice)."""
    rules = (
        db.query(ShareRule)
        .filter(ShareRule.user_id == author.id, ShareRule.active.is_(True))
        .all()
    )
    applied = []
    for fact in facts:
        for rule in rules:
            if not _fact_matches(fact, rule.match or {}):
                continue
            if rule.audience == "all":
                fact.visibility = Visibility.circle
            else:
                fact.visibility = Visibility.custom
                for viewer_id in rule.audience:
                    db.add(ShareTarget(fact_id=fact.id, user_id=viewer_id))
            applied.append(rule.description)
            from services import audit

            audit.record(author.id, "rule_applied", "fact", fact.id, {
                "rule_id": rule.id,
                "visibility": fact.visibility.value,
            })
            break
    if applied:
        db.commit()
    return applied


def set_visibility(
    db: Session,
    actor: User,
    *,
    entry_id: int | None = None,
    fact_id: int | None = None,
    visibility: Visibility,
    viewer_ids: list[int] | None = None,
):
    """Explicit share (or un-share) by the author. Anyone else is refused.
    Sharing a fact never touches its parent entry's visibility."""
    if fact_id:
        row = db.get(Fact, fact_id)
    elif entry_id:
        row = db.get(JournalEntry, entry_id)
    else:
        raise ValueError("entry_id or fact_id required")
    if row is None:
        raise LookupError("not found")
    if row.author_id != actor.id:
        raise NotYourContent("Only the author can change what is shared.")
    if visibility == Visibility.custom and not viewer_ids:
        raise ValueError("Choose at least one person to share with.")

    old_visibility = row.visibility.value if row.visibility else "private"
    row.visibility = visibility

    # replace share targets for this item
    q = db.query(ShareTarget)
    q = q.filter(ShareTarget.fact_id == fact_id) if fact_id else q.filter(
        ShareTarget.entry_id == entry_id, ShareTarget.fact_id.is_(None)
    )
    q.delete()
    if visibility == Visibility.custom:
        for viewer_id in viewer_ids:
            db.add(
                ShareTarget(
                    entry_id=None if fact_id else entry_id,
                    fact_id=fact_id,
                    user_id=viewer_id,
                )
            )
    db.commit()

    # keep the vector store's metadata in step with the new visibility
    entry = row.entry if fact_id else row
    librarian.upsert_entry(db, entry)

    from services import audit

    audit.record(
        actor.id, "visibility_changed",
        "fact" if fact_id else "entry",
        fact_id or entry_id,
        {"from": old_visibility, "to": visibility.value, "viewer_ids": viewer_ids or []},
    )
    return row
