"""Transcriber: Deepgram speech to text with language auto-detection."""
from dataclasses import dataclass

from config import settings


class TranscriptionUnavailable(Exception):
    """No Deepgram key (or the service failed) — the route turns this into a
    friendly 503 and the client offers typing instead."""


@dataclass
class Transcription:
    text: str
    language: str
    duration_sec: int


def transcribe(audio_path: str) -> Transcription:
    if not settings.deepgram_api_key:
        raise TranscriptionUnavailable(
            "Voice transcription isn't set up yet (add DEEPGRAM_API_KEY to backend/.env). "
            "You can type your entry instead."
        )
    try:
        from deepgram import DeepgramClient

        client = DeepgramClient(api_key=settings.deepgram_api_key)
        with open(audio_path, "rb") as f:
            response = client.listen.v1.media.transcribe_file(
                request=f.read(),
                model="nova-3",
                detect_language=True,
                smart_format=True,
            )
        channel = response.results.channels[0]
        alternative = channel.alternatives[0]
        text = (alternative.transcript or "").strip()
        if not text:
            raise TranscriptionUnavailable(
                "I couldn't hear anything in that recording — try again a little closer to the mic?"
            )
        language = (getattr(channel, "detected_language", None) or "en")[:2]
        duration = int(getattr(response.metadata, "duration", 0) or 0)
        return Transcription(text=text, language=language, duration_sec=duration)
    except TranscriptionUnavailable:
        raise
    except Exception as exc:
        import logging

        logging.getLogger("aangan.transcriber").warning("deepgram failed: %s", exc)
        raise TranscriptionUnavailable(
            "Transcription didn't work just now. You can type your entry instead."
        ) from exc
