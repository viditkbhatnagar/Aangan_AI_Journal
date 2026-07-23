"""Capture pipeline (spec Section 9). The `transcript` parameter is the
no-Deepgram path: seed.py and the type-it-instead flow inject text directly."""
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from agents import consent_guardian, doer, extractor, librarian, summarizer, transcriber
from agents.consent_guardian import ShareSuggestion
from models import Action, Fact, JournalEntry, User
from services import activity, metering
from services.events import record_event


@dataclass
class CaptureResult:
    entry: JournalEntry
    facts: list[Fact] = field(default_factory=list)
    share_suggestions: list[ShareSuggestion] = field(default_factory=list)
    applied_rules: list[str] = field(default_factory=list)
    suggested_action: Action | None = None


def run_capture(
    db: Session,
    author: User,
    circle_id: int,
    *,
    audio_path: str | None = None,
    transcript: str | None = None,
    language: str | None = None,
) -> CaptureResult:
    with metering.context(user_id=author.id):
        return _run_capture_metered(
            db, author, circle_id,
            audio_path=audio_path, transcript=transcript, language=language,
        )


def _run_capture_metered(
    db: Session,
    author: User,
    circle_id: int,
    *,
    audio_path: str | None,
    transcript: str | None,
    language: str | None,
) -> CaptureResult:
    duration = 0
    if transcript is None:
        activity.emit(author.id, "Transcriber", "Listening to your recording…")
        transcription = transcriber.transcribe(audio_path)  # may raise TranscriptionUnavailable
        transcript = transcription.text
        language = language or transcription.language
        duration = transcription.duration_sec
        activity.emit(
            author.id, "Transcriber",
            f"Heard {duration}s of {language or 'en'} — transcript ready.",
        )
    language = language or author.language or "en"

    # 1-2) entry row, private by default
    entry = JournalEntry(
        author_id=author.id,
        circle_id=circle_id,
        audio_path=audio_path,
        transcript=transcript,
        language=language,
        duration_sec=duration,
    )
    db.add(entry)
    db.flush()
    metering.update_context(entry_id=entry.id)

    # 3-4) summary and shareable snippets
    activity.emit(author.id, "Summarizer", "Writing a gentle summary…")
    summary = summarizer.summarize(transcript, language)
    entry.summary = summary.summary

    # 5) facts, private by default
    activity.emit(author.id, "Extractor", "Noting the little things…")
    facts = []
    for draft in extractor.extract_facts(transcript, summary.summary):
        fact = Fact(
            entry_id=entry.id,
            author_id=author.id,
            circle_id=circle_id,
            type=draft.type,
            content=draft.content,
            structured=draft.structured,
            source_quote=draft.source_quote,
        )
        db.add(fact)
        facts.append(fact)
    db.commit()
    activity.emit(
        author.id, "Extractor",
        f"Kept {len(facts)} note(s) — all private to you.",
    )

    # 6) the author's own standing rules, then suggestions to confirm in-app
    applied_rules = consent_guardian.apply_rules(db, author, facts)
    for rule in applied_rules:
        activity.emit(author.id, "Consent Guardian", f"Applied your rule: “{rule}”.")
    suggestions = consent_guardian.suggest_shares(entry, facts)
    if suggestions:
        activity.emit(
            author.id, "Consent Guardian",
            f"{len(suggestions)} share suggestion(s) — your call, always.",
        )

    # 7) index into the vector store with visibility metadata
    librarian.upsert_entry(db, entry, facts)
    activity.emit(author.id, "Librarian", "Tucked into the family memory, visibility-tagged.")

    # 8) the author's alert triggers
    _run_alerter(db, entry, facts)

    # 9) does this entry ask for something to be DONE? draft it for approval
    suggested_action = _suggest_action(db, author, transcript)

    record_event(author.id, "entry", {
        "entry_id": entry.id,
        "voice_seconds": duration,
        "facts": len(facts),
    })

    return CaptureResult(
        entry=entry,
        facts=facts,
        share_suggestions=suggestions,
        applied_rules=applied_rules,
        suggested_action=suggested_action,
    )


def _run_alerter(db: Session, entry: JournalEntry, facts: list[Fact]) -> None:
    try:
        from agents import alerter
    except ImportError:
        return
    created = alerter.evaluate(db, entry, facts)
    if created:
        from models import User as UserModel

        names = ", ".join(
            db.get(UserModel, a.recipient_id).name for a in created
        )
        activity.emit(
            entry.author_id, "Alerter",
            f"Your trigger matched — gently told {names}.",
        )


def _suggest_action(db: Session, author: User, transcript: str) -> Action | None:
    intent = doer.detect_action_intent(transcript)
    if not intent:
        return None
    from services import actions as actions_service

    action = actions_service.create_action(db, author, intent)
    activity.emit(
        author.id, "Doer",
        f"Prepared “{intent[:60]}” — waiting for YOUR approval on the Actions page.",
    )
    return action
