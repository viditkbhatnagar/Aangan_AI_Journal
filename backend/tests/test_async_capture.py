"""Async capture: the save returns instantly with status='enriching'; the
background task (which TestClient runs before the response is handed back)
produces summary/facts/rules/actions on its own session; the enrichment
endpoint serves the same CaptureOut shape the sync pipeline returns."""
import pytest

from config import settings
from models import JournalEntry
from tests.conftest import auth_headers


@pytest.fixture()
def async_mode(monkeypatch):
    monkeypatch.setattr(settings, "async_capture", True)


def test_async_save_returns_enriching_then_enrichment_fills_in(
    client, db, family, async_mode
):
    headers = auth_headers(family.deepa)
    response = client.post(
        "/entries",
        data={"transcript": "Aditya ne kaha he would love a new cricket bat for his birthday."},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    # the immediate response is the bare save — no summary/facts yet
    assert body["entry"]["status"] == "enriching"
    assert body["share_suggestions"] == []
    assert body["suggested_action"] is None

    # TestClient runs BackgroundTasks before returning, so by now the
    # enrichment is done and persisted
    enriched = client.get(f"/entries/{body['entry']['id']}/enrichment", headers=headers).json()
    assert enriched["entry"]["status"] == "ready"
    assert enriched["entry"]["summary"]
    assert len(enriched["entry"]["facts"]) >= 1

    entry = db.get(JournalEntry, body["entry"]["id"])
    db.refresh(entry)
    assert entry.status == "ready"


def test_async_delegation_surfaces_via_enrichment(client, db, family, async_mode):
    headers = auth_headers(family.deepa)
    response = client.post(
        "/entries",
        data={"transcript": "Order chocolates for Aditya's birthday — you do it please."},
        headers=headers,
    )
    assert response.status_code == 200
    entry_id = response.json()["entry"]["id"]

    enriched = client.get(f"/entries/{entry_id}/enrichment", headers=headers).json()
    action = enriched["suggested_action"]
    assert action is not None
    assert action["status"] == "clarifying"  # drafted as a chat, never auto-run


def test_enrichment_is_author_only(client, db, family, async_mode):
    response = client.post(
        "/entries",
        data={"transcript": "A private thought."},
        headers=auth_headers(family.deepa),
    )
    entry_id = response.json()["entry"]["id"]
    other = client.get(
        f"/entries/{entry_id}/enrichment", headers=auth_headers(family.abhishek)
    )
    assert other.status_code == 404


def test_sync_mode_is_unchanged_by_default(client, db, family):
    """settings.async_capture defaults to False: the old contract holds."""
    response = client.post(
        "/entries",
        data={"transcript": "Mumma would love marigolds for the balcony."},
        headers=auth_headers(family.deepa),
    )
    body = response.json()
    assert body["entry"]["status"] == "ready"
    assert body["entry"]["summary"]
