"""POST /ask: grounded, visibility-scoped answers. A member's private entry
never appears in any other member's ask, by any phrasing."""
import pytest

from models import Relationship, Visibility
from tests.conftest import auth_headers, make_entry

MARKER = "zanzibar sapphire"

PHRASINGS = [
    "What did Deepa write today?",
    "How was Deepa's day?",
    "Tell me everything about Deepa.",
    "zanzibar sapphire",
    "What secret is Deepa keeping?",
    "दीपा का दिन कैसा था?",
]


def ask(client, user, question):
    resp = client.post("/ask", json={"question": question}, headers=auth_headers(user))
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.mark.parametrize("phrasing", PHRASINGS)
def test_private_entry_never_leaks_by_any_phrasing(client, db, family, phrasing):
    make_entry(
        db, family.deepa, family.circle,
        f"Today I hid the {MARKER} necklace for a surprise.",
        facts=[{"type": "event", "content": f"hid the {MARKER} necklace"}],
    )
    body = ask(client, family.aditya, phrasing)
    assert MARKER not in body["answer"]
    assert all(MARKER not in s["text"] for s in body["snippets"])


def test_birthday_question_returns_shared_dress_with_date(client, db, family):
    make_entry(
        db, family.deepa, family.circle,
        "Saw a beautiful black dress at H&M today, I could not stop thinking about it.",
        visibility=Visibility.circle,
        facts=[{
            "type": "preference",
            "content": "Deepa loved a black dress at H&M",
            "structured": {"item": "dress", "brand": "H&M", "sentiment": "loved", "tags": ["gift"]},
            "visibility": Visibility.circle,
        }],
    )
    body = ask(client, family.aditya, "What would Deepa want for her birthday?")
    assert "black dress" in body["answer"].lower() or any(
        "black dress" in s["text"].lower() for s in body["snippets"]
    )
    assert body["snippets"], "answer must be grounded in shared snippets"


def test_nothing_shared_is_a_kind_answer(client, db, family):
    body = ask(client, family.abhishek, "What does Mumma want for Diwali?")
    assert body["snippets"] == []
    assert body["answer"]  # kind, non-empty
    assert "shared" in body["answer"].lower() or "साझा" in body["answer"]


def test_hindi_speaker_gets_hindi_nothing_shared(client, db, family):
    body = ask(client, family.mumma, "बच्चों का क्या हाल है?")
    assert body["snippets"] == []
    assert "साझा" in body["answer"]


def test_relationship_labels_available_to_companion(client, db, family):
    db.add(Relationship(
        circle_id=family.circle.id,
        from_user_id=family.aditya.id,
        to_user_id=family.deepa.id,
        label="wife",
    ))
    db.commit()
    make_entry(
        db, family.deepa, family.circle,
        "I am so excited for the pottery class next week!",
        visibility=Visibility.circle,
        facts=[{
            "type": "plan",
            "content": "Deepa is excited for a pottery class next week",
            "visibility": Visibility.circle,
        }],
    )
    body = ask(client, family.aditya, "What is Deepa excited about?")
    assert "pottery" in body["answer"].lower() or any(
        "pottery" in s["text"].lower() for s in body["snippets"]
    )


def test_ask_requires_a_question(client, family):
    resp = client.post("/ask", json={}, headers=auth_headers(family.aditya))
    assert resp.status_code == 422
