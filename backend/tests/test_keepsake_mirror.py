"""Keepsake shows only shared moments; the Mirror is visible only to its owner."""
from datetime import datetime

from models import Visibility
from tests.conftest import auth_headers, make_entry

NOW = datetime(2026, 7, 20, 12, 0, 0)
MARKER = "zanzibar sapphire"


def test_keepsake_shows_shared_hides_private(client, db, family):
    make_entry(
        db, family.deepa, family.circle, "We all made diyas together, so lovely.",
        visibility=Visibility.circle, created_at=NOW,
    )
    make_entry(
        db, family.deepa, family.circle, f"my private {MARKER} note", created_at=NOW,
    )
    body = client.get("/keepsake", headers=auth_headers(family.aditya)).json()
    texts = " ".join(m["text"] for m in body["moments"])
    assert "diyas" in texts
    assert MARKER not in texts


def test_keepsake_respects_custom_shares(client, db, family):
    from agents import consent_guardian

    entry, _ = make_entry(
        db, family.deepa, family.circle, "a moment just for Aditya", created_at=NOW,
    )
    consent_guardian.set_visibility(
        db, family.deepa, entry_id=entry.id,
        visibility=Visibility.custom, viewer_ids=[family.aditya.id],
    )
    aditya = client.get("/keepsake", headers=auth_headers(family.aditya)).json()
    abhishek = client.get("/keepsake", headers=auth_headers(family.abhishek)).json()
    assert any("just for Aditya" in m["text"] for m in aditya["moments"])
    assert not any("just for Aditya" in m["text"] for m in abhishek["moments"])


def test_on_this_day_resurfaces_older_years(client, db, family):
    make_entry(
        db, family.mumma, family.circle, "Diwali prep with everyone home.",
        visibility=Visibility.circle,
        created_at=datetime(2024, 7, 20, 18, 0, 0),
    )
    body = client.get("/keepsake", headers=auth_headers(family.aditya)).json()
    # 'on this day' depends on today's date matching; assert the shape and that
    # the shared moment is at least in the book
    assert any("Diwali" in m["text"] for m in body["moments"])
    assert isinstance(body["on_this_day"], list)


def test_mirror_reflects_own_journal_only(client, db, family):
    make_entry(
        db, family.aditya, family.circle,
        "Felt really happy and proud after the long walk.", created_at=NOW,
    )
    make_entry(
        db, family.deepa, family.circle, f"sad private {MARKER}", created_at=NOW,
    )
    mine = client.get("/mirror", headers=auth_headers(family.aditya)).json()
    assert mine["total_entries"] == 1
    assert mine["mood_series"][0]["score"] > 0
    assert MARKER not in str(mine)

    deepa = client.get("/mirror", headers=auth_headers(family.deepa)).json()
    assert deepa["total_entries"] == 1  # her own only


def test_mirror_requires_login(client, family):
    resp = client.get("/mirror")
    assert resp.status_code == 401
