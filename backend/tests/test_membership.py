"""Invite loop, leaving/removing members with grant purge, and password reset."""
from datetime import datetime, timedelta

from models import AlertTrigger, Membership, PasswordReset, ShareTarget, Visibility
from tests.conftest import auth_headers, make_entry


def test_my_circle_returns_invite_code(client, family):
    resp = client.get("/circles/mine", headers=auth_headers(family.aditya))
    assert resp.status_code == 200
    assert resp.json()["invite_code"] == "GHAR01"


def test_leave_purges_grants_and_audiences(client, db, family):
    # Deepa custom-shares a fact with Abhishek; Mumma's trigger audiences him
    _, facts = make_entry(
        db, family.deepa, family.circle, "x",
        facts=[{"type": "preference", "content": "secret gift", "visibility": Visibility.custom}],
    )
    db.add(ShareTarget(fact_id=facts[0].id, user_id=family.abhishek.id))
    trigger = AlertTrigger(
        author_id=family.mumma.id, circle_id=family.circle.id,
        description="t", match={"type": "state"},
        audience=[family.aditya.id, family.abhishek.id],
    )
    db.add(trigger)
    db.commit()

    resp = client.post("/circles/leave", headers=auth_headers(family.abhishek))
    assert resp.status_code == 200

    assert db.query(ShareTarget).filter(ShareTarget.user_id == family.abhishek.id).count() == 0
    db.refresh(trigger)
    assert family.abhishek.id not in trigger.audience
    assert (
        db.query(Membership)
        .filter(Membership.user_id == family.abhishek.id)
        .count() == 0
    )


def test_only_admin_can_remove_members(client, db, family):
    # make Aditya the admin
    db.query(Membership).filter(Membership.user_id == family.aditya.id).update({"role": "admin"})
    db.commit()

    denied = client.post(
        f"/circles/members/{family.abhishek.id}/remove",
        headers=auth_headers(family.deepa),
    )
    assert denied.status_code == 403

    ok = client.post(
        f"/circles/members/{family.abhishek.id}/remove",
        headers=auth_headers(family.aditya),
    )
    assert ok.status_code == 200
    assert (
        db.query(Membership).filter(Membership.user_id == family.abhishek.id).count() == 0
    )


def test_admin_role_promoted_when_admin_leaves(client, db, family):
    db.query(Membership).filter(Membership.user_id == family.aditya.id).update({"role": "admin"})
    db.commit()
    client.post("/circles/leave", headers=auth_headers(family.aditya))
    remaining = db.query(Membership).filter(Membership.circle_id == family.circle.id).all()
    assert remaining and any(m.role == "admin" for m in remaining)


def test_password_reset_flow(client, db, family):
    db.add(PasswordReset(
        user_id=family.mumma.id, token="tok-good",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    ))
    db.add(PasswordReset(
        user_id=family.mumma.id, token="tok-expired",
        expires_at=datetime.utcnow() - timedelta(hours=1),
    ))
    db.commit()

    bad = client.post("/auth/reset", json={"token": "tok-expired", "new_password": "newpass123"})
    assert bad.status_code == 400
    short = client.post("/auth/reset", json={"token": "tok-good", "new_password": "tiny"})
    assert short.status_code == 422

    ok = client.post("/auth/reset", json={"token": "tok-good", "new_password": "newpass123"})
    assert ok.status_code == 200 and ok.json()["access_token"]

    again = client.post("/auth/reset", json={"token": "tok-good", "new_password": "another123"})
    assert again.status_code == 400  # one-time

    login = client.post("/auth/login", json={"email": family.mumma.email, "password": "newpass123"})
    assert login.status_code == 200
