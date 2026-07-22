"""Consent Guardian: facts stay private unless the author's own rule or an
explicit share moves them. Suggestions never write."""
from agents import consent_guardian
from models import ShareRule, ShareTarget, Visibility
from tests.conftest import make_entry


def gift_fact():
    return {
        "type": "preference",
        "content": "Deepa loved a black dress at H&M",
        "structured": {"item": "dress", "brand": "H&M", "sentiment": "loved", "tags": ["gift"]},
    }


def add_rule(db, user, circle, *, match, audience="all", active=True):
    rule = ShareRule(
        user_id=user.id,
        circle_id=circle.id,
        description="share my gift ideas with the family",
        match=match,
        audience=audience,
        active=active,
    )
    db.add(rule)
    db.commit()
    return rule


def test_new_facts_default_private(db, family):
    _, facts = make_entry(db, family.deepa, family.circle, "x", facts=[gift_fact()])
    assert facts[0].visibility == Visibility.private


def test_gift_rule_applies_circle_visibility(db, family):
    add_rule(db, family.deepa, family.circle, match={"type": "preference", "tag": "gift"})
    _, facts = make_entry(db, family.deepa, family.circle, "x", facts=[gift_fact()])
    applied = consent_guardian.apply_rules(db, family.deepa, facts)
    assert applied == ["share my gift ideas with the family"]
    assert facts[0].visibility == Visibility.circle


def test_rule_with_user_list_creates_share_targets(db, family):
    add_rule(
        db, family.deepa, family.circle,
        match={"type": "preference", "tag": "gift"},
        audience=[family.aditya.id],
    )
    _, facts = make_entry(db, family.deepa, family.circle, "x", facts=[gift_fact()])
    consent_guardian.apply_rules(db, family.deepa, facts)
    assert facts[0].visibility == Visibility.custom
    targets = db.query(ShareTarget).filter(ShareTarget.fact_id == facts[0].id).all()
    assert [t.user_id for t in targets] == [family.aditya.id]


def test_inactive_rule_not_applied(db, family):
    add_rule(
        db, family.deepa, family.circle,
        match={"type": "preference", "tag": "gift"}, active=False,
    )
    _, facts = make_entry(db, family.deepa, family.circle, "x", facts=[gift_fact()])
    assert consent_guardian.apply_rules(db, family.deepa, facts) == []
    assert facts[0].visibility == Visibility.private


def test_non_matching_fact_untouched(db, family):
    add_rule(db, family.deepa, family.circle, match={"type": "preference", "tag": "gift"})
    _, facts = make_entry(
        db, family.deepa, family.circle, "x",
        facts=[{"type": "state", "content": "feeling tired today", "structured": {"topic": "health"}}],
    )
    assert consent_guardian.apply_rules(db, family.deepa, facts) == []
    assert facts[0].visibility == Visibility.private


def test_suggestions_are_proposals_not_writes(db, family):
    entry, facts = make_entry(db, family.deepa, family.circle, "x", facts=[gift_fact()])
    suggestions = consent_guardian.suggest_shares(entry, facts)
    assert suggestions and suggestions[0].fact_id == facts[0].id
    db.refresh(facts[0])
    assert facts[0].visibility == Visibility.private


def test_only_authors_own_rules_apply(db, family):
    # Aditya's rule must never share Deepa's facts
    add_rule(db, family.aditya, family.circle, match={"type": "preference"})
    _, facts = make_entry(db, family.deepa, family.circle, "x", facts=[gift_fact()])
    assert consent_guardian.apply_rules(db, family.deepa, facts) == []
    assert facts[0].visibility == Visibility.private
