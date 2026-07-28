"""Personal Radar: prospective memory for the AUTHOR alone. The journal
remembers what you told it — "on Monday you said Friday matters" — and hands
it back warmly at the right moment. Reads ONLY the author's own facts; other
members never see these nudges (the route computes them per-request for the
logged-in user).

Delivery note: real scheduled delivery (a Thursday-night push) needs a push
channel that doesn't exist yet — on-next-open is the pilot behavior,
documented, not a bug.
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from agents.llm import complete
from agents.prompter import Nudge
from agents.wording_guard import sounds_medical
from models import Fact, User

FACT_MAX_AGE = timedelta(days=14)  # nothing older than this, ever
DATE_WINDOW_DAYS = 2               # personal_date: today .. +2 days
OPEN_PLAN_MIN_AGE = 3              # open_plan: 3..10 days old, no date
OPEN_PLAN_MAX_AGE = 10
MAX_NUDGES = 2                     # anti-nag: hard cap per call

SYSTEM = (
    "You write ONE short personal reminder for the author of a private "
    "journal, addressed as 'you'. They told their journal about something "
    "coming up; remind them warmly, mentioning the weekday they said it. "
    "1-2 plain sentences, encouraging, like a friend. NEVER medical, never "
    "diagnostic, never alarming. Write in the language requested."
)

# Within-day memo so wording stays stable for a given fact on a given day
# (and repeated Home polls don't re-spend LLM calls). Process-local, tiny.
_wording_memo: dict[tuple, str] = {}


def _wish(days_away: int, lang: str) -> str:
    if lang == "hi":
        if days_away == 0:
            return "आज ही है — आप कर लेंगे!"
        if days_away == 1:
            return "कल के लिए शुभकामनाएँ!"
        return "शुभकामनाएँ!"
    if days_away == 0:
        return "it's today — you've got this!"
    if days_away == 1:
        return "all the best for tomorrow!"
    return "all the best!"


def _fallback_date_text(fact: Fact, days_away: int, lang: str) -> str:
    said_on = fact.created_at.strftime("%A")
    what = fact.source_quote or fact.content
    if lang == "hi":
        return f"{said_on} को आपने कहा था: “{what}” — {_wish(days_away, lang)}"
    return f"On {said_on} you mentioned: “{what}” — {_wish(days_away, lang)}"


def _fallback_plan_text(fact: Fact, lang: str) -> str:
    what = fact.source_quote or fact.content
    if lang == "hi":
        return f"कुछ दिन पहले आपने कहा था: “{what}” — क्या यह अब भी मन में है?"
    return f"A few days ago you voiced: “{what}” — still on your mind?"


def _wording(user: User, fact: Fact, kind: str, fallback_text: str, now: datetime) -> str:
    memo_key = (user.id, fact.id, kind, now.date().isoformat())
    if memo_key in _wording_memo:
        return _wording_memo[memo_key]

    lang = (user.language or "en")[:2]
    text = complete(
        (
            f"Author: {user.name} (language '{lang}'). Today is "
            f"{now.strftime('%A %d %b')}. On {fact.created_at.strftime('%A')} "
            f"they journaled: \"{fact.source_quote or fact.content}\".\n"
            f"Reminder kind: {kind}. A good plain version: \"{fallback_text}\""
        ),
        system=SYSTEM,
        fallback=lambda: fallback_text,
        max_tokens=150,
        agent="PersonalRadar",
    )
    if sounds_medical(text):
        text = fallback_text
    _wording_memo[memo_key] = text
    if len(_wording_memo) > 500:
        _wording_memo.clear()  # crude but sufficient day-scale hygiene
    return text


def _next_occurrence(raw: str, now: datetime) -> datetime | None:
    """Month/day recurrence, same style as relationship_radar."""
    try:
        when = datetime.fromisoformat(raw)
    except (ValueError, TypeError):
        return None
    this_year = when.replace(year=now.year)
    if this_year < now - timedelta(days=1):
        this_year = this_year.replace(year=now.year + 1)
    return this_year


def radar(db: Session, user: User, now: datetime | None = None) -> list[Nudge]:
    """The author's own prospective-memory nudges. Anti-nag rules enforced in
    code: max 2 per call, deterministic within a day, nothing older than 14
    days. Own facts only — the query is filtered on the author's id."""
    from services import metering

    now = now or datetime.utcnow()
    lang = (user.language or "en")[:2]
    facts = (
        db.query(Fact)
        .filter(Fact.author_id == user.id, Fact.created_at >= now - FACT_MAX_AGE)
        .order_by(Fact.created_at.desc())
        .all()
    )

    nudges: list[Nudge] = []

    with metering.context(user_id=user.id):  # PersonalRadar LLM calls land in llm_calls
        # 1) personal_date: a dated fact (or dated plan) landing today .. +2 days
        for fact in facts:
            if fact.type not in ("date", "plan"):
                continue
            raw = (fact.structured or {}).get("date")
            if not raw:
                continue
            occurrence = _next_occurrence(raw, now)
            if occurrence is None:
                continue
            days_away = (occurrence.date() - now.date()).days
            if not 0 <= days_away <= DATE_WINDOW_DAYS:
                continue
            fallback_text = _fallback_date_text(fact, days_away, lang)
            nudges.append(
                Nudge(kind="personal_date", text=_wording(user, fact, "personal_date", fallback_text, now))
            )
            if len(nudges) >= MAX_NUDGES:
                break

        # 2) open_plan: at most ONE gentle "still on your mind?" for an undated plan
        if len(nudges) < MAX_NUDGES:
            for fact in facts:
                if fact.type != "plan" or (fact.structured or {}).get("date"):
                    continue
                age_days = (now - fact.created_at).days
                if not OPEN_PLAN_MIN_AGE <= age_days <= OPEN_PLAN_MAX_AGE:
                    continue
                fallback_text = _fallback_plan_text(fact, lang)
                nudges.append(
                    Nudge(kind="open_plan", text=_wording(user, fact, "open_plan", fallback_text, now))
                )
                break  # never more than one open_plan nudge

    if nudges:
        from services import activity

        activity.emit(user.id, "Radar", "Remembering the days you mentioned — a gentle note is up.")
    return nudges[:MAX_NUDGES]
