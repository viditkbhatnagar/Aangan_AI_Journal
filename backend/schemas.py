"""Pydantic request/response models."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- auth ---

class RegisterIn(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=3)
    password: str = Field(min_length=4)
    language: str = "en"


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORMModel):
    id: int
    name: str
    email: str
    language: str
    created_at: datetime


# --- circles ---

class CircleCreateIn(BaseModel):
    name: str = Field(min_length=1)


class CircleJoinIn(BaseModel):
    invite_code: str


class CircleOut(ORMModel):
    id: int
    name: str
    invite_code: str


class MemberOut(BaseModel):
    id: int
    name: str
    language: str
    relationship_label: str | None = None  # how *I* refer to them


# --- entries and facts ---

class FactOut(ORMModel):
    id: int
    entry_id: int
    type: str
    content: str
    structured: dict
    source_quote: str | None
    visibility: str
    created_at: datetime


class EntryOut(ORMModel):
    id: int
    author_id: int
    transcript: str | None
    summary: str | None
    language: str
    duration_sec: int
    visibility: str
    created_at: datetime
    facts: list[FactOut] = []


class ShareSuggestionOut(BaseModel):
    kind: str  # "entry" | "fact"
    fact_id: int | None = None
    text: str
    reason: str


class CaptureOut(BaseModel):
    entry: EntryOut
    share_suggestions: list[ShareSuggestionOut] = []
    applied_rules: list[str] = []


class ShareIn(BaseModel):
    fact_id: int | None = None  # None => share the whole entry
    visibility: str  # "private" | "circle" | "custom"
    viewer_ids: list[int] | None = None  # required when visibility == "custom"


# --- ask ---

class AskIn(BaseModel):
    question: str = Field(min_length=1)


class SnippetOut(BaseModel):
    text: str
    author_id: int
    author_name: str
    created_at: datetime
    source: str  # "entry" | fact type


class AskOut(BaseModel):
    answer: str
    language: str
    snippets: list[SnippetOut] = []


# --- rules and triggers ---

class ShareRuleIn(BaseModel):
    description: str
    match: dict  # e.g. {"type": "preference", "tag": "gift"}
    audience: object = "all"  # "all" | [user ids]


class ShareRuleOut(ORMModel):
    id: int
    description: str
    match: dict
    audience: object
    active: bool
    created_at: datetime


class AlertTriggerIn(BaseModel):
    description: str
    match: dict  # e.g. {"type": "state", "topic": "health"}
    audience: list[int]
    severity_hint: str = "notable"


class AlertTriggerOut(ORMModel):
    id: int
    description: str
    match: dict
    audience: list
    severity_hint: str
    active: bool
    created_at: datetime


# --- alerts ---

class AlertOut(ORMModel):
    id: int
    author_id: int
    severity: str
    message: str
    suggested_action: str | None
    status: str
    created_at: datetime


class AlertStatusIn(BaseModel):
    status: str  # seen | acted | dismissed


# --- actions ---

class ActionIn(BaseModel):
    intent: str
    related_alert_id: int | None = None
    plan_hint: dict | None = None  # optional shape hints (type, item, to, body...)


class ActionOut(ORMModel):
    id: int
    created_by: int
    related_alert_id: int | None
    intent: str
    plan: dict
    status: str
    result: dict | None
    created_at: datetime
    completed_at: datetime | None
