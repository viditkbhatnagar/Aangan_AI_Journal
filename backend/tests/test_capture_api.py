"""Capture pipeline through the API: upload/type an entry, get it transcribed
(or typed), summarized, turned into private facts, with share prompts."""
import io

from tests.conftest import auth_headers


def post_entry(client, user, text):
    return client.post("/entries", data={"transcript": text}, headers=auth_headers(user))


def test_typed_entry_creates_private_entry_and_facts(client, family):
    resp = post_entry(
        client, family.deepa,
        "Saw a beautiful black dress at H&M today, I could not stop thinking about it.",
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["entry"]["visibility"] == "private"
    assert body["entry"]["summary"]
    facts = body["entry"]["facts"]
    assert facts and all(f["visibility"] == "private" for f in facts)
    assert any(f["type"] == "preference" for f in facts)
    # the guardian proposes, never decides
    assert body["share_suggestions"]


def test_entry_requires_audio_or_text(client, family):
    resp = client.post("/entries", data={}, headers=auth_headers(family.deepa))
    assert resp.status_code == 422


def test_audio_without_deepgram_key_returns_friendly_503(client, family):
    resp = client.post(
        "/entries",
        files={"audio": ("entry.webm", io.BytesIO(b"fake-audio"), "audio/webm")},
        headers=auth_headers(family.deepa),
    )
    assert resp.status_code == 503
    assert "type" in resp.json()["detail"].lower()


def test_entries_list_is_own_only(client, family):
    post_entry(client, family.deepa, "A private little note about the zanzibar sapphire.")
    resp = client.get("/entries", headers=auth_headers(family.aditya))
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_other_members_entry_is_404(client, family):
    created = post_entry(client, family.deepa, "my own words").json()["entry"]
    resp = client.get(f"/entries/{created['id']}", headers=auth_headers(family.aditya))
    assert resp.status_code == 404


def test_share_endpoint_author_only(client, family):
    created = post_entry(
        client, family.deepa, "I loved the little clay diya from the market."
    ).json()["entry"]
    entry_id = created["id"]

    stranger = client.post(
        f"/entries/{entry_id}/share",
        json={"visibility": "circle"},
        headers=auth_headers(family.abhishek),
    )
    assert stranger.status_code == 403

    author = client.post(
        f"/entries/{entry_id}/share",
        json={"visibility": "circle"},
        headers=auth_headers(family.deepa),
    )
    assert author.status_code == 200
    assert author.json()["visibility"] == "circle"


def test_share_single_fact_leaves_entry_private(client, family):
    body = post_entry(
        client, family.deepa, "I loved the black dress at H&M so much."
    ).json()
    entry = body["entry"]
    fact_id = entry["facts"][0]["id"]

    resp = client.post(
        f"/entries/{entry['id']}/share",
        json={"fact_id": fact_id, "visibility": "circle"},
        headers=auth_headers(family.deepa),
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["visibility"] == "private"  # parent entry untouched
    assert [f for f in updated["facts"] if f["id"] == fact_id][0]["visibility"] == "circle"


def test_share_rule_applies_on_capture(client, family):
    rule = client.post(
        "/share-rules",
        json={
            "description": "share my gift ideas with the family",
            "match": {"type": "preference", "tag": "gift"},
            "audience": "all",
        },
        headers=auth_headers(family.deepa),
    )
    assert rule.status_code == 200

    body = post_entry(
        client, family.deepa, "I loved a beautiful silver jhumka at the bazaar."
    ).json()
    assert "share my gift ideas with the family" in body["applied_rules"]
    prefs = [f for f in body["entry"]["facts"] if f["type"] == "preference"]
    assert prefs and prefs[0]["visibility"] == "circle"
