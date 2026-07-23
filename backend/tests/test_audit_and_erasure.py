"""Audit trail, code-level never-medical enforcement, export, and full erasure."""
from agents import alerter, librarian
from models import AuditEvent, JournalEntry, User, Visibility
from tests.conftest import auth_headers, make_entry

MARKER = "zanzibar sapphire"


def test_visibility_changes_are_audited(client, db, family):
    entry, _ = make_entry(db, family.deepa, family.circle, "a moment")
    client.post(
        f"/entries/{entry.id}/share", json={"visibility": "circle"},
        headers=auth_headers(family.deepa),
    )
    row = db.query(AuditEvent).filter(AuditEvent.event == "visibility_changed").one()
    assert row.actor_id == family.deepa.id
    assert row.detail["from"] == "private" and row.detail["to"] == "circle"


def test_medical_wording_is_rejected_in_code(db, family, monkeypatch):
    # simulate an LLM that ignores its instructions and writes clinically
    monkeypatch.setattr(
        alerter, "complete",
        lambda *a, **k: "Her symptoms suggest a diagnosis; adjust her medication dosage.",
    )
    from models import AlertTrigger

    db.add(AlertTrigger(
        author_id=family.mumma.id, circle_id=family.circle.id,
        description="knee", match={"type": "state", "topic": "health"},
        audience=[family.aditya.id], severity_hint="notable",
    ))
    db.commit()
    entry, facts = make_entry(
        db, family.mumma, family.circle, "My knee hurts.",
        facts=[{"type": "state", "content": "knee hurts", "structured": {"topic": "health"},
                "source_quote": "My knee hurts."}],
    )
    created = alerter.evaluate(db, entry, facts)
    assert created
    assert "diagnos" not in created[0].message.lower()
    assert "dosage" not in created[0].message.lower()
    assert db.query(AuditEvent).filter(AuditEvent.event == "alert_wording_rejected").count() == 1


def test_export_contains_own_content_only(client, db, family):
    make_entry(db, family.deepa, family.circle, "deepa's own words")
    make_entry(db, family.aditya, family.circle, f"aditya's {MARKER}")
    export = client.get("/me/export", headers=auth_headers(family.deepa)).json()
    blob = str(export)
    assert "deepa's own words" in blob
    assert MARKER not in blob
    assert export["profile"]["email"] == family.deepa.email


def test_delete_account_erases_everything(client, db, family):
    make_entry(
        db, family.deepa, family.circle, f"the {MARKER} note",
        visibility=Visibility.circle,
    )
    deepa_id = family.deepa.id
    headers = auth_headers(family.deepa)

    resp = client.delete("/me", headers=headers)
    assert resp.status_code == 200

    assert db.get(User, deepa_id) is None
    assert db.query(JournalEntry).filter(JournalEntry.author_id == deepa_id).count() == 0
    assert MARKER not in " ".join(
        s.text for s in librarian.search(db, family.aditya, MARKER)
    )
    # her token no longer works
    assert client.get("/entries", headers=headers).status_code == 401
    # audit trail records the erasure
    assert db.query(AuditEvent).filter(AuditEvent.event == "account_deleted").count() == 1
