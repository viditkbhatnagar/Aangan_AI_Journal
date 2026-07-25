"""TOTP two-factor: enrollment, challenge login, and the hard guarantees —
a challenge token is never a session, and the secret never leaves the server."""
import pyotp

from auth import hash_password
from tests.conftest import auth_headers


def _make_login_user(db):
    from models import User

    user = User(
        name="Guard", email="guard@ghar.family",
        password_hash=hash_password("aangan123"), language="en",
    )
    db.add(user)
    db.commit()
    return user


def _enroll(client, headers):
    setup = client.post("/auth/mfa/setup", headers=headers).json()
    code = pyotp.TOTP(setup["secret"]).now()
    enabled = client.post("/auth/mfa/enable", json={"code": code}, headers=headers)
    assert enabled.status_code == 200
    return setup["secret"]


def test_setup_returns_qr_and_enable_requires_valid_code(client, db):
    user = _make_login_user(db)
    headers = auth_headers(user)

    setup = client.post("/auth/mfa/setup", headers=headers)
    assert setup.status_code == 200
    body = setup.json()
    assert body["otpauth_uri"].startswith("otpauth://totp/")
    assert "<svg" in body["qr_svg"] or "svg" in body["qr_svg"]

    wrong = client.post("/auth/mfa/enable", json={"code": "000000"}, headers=headers)
    assert wrong.status_code == 403

    good = client.post(
        "/auth/mfa/enable",
        json={"code": pyotp.TOTP(body["secret"]).now()},
        headers=headers,
    )
    assert good.status_code == 200
    assert client.get("/me", headers=headers).json()["mfa_enabled"] is True


def test_login_challenges_and_verify_grants_session(client, db):
    user = _make_login_user(db)
    secret = _enroll(client, auth_headers(user))

    login = client.post(
        "/auth/login", json={"email": user.email, "password": "aangan123"}
    ).json()
    assert login["mfa_required"] is True
    assert login["access_token"] is None
    mfa_token = login["mfa_token"]

    # the challenge token is NOT a session
    sneaky = client.get("/me", headers={"Authorization": f"Bearer {mfa_token}"})
    assert sneaky.status_code == 401

    wrong = client.post("/auth/mfa/verify", json={"mfa_token": mfa_token, "code": "000000"})
    assert wrong.status_code == 403

    right = client.post(
        "/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": pyotp.TOTP(secret).now()},
    )
    assert right.status_code == 200
    session = right.json()["access_token"]
    assert client.get("/me", headers={"Authorization": f"Bearer {session}"}).status_code == 200


def test_login_without_mfa_still_returns_full_session(client, db):
    user = _make_login_user(db)
    login = client.post(
        "/auth/login", json={"email": user.email, "password": "aangan123"}
    ).json()
    assert login["mfa_required"] is False
    assert login["access_token"]


def test_code_guessing_is_throttled_per_account(client, db, monkeypatch):
    """The /auth/* middleware limit is per IP; a distributed attacker holding
    the password must still hit a per-ACCOUNT ceiling."""
    from routes import auth_routes

    monkeypatch.setattr(auth_routes, "MFA_ATTEMPTS_PER_WINDOW", 3)
    user = _make_login_user(db)
    _enroll(client, auth_headers(user))
    mfa_token = client.post(
        "/auth/login", json={"email": user.email, "password": "aangan123"}
    ).json()["mfa_token"]

    statuses = [
        client.post(
            "/auth/mfa/verify", json={"mfa_token": mfa_token, "code": "000000"}
        ).status_code
        for _ in range(4)
    ]
    assert statuses[:3] == [403, 403, 403]
    assert statuses[3] == 429  # throttled by account, not by IP


def test_password_reset_is_not_an_mfa_bypass(client, db):
    import secrets
    from datetime import datetime, timedelta

    from models import PasswordReset

    user = _make_login_user(db)
    secret = _enroll(client, auth_headers(user))
    token = secrets.token_urlsafe(24)
    db.add(PasswordReset(
        user_id=user.id, token=token,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    ))
    db.commit()

    reset = client.post(
        "/auth/reset", json={"token": token, "new_password": "brandnew123"}
    ).json()
    assert reset["mfa_required"] is True
    assert reset["access_token"] is None  # no session without the second factor

    verified = client.post(
        "/auth/mfa/verify",
        json={"mfa_token": reset["mfa_token"], "code": pyotp.TOTP(secret).now()},
    )
    assert verified.status_code == 200
    session = verified.json()["access_token"]
    assert client.get("/me", headers={"Authorization": f"Bearer {session}"}).status_code == 200


def test_disable_requires_code_and_secret_never_leaks(client, db):
    user = _make_login_user(db)
    headers = auth_headers(user)
    secret = _enroll(client, headers)

    # secret never appears in profile or export
    assert "totp_secret" not in client.get("/me", headers=headers).json()
    export = client.get("/me/export", headers=headers).json()
    assert secret not in str(export)

    off_wrong = client.post("/auth/mfa/disable", json={"code": "000000"}, headers=headers)
    assert off_wrong.status_code == 403
    off = client.post(
        "/auth/mfa/disable", json={"code": pyotp.TOTP(secret).now()}, headers=headers
    )
    assert off.status_code == 200
    assert client.get("/me", headers=headers).json()["mfa_enabled"] is False
    # next login is passwordly again
    login = client.post(
        "/auth/login", json={"email": user.email, "password": "aangan123"}
    ).json()
    assert login["mfa_required"] is False
