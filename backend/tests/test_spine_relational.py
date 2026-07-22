"""The spine, relational side: the Section 7 visibility test. A private item
must never be visible to anyone but its author, no matter what."""
import pytest

from agents import consent_guardian, librarian
from models import ShareTarget, Visibility
from tests.conftest import make_entry


def test_owner_sees_own_private_entry(db, family):
    entry, _ = make_entry(db, family.deepa, family.circle, "a private thought")
    assert librarian.is_visible(db, family.deepa, entry_id=entry.id)


def test_other_member_cannot_see_private_entry(db, family):
    entry, _ = make_entry(db, family.deepa, family.circle, "a private thought")
    assert not librarian.is_visible(db, family.aditya, entry_id=entry.id)
    assert not librarian.is_visible(db, family.mumma, entry_id=entry.id)


def test_circle_entry_visible_to_members_only(db, family, outsider):
    entry, _ = make_entry(
        db, family.deepa, family.circle, "shared with everyone", visibility=Visibility.circle
    )
    assert librarian.is_visible(db, family.aditya, entry_id=entry.id)
    assert librarian.is_visible(db, family.abhishek, entry_id=entry.id)
    assert not librarian.is_visible(db, outsider, entry_id=entry.id)


def test_custom_fact_visible_only_to_share_target(db, family):
    _, facts = make_entry(
        db,
        family.deepa,
        family.circle,
        "the gift idea",
        facts=[{"type": "preference", "content": "loved the black dress", "visibility": Visibility.custom}],
    )
    db.add(ShareTarget(fact_id=facts[0].id, user_id=family.aditya.id))
    db.commit()
    assert librarian.is_visible(db, family.aditya, fact_id=facts[0].id)
    assert not librarian.is_visible(db, family.abhishek, fact_id=facts[0].id)
    assert librarian.is_visible(db, family.deepa, fact_id=facts[0].id)  # author always


def test_custom_without_targets_hidden_from_everyone_but_author(db, family):
    _, facts = make_entry(
        db,
        family.deepa,
        family.circle,
        "x",
        facts=[{"type": "preference", "content": "secret wish", "visibility": Visibility.custom}],
    )
    assert not librarian.is_visible(db, family.aditya, fact_id=facts[0].id)
    assert librarian.is_visible(db, family.deepa, fact_id=facts[0].id)


def test_sharing_fact_does_not_expose_parent_entry(db, family):
    entry, facts = make_entry(
        db,
        family.deepa,
        family.circle,
        "long private entry with feelings",
        facts=[{"type": "preference", "content": "loved the black dress at H&M"}],
    )
    consent_guardian.set_visibility(
        db, family.deepa, fact_id=facts[0].id, visibility=Visibility.circle
    )
    assert librarian.is_visible(db, family.aditya, fact_id=facts[0].id)
    assert not librarian.is_visible(db, family.aditya, entry_id=entry.id)


def test_unshare_immediately_revokes(db, family):
    entry, _ = make_entry(
        db, family.deepa, family.circle, "was shared", visibility=Visibility.circle
    )
    assert librarian.is_visible(db, family.aditya, entry_id=entry.id)
    consent_guardian.set_visibility(
        db, family.deepa, entry_id=entry.id, visibility=Visibility.private
    )
    assert not librarian.is_visible(db, family.aditya, entry_id=entry.id)


def test_set_visibility_rejects_non_author(db, family):
    entry, _ = make_entry(db, family.deepa, family.circle, "deepa's own words")
    with pytest.raises(consent_guardian.NotYourContent):
        consent_guardian.set_visibility(
            db, family.aditya, entry_id=entry.id, visibility=Visibility.circle
        )
    db.refresh(entry)
    assert entry.visibility == Visibility.private


def test_custom_share_requires_viewers(db, family):
    entry, _ = make_entry(db, family.deepa, family.circle, "x")
    with pytest.raises(ValueError):
        consent_guardian.set_visibility(
            db, family.deepa, entry_id=entry.id, visibility=Visibility.custom, viewer_ids=[]
        )


def test_missing_row_is_invisible(db, family):
    assert not librarian.is_visible(db, family.aditya, entry_id=99999)
    assert not librarian.is_visible(db, family.aditya, fact_id=99999)
