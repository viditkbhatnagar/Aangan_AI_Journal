"""Usage metering and the first-party event spine — the numbers behind the
business plan's funnel and unit-economics sections."""
from models import AskRecord, LlmCall, ProductEvent, User
from scripts.metrics import compute
from tests.conftest import auth_headers


def test_ask_writes_ask_record_and_event(client, db, family):
    resp = client.post(
        "/ask", json={"question": "How is everyone?"},
        headers=auth_headers(family.aditya),
    )
    assert resp.status_code == 200
    record = db.query(AskRecord).filter(AskRecord.user_id == family.aditya.id).one()
    assert record.answered_by == "fallback"  # keyless test mode
    assert record.circle_id == family.circle.id
    events = [e.name for e in db.query(ProductEvent).filter(ProductEvent.user_id == family.aditya.id)]
    assert "ask" in events


def test_capture_records_llm_calls_with_context(client, db, family):
    resp = client.post(
        "/entries", data={"transcript": "I loved the sunset at the ghat today."},
        headers=auth_headers(family.deepa),
    )
    entry_id = resp.json()["entry"]["id"]
    calls = db.query(LlmCall).filter(LlmCall.user_id == family.deepa.id).all()
    agents_seen = {c.agent for c in calls}
    assert {"Summarizer", "Extractor"} <= agents_seen
    assert all(c.provider == "fallback" for c in calls)  # keyless
    assert any(c.entry_id == entry_id for c in calls)
    events = [e.name for e in db.query(ProductEvent).filter(ProductEvent.user_id == family.deepa.id)]
    assert "entry" in events


def test_register_and_share_events(client, db, family):
    client.post("/auth/register", json={
        "name": "Nia", "email": "nia@x.test", "password": "longenough",
        "accept_terms": True,
    })
    nia = db.query(User).filter(User.email == "nia@x.test").one()
    assert [e.name for e in db.query(ProductEvent).filter(ProductEvent.user_id == nia.id)] == ["registered"]

    entry = client.post(
        "/entries", data={"transcript": "notes"}, headers=auth_headers(family.deepa),
    ).json()["entry"]
    client.post(
        f"/entries/{entry['id']}/share", json={"visibility": "circle"},
        headers=auth_headers(family.deepa),
    )
    names = [e.name for e in db.query(ProductEvent).filter(ProductEvent.user_id == family.deepa.id)]
    assert "share" in names


def test_last_seen_updated_on_authed_request(client, db, family):
    assert family.mumma.last_seen_at is None
    client.get("/entries", headers=auth_headers(family.mumma))
    db.refresh(family.mumma)
    assert family.mumma.last_seen_at is not None


def test_metrics_compute(client, db, family):
    client.post("/entries", data={"transcript": "pehli entry"}, headers=auth_headers(family.mumma))
    client.post("/ask", json={"question": "sab kaisa hai?"}, headers=auth_headers(family.mumma))
    report = compute(db)
    assert report["users"] == 4
    assert report["entries"] >= 1
    assert report["asks_total"] >= 1
    assert report["llm_calls"] >= 2
    assert 0.0 <= report["activation_rate"] <= 1.0
    assert "ask" in report["funnel_events"]
