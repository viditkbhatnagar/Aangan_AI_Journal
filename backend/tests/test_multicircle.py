"""Multi-circle: a member can belong to several family circles. The spine
guarantee becomes membership-in-the-row's-circle; the active circle for
scoped routes is the validated X-Circle-Id header (oldest membership
otherwise); and leaving one circle never disturbs grants in another."""
import pytest

from agents import librarian
from models import FamilyCircle, Membership, ShareTarget, User, Visibility
from tests.conftest import auth_headers, make_entry


@pytest.fixture()
def second_circle(db, family):
    """Aditya starts a second circle 'Sasural' that Deepa also joins."""
    circle = FamilyCircle(name="Sasural", invite_code="SASU01", created_by=family.aditya.id)
    db.add(circle)
    db.flush()
    db.add(Membership(circle_id=circle.id, user_id=family.aditya.id, role="admin"))
    db.add(Membership(circle_id=circle.id, user_id=family.deepa.id))
    db.commit()
    return circle


def test_can_join_a_second_circle_but_not_twice(client, db, family):
    circle = FamilyCircle(name="Extra", invite_code="XTRA01", created_by=family.mumma.id)
    db.add(circle)
    db.flush()
    db.add(Membership(circle_id=circle.id, user_id=family.mumma.id, role="admin"))
    db.commit()

    headers = auth_headers(family.aditya)
    first = client.post("/circles/join", json={"invite_code": "XTRA01"}, headers=headers)
    assert first.status_code == 200
    again = client.post("/circles/join", json={"invite_code": "XTRA01"}, headers=headers)
    assert again.status_code == 409

    listing = client.get("/circles", headers=headers).json()
    assert [c["name"] for c in listing] == ["Ghar", "Extra"]
    assert listing[0]["member_count"] == 4


def test_visibility_follows_membership_of_the_rows_circle(db, family, second_circle):
    """Content shared to 'circle' in Sasural is visible to Sasural members
    only — Mumma (Ghar-only) must never see it, whatever her active circle."""
    entry, _ = make_entry(
        db, family.aditya, second_circle,
        "Planning the Sasural reunion surprise",
        visibility=Visibility.circle,
    )
    assert librarian.is_visible(db, family.deepa, entry_id=entry.id) is True
    assert librarian.is_visible(db, family.mumma, entry_id=entry.id) is False


def test_search_scopes_to_active_circle_header(client, db, family, second_circle):
    make_entry(
        db, family.aditya, family.circle,
        "Ghar note: the mango pickle is ready",
        visibility=Visibility.circle,
    )
    make_entry(
        db, family.aditya, second_circle,
        "Sasural note: reunion cake ordered",
        visibility=Visibility.circle,
    )
    headers = auth_headers(family.deepa)

    in_ghar = client.post(
        "/ask", json={"question": "what about the mango pickle?"},
        headers={**headers, "X-Circle-Id": str(family.circle.id)},
    ).json()
    assert any("pickle" in s["text"] for s in in_ghar["snippets"])

    in_sasural = client.post(
        "/ask", json={"question": "what about the mango pickle?"},
        headers={**headers, "X-Circle-Id": str(second_circle.id)},
    ).json()
    assert not any("pickle" in s["text"] for s in in_sasural["snippets"])


def test_spoofed_circle_header_is_refused(client, db, family, second_circle):
    # Mumma is not in Sasural — naming it in the header must 403, not bill/read
    response = client.get(
        "/circles/mine",
        headers={**auth_headers(family.mumma), "X-Circle-Id": str(second_circle.id)},
    )
    assert response.status_code == 403


def test_circle_switch_changes_mine_and_members(client, family, second_circle):
    headers = auth_headers(family.deepa)
    default = client.get("/circles/mine", headers=headers).json()
    assert default["name"] == "Ghar"

    switched = client.get(
        "/circles/mine", headers={**headers, "X-Circle-Id": str(second_circle.id)}
    ).json()
    assert switched["name"] == "Sasural"

    members = client.get(
        "/circles/members", headers={**headers, "X-Circle-Id": str(second_circle.id)}
    ).json()
    assert {m["name"] for m in members} == {"Aditya", "Deepa"}


def test_leaving_one_circle_keeps_grants_in_the_other(client, db, family, second_circle):
    """Regression: the detach purge used to delete the departing user's
    ShareTargets across ALL circles."""
    entry, facts = make_entry(
        db, family.aditya, family.circle,
        "Ghar secret for Deepa only",
        visibility=Visibility.custom,
        facts=[{"type": "preference", "content": "Deepa loves jasmine", "visibility": Visibility.custom}],
    )
    db.add(ShareTarget(entry_id=entry.id, fact_id=None, user_id=family.deepa.id))
    db.add(ShareTarget(entry_id=None, fact_id=facts[0].id, user_id=family.deepa.id))
    db.commit()
    librarian.upsert_entry(db, entry, facts)
    assert librarian.is_visible(db, family.deepa, entry_id=entry.id) is True

    # Deepa leaves SASURAL — her Ghar grants must survive
    left = client.post(
        "/circles/leave",
        headers={**auth_headers(family.deepa), "X-Circle-Id": str(second_circle.id)},
    )
    assert left.status_code == 200
    assert db.query(Membership).filter(
        Membership.user_id == family.deepa.id, Membership.circle_id == second_circle.id
    ).first() is None
    assert db.query(ShareTarget).filter(ShareTarget.user_id == family.deepa.id).count() == 2
    assert librarian.is_visible(db, family.deepa, entry_id=entry.id) is True


def test_account_deletion_detaches_every_circle(client, db, family, second_circle):
    headers = auth_headers(family.deepa)
    response = client.delete("/me", headers=headers)
    assert response.status_code == 200
    assert db.query(Membership).filter(Membership.user_id == family.deepa.id).count() == 0
    assert db.query(User).filter(User.id == family.deepa.id).first() is None


def test_new_entry_lands_in_the_active_circle(client, db, family, second_circle):
    headers = {**auth_headers(family.deepa), "X-Circle-Id": str(second_circle.id)}
    response = client.post(
        "/entries", data={"transcript": "A quiet Sasural afternoon."}, headers=headers
    )
    assert response.status_code == 200
    from models import JournalEntry

    entry = db.get(JournalEntry, response.json()["entry"]["id"])
    assert entry.circle_id == second_circle.id
