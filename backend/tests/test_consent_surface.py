"""Legal pages exist; registration requires informed acceptance and records it."""
from models import User


def test_legal_documents_served(client):
    for doc in ("privacy", "terms"):
        resp = client.get(f"/legal/{doc}")
        assert resp.status_code == 200
        assert "Aangan" in resp.text
    assert client.get("/legal/nope").status_code == 404


def test_register_requires_acceptance(client, db):
    resp = client.post("/auth/register", json={
        "name": "New", "email": "new@x.test", "password": "longenough",
    })
    assert resp.status_code == 422
    assert db.query(User).filter(User.email == "new@x.test").first() is None


def test_register_records_policy_version(client, db):
    resp = client.post("/auth/register", json={
        "name": "New", "email": "new2@x.test", "password": "longenough",
        "accept_terms": True,
    })
    assert resp.status_code == 200
    user = db.query(User).filter(User.email == "new2@x.test").first()
    assert user.accepted_policy_version == "2026-07-23"
    assert user.accepted_at is not None
