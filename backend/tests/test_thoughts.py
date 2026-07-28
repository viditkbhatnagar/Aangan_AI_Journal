"""My Thoughts: author-only personal dashboard. The reflection, open loops,
and upcoming dates come from the CURRENT user's rows alone — another member's
content never appears, shared or not."""
from datetime import datetime, timedelta

from agents import reflector
from models import Visibility
from tests.conftest import auth_headers, make_entry

MARKER = "zanzibar sapphire"


def test_reflection_fallback_is_deterministic(db, family):
    now = datetime.utcnow()
    make_entry(db, family.aditya, family.circle, "tonight's dinner made me so happy",
               created_at=now - timedelta(days=1))
    make_entry(db, family.aditya, family.circle, "a tiring but good day",
               created_at=now - timedelta(days=2))
    first = reflector.weekly_reflection(db, family.aditya, now=now)
    second = reflector.weekly_reflection(db, family.aditya, now=now)
    assert first == second
    assert "2 times" in first
    assert "happy" in first  # the brightest word shines through


def test_reflection_only_covers_the_last_7_days(db, family):
    now = datetime.utcnow()
    make_entry(db, family.aditya, family.circle, "ancient news",
               created_at=now - timedelta(days=30))
    reflection = reflector.weekly_reflection(db, family.aditya, now=now)
    # no entries this week → the gentle empty-state line, not a count
    assert "wrote" not in reflection


def test_reflection_never_reads_other_members(db, family):
    now = datetime.utcnow()
    make_entry(db, family.deepa, family.circle, f"my secret {MARKER} plan",
               visibility=Visibility.circle, created_at=now - timedelta(days=1))
    make_entry(db, family.aditya, family.circle, "my own quiet day",
               created_at=now - timedelta(days=1))
    reflection = reflector.weekly_reflection(db, family.aditya, now=now)
    assert MARKER not in reflection


def test_reflection_is_never_medical(db, family, monkeypatch):
    now = datetime.utcnow()
    make_entry(db, family.aditya, family.circle, "a day", created_at=now - timedelta(days=1))
    monkeypatch.setattr(
        reflector, "complete",
        lambda *a, **k: "Your symptoms suggest you should adjust your medication.",
    )
    reflection = reflector.weekly_reflection(db, family.aditya, now=now)
    assert "symptom" not in reflection.lower()
    assert "medication" not in reflection.lower()


def test_hindi_author_gets_hindi_fallback(db, family):
    now = datetime.utcnow()
    make_entry(db, family.mumma, family.circle, "आज अच्छा दिन था",
               created_at=now - timedelta(days=1))
    reflection = reflector.weekly_reflection(db, family.mumma, now=now)
    assert "हफ़्ते" in reflection


def test_thoughts_endpoint_is_author_only(client, db, family):
    now = datetime.utcnow()
    # Aditya: an entry, an undated plan (open loop), a dated plan (upcoming)
    make_entry(
        db, family.aditya, family.circle,
        "I want to plan something special for Deepa's birthday.",
        facts=[{
            "type": "plan",
            "content": "plan something special for Deepa's birthday",
            "structured": {},
            "source_quote": "plan something special for Deepa's birthday",
        }],
        created_at=now - timedelta(days=4),
    )
    make_entry(
        db, family.aditya, family.circle, "Client presentation soon.",
        facts=[{
            "type": "plan",
            "content": "client presentation",
            "structured": {"date": (now + timedelta(days=2)).strftime("%Y-%m-%d")},
        }],
        created_at=now - timedelta(days=1),
    )
    # Deepa's content — shared AND private — must never surface here
    make_entry(
        db, family.deepa, family.circle, f"the {MARKER} surprise",
        visibility=Visibility.circle,
        facts=[{
            "type": "plan",
            "content": f"{MARKER} plan",
            "structured": {"date": (now + timedelta(days=1)).strftime("%Y-%m-%d")},
            "visibility": Visibility.circle,
        }],
        created_at=now - timedelta(days=1),
    )

    body = client.get("/thoughts", headers=auth_headers(family.aditya)).json()
    assert body["mirror"]["total_entries"] == 2
    assert "time" in body["reflection"]  # fallback counts his week
    loops = [loop["content"] for loop in body["open_loops"]]
    assert "plan something special for Deepa's birthday" in loops
    coming = [u["content"] for u in body["upcoming"]]
    assert "client presentation" in coming
    blob = str(body)
    assert MARKER not in blob  # nothing of Deepa's, shared or not

    # and Deepa's own /thoughts sees only hers
    body = client.get("/thoughts", headers=auth_headers(family.deepa)).json()
    assert body["mirror"]["total_entries"] == 1
    assert "plan something special" not in str(body)


def test_thoughts_requires_auth(client):
    assert client.get("/thoughts").status_code == 401


def test_reflector_llm_calls_are_metered(client, db, family):
    now = datetime.utcnow()
    make_entry(db, family.aditya, family.circle, "a good day",
               created_at=now - timedelta(days=1))
    client.get("/thoughts", headers=auth_headers(family.aditya))
    from models import LlmCall

    rows = db.query(LlmCall).filter(LlmCall.agent == "Reflector").all()
    assert rows, "Reflector must meter its calls"
    assert rows[0].provider == "fallback"  # keyless in tests
    assert rows[0].user_id == family.aditya.id
