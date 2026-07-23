"""Security floor: production refuses unsafe defaults; bursts are rate limited."""
import pytest

from config import settings
from services import ratelimit
from tests.conftest import auth_headers


def test_production_refuses_default_jwt_secret(monkeypatch):
    from app import startup

    monkeypatch.setattr(settings, "aangan_env", "production")
    monkeypatch.setattr(settings, "jwt_secret", "change-me")
    with pytest.raises(RuntimeError):
        startup()


def test_short_password_rejected(client):
    resp = client.post("/auth/register", json={
        "name": "N", "email": "n@x.test", "password": "short", "accept_terms": True,
    })
    assert resp.status_code == 422


def test_auth_rate_limited(client, monkeypatch, family):
    monkeypatch.setattr(settings, "rate_limit_auth_max", 3)
    ratelimit.reset()
    payload = {"email": family.deepa.email, "password": "wrong-password"}
    codes = [client.post("/auth/login", json=payload).status_code for _ in range(4)]
    assert codes[:3] == [401, 401, 401]
    assert codes[3] == 429


def test_ask_rate_limited(client, monkeypatch, family):
    monkeypatch.setattr(settings, "rate_limit_ask_max", 2)
    ratelimit.reset()
    headers = auth_headers(family.aditya)
    codes = [
        client.post("/ask", json={"question": "hello?"}, headers=headers).status_code
        for _ in range(3)
    ]
    assert codes[:2] == [200, 200]
    assert codes[2] == 429
