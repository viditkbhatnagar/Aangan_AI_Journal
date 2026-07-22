"""Capture pipeline (spec Section 9). The `transcript` parameter is the
no-Deepgram path: seed.py and the type-it-instead flow inject text directly."""
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from agents import consent_guardian, extractor, librarian, summarizer, transcriber
from agents.consent_guardian import ShareSuggestion
from models import Fact, JournalEntry, User


@dataclass
class CaptureResult:
    entry: JournalEntry
    facts: list[Fact] = field(default_factory=list)
    share_suggestions: list[ShareSuggestion] = field(default_factory=list)
    applied_rules: list[str] = field(default_factory=list)


def run_capture(
    db: Session,
    author: User,
    circle_id: int,
    *,
    audio_path: str | None = None,
    transcript: str | None = None,
    language: str | None = None,
) -> CaptureResult:
    duration = 0
    if transcript is None:
        transcription = transcriber.transcribe(audio_path)  # may raise TranscriptionUnavailable
        transcript = transcription.text
        language = language or transcription.language
        duration = transcription.duration_sec
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

    # 3-4) summary and shareable snippets
    summary = summarizer.summarize(transcript, language)
    entry.summary = summary.summary

    # 5) facts, private by default
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

    # 6) the author's own standing rules, then suggestions to confirm in-app
    applied_rules = consent_guardian.apply_rules(db, author, facts)
    suggestions = consent_guardian.suggest_shares(entry, facts)

    # 7) index into the vector store with visibility metadata
    librarian.upsert_entry(db, entry, facts)

    # 8) the author's alert triggers (wired in the alerts milestone)
    _run_alerter(db, entry, facts)

    return CaptureResult(
        entry=entry,
        facts=facts,
        share_suggestions=suggestions,
        applied_rules=applied_rules,
    )


def _run_alerter(db: Session, entry: JournalEntry, facts: list[Fact]) -> None:
    try:
        from agents import alerter
    except ImportError:
        return
    alerter.evaluate(db, entry, facts)
