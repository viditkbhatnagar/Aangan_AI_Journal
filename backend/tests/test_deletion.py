"""Deletion rights: the author can erase an entry everywhere — rows, vectors,
share grants, alerts — and nobody else can."""
from agents import librarian
from models import Alert, AlertTrigger, Fact, JournalEntry, ShareTarget, Visibility
from tests.conftest import auth_headers, make_entry

MARKER = "zanzibar sapphire"


def test_author_can_delete_entry_everywhere(client, db, family):
    entry, facts = make_entry(
        db, family.deepa, family.circle,
        f"shared {MARKER} moment", visibility=Visibility.circle,
        facts=[{
            "type": "preference",
            "content": f"loved the {MARKER}",
            "visibility": Visibility.circle,
        }],
    )
    entry_id, fact_id = entry.id, facts[0].id
    assert MARKER in " ".join(s.text for s in librarian.search(db, family.aditya, MARKER))

    resp = client.delete(f"/entries/{entry_id}", headers=auth_headers(family.deepa))
    assert resp.status_code == 200

    assert db.get(JournalEntry, entry_id) is None
    assert db.get(Fact, fact_id) is None
    assert MARKER not in " ".join(s.text for s in librarian.search(db, family.aditya, MARKER))
    assert MARKER not in " ".join(s.text for s in librarian.search(db, family.deepa, MARKER))


def test_delete_cascades_share_targets_and_alerts(client, db, family):
    db.add(AlertTrigger(
        author_id=family.mumma.id, circle_id=family.circle.id,
        description="knee", match={"type": "state", "topic": "health"},
        audience=[family.aditya.id], severity_hint="notable",
    ))
    db.commit()
    resp = client.post(
        "/entries", data={"transcript": "My knee hurts today."},
        headers=auth_headers(family.mumma),
    )
    entry_id = resp.json()["entry"]["id"]
    fact_id = resp.json()["entry"]["facts"][0]["id"]
    client.post(
        f"/entries/{entry_id}/share",
        json={"fact_id": fact_id, "visibility": "custom", "viewer_ids": [family.aditya.id]},
        headers=auth_headers(family.mumma),
    )
    assert db.query(Alert).filter(Alert.source_entry_id == entry_id).count() == 1
    assert db.query(ShareTarget).filter(ShareTarget.fact_id == fact_id).count() == 1

    client.delete(f"/entries/{entry_id}", headers=auth_headers(family.mumma))
    assert db.query(Alert).filter(Alert.source_entry_id == entry_id).count() == 0
    assert db.query(ShareTarget).filter(ShareTarget.fact_id == fact_id).count() == 0


def test_only_author_can_delete(client, db, family):
    entry, _ = make_entry(db, family.deepa, family.circle, "mine alone")
    resp = client.delete(f"/entries/{entry.id}", headers=auth_headers(family.aditya))
    assert resp.status_code == 404  # existence not even revealed
    assert db.get(JournalEntry, entry.id) is not None


def test_delete_missing_entry_404(client, family):
    resp = client.delete("/entries/99999", headers=auth_headers(family.deepa))
    assert resp.status_code == 404
