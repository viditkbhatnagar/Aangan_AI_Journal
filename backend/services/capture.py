"""Capture pipeline (spec Section 9). The `transcript` parameter is the
no-Deepgram path: seed.py and the type-it-instead flow inject text directly.

Two shapes, chosen by settings.async_capture:
- sync (default, and always for seed/tests): the whole pipeline runs in the
  request and CaptureOut carries summary/facts/suggestions immediately.
- async: the entry is saved and committed fast with status='enriching';
  summarize/extract/rules/index/alerts/actions continue in a background
  task on a fresh session, and the UI polls GET /entries/{id}/enrichment.
Transcription always stays in the request — its 503 fallback contract
(switch to typing) depends on the status code reaching the client.
"""
import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from agents import consent_guardian, doer, extractor, librarian, summarizer, transcriber
from agents.consent_guardian import ShareSuggestion
from models import Action, Fact, JournalEntry, User
from services import activity, metering
from services.events import record_event

_logger = logging.getLogger("aangan.capture")


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
    background=None,
) -> CaptureResult:
    """background: a FastAPI BackgroundTasks. Async enrichment happens only
    when settings.async_capture is on AND a background runner was provided —
    seed.py and direct callers always get the full synchronous pipeline."""
    from config import settings

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

    go_async = bool(settings.async_capture and background is not None)

    # 1-2) entry row, private by default
    entry = JournalEntry(
        author_id=author.id,
        circle_id=circle_id,
        audio_path=audio_path,
        transcript=transcript,
        language=language,
        duration_sec=duration,
        status="enriching" if go_async else "ready",
    )
    db.add(entry)
    db.flush()

    if go_async:
        db.commit()  # durable before the request returns
        background.add_task(enrich_entry, entry.id, author.id)
        activity.emit(author.id, "Journal", "Saved. Making notes in the background…")
        return CaptureResult(entry=entry)

    with metering.context(user_id=author.id, db=db, entry_id=entry.id):
        return _enrich(db, author, entry)


def enrich_entry(entry_id: int, author_id: int) -> None:
    """Background phase: fresh session (the request's is closed by now),
    fresh metering context. Failures are logged, never raised — the entry
    stays readable either way and is always marked ready."""
    import db as db_module

    session = db_module.SessionLocal()
    try:
        entry = session.get(JournalEntry, entry_id)
        author = session.get(User, author_id)
        if entry is None or author is None:
            return
        with metering.context(user_id=author_id, db=session, entry_id=entry_id):
            _enrich(session, author, entry)
    except Exception:
        _logger.exception("background enrichment failed for entry %s", entry_id)
        try:
            session.rollback()
            row = session.get(JournalEntry, entry_id)
            if row is not None:
                row.status = "ready"  # never leave an entry stuck in 'enriching'
                session.commit()
        except Exception:
            _logger.exception("could not mark entry %s ready after failure", entry_id)
    finally:
        session.close()


def _enrich(db: Session, author: User, entry: JournalEntry) -> CaptureResult:
    """Steps 3-9. Ordering invariant: consent rules run BEFORE the vector
    index so Chroma metadata carries post-rule visibility."""
    transcript = entry.transcript

    # 3-4) summary and shareable snippets
    activity.emit(author.id, "Summarizer", "Writing a gentle summary…")
    summary = summarizer.summarize(transcript, entry.language)
    entry.summary = summary.summary

    # 5) facts, private by default
    activity.emit(author.id, "Extractor", "Noting the little things…")
    facts = []
    for draft in extractor.extract_facts(transcript, summary.summary):
        fact = Fact(
            entry_id=entry.id,
            author_id=author.id,
            circle_id=entry.circle_id,
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
    suggested_action = _suggest_action(db, author, transcript, entry_id=entry.id)

    entry.applied_rules = applied_rules
    entry.status = "ready"
    db.commit()

    record_event(author.id, "entry", {
        "entry_id": entry.id,
        "voice_seconds": entry.duration_sec,
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


def _suggest_action(
    db: Session, author: User, transcript: str, *, entry_id: int | None = None
) -> Action | None:
    intent = doer.detect_action_intent(transcript)
    if not intent:
        return None
    from services import actions as actions_service

    action = actions_service.create_action(db, author, intent, source_entry_id=entry_id)
    if action.status == "clarifying":
        activity.emit(
            author.id, "Doer",
            f"Noted “{intent[:60]}” — I have a couple of quick questions on the Actions page before I buy.",
        )
    else:
        activity.emit(
            author.id, "Doer",
            f"Prepared “{intent[:60]}” — waiting for YOUR approval on the Actions page.",
        )
    return action
