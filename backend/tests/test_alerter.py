"""Alert engine: author-set triggers only, permitted recipients only, right
severity, daily cap, no duplicate alerts per fact, collapsed similar alerts,
never-medical wording."""
import re
from datetime import datetime, timedelta

from agents import alerter
from models import Alert, AlertTrigger
from tests.conftest import make_entry

NOW = datetime(2026, 7, 20, 10, 0, 0)

MEDICAL_WORDS = re.compile(r"\b(diagnos|prescri|dosage|symptom|medication)\w*\b", re.I)


def knee_trigger(db, family, audience=None, active=True, severity="notable"):
    trigger = AlertTrigger(
        author_id=family.mumma.id,
        circle_id=family.circle.id,
        description="if I say my knee hurts, tell my sons",
        match={"type": "state", "topic": "health"},
        audience=audience if audience is not None else [family.aditya.id, family.abhishek.id],
        severity_hint=severity,
        active=active,
    )
    db.add(trigger)
    db.commit()
    return trigger


def knee_entry(db, family, text="My knee has been paining a little today."):
    return make_entry(
        db, family.mumma, family.circle, text,
        facts=[{
            "type": "state",
            "content": text,
            "structured": {"topic": "health"},
            "source_quote": text,
        }],
        created_at=NOW,
    )


def test_matching_trigger_alerts_audience_only(db, family):
    knee_trigger(db, family)
    entry, facts = knee_entry(db, family)
    created = alerter.evaluate(db, entry, facts, now=NOW)
    recipients = sorted(a.recipient_id for a in created)
    assert recipients == sorted([family.aditya.id, family.abhishek.id])
    assert all(a.severity == "notable" for a in created)
    assert all(a.recipient_id != family.deepa.id for a in created)


def test_no_trigger_no_alert(db, family):
    entry, facts = knee_entry(db, family)
    assert alerter.evaluate(db, entry, facts, now=NOW) == []


def test_inactive_trigger_ignored(db, family):
    knee_trigger(db, family, active=False)
    entry, facts = knee_entry(db, family)
    assert alerter.evaluate(db, entry, facts, now=NOW) == []


def test_non_matching_fact_no_alert(db, family):
    knee_trigger(db, family)
    entry, facts = make_entry(
        db, family.mumma, family.circle, "Made lovely halwa today.",
        facts=[{"type": "event", "content": "made halwa", "structured": {}}],
        created_at=NOW,
    )
    assert alerter.evaluate(db, entry, facts, now=NOW) == []


def test_never_two_alerts_for_same_fact(db, family):
    knee_trigger(db, family)
    entry, facts = knee_entry(db, family)
    first = alerter.evaluate(db, entry, facts, now=NOW)
    assert len(first) == 2
    again = alerter.evaluate(db, entry, facts, now=NOW)
    assert again == []
    assert db.query(Alert).count() == 2


def test_similar_alerts_collapse_within_entry(db, family):
    knee_trigger(db, family, audience=[family.aditya.id])
    text = "My knee hurts. My back is paining too."
    entry, facts = make_entry(
        db, family.mumma, family.circle, text,
        facts=[
            {"type": "state", "content": "knee hurts", "structured": {"topic": "health"}},
            {"type": "state", "content": "back paining", "structured": {"topic": "health"}},
        ],
        created_at=NOW,
    )
    created = alerter.evaluate(db, entry, facts, now=NOW)
    assert len(created) == 1  # one nudge per recipient per entry


def test_daily_cap_per_recipient(db, family):
    knee_trigger(db, family, audience=[family.aditya.id])
    for i in range(7):
        entry, facts = knee_entry(db, family, f"Knee pain again, episode {i}.")
        alerter.evaluate(db, entry, facts, now=NOW + timedelta(minutes=i))
    today = (
        db.query(Alert)
        .filter(Alert.recipient_id == family.aditya.id)
        .count()
    )
    assert today == 5  # capped

    # next day the counter resets
    entry, facts = knee_entry(db, family, "Knee pain, new day.")
    created = alerter.evaluate(db, entry, facts, now=NOW + timedelta(days=1))
    assert len(created) == 1


def test_wording_is_never_medical(db, family):
    knee_trigger(db, family)
    entry, facts = knee_entry(db, family)
    created = alerter.evaluate(db, entry, facts, now=NOW)
    for alert in created:
        assert not MEDICAL_WORDS.search(alert.message)
        assert alert.suggested_action


def test_author_never_alerts_themselves(db, family):
    knee_trigger(db, family, audience=[family.mumma.id, family.aditya.id])
    entry, facts = knee_entry(db, family)
    created = alerter.evaluate(db, entry, facts, now=NOW)
    assert all(a.recipient_id != family.mumma.id for a in created)


def test_alerts_api_scoped_to_recipient(client, db, family):
    from tests.conftest import auth_headers

    knee_trigger(db, family, audience=[family.aditya.id])
    entry, facts = knee_entry(db, family)
    alerter.evaluate(db, entry, facts, now=NOW)

    mine = client.get("/alerts", headers=auth_headers(family.aditya)).json()
    assert len(mine) == 1
    others = client.get("/alerts", headers=auth_headers(family.deepa)).json()
    assert others == []

    # only the recipient can change status
    alert_id = mine[0]["id"]
    resp = client.post(
        f"/alerts/{alert_id}/status", json={"status": "dismissed"},
        headers=auth_headers(family.deepa),
    )
    assert resp.status_code == 404
    resp = client.post(
        f"/alerts/{alert_id}/status", json={"status": "acted"},
        headers=auth_headers(family.aditya),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "acted"


def test_capture_pipeline_fires_trigger_end_to_end(client, db, family):
    from tests.conftest import auth_headers

    knee_trigger(db, family)
    resp = client.post(
        "/entries",
        data={"transcript": "My knee has been paining a little today."},
        headers=auth_headers(family.mumma),
    )
    assert resp.status_code == 200
    aditya_alerts = client.get("/alerts", headers=auth_headers(family.aditya)).json()
    assert len(aditya_alerts) == 1
    assert aditya_alerts[0]["severity"] == "notable"
