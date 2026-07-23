"""The correction loop: authors can fix or remove the Extractor's notes, and
anyone can flag something for a human."""
from agents import librarian
from models import Feedback, ShareTarget, Visibility
from tests.conftest import auth_headers, make_entry


def test_author_edits_fact_and_reindexes(client, db, family):
    _, facts = make_entry(
        db, family.deepa, family.circle, "note",
        facts=[{
            "type": "preference",
            "content": "loved the blue kurta",
            "visibility": Visibility.circle,
        }],
    )
    resp = client.patch(
        f"/facts/{facts[0].id}", json={"content": "loved the green saree"},
        headers=auth_headers(family.deepa),
    )
    assert resp.status_code == 200
    results = " ".join(s.text for s in librarian.search(db, family.aditya, "green saree"))
    assert "green saree" in results
    assert "blue kurta" not in results


def test_fact_edit_and_delete_author_only(client, db, family):
    _, facts = make_entry(
        db, family.deepa, family.circle, "note",
        facts=[{"type": "event", "content": "went to the market"}],
    )
    assert client.patch(
        f"/facts/{facts[0].id}", json={"content": "x"},
        headers=auth_headers(family.aditya),
    ).status_code == 404
    assert client.delete(
        f"/facts/{facts[0].id}", headers=auth_headers(family.aditya)
    ).status_code == 404


def test_delete_fact_cascades(client, db, family):
    _, facts = make_entry(
        db, family.deepa, family.circle, "note",
        facts=[{"type": "preference", "content": "secret zanzibar wish", "visibility": Visibility.custom}],
    )
    db.add(ShareTarget(fact_id=facts[0].id, user_id=family.aditya.id))
    db.commit()

    resp = client.delete(f"/facts/{facts[0].id}", headers=auth_headers(family.deepa))
    assert resp.status_code == 200
    assert db.query(ShareTarget).filter(ShareTarget.fact_id == facts[0].id).count() == 0
    assert "zanzibar" not in " ".join(
        s.text for s in librarian.search(db, family.deepa, "zanzibar wish")
    )


def test_feedback_and_reports_persist(client, db, family):
    ok = client.post(
        "/feedback",
        json={"kind": "feedback", "message": "love this app, want reminders"},
        headers=auth_headers(family.mumma),
    )
    assert ok.status_code == 200
    report = client.post(
        "/feedback",
        json={"kind": "report", "subject_kind": "answer", "message": "answer felt off"},
        headers=auth_headers(family.aditya),
    )
    assert report.status_code == 200
    rows = db.query(Feedback).all()
    assert {r.kind for r in rows} == {"feedback", "report"}

    bad = client.post(
        "/feedback", json={"kind": "nonsense", "message": "x"},
        headers=auth_headers(family.aditya),
    )
    assert bad.status_code == 422
