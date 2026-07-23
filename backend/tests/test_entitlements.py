"""Freemium entitlements: caps are enforced in code, Plus lifts them, and the
fake-door records willingness-to-pay."""
import io
from datetime import datetime, timedelta

import entitlements
from models import JournalEntry, ProductEvent, Visibility
from tests.conftest import auth_headers, make_entry


def tiny_caps(monkeypatch, **overrides):
    caps = {"asks_per_month": 1, "voice_minutes_per_month": 1, "memory_days": 90}
    caps.update(overrides)
    monkeypatch.setitem(entitlements.CAPS, "free", caps)


def test_ask_cap_enforced_and_plus_bypasses(client, db, family, monkeypatch):
    tiny_caps(monkeypatch)
    headers = auth_headers(family.aditya)
    assert client.post("/ask", json={"question": "one"}, headers=headers).status_code == 200
    blocked = client.post("/ask", json={"question": "two"}, headers=headers)
    assert blocked.status_code == 402
    assert "Plus" in blocked.json()["detail"]

    family.circle.plan = "plus"
    db.commit()
    assert client.post("/ask", json={"question": "three"}, headers=headers).status_code == 200


def test_voice_cap_blocks_new_recordings_not_typing(client, db, family, monkeypatch):
    tiny_caps(monkeypatch, voice_minutes_per_month=1)
    # 120s of voice already used this month
    make_entry(db, family.deepa, family.circle, "long voice note")
    entry = db.query(JournalEntry).filter_by(author_id=family.deepa.id).first()
    entry.duration_sec = 120
    db.commit()

    blocked = client.post(
        "/entries",
        files={"audio": ("a.webm", io.BytesIO(b"x"), "audio/webm")},
        headers=auth_headers(family.deepa),
    )
    assert blocked.status_code == 402  # cap fires before transcription

    typed = client.post(
        "/entries", data={"transcript": "typing is always free"},
        headers=auth_headers(family.deepa),
    )
    assert typed.status_code == 200


def test_memory_book_window_by_plan(client, db, family):
    make_entry(
        db, family.deepa, family.circle, "old shared moment",
        visibility=Visibility.circle,
        created_at=datetime.utcnow() - timedelta(days=200),
    )
    make_entry(
        db, family.deepa, family.circle, "recent shared moment",
        visibility=Visibility.circle,
        created_at=datetime.utcnow() - timedelta(days=2),
    )
    free_book = client.get("/keepsake", headers=auth_headers(family.aditya)).json()
    texts = " ".join(m["text"] for m in free_book["moments"])
    assert "recent shared moment" in texts
    assert "old shared moment" not in texts  # beyond the 90-day free window

    family.circle.plan = "plus"
    db.commit()
    plus_book = client.get("/keepsake", headers=auth_headers(family.aditya)).json()
    texts = " ".join(m["text"] for m in plus_book["moments"])
    assert "old shared moment" in texts


def test_fake_door_records_interest(client, db, family):
    resp = client.post("/plus/interest", headers=auth_headers(family.deepa))
    assert resp.status_code == 200
    events = db.query(ProductEvent).filter(
        ProductEvent.user_id == family.deepa.id, ProductEvent.name == "plus_interest"
    ).count()
    assert events == 1


def test_plan_info_endpoint(client, family):
    resp = client.get("/plus", headers=auth_headers(family.aditya))
    assert resp.status_code == 200
    body = resp.json()
    assert body["plan"] == "free"
    assert "asks_per_month" in body["caps"]
