"""App settings. Every field has a default so a fresh clone runs with no .env at all."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    # base_url lets any OpenAI-compatible gateway serve the same code —
    # e.g. https://openrouter.ai/api/v1 (models then look like openai/gpt-5.4-mini)
    openai_base_url: str | None = None
    # preferred model; llm.py falls back through OPENAI_CANDIDATES if this one
    # isn't available to the account
    openai_model: str = "gpt-5.4-mini"
    deepgram_api_key: str | None = None
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    database_url: str = f"sqlite:///{BACKEND_DIR / 'aangan.db'}"
    chroma_path: str = str(BACKEND_DIR / "chroma_data")

    audio_dir: str = str(BACKEND_DIR / "data" / "audio")
    actions_dir: str = str(BACKEND_DIR / "data" / "actions")

    # Model tiers for the reasoning agents. Fast tier does summarize/extract/word
    # alerts; chat tier is the Companion's voice. Both env-overridable.
    model_fast: str = "claude-opus-4-8"
    model_chat: str = "claude-opus-4-8"

    # Doer defaults: a public demo store where the cart works without login, so
    # the no-credentials rule is never even tempted.
    doer_purchase_site: str = "https://www.demoblaze.com"
    doer_headless: bool = True

    # Anti alert-fatigue: max alerts per recipient per day.
    alert_daily_cap: int = 5


settings = Settings()
