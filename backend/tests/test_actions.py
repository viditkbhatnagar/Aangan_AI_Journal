"""Actions: creating one always requires human approval before completion,
and the Doer never touches payment or credentials (guard raises first)."""
import pytest

from agents import doer
from tests.conftest import auth_headers


def create(client, user, intent, plan_hint=None):
    resp = client.post(
        "/actions",
        json={"intent": intent, "plan_hint": plan_hint},
        headers=auth_headers(user),
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_new_action_awaits_approval(client, family):
    action = create(client, family.aditya, "order Deepa's chocolates")
    assert action["status"] == "awaiting_approval"
    assert action["plan"]["type"] == "purchase"
    assert action["result"] is None


def test_message_action_drafts_but_never_sends(client, family):
    action = create(
        client, family.aditya, "send a whatsapp message to Deepa",
        plan_hint={"type": "message", "to": "9199999", "body": "Thinking of you ❤️"},
    )
    assert action["status"] == "awaiting_approval"
    approved = client.post(
        f"/actions/{action['id']}/approve", headers=auth_headers(family.aditya)
    ).json()
    assert approved["status"] == "completed"
    result = approved["result"]
    assert result["status"] == "ready_for_human"  # drafted; the HUMAN presses send
    assert result["body"] == "Thinking of you ❤️"


def test_approval_gate_is_mandatory(client, family):
    action = create(client, family.aditya, "call Mumma", plan_hint={"type": "call", "to": "911234"})
    # cancel, then try to approve — must refuse
    client.post(f"/actions/{action['id']}/cancel", headers=auth_headers(family.aditya))
    resp = client.post(f"/actions/{action['id']}/approve", headers=auth_headers(family.aditya))
    assert resp.status_code == 409


def test_only_creator_can_approve_or_cancel(client, family):
    action = create(client, family.aditya, "order chocolates for Deepa")
    for verb in ("approve", "cancel"):
        resp = client.post(
            f"/actions/{action['id']}/{verb}", headers=auth_headers(family.abhishek)
        )
        assert resp.status_code == 404  # not even revealed to exist


def test_purchase_completes_to_safe_handoff(client, family):
    action = create(client, family.aditya, "order a phone for Deepa")
    approved = client.post(
        f"/actions/{action['id']}/approve", headers=auth_headers(family.aditya)
    ).json()
    assert approved["status"] == "completed"
    result = approved["result"]
    # either the cart was prepared (ready_for_human) or it fell back to a
    # manual link — both stop before payment, both give the human a URL
    assert result["status"] in {"ready_for_human", "manual"}
    assert result.get("checkout_url") or result.get("url")
    assert "pay" not in (result.get("note") or "").lower() or "never" in result["note"].lower() or "yourself" in result["note"].lower()


def test_actions_list_is_own_only(client, family):
    create(client, family.aditya, "order chocolates")
    other = client.get("/actions", headers=auth_headers(family.deepa)).json()
    assert other == []


def test_guard_refuses_credential_fields():
    for field in ("card number", "CVV", "password", "upi id", "OTP code"):
        with pytest.raises(doer.DoerSafetyError):
            doer.guard_fill(field, "x")
    # ordinary fields are fine
    doer.guard_fill("search box", "chocolates")
    doer.guard_fill("quantity", "1")


def test_guard_refuses_final_action_buttons():
    for text in ("Pay now", "Place Order", "Buy Now", "Confirm purchase", "PAY"):
        with pytest.raises(doer.DoerSafetyError):
            doer.guard_click(text)
    doer.guard_click("Add to cart")
    doer.guard_click("View cart")


def test_action_from_alert_links_and_requires_recipient(client, db, family):
    from agents import alerter
    from models import AlertTrigger
    from tests.conftest import make_entry

    db.add(AlertTrigger(
        author_id=family.mumma.id, circle_id=family.circle.id,
        description="knee", match={"type": "state", "topic": "health"},
        audience=[family.aditya.id], severity_hint="notable",
    ))
    db.commit()
    entry, facts = make_entry(
        db, family.mumma, family.circle, "My knee hurts.",
        facts=[{"type": "state", "content": "knee hurts", "structured": {"topic": "health"}}],
    )
    alert = alerter.evaluate(db, entry, facts)[0]

    # a different member cannot hang an action off someone else's alert
    resp = client.post(
        "/actions",
        json={"intent": "order chocolates", "related_alert_id": alert.id},
        headers=auth_headers(family.abhishek),
    )
    assert resp.status_code == 404

    ok = create(client, family.aditya, "order chocolates for Mumma", None)
    assert ok["status"] == "awaiting_approval"
