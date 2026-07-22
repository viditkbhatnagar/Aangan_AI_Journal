"""The spine, vector side: librarian.search must never return another
member's private content — even when Chroma's own metadata is stale or
corrupted. Marker strings make any leak string-detectable."""
from agents import consent_guardian, librarian
from memory import store
from models import Visibility
from tests.conftest import make_entry

MARKER = "zanzibar sapphire"


def all_text(snippets):
    return " ".join(s.text for s in snippets)


def test_vector_search_excludes_others_private(db, family):
    make_entry(db, family.deepa, family.circle, f"today I found the {MARKER} necklace")
    results = librarian.search(db, family.aditya, "what did Deepa find today?")
    assert MARKER not in all_text(results)


def test_author_finds_own_private(db, family):
    make_entry(db, family.deepa, family.circle, f"today I found the {MARKER} necklace")
    results = librarian.search(db, family.deepa, f"the {MARKER} necklace")
    assert MARKER in all_text(results)


def test_vector_search_includes_circle_shared(db, family):
    make_entry(
        db,
        family.deepa,
        family.circle,
        "Saw a beautiful black dress at H&M today",
        visibility=Visibility.circle,
        facts=[{
            "type": "preference",
            "content": "Deepa loved a black dress at H&M",
            "visibility": Visibility.circle,
        }],
    )
    results = librarian.search(db, family.aditya, "black dress H&M")
    assert "black dress" in all_text(results)
    assert all(r.created_at is not None for r in results)


def test_custom_overfetch_is_postfiltered(db, family):
    # custom doc shared with Aditya only: passes the Chroma $or for everyone,
    # must be dropped by the relational guard for Abhishek
    _, facts = make_entry(
        db,
        family.deepa,
        family.circle,
        "x",
        facts=[{"type": "preference", "content": f"the {MARKER} plan"}],
    )
    consent_guardian.set_visibility(
        db, family.deepa, fact_id=facts[0].id, visibility=Visibility.custom,
        viewer_ids=[family.aditya.id],
    )
    assert MARKER in all_text(librarian.search(db, family.aditya, f"{MARKER} plan"))
    assert MARKER not in all_text(librarian.search(db, family.abhishek, f"{MARKER} plan"))


def test_stale_chroma_metadata_cannot_leak(db, family):
    """THE second-guard proof: corrupt Chroma's copy to say 'circle' while the
    DB row stays private — search must still exclude it."""
    entry, _ = make_entry(db, family.deepa, family.circle, f"my {MARKER} secret")
    collection = store.get_collection()
    doc = collection.get(ids=[f"entry:{entry.id}"])
    meta = doc["metadatas"][0]
    meta["visibility"] = "circle"  # lie in the vector store
    collection.update(ids=[f"entry:{entry.id}"], metadatas=[meta])

    results = librarian.search(db, family.aditya, f"{MARKER} secret")
    assert MARKER not in all_text(results)


def test_unshare_revokes_in_vector_search(db, family):
    entry, _ = make_entry(
        db, family.deepa, family.circle, f"the {MARKER} trip", visibility=Visibility.circle
    )
    assert MARKER in all_text(librarian.search(db, family.aditya, f"{MARKER} trip"))
    consent_guardian.set_visibility(
        db, family.deepa, entry_id=entry.id, visibility=Visibility.private
    )
    assert MARKER not in all_text(librarian.search(db, family.aditya, f"{MARKER} trip"))


def test_keyword_lookup_respects_visibility(db, family):
    make_entry(
        db,
        family.deepa,
        family.circle,
        "x",
        facts=[{"type": "date", "content": f"the {MARKER} anniversary is on 2026-03-14"}],
    )
    results = librarian.search(db, family.aditya, f"when is the {MARKER} anniversary?")
    assert MARKER not in all_text(results)


def test_no_circle_no_results(db, family, outsider):
    make_entry(
        db, family.deepa, family.circle, f"{MARKER} moment", visibility=Visibility.circle
    )
    assert librarian.search(db, outsider, MARKER) == []
