"""Speaker provider chain: English → Aura; other languages → OpenAI TTS only
with a DIRECT OpenAI key (OpenRouter has no audio endpoint); else None so the
browser voice takes over."""
from agents import speaker
from config import settings


def test_keyless_returns_none_for_all_languages():
    assert speaker.synthesize("hello", "en") is None
    assert speaker.synthesize("नमस्ते", "hi") is None


def test_empty_text_returns_none():
    assert speaker.synthesize("   ", "en") is None


def test_openai_tts_gated_off_for_openrouter_keys(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-or-v1-fake")
    monkeypatch.setattr(settings, "openai_base_url", "https://openrouter.ai/api/v1")
    monkeypatch.setattr(speaker, "_warned_openrouter_tts", False)
    assert not speaker._openai_tts_usable()
    # and the full call degrades to None (browser voice), never an HTTP attempt
    assert speaker.synthesize("नमस्ते", "hi") is None


def test_openai_tts_usable_with_direct_key(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-fake")
    monkeypatch.setattr(settings, "openai_base_url", None)
    assert speaker._openai_tts_usable()
    monkeypatch.setattr(settings, "openai_base_url", "https://api.openai.com/v1")
    assert speaker._openai_tts_usable()


def test_hindi_goes_to_openai_tts_english_goes_to_aura(monkeypatch):
    calls = []
    monkeypatch.setattr(speaker, "_aura", lambda text: calls.append("aura") or b"mp3a")
    monkeypatch.setattr(speaker, "_openai_tts", lambda text: calls.append("openai") or b"mp3b")
    assert speaker.synthesize("hello", "en") == b"mp3a"
    assert speaker.synthesize("नमस्ते", "hi") == b"mp3b"
    assert calls == ["aura", "openai"]
