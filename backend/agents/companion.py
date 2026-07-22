"""Companion: the one warm face of the app. Composes answers ONLY from what
the Librarian returned — it never invents facts, and when nothing is visible
it says so kindly."""
from agents.librarian import Snippet
from agents.llm import complete
from config import settings
from models import User

NOTHING_SHARED = {
    "en": (
        "I don't have anything shared about that yet. "
        "Maybe gently ask them yourself — or invite them to share it here. 🪔"
    ),
    "hi": (
        "इस बारे में अभी तक कुछ साझा नहीं हुआ है। "
        "शायद आप खुद प्यार से पूछ लें — या उन्हें यहाँ साझा करने के लिए कहें। 🪔"
    ),
}

SYSTEM = (
    "You are the Companion of Aangan, a private family journal app. You answer a "
    "family member's question using ONLY the shared journal snippets provided — "
    "never invent, never add outside knowledge about the family. Mention when "
    "things were said (e.g. 'back in January'). Be warm, gentle, and plain-spoken; "
    "1-3 short sentences. Use the relationship words given (e.g. 'your wife Deepa'). "
    "Answer in the language requested. If the snippets don't answer the question, "
    "say kindly that nothing has been shared about it."
)


def _fallback_answer(user: User, snippets: list[Snippet], relationships: dict[int, str]) -> str:
    if not snippets:
        return NOTHING_SHARED.get(user.language[:2], NOTHING_SHARED["en"])
    lines = []
    for snippet in snippets[:3]:
        who = relationships.get(snippet.author_id)
        name = f"your {who} {snippet.author_name}" if who else snippet.author_name
        when = snippet.created_at.strftime("%d %b %Y")
        lines.append(f"{name} shared on {when}: “{snippet.text}”")
    return "Here is what has been shared — " + " ".join(lines)


def compose_answer(
    user: User,
    question: str,
    snippets: list[Snippet],
    relationships: dict[int, str],
    answer_language: str | None = None,
) -> str:
    language = (answer_language or user.language or "en")[:2]
    if not snippets:
        return NOTHING_SHARED.get(language, NOTHING_SHARED["en"])

    context_lines = []
    for snippet in snippets:
        who = relationships.get(snippet.author_id)
        name = f"{snippet.author_name} ({user.name}'s {who})" if who else snippet.author_name
        context_lines.append(
            f"- [{snippet.created_at.strftime('%Y-%m-%d')}] {name} ({snippet.source}): {snippet.text}"
        )
    prompt = (
        f"Question from {user.name} (answer in language '{language}'):\n{question}\n\n"
        f"Shared snippets they are allowed to see:\n" + "\n".join(context_lines)
    )
    return complete(
        prompt,
        system=SYSTEM,
        model=settings.model_chat,
        fallback=lambda: _fallback_answer(user, snippets, relationships),
    )
