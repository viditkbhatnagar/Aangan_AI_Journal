"""Extractor: pulls facts (preference/event/state/plan/person/date) from a
transcript, each with a source quote. Every fact is private by default — the
Consent Guardian is the only path outward. Deterministic keyword fallback
(English + Hindi) when no LLM key."""
import re
from dataclasses import dataclass, field

from agents.llm import complete_json

FACTS_SCHEMA = {
    "type": "object",
    "properties": {
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["preference", "event", "state", "plan", "person", "date"],
                    },
                    "content": {"type": "string"},
                    "structured": {
                        "type": "object",
                        "properties": {
                            "item": {"type": "string"},
                            "brand": {"type": "string"},
                            "sentiment": {"type": "string"},
                            "topic": {"type": "string"},
                            "person": {"type": "string"},
                            "date": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                        },
                        "additionalProperties": False,
                    },
                    "source_quote": {"type": "string"},
                },
                "required": ["type", "content", "structured", "source_quote"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["facts"],
    "additionalProperties": False,
}

SYSTEM = (
    "You extract small factual notes from a private family journal entry. "
    "Types: preference (things liked/wanted — tag gift-worthy ones with tags:['gift']), "
    "event (something that happened), state (how the author is doing — set "
    "structured.topic, e.g. 'health'), plan (something they intend to do), "
    "person (someone mentioned), date (a specific date — structured.date as YYYY-MM-DD). "
    "content is one human-readable sentence in third person, in the entry's language. "
    "source_quote is the exact phrase from the entry. Extract only what is clearly "
    "there — no guesses. Usually 1-4 facts."
)

HEALTH_WORDS = {
    "unwell", "sick", "pain", "paining", "hurts", "hurt", "ache", "aching",
    "tired", "fever", "headache", "knee", "ill", "rough day",
    "दर्द", "तबीयत", "बीमार", "थकान", "घुटना", "बुखार",
}
PREFERENCE_WORDS = {
    "love", "loved", "want", "wish", "beautiful", "liked", "adore",
    "could not stop thinking", "can't stop thinking", "dream",
    "पसंद", "सुंदर", "चाहिए", "अच्छा लगा",
}
PLAN_WORDS = {"going to", "will ", "planning", "plan to", "next week", "tomorrow", "करूँगा", "करेंगे", "जाना है"}
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

_SENT_SPLIT = re.compile(r"(?<=[.!?।])\s+")


@dataclass
class FactDraft:
    type: str
    content: str
    structured: dict = field(default_factory=dict)
    source_quote: str | None = None


def _fallback(transcript: str) -> dict:
    facts = []
    for sentence in _SENT_SPLIT.split(transcript.strip()):
        sentence = sentence.strip()
        if not sentence:
            continue
        lowered = sentence.lower()
        if any(w in lowered for w in HEALTH_WORDS):
            facts.append({
                "type": "state",
                "content": sentence,
                "structured": {"topic": "health"},
                "source_quote": sentence,
            })
        elif any(w in lowered for w in PREFERENCE_WORDS):
            facts.append({
                "type": "preference",
                "content": sentence,
                "structured": {"tags": ["gift"], "sentiment": "loved"},
                "source_quote": sentence,
            })
        elif any(w in lowered for w in PLAN_WORDS):
            facts.append({
                "type": "plan",
                "content": sentence,
                "structured": {},
                "source_quote": sentence,
            })
        match = DATE_RE.search(sentence)
        if match:
            facts.append({
                "type": "date",
                "content": sentence,
                "structured": {"date": match.group(1)},
                "source_quote": sentence,
            })
    return {"facts": facts[:5]}


def extract_facts(transcript: str, summary: str = "") -> list[FactDraft]:
    result = complete_json(
        f"Entry:\n{transcript}\n\nSummary:\n{summary}",
        system=SYSTEM,
        schema=FACTS_SCHEMA,
        fallback=lambda: _fallback(transcript),
        agent="Extractor",
    )
    drafts = []
    for raw in result.get("facts", []):
        if raw.get("type") not in {"preference", "event", "state", "plan", "person", "date"}:
            continue
        drafts.append(
            FactDraft(
                type=raw["type"],
                content=str(raw.get("content", "")).strip(),
                structured=raw.get("structured") or {},
                source_quote=raw.get("source_quote"),
            )
        )
    return [d for d in drafts if d.content][:6]
