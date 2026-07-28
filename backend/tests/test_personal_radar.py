"""Personal Radar: prospective memory for the author ALONE. Own facts only,
warm never-medical wording, anti-nag caps, deterministic keyless output."""
from datetime import datetime, timedelta

from agents import personal_radar
from models import Visibility
from tests.conftest import auth_headers, make_entry

NOW = datetime(2026, 7, 20, 9, 0, 0)  # a Monday


def plan_with_date(db, family, author, days_ahead, *, created_at=None, content="important meeting"):
    date = (NOW + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    return make_entry(
        db, author, family.circle, f"I have an {content} coming up.",
        facts=[{
            "type": "plan",
            "content": content,
            "structured": {"date": date},
            "source_quote": f"I have an {content} on Friday",
        }],
        created_at=created_at or NOW - timedelta(days=3),
    )


def test_founders_example_meeting_nudge(db, family):
    """Journal 'important meeting on Friday' on Monday → warm nudge near the day."""
    monday = NOW
    friday = NOW + timedelta(days=4)
    make_entry(
        db, family.aditya, family.circle, "I have an important meeting on Friday.",
        facts=[{
            "type": "plan",
            "content": "important meeting on Friday",
            "structured": {"date": friday.strftime("%Y-%m-%d")},
            "source_quote": "I have an important meeting on Friday",
        }],
        created_at=monday,
    )
    # Thursday: one day away → "tomorrow" wish, referencing Monday
    nudges = personal_radar.radar(db, family.aditya, now=NOW + timedelta(days=3))
    assert len(nudges) == 1
    assert nudges[0].kind == "personal_date"
    assert "Monday" in nudges[0].text
    assert "tomorrow" in nudges[0].text.lower()

    # Friday itself: "it's today"
    nudges = personal_radar.radar(db, family.aditya, now=friday)
    assert len(nudges) == 1 and "today" in nudges[0].text.lower()


def test_date_proximity_windows(db, family):
    plan_with_date(db, family, family.aditya, days_ahead=5)
    # 5 days away: outside the 2-day window
    assert personal_radar.radar(db, family.aditya, now=NOW) == []
    # 2 days away: inside
    assert len(personal_radar.radar(db, family.aditya, now=NOW + timedelta(days=3))) == 1
    # the day after: gone
    assert personal_radar.radar(db, family.aditya, now=NOW + timedelta(days=6)) == []


def test_stale_facts_never_nudge(db, family):
    # said 20 days ago — older than the 14-day memory, even if the date is near
    plan_with_date(
        db, family, family.aditya, days_ahead=1,
        created_at=NOW - timedelta(days=20),
    )
    assert personal_radar.radar(db, family.aditya, now=NOW) == []


def test_anti_nag_max_two_per_call(db, family):
    for i in range(3):
        plan_with_date(db, family, family.aditya, days_ahead=1, content=f"thing {i}")
    nudges = personal_radar.radar(db, family.aditya, now=NOW)
    assert len(nudges) == 2


def test_open_plan_at_most_one_gentle_nudge(db, family):
    for i in range(2):
        make_entry(
            db, family.aditya, family.circle, f"plan {i}",
            facts=[{"type": "plan", "content": f"vague plan {i}", "structured": {}}],
            created_at=NOW - timedelta(days=5),
        )
    nudges = personal_radar.radar(db, family.aditya, now=NOW)
    assert len(nudges) == 1
    assert nudges[0].kind == "open_plan"
    assert "mind" in nudges[0].text.lower()


def test_open_plan_age_window(db, family):
    make_entry(
        db, family.aditya, family.circle, "too fresh",
        facts=[{"type": "plan", "content": "fresh plan", "structured": {}}],
        created_at=NOW - timedelta(days=1),  # younger than 3 days: no nudge yet
    )
    assert personal_radar.radar(db, family.aditya, now=NOW) == []
    make_entry(
        db, family.aditya, family.circle, "aged well",
        facts=[{"type": "plan", "content": "aged plan", "structured": {}}],
        created_at=NOW - timedelta(days=8),
    )
    nudges = personal_radar.radar(db, family.aditya, now=NOW)
    assert len(nudges) == 1 and "aged plan" in nudges[0].text


def test_own_facts_only_even_when_shared(db, family):
    # Deepa's dated plan, shared with the whole circle: it is HER radar's
    # business, never Aditya's — personal nudges read only the author's rows
    plan_with_date(db, family, family.deepa, days_ahead=1)
    entry_facts = plan_with_date(db, family, family.deepa, days_ahead=1, content="shared meeting")
    from agents import consent_guardian
    consent_guardian.set_visibility(
        db, family.deepa, fact_id=entry_facts[1][0].id, visibility=Visibility.circle
    )
    assert personal_radar.radar(db, family.aditya, now=NOW) == []
    assert len(personal_radar.radar(db, family.deepa, now=NOW)) == 2


def test_medical_wording_rejected_in_code(db, family, monkeypatch):
    plan_with_date(db, family, family.aditya, days_ahead=1)
    monkeypatch.setattr(
        personal_radar, "complete",
        lambda *a, **k: "Remember your appointment — discuss your symptoms and medication dosage.",
    )
    personal_radar._wording_memo.clear()
    nudges = personal_radar.radar(db, family.aditya, now=NOW)
    assert len(nudges) == 1
    assert "dosage" not in nudges[0].text.lower()
    assert "symptom" not in nudges[0].text.lower()
    assert "On " in nudges[0].text  # the deterministic template took over


def test_keyless_fallback_is_deterministic_within_a_day(db, family):
    plan_with_date(db, family, family.aditya, days_ahead=1)
    personal_radar._wording_memo.clear()
    first = personal_radar.radar(db, family.aditya, now=NOW)
    second = personal_radar.radar(db, family.aditya, now=NOW + timedelta(hours=6))
    assert [n.text for n in first] == [n.text for n in second]


def test_hindi_author_gets_hindi_nudge(db, family):
    plan_with_date(db, family, family.mumma, days_ahead=1)
    nudges = personal_radar.radar(db, family.mumma, now=NOW)
    assert len(nudges) == 1
    assert "शुभकामनाएँ" in nudges[0].text


def test_nudges_endpoint_includes_personal_kinds(client, db, family):
    plan_with_date(db, family, family.aditya, days_ahead=1, created_at=datetime.utcnow() - timedelta(days=1))
    # the endpoint uses the real clock; the fact's date is NOW-anchored, so
    # re-anchor it to the real tomorrow
    from models import Fact
    fact = db.query(Fact).filter(Fact.author_id == family.aditya.id).first()
    fact.structured = {"date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")}
    db.commit()
    personal_radar._wording_memo.clear()
    resp = client.get("/nudges", headers=auth_headers(family.aditya))
    assert resp.status_code == 200
    kinds = [n["kind"] for n in resp.json()]
    assert "personal_date" in kinds

    # Deepa sees none of Aditya's personal nudges
    resp = client.get("/nudges", headers=auth_headers(family.deepa))
    assert all(k not in ("personal_date", "open_plan") for k in [n["kind"] for n in resp.json()])
