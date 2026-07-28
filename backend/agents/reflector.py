"""Reflector: a warm weekly reflection over the author's OWN last-7-days
entries — "what you kept coming back to", written to the author ("you"), in
the author's language. Reads only the author's rows; the /thoughts route
guarantees the owner is the asker. Never clinical, never diagnostic — the
shared wording guard enforces that in code, not just in the prompt."""
from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from agents.llm import complete
from agents.mirror import NEGATIVE, POSITIVE
from agents.wording_guard import sounds_medical
from models import Fact, JournalEntry, User

WEEK = timedelta(days=7)

SYSTEM = (
    "You write a short weekly reflection for the author of a private journal, "
    "addressed to them as 'you'. Use ONLY the journal excerpts provided — never "
    "invent events or feelings. 2-3 warm, plain sentences about what they kept "
    "coming back to this week. Gentle and encouraging, like a kind friend "
    "reading their week back to them. NEVER medical, never diagnostic, never "
    "clinical, no advice about health or treatment. Write in the language "
    "requested."
)

EMPTY = {
    "en": "Your thoughts will gather here as you write. Whenever you're ready — ten seconds is plenty.",
    "hi": "जैसे-जैसे आप लिखेंगे, आपकी बातें यहाँ इकट्ठा होंगी। जब मन करे — दस सेकंड भी बहुत हैं।",
}


def _week_entries(db: Session, user: User, now: datetime) -> list[JournalEntry]:
    return (
        db.query(JournalEntry)
        .filter(
            JournalEntry.author_id == user.id,
            JournalEntry.created_at >= now - WEEK,
        )
        .order_by(JournalEntry.created_at.asc())
        .all()
    )


def _fallback_reflection(db: Session, user: User, entries: list[JournalEntry]) -> str:
    """Deterministic keyless reflection: counts, themes, and the week's most
    frequent positive/negative words — same inputs, same sentence, always."""
    lang = (user.language or "en")[:2]
    n = len(entries)
    text = " ".join((e.transcript or e.summary or "") for e in entries).lower()

    facts = (
        db.query(Fact)
        .filter(Fact.author_id == user.id, Fact.created_at >= entries[0].created_at)
        .all()
    )
    theme_counts = Counter(f.type for f in facts)
    themes = ", ".join(name for name, _ in theme_counts.most_common(2))

    pos_counts = Counter({w: text.count(w) for w in POSITIVE if w in text})
    neg_counts = Counter({w: text.count(w) for w in NEGATIVE if w in text})
    brightest = pos_counts.most_common(1)
    heaviest = neg_counts.most_common(1)

    if lang == "hi":
        parts = [f"इस हफ़्ते आपने {n} बार लिखा।"]
        if themes:
            parts.append(f"आप बार-बार इन बातों पर लौटे: {themes}।")
        if brightest:
            parts.append(f"“{brightest[0][0]}” जैसे शब्द आपकी चिट्ठियों में चमकते रहे।")
        elif heaviest:
            parts.append(f"“{heaviest[0][0]}” जैसे शब्द थोड़े भारी रहे — अपने लिए कोमल रहिए।")
        return " ".join(parts)

    parts = [f"You wrote {n} time{'s' if n != 1 else ''} this week."]
    if themes:
        parts.append(f"You kept coming back to: {themes}.")
    if brightest:
        parts.append(f"Words like “{brightest[0][0]}” kept shining through your letters.")
    elif heaviest:
        parts.append(f"Words like “{heaviest[0][0]}” sat a little heavy — be gentle with yourself.")
    return " ".join(parts)


def weekly_reflection(db: Session, user: User, now: datetime | None = None) -> str:
    """The 2-3 sentence weekly note for /thoughts. Author-only by construction:
    every query in this module filters on the author's id."""
    now = now or datetime.utcnow()
    entries = _week_entries(db, user, now)
    lang = (user.language or "en")[:2]
    if not entries:
        return EMPTY.get(lang, EMPTY["en"])

    def fallback() -> str:
        return _fallback_reflection(db, user, entries)

    excerpts = "\n".join(
        f"- [{e.created_at.strftime('%A')}] {(e.transcript or e.summary or '')[:300]}"
        for e in entries[-10:]
    )
    reflection = complete(
        (
            f"Author: {user.name} (write in language '{lang}').\n"
            f"Their journal entries from the last 7 days:\n{excerpts}"
        ),
        system=SYSTEM,
        fallback=fallback,
        max_tokens=300,
        agent="Reflector",
    )
    if sounds_medical(reflection):
        reflection = fallback()
    return reflection
