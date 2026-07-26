"""Text-to-speech: the Companion's warm voice (Deepgram Aura). Returns MP3
audio, or 204 No Content when speech isn't available so the client falls back
to the browser's built-in voice."""
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from agents import speaker
from auth import get_current_user
from models import User

router = APIRouter(tags=["speak"])


class SpeakIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    language: str = "en"


@router.post("/speak")
def speak(body: SpeakIn, user: User = Depends(get_current_user)):
    audio = speaker.synthesize(body.text, body.language)
    if not audio:
        return Response(status_code=204)
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-store"},
    )
