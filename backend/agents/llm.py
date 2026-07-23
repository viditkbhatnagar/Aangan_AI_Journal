"""Shared LLM helper. Providers, in order of preference:

1. OpenAI  (OPENAI_API_KEY; model OPENAI_MODEL, falling back through
   OPENAI_CANDIDATES if the preferred one isn't available to the account)
2. Anthropic (ANTHROPIC_API_KEY)
3. Deterministic local fallback — every agent passes one, so the whole app
   keeps working with no keys at all.
"""
import json
import logging
import re
import time
from collections.abc import Callable

from config import settings
from services import metering

_logger = logging.getLogger("aangan.llm")

_anthropic_client = None
_openai_client = None
_openai_model: str | None = None  # resolved working model, cached
_openai_disabled = False  # set on auth failure so we don't retry every call

OPENAI_CANDIDATES = [
    # OpenRouter-style ids first (used when OPENAI_BASE_URL points there),
    # then direct-OpenAI ids
    "openai/gpt-5.4-nano",
    "openai/gpt-5-mini",
    "openai/gpt-4o-mini",
    "gpt-5-mini",
    "gpt-5-nano",
    "gpt-4o-mini",
]


def _get_openai():
    global _openai_client
    if _openai_client is None and settings.openai_api_key and not _openai_disabled:
        from openai import OpenAI

        _openai_client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url or None,
        )
    return None if _openai_disabled else _openai_client


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None and settings.anthropic_api_key:
        import anthropic

        _anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def llm_available() -> bool:
    return bool(settings.openai_api_key or settings.anthropic_api_key)


def _openai_complete(prompt: str, system: str, max_tokens: int, agent: str) -> str | None:
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
        started = time.monotonic()
        try:
            # chat.completions works on both api.openai.com and OpenAI-compatible
            # gateways (OpenRouter). No token cap: max_tokens vs
            # max_completion_tokens differs between them, and replies are short.
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            )
            text = (response.choices[0].message.content or "").strip()
            if text:
                _openai_model = model
                usage = getattr(response, "usage", None)
                metering.record_llm(
                    agent, "openai", model,
                    getattr(usage, "prompt_tokens", 0) or 0,
                    getattr(usage, "completion_tokens", 0) or 0,
                    int((time.monotonic() - started) * 1000),
                )
                metering.last_provenance = {"provider": "openai", "model": model}
                return text
            return None
        except AuthenticationError:
            _openai_disabled = True  # bad key: stop trying on every call
            _logger.warning("openai auth failed — provider disabled for this process")
            return None
        except (NotFoundError, BadRequestError):
            continue  # model not available to this account — try the next
        except Exception as exc:
            _logger.warning("openai call failed (%s): %s", model, exc)
            return None
    return None


def _anthropic_complete(
    prompt: str, system: str, model: str | None, max_tokens: int, agent: str
) -> str | None:
    client = _get_anthropic()
    if client is None:
        return None
    started = time.monotonic()
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
        if text.strip():
            usage = getattr(response, "usage", None)
            metering.record_llm(
                agent, "anthropic", model or settings.model_fast,
                getattr(usage, "input_tokens", 0) or 0,
                getattr(usage, "output_tokens", 0) or 0,
                int((time.monotonic() - started) * 1000),
            )
            metering.last_provenance = {"provider": "anthropic", "model": model or settings.model_fast}
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
    agent: str = "agent",
) -> str:
    text = _openai_complete(prompt, system, max_tokens, agent)
    if text is None:
        text = _anthropic_complete(prompt, system, model, max_tokens, agent)
    if text:
        return text
    metering.record_llm(agent, "fallback", None, 0, 0, 0)
    metering.last_provenance = {"provider": "fallback", "model": None}
    return fallback()


_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.M)


def complete_json(
    prompt: str,
    *,
    system: str,
    schema: dict,
    fallback: Callable[[], dict | list],
    model: str | None = None,
    max_tokens: int = 2048,
    agent: str = "agent",
) -> dict | list:
    """Structured completion. OpenAI path asks for JSON matching the schema and
    parses it; Anthropic path uses output_config json_schema. Any failure
    returns the deterministic fallback."""
    json_system = (
        system
        + "\nReply with ONLY a JSON object matching this JSON schema — no prose, no code fences:\n"
        + json.dumps(schema)
    )
    text = _openai_complete(prompt, json_system, max_tokens, agent)
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
    metering.record_llm(agent, "fallback", None, 0, 0, 0)
    metering.last_provenance = {"provider": "fallback", "model": None}
    return fallback()


def reset_for_tests() -> None:
    """Drop cached clients/flags so tests always run in fallback mode."""
    global _anthropic_client, _openai_client, _openai_model, _openai_disabled
    _anthropic_client = None
    _openai_client = None
    _openai_model = None
    _openai_disabled = False
