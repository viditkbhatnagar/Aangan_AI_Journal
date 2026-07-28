"""Speaker: the warm voice that reads the Companion's replies aloud.

Provider chain (same signature as ever — synthesize(text, language) -> bytes
or None, and None means "browser voice, please"):

1. English → Deepgram Aura (unchanged; Aura voices are English-only today).
2. Other languages (Hindi first among them) → OpenAI TTS (gpt-4o-mini-tts),
   which speaks Hindi warmly. ONLY when the OpenAI key talks to
   api.openai.com — OpenRouter does NOT proxy /v1/audio/speech, so an
   OpenRouter-gatewayed key skips this hop (logged once, never an error).
3. Anything else → None → the frontend falls back to the browser voice, so
   speech never simply goes silent.
"""
import logging

import httpx

from config import settings

logger = logging.getLogger("aangan.speaker")

# One reused client with keep-alive, so every synth after the first skips the
# DNS + TCP + TLS handshake to the TTS host — noticeably faster read-aloud.
_client = httpx.Client(timeout=30.0)

_AURA_ENDPOINT = "https://api.deepgram.com/v1/speak"
_OPENAI_TTS_ENDPOINT = "https://api.openai.com/v1/audio/speech"
_OPENAI_TTS_MODEL = "gpt-4o-mini-tts"
_OPENAI_TTS_VOICE = "coral"  # warm, gentle
_OPENAI_TTS_INSTRUCTIONS = (
    "Speak warmly and gently, like a beloved family member reading a note "
    "aloud at home — unhurried, soft, full of affection. Never clinical."
)
# Aura voices are English-only today; everything else goes to hop 2.
_AURA_LANGS = {"en"}
# Both services cap a single request; answers are short, but guard anyway.
_MAX_CHARS = 1900

_warned_openrouter_tts = False  # log the skip once per process, not per call


def _aura(text: str) -> bytes | None:
    if not settings.deepgram_api_key:
        return None
    try:
        response = _client.post(
            _AURA_ENDPOINT,
            params={"model": settings.deepgram_tts_model, "encoding": "mp3"},
            headers={
                "Authorization": f"Token {settings.deepgram_api_key}",
                "Content-Type": "application/json",
            },
            json={"text": text},
            timeout=30.0,
        )
        if response.status_code != 200:
            logger.warning("deepgram tts %s: %s", response.status_code, response.text[:200])
            return None
        return response.content or None
    except Exception as exc:  # network/timeout — fall back to browser voice
        logger.warning("deepgram tts failed: %s", exc)
        return None


def _openai_tts_usable() -> bool:
    """A direct-OpenAI key only. OpenRouter (or any other gateway in
    OPENAI_BASE_URL) does not proxy the audio/speech endpoint."""
    global _warned_openrouter_tts
    if not settings.openai_api_key:
        return False
    base = (settings.openai_base_url or "").strip()
    if not base or "api.openai.com" in base:
        return True
    if not _warned_openrouter_tts:
        logger.info(
            "OPENAI_BASE_URL points at a gateway (%s) that has no TTS endpoint — "
            "non-English replies will use the browser voice.", base
        )
        _warned_openrouter_tts = True
    return False


def _openai_tts(text: str) -> bytes | None:
    if not _openai_tts_usable():
        return None
    try:
        response = _client.post(
            _OPENAI_TTS_ENDPOINT,
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": _OPENAI_TTS_MODEL,
                "voice": _OPENAI_TTS_VOICE,
                "input": text,
                "response_format": "mp3",
                "instructions": _OPENAI_TTS_INSTRUCTIONS,
            },
            timeout=30.0,
        )
        if response.status_code != 200:
            logger.warning("openai tts %s: %s", response.status_code, response.text[:200])
            return None
        return response.content or None
    except Exception as exc:
        logger.warning("openai tts failed: %s", exc)
        return None


def synthesize(text: str, language: str = "en") -> bytes | None:
    text = (text or "").strip()
    if not text:
        return None
    if len(text) > _MAX_CHARS:
        text = text[:_MAX_CHARS]
    if (language or "en")[:2] in _AURA_LANGS:
        return _aura(text)
    return _openai_tts(text)
