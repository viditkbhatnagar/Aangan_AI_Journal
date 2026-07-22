"""Shared Anthropic helper. Every reasoning agent goes through complete():
when ANTHROPIC_API_KEY is missing or the API errors, the deterministic
fallback keeps the whole app usable offline."""
import json
from collections.abc import Callable

from config import settings

_client = None


def _get_client():
    global _client
    if _client is None and settings.anthropic_api_key:
        import anthropic

        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def llm_available() -> bool:
    return bool(settings.anthropic_api_key)


def complete(
    prompt: str,
    *,
    system: str,
    fallback: Callable[[], str],
    model: str | None = None,
    max_tokens: int = 1024,
) -> str:
    client = _get_client()
    if client is None:
        return fallback()
    try:
        response = client.messages.create(
            model=model or settings.model_fast,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        if response.stop_reason == "refusal":
            return fallback()
        text = next((b.text for b in response.content if b.type == "text"), "")
        return text.strip() or fallback()
    except Exception:
        return fallback()


def complete_json(
    prompt: str,
    *,
    system: str,
    schema: dict,
    fallback: Callable[[], dict | list],
    model: str | None = None,
    max_tokens: int = 2048,
) -> dict | list:
    """Structured completion via output_config json_schema; falls back to the
    deterministic result on any failure."""
    client = _get_client()
    if client is None:
        return fallback()
    try:
        response = client.messages.create(
            model=model or settings.model_fast,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        if response.stop_reason == "refusal":
            return fallback()
        text = next((b.text for b in response.content if b.type == "text"), "")
        return json.loads(text)
    except Exception:
        return fallback()
