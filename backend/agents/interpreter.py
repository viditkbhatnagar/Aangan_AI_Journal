"""Interpreter: language bridge and tone. Log in Hindi, ask in English, and
back. Passthrough fallback when no LLM key (content is already grounded)."""
from agents.llm import complete


def bridge(text: str, source_lang: str, target_lang: str) -> str:
    if not text or source_lang[:2] == target_lang[:2]:
        return text
    return complete(
        text,
        system=(
            f"Translate the user's text from '{source_lang}' to '{target_lang}'. "
            "Keep it warm, plain, and faithful — no additions, no commentary. "
            "Return only the translation."
        ),
        fallback=lambda: text,
    )
