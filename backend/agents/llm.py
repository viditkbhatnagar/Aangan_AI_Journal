"""Shared LLM helper. Providers, in order of preference:

1. OpenAI  (OPENAI_API_KEY; model OPENAI_MODEL, falling back through
   OPENAI_CANDIDATES if the preferred one isn't available to the account)
2. Anthropic (ANTHROPIC_API_KEY)
3. Deterministic local fallback — every agent passes one, so the whole app
   keeps working with no keys at all.
"""
import json
import re
from collections.abc import Callable

from config import settings

_anthropic_client = None
_openai_client = None
_openai_model: str | None = None  # resolved working model, cached
_openai_disabled = False  # set on auth failure so we don't retry every call

OPENAI_CANDIDATES = ["gpt-5-mini", "gpt-5-nano", "gpt-5.1-mini", "gpt-4o-mini"]


def _get_openai():
    global _openai_client
    if _openai_client is None and settings.openai_api_key and not _openai_disabled:
        from openai import OpenAI

        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return None if _openai_disabled else _openai_client


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None and settings.anthropic_api_key:
        import anthropic

        _anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def llm_available() -> bool:
    return bool(settings.openai_api_key or settings.anthropic_api_key)


def _openai_complete(prompt: str, system: str, max_tokens: int) -> str | None:
    """Try the configured model, then fall back through candidates the account
    actually has. Returns None if OpenAI can't serve the request."""
    global _openai_model, _openai_disabled
    client = _get_openai()
    if client is None:
        return None

    from openai import AuthenticationError, BadRequestError, NotFoundError

    candidates = [_openai_model] if _openai_model else [settings.openai_model, *OPENAI_CANDIDATES]
    for model in candidates:
        if not model:
            continue
        try:
            response = client.responses.create(
                model=model,
                instructions=system,
                input=prompt,
                max_output_tokens=max(max_tokens, 512),  # reasoning models need headroom
            )
            text = (response.output_text or "").strip()
            if text:
                _openai_model = model
                return text
            return None
        except AuthenticationError:
            _openai_disabled = True  # bad key: stop trying on every call
            return None
        except (NotFoundError, BadRequestError):
            continue  # model not available to this account — try the next
        except Exception:
            return None
    return None


def _anthropic_complete(prompt: str, system: str, model: str | None, max_tokens: int) -> str | None:
    client = _get_anthropic()
    if client is None:
        return None
    try:
        response = client.messages.create(
            model=model or settings.model_fast,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        if response.stop_reason == "refusal":
            return None
        text = next((b.text for b in response.content if b.type == "text"), "")
        return text.strip() or None
    except Exception:
        return None


def complete(
    prompt: str,
    *,
    system: str,
    fallback: Callable[[], str],
    model: str | None = None,
    max_tokens: int = 1024,
) -> str:
    text = _openai_complete(prompt, system, max_tokens)
    if text is None:
        text = _anthropic_complete(prompt, system, model, max_tokens)
    return text if text else fallback()


_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.M)


def complete_json(
    prompt: str,
    *,
    system: str,
    schema: dict,
    fallback: Callable[[], dict | list],
    model: str | None = None,
    max_tokens: int = 2048,
) -> dict | list:
    """Structured completion. OpenAI path asks for JSON matching the schema and
    parses it; Anthropic path uses output_config json_schema. Any failure
    returns the deterministic fallback."""
    json_system = (
        system
        + "\nReply with ONLY a JSON object matching this JSON schema — no prose, no code fences:\n"
        + json.dumps(schema)
    )
    text = _openai_complete(prompt, json_system, max_tokens)
    if text is not None:
        try:
            return json.loads(_JSON_FENCE.sub("", text).strip())
        except ValueError:
            pass

    client = _get_anthropic()
    if client is not None:
        try:
            response = client.messages.create(
                model=model or settings.model_fast,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                output_config={"format": {"type": "json_schema", "schema": schema}},
            )
            if response.stop_reason != "refusal":
                text = next((b.text for b in response.content if b.type == "text"), "")
                return json.loads(text)
        except Exception:
            pass
    return fallback()


def reset_for_tests() -> None:
    """Drop cached clients/flags so tests always run in fallback mode."""
    global _anthropic_client, _openai_client, _openai_model, _openai_disabled
    _anthropic_client = None
    _openai_client = None
    _openai_model = None
    _openai_disabled = False
