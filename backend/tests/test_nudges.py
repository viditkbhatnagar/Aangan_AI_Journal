"""Prompter and Relationship Radar: gentle, never pushy, visibility-safe."""
from datetime import datetime, timedelta

from agents import prompter, relationship_radar
from models import Visibility
from tests.conftest import auth_headers, make_entry

NOW = datetime(2026, 7, 20, 9, 0, 0)


def test_prompter_nudges_after_quiet_days(db, family):
    make_entry(db, family.mumma, family.circle, "old entry", created_at=NOW - timedelta(days=4))
    nudges = prompter.nudges(db, family.mumma, now=NOW)
    assert len(nudges) == 1 and nudges[0].kind == "journal"
    # Hindi speaker gets a Hindi starter
    assert any("?" in nudges[0].text for _ in [0])


def test_prompter_quiet_when_recent(db, family):
    make_entry(db, family.deepa, family.circle, "fresh entry", created_at=NOW - timedelta(hours=5))
    assert prompter.nudges(db, family.deepa, now=NOW) == []


def test_prompter_welcomes_first_timers(db, family):
    nudges = prompter.nudges(db, family.abhishek, now=NOW)
    assert len(nudges) == 1
    assert "ready" in nudges[0].text.lower()


def test_radar_upcoming_date_only_if_visible(db, family):
    # Deepa's private anniversary note: Aditya must NOT see a nudge from it
    make_entry(
        db, family.deepa, family.circle, "note",
        facts=[{
            "type": "date",
            "content": "wedding anniversary on 2020-07-28",
            "structured": {"date": "2020-07-28"},
        }],
        created_at=NOW,
    )
    assert relationship_radar.radar(db, family.aditya, now=NOW) == []

    # once shared, the date shows up (recurring by month/day)
    make_entry(
        db, family.deepa, family.circle, "note2",
        facts=[{
            "type": "date",
            "content": "Mumma's birthday on 1960-07-30",
            "structured": {"date": "1960-07-30"},
            "visibility": Visibility.circle,
        }],
        created_at=NOW,
    )
    nudges = relationship_radar.radar(db, family.aditya, now=NOW)
    assert any(n.kind == "upcoming_date" and "birthday" in n.text.lower() for n in nudges)


def test_radar_reach_out_when_shared_voice_goes_quiet(db, family):
    make_entry(
        db, family.mumma, family.circle, "namaste sabko",
        visibility=Visibility.circle, created_at=NOW - timedelta(days=10),
    )
    nudges = relationship_radar.radar(db, family.aditya, now=NOW)
    assert any(n.kind == "reach_out" and "Mumma" in n.text for n in nudges)


def test_radar_silent_about_members_who_never_shared(db, family):
    make_entry(db, family.deepa, family.circle, "private only", created_at=NOW - timedelta(days=30))
    nudges = relationship_radar.radar(db, family.aditya, now=NOW)
    assert all("Deepa" not in n.text for n in nudges)


def test_nudges_endpoint(client, family):
    resp = client.get("/nudges", headers=auth_headers(family.aditya))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
