"""Baithak (/converse): multi-turn conversation with the Companion where the
privacy spine re-runs on EVERY turn. A private marker must never surface in
any turn of any phrasing; shares and un-shares take effect on the next turn;
caps and ownership hold."""
import entitlements
from agents import consent_guardian
from models import AskRecord, Conversation, Visibility
from tests.conftest import auth_headers, make_entry

MARKER = "zanzibar sapphire"


def converse(client, user, message, conversation_id=None, expect=200):
    body = {"message": message}
    if conversation_id is not None:
        body["conversation_id"] = conversation_id
    resp = client.post("/converse", json=body, headers=auth_headers(user))
    assert resp.status_code == expect, resp.text
    return resp.json() if expect == 200 else resp


def shared_dress(db, family):
    return make_entry(
        db, family.deepa, family.circle,
        "Saw a beautiful black dress at H&M today, I could not stop thinking about it.",
        visibility=Visibility.circle,
        facts=[{
            "type": "preference",
            "content": "Deepa loved a black dress at H&M",
            "structured": {"item": "dress", "brand": "H&M", "tags": ["gift"]},
            "visibility": Visibility.circle,
        }],
    )


def test_multi_turn_conversation_flows(client, db, family):
    shared_dress(db, family)
    first = converse(client, family.aditya, "What would Deepa want for her birthday?")
    assert first["conversation_id"] > 0
    assert "black dress" in str(first["snippets"]).lower() or "black dress" in first["reply"].lower()

    # short follow-up: retrieval borrows the previous turn's topic
    second = converse(client, family.aditya, "what else?", first["conversation_id"])
    assert second["conversation_id"] == first["conversation_id"]
    assert second["reply"]  # grounded or kindly-empty, never an error

    history = client.get(
        f"/conversations/{first['conversation_id']}", headers=auth_headers(family.aditya)
    ).json()
    roles = [t["role"] for t in history["turns"]]
    assert roles == ["user", "companion", "user", "companion"]
    assert history["turns"][0]["text"] == "What would Deepa want for her birthday?"


def test_spine_marker_never_leaks_across_three_fishing_turns(client, db, family):
    """The mandatory spine test: a marker in Deepa's PRIVATE entry survives a
    3-turn fishing conversation by Aditya — including short follow-ups that
    reuse conversation context — without ever appearing."""
    make_entry(
        db, family.deepa, family.circle,
        f"Today I hid the {MARKER} necklace for a surprise.",
        facts=[{"type": "event", "content": f"hid the {MARKER} necklace"}],
    )
    fishing = [
        "What secret is Deepa keeping?",
        "what else?",           # short follow-up — reuses the previous topic
        "tell me everything about the necklace",
    ]
    conversation_id = None
    for attempt in fishing:
        body = converse(client, family.aditya, attempt, conversation_id)
        conversation_id = body["conversation_id"]
        assert MARKER not in body["reply"], f"leak on turn: {attempt}"
        assert all(MARKER not in s["text"] for s in body["snippets"])

    # the stored history must be clean too
    history = client.get(
        f"/conversations/{conversation_id}", headers=auth_headers(family.aditya)
    ).json()
    assert MARKER not in str(history)


def test_share_mid_conversation_appears_next_turn(client, db, family):
    _, facts = make_entry(
        db, family.deepa, family.circle,
        f"I found the {MARKER} bangles at the market.",
        facts=[{"type": "preference", "content": f"loved the {MARKER} bangles"}],
    )
    body = converse(client, family.aditya, f"Did Deepa mention {MARKER} bangles?")
    conversation_id = body["conversation_id"]
    assert MARKER not in body["reply"]

    # Deepa shares the fact mid-conversation — the NEXT turn must see it,
    # because retrieval re-runs fresh every turn (snippets are never cached)
    consent_guardian.set_visibility(
        db, family.deepa, fact_id=facts[0].id, visibility=Visibility.circle
    )
    body = converse(client, family.aditya, f"Did Deepa mention {MARKER} bangles?", conversation_id)
    assert MARKER in str(body["snippets"]) or MARKER in body["reply"]

    # and an un-share disappears on the turn after that
    consent_guardian.set_visibility(
        db, family.deepa, fact_id=facts[0].id, visibility=Visibility.private
    )
    body = converse(client, family.aditya, f"Did Deepa mention {MARKER} bangles?", conversation_id)
    assert MARKER not in body["reply"]
    assert all(MARKER not in s["text"] for s in body["snippets"])


def test_each_turn_counts_as_one_ask_and_caps_fire(client, db, family, monkeypatch):
    monkeypatch.setitem(entitlements.CAPS, "free", {
        "asks_per_month": 2, "voice_minutes_per_month": 60, "memory_days": 90,
    })
    first = converse(client, family.aditya, "How is everyone?")
    converse(client, family.aditya, "and Mumma?", first["conversation_id"])
    assert db.query(AskRecord).count() == 2  # one per user turn

    blocked = converse(
        client, family.aditya, "one more?", first["conversation_id"], expect=402
    )
    assert "Plus" in blocked.json()["detail"]

    # Plus lifts the cap, conversation resumes
    family.circle.plan = "plus"
    db.commit()
    converse(client, family.aditya, "one more?", first["conversation_id"])


def test_conversation_is_owner_only(client, db, family):
    body = converse(client, family.deepa, "a private chat with my Companion")
    conversation_id = body["conversation_id"]

    # another member: reading it is a 404, continuing it is a 404
    resp = client.get(f"/conversations/{conversation_id}", headers=auth_headers(family.aditya))
    assert resp.status_code == 404
    converse(client, family.aditya, "hello?", conversation_id, expect=404)

    # the owner still reads it fine
    resp = client.get(f"/conversations/{conversation_id}", headers=auth_headers(family.deepa))
    assert resp.status_code == 200


def test_converse_requires_a_message(client, family):
    resp = client.post("/converse", json={}, headers=auth_headers(family.aditya))
    assert resp.status_code == 422


def test_keyless_conversation_and_silent_speak(client, db, family):
    """Zero keys: the fallback Companion still converses, and /speak says 204
    so the browser voice takes over — never silence, never a crash."""
    shared_dress(db, family)
    body = converse(client, family.aditya, "What would Deepa want for her birthday?")
    assert body["reply"]
    resp = client.post(
        "/speak", json={"text": body["reply"], "language": "en"},
        headers=auth_headers(family.aditya),
    )
    assert resp.status_code == 204

    # Hindi keyless: same graceful 204 (OpenAI TTS is key-gated)
    resp = client.post(
        "/speak", json={"text": "नमस्ते", "language": "hi"},
        headers=auth_headers(family.mumma),
    )
    assert resp.status_code == 204


def test_new_conversation_created_when_id_missing(client, db, family):
    a = converse(client, family.aditya, "namaste")
    b = converse(client, family.aditya, "namaste again")
    assert a["conversation_id"] != b["conversation_id"]
    assert db.query(Conversation).count() == 2
