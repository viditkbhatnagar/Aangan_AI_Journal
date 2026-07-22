"""Agent activity feed (scoped to the requester) and journal action-intent
detection (drafts an action, never runs it without approval)."""
from agents import doer
from tests.conftest import auth_headers


def test_intent_detection_positive_and_negative():
    assert doer.detect_action_intent(
        "I want to order chocolates for my husband. You do it."
    ).startswith("I want to order chocolates")
    assert doer.detect_action_intent("आज अच्छा दिन था। मिठाई मंगवा दो।") is not None
    # feelings and shopping stories are NOT delegations
    assert doer.detect_action_intent("I ordered chocolates yesterday, they were lovely.") is None
    assert doer.detect_action_intent("A quiet day, made poha and read a book.") is None


def test_journal_delegation_drafts_action_awaiting_approval(client, family):
    resp = client.post(
        "/entries",
        data={"transcript": "I want to order chocolates for my husband. You do it."},
        headers=auth_headers(family.deepa),
    )
    assert resp.status_code == 200
    action = resp.json()["suggested_action"]
    assert action is not None
    assert action["status"] == "awaiting_approval"  # drafted, NOT executed
    assert action["result"] is None
    assert "chocolate" in action["intent"].lower()

    # and it belongs to Deepa — visible in her actions list, not others'
    mine = client.get("/actions", headers=auth_headers(family.deepa)).json()
    assert any(a["id"] == action["id"] for a in mine)
    others = client.get("/actions", headers=auth_headers(family.aditya)).json()
    assert all(a["id"] != action["id"] for a in others)


def test_plain_entry_suggests_no_action(client, family):
    resp = client.post(
        "/entries",
        data={"transcript": "A calm evening. We watched the rain from the balcony."},
        headers=auth_headers(family.deepa),
    )
    assert resp.json()["suggested_action"] is None


def test_activity_feed_is_scoped_to_requester(client, family):
    client.post(
        "/entries",
        data={"transcript": "I loved the little clay diya at the market."},
        headers=auth_headers(family.deepa),
    )
    deepa_feed = client.get("/activity", headers=auth_headers(family.deepa)).json()["events"]
    assert deepa_feed, "the author sees her own pipeline at work"
    agents_seen = {e["agent"] for e in deepa_feed}
    assert {"Summarizer", "Extractor", "Librarian"} <= agents_seen

    aditya_feed = client.get("/activity", headers=auth_headers(family.aditya)).json()["events"]
    assert aditya_feed == []  # never anyone else's activity


def test_activity_incremental_after_param(client, family):
    client.post("/entries", data={"transcript": "pehla note"}, headers=auth_headers(family.mumma))
    feed = client.get("/activity", headers=auth_headers(family.mumma)).json()["events"]
    last_id = feed[-1]["id"]
    again = client.get(f"/activity?after={last_id}", headers=auth_headers(family.mumma)).json()["events"]
    assert again == []
