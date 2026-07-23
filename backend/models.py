"""All ORM models (spec Section 6). `visibility` defaults to private everywhere:
nothing an author records is readable by anyone else until they share it."""
import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class Visibility(str, enum.Enum):
    private = "private"
    circle = "circle"
    custom = "custom"


def _vis_column():
    return mapped_column(
        Enum(Visibility, values_callable=lambda e: [v.value for v in e]),
        default=Visibility.private,
        nullable=False,
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str] = mapped_column(String, default="en", nullable=False)
    voice_sample_path: Mapped[str | None] = mapped_column(String, nullable=True)
    accepted_policy_version: Mapped[str | None] = mapped_column(String, nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    memberships: Mapped[list["Membership"]] = relationship(back_populates="user")


class FamilyCircle(Base):
    __tablename__ = "family_circles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    invite_code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(String, default="free", nullable=False)  # free|plus
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    memberships: Mapped[list["Membership"]] = relationship(back_populates="circle")


class Membership(Base):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    circle_id: Mapped[int] = mapped_column(ForeignKey("family_circles.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String, default="member", nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    circle: Mapped["FamilyCircle"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="memberships")


class Relationship(Base):
    """How from_user refers to to_user ("spouse", "mother", ...)."""

    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    circle_id: Mapped[int] = mapped_column(ForeignKey("family_circles.id"), nullable=False)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    circle_id: Mapped[int] = mapped_column(ForeignKey("family_circles.id"), nullable=False)
    audio_path: Mapped[str | None] = mapped_column(String, nullable=True)
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String, default="en", nullable=False)
    duration_sec: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    visibility: Mapped[Visibility] = _vis_column()
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    facts: Mapped[list["Fact"]] = relationship(back_populates="entry")


class Fact(Base):
    __tablename__ = "facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    circle_id: Mapped[int] = mapped_column(ForeignKey("family_circles.id"), nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)  # preference|event|state|plan|person|date
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured: Mapped[dict] = mapped_column(JSON, default=dict)
    source_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[Visibility] = _vis_column()
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    entry: Mapped["JournalEntry"] = relationship(back_populates="facts")


class ShareTarget(Base):
    """One row per allowed viewer of a `custom`-visibility entry or fact."""

    __tablename__ = "share_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("journal_entries.id"), nullable=True, index=True
    )
    fact_id: Mapped[int | None] = mapped_column(ForeignKey("facts.id"), nullable=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)


class ShareRule(Base):
    """A standing pre-approval the author created ("share my gift ideas")."""

    __tablename__ = "share_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    circle_id: Mapped[int] = mapped_column(ForeignKey("family_circles.id"), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    match: Mapped[dict] = mapped_column(JSON, default=dict)  # e.g. {"type":"preference","tag":"gift"}
    audience: Mapped[object] = mapped_column(JSON, default="all")  # "all" | [user ids]
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AlertTrigger(Base):
    """Authored by the person the alert is ABOUT ("if I say I'm unwell, tell Aditya")."""

    __tablename__ = "alert_triggers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    circle_id: Mapped[int] = mapped_column(ForeignKey("family_circles.id"), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    match: Mapped[dict] = mapped_column(JSON, default=dict)  # e.g. {"type":"state","topic":"health"}
    audience: Mapped[list] = mapped_column(JSON, default=list)  # list of user ids
    severity_hint: Mapped[str] = mapped_column(String, default="gentle")  # gentle|notable|urgent
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_entry_id: Mapped[int] = mapped_column(ForeignKey("journal_entries.id"), nullable=False)
    source_fact_id: Mapped[int | None] = mapped_column(ForeignKey("facts.id"), nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    circle_id: Mapped[int] = mapped_column(ForeignKey("family_circles.id"), nullable=False)
    severity: Mapped[str] = mapped_column(String, default="gentle", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="new", nullable=False)  # new|seen|acted|dismissed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LlmCall(Base):
    """One row per LLM helper invocation — the unit-economics ground truth.
    provider='fallback' rows make the LLM-vs-fallback quality metric honest."""

    __tablename__ = "llm_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)  # openai|anthropic|fallback
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    entry_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ask_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AskRecord(Base):
    """One row per Companion question — the countable freemium unit."""

    __tablename__ = "asks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    circle_id: Mapped[int] = mapped_column(ForeignKey("family_circles.id"), nullable=False, index=True)
    answered_by: Mapped[str] = mapped_column(String, default="fallback", nullable=False)  # llm|fallback
    snippet_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    audio_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProductEvent(Base):
    """First-party funnel events — no third-party trackers, ever."""

    __tablename__ = "product_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    properties: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditEvent(Base):
    """Append-only trail of consequential events: consent changes, alerts,
    approvals, logins, membership changes. Never updated, never deleted by
    application code."""

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    event: Mapped[str] = mapped_column(String, nullable=False, index=True)
    object_type: Mapped[str | None] = mapped_column(String, nullable=True)
    object_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    """Support messages and 'this looks wrong' reports — the correction loop."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    kind: Mapped[str] = mapped_column(String, default="feedback", nullable=False)  # feedback|report
    subject_kind: Mapped[str | None] = mapped_column(String, nullable=True)  # answer|alert|fact|other
    subject_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PasswordReset(Base):
    """One-time reset token, minted by the admin CLI for the pilot."""

    __tablename__ = "password_resets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    related_alert_id: Mapped[int | None] = mapped_column(ForeignKey("alerts.id"), nullable=True)
    intent: Mapped[str] = mapped_column(Text, nullable=False)
    plan: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(
        String, default="draft", nullable=False
    )  # draft|awaiting_approval|approved|completed|cancelled
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
