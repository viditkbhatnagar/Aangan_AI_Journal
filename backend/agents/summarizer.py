"""Summarizer: a clean summary plus 0-3 short shareable snippets, keeping the
author's meaning and voice. Deterministic fallback when no LLM key."""
import re
from dataclasses import dataclass, field

from agents.llm import complete_json

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "snippets": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "snippets"],
    "additionalProperties": False,
}

SYSTEM = (
    "You summarize private family journal entries. Keep the author's meaning and "
    "voice; be warm and plain. Reply in the same language as the entry. "
    "Also pick 0 to 3 short snippets (a sentence each, close to the author's own "
    "words) that the author might want to share with family — happy moments, "
    "wishes, plans. Never invent anything."
)

POSITIVE_WORDS = {
    "love", "loved", "beautiful", "happy", "excited", "wonderful", "proud",
    "great", "enjoyed", "khush", "खुश", "सुंदर", "अच्छा", "मज़ा",
}


@dataclass
class Summary:
    summary: str
    snippets: list[str] = field(default_factory=list)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?।])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _fallback(transcript: str) -> dict:
    sentences = _sentences(transcript)
    summary = " ".join(sentences[:2]) if sentences else transcript.strip()
    snippets = [
        s for s in sentences if any(w in s.lower() for w in POSITIVE_WORDS)
    ][:3]
    return {"summary": summary, "snippets": snippets}


def summarize(transcript: str, language: str = "en") -> Summary:
    result = complete_json(
        f"Journal entry (language: {language}):\n\n{transcript}",
        system=SYSTEM,
        schema=SUMMARY_SCHEMA,
        fallback=lambda: _fallback(transcript),
        agent="Summarizer",
    )
    return Summary(
        summary=str(result.get("summary") or transcript[:300]),
        snippets=[str(s) for s in (result.get("snippets") or [])][:3],
    )
