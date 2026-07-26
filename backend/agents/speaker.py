"""Speaker: Deepgram Aura text-to-speech — the warm voice that reads the
Companion's answers aloud. Returns MP3 bytes, or None when speech can't be
produced (no key, unsupported language, or the service failed) so the client
falls back to the browser's built-in voice."""
import logging

import httpx

from config import settings

logger = logging.getLogger("aangan.speaker")

_ENDPOINT = "https://api.deepgram.com/v1/speak"
# Aura voices are English-only today. For other languages we return None and
# the frontend uses the browser voice, so nothing breaks for Hindi.
_SUPPORTED_LANGS = {"en"}
# Aura caps a single request; answers are short, but guard anyway.
_MAX_CHARS = 1900


def synthesize(text: str, language: str = "en") -> bytes | None:
    text = (text or "").strip()
    if not text:
        return None
    if not settings.deepgram_api_key:
        return None
    if (language or "en")[:2] not in _SUPPORTED_LANGS:
        return None
    if len(text) > _MAX_CHARS:
        text = text[:_MAX_CHARS]
    try:
        response = httpx.post(
            _ENDPOINT,
            params={"model": settings.deepgram_tts_model, "encoding": "mp3"},
            headers={
                "Authorization": f"Token {settings.deepgram_api_key}",
                "Content-Type": "application/json",
            },
            json={"text": text},
            timeout=30.0,
        )
        if response.status_code != 200:
            logger.warning(
                "deepgram tts %s: %s", response.status_code, response.text[:200]
            )
            return None
        audio = response.content
        return audio or None
    except Exception as exc:  # network/timeout — fall back to browser voice
        logger.warning("deepgram tts failed: %s", exc)
        return None
