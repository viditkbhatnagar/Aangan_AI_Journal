"""Doer: prepares real-world actions and always stops at the safe handoff.
The human approves before anything runs, and the human pays/sends/calls.

Hard invariants, enforced in code (not prompts):
- No action completes without explicit approval (services/actions.py gate).
- The browser automation NEVER fills credential/payment fields and NEVER
  clicks a pay/confirm button — see the guard below, which raises before
  either could happen. We never call fill() at all in the purchase flow.
"""
import os
import re
from datetime import datetime
from urllib.parse import quote

from sqlalchemy.orm import Session

from agents.llm import complete
from config import settings
from models import Action, User


class DoerSafetyError(RuntimeError):
    """Raised if automation would touch payment, credentials, or a send."""


CREDENTIAL_PATTERN = re.compile(
    r"(card|cvv|cvc|password|passwd|otp|upi|pin\b|account.?number|iban)", re.I
)
FINAL_ACTION_PATTERN = re.compile(
    r"(pay now|place (your )?order|buy now|confirm (purchase|payment|order)|complete (purchase|payment)|^pay$|^send$)",
    re.I,
)


def guard_fill(field_descriptor: str, _value: str = "") -> None:
    """Call before ANY form fill. Refuses credential/payment fields."""
    if CREDENTIAL_PATTERN.search(field_descriptor or ""):
        raise DoerSafetyError(f"Refusing to fill a sensitive field: {field_descriptor!r}")


def guard_click(element_text: str) -> None:
    """Call before ANY click. Refuses final pay/send buttons."""
    if FINAL_ACTION_PATTERN.search((element_text or "").strip()):
        raise DoerSafetyError(f"Refusing to click a final action button: {element_text!r}")


PURCHASE_WORDS = ("order", "buy", "purchase", "shop", "get her", "get him", "get them")
MESSAGE_WORDS = ("message", "whatsapp", "text ", "sms", "email", "write to")
CALL_WORDS_RE = re.compile(r"\b(call|ring|dial)\b", re.I)

DRAFT_SYSTEM = (
    "Draft a short, warm message from one family member to another based on the "
    "intent given. 1-3 sentences, plain words, no signature. Return only the message."
)


def prepare(db: Session, action: Action, plan_hint: dict | None = None) -> dict:
    """Build the plan and set the action to awaiting_approval. No browser runs
    here — nothing happens in the world until a human approves."""
    intent = action.intent.lower()
    hint = plan_hint or {}
    kind = hint.get("type")
    if kind not in {"purchase", "message", "call"}:
        if any(w in intent for w in PURCHASE_WORDS):
            kind = "purchase"
        elif any(w in intent for w in MESSAGE_WORDS):
            kind = "message"
        elif CALL_WORDS_RE.search(intent):
            kind = "call"
        else:
            kind = "purchase"

    if kind == "purchase":
        item = hint.get("item") or action.intent
        plan = {
            "type": "purchase",
            "item": item,
            "site": hint.get("site") or settings.doer_purchase_site,
            "url": hint.get("url") or settings.doer_purchase_site,
            "price": hint.get("price") or "to confirm at checkout",
            "deliver_to": hint.get("deliver_to") or "confirm your address at checkout",
        }
    elif kind == "message":
        body = hint.get("body") or complete(
            f"Intent: {action.intent}",
            system=DRAFT_SYSTEM,
            fallback=lambda: f"Thinking of you! ({action.intent})",
            max_tokens=200,
        )
        plan = {
            "type": "message",
            "channel": hint.get("channel", "whatsapp"),
            "to": hint.get("to", ""),
            "body": body,
        }
    else:
        plan = {
            "type": "call",
            "to": hint.get("to", ""),
            "note": hint.get("note") or action.intent,
        }

    action.plan = plan
    action.status = "awaiting_approval"
    db.commit()
    return plan


def complete_action(db: Session, action: Action, user: User) -> dict:
    """Runs AFTER human approval only. Completes up to the safe handoff:
    cart ready to review, message drafted to send, number ready to dial."""
    plan = action.plan or {}
    kind = plan.get("type")

    if kind == "purchase":
        result = _prepare_purchase(action, plan)
    elif kind == "message":
        body = quote(plan.get("body", ""))
        result = {
            "status": "ready_for_human",
            "note": "Your message is drafted — read it once and press send yourself.",
            "deep_link": f"https://wa.me/{plan.get('to', '')}?text={body}"
            if plan.get("channel") == "whatsapp"
            else None,
            "body": plan.get("body", ""),
        }
    elif kind == "call":
        result = {
            "status": "ready_for_human",
            "note": "All set — place the call whenever you're ready.",
            "deep_link": f"tel:{plan.get('to', '')}" if plan.get("to") else None,
            "talking_note": plan.get("note", ""),
        }
    else:
        result = {"status": "manual", "note": "I wasn't sure how to prepare this — it's all yours."}

    action.result = result
    action.status = "completed"
    action.completed_at = datetime.utcnow()
    db.commit()
    return result


def _prepare_purchase(action: Action, plan: dict) -> dict:
    """Best-effort Playwright cart prep on the configured demo store. Stops at
    the cart/checkout page — the human reviews and pays. Any failure (site
    changed, no browser installed, offline) still hands the human a useful
    link, so approval always ends in something actionable."""
    item = plan.get("item", "")
    site = plan.get("site") or settings.doer_purchase_site
    manual = {
        "status": "manual",
        "url": site,
        "note": (
            "I couldn't finish preparing the cart automatically — here's the shop "
            "with the details, you can do it in one tap. I never enter payment details."
        ),
        "plan": plan,
    }
    try:
        from playwright.sync_api import sync_playwright

        words = [w for w in re.findall(r"[a-z0-9]+", item.lower()) if len(w) > 2]
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=settings.doer_headless)
            try:
                page = browser.new_page()
                page.goto(site, timeout=20000)
                page.wait_for_load_state("domcontentloaded")

                target = None
                links = page.locator("a")
                for i in range(min(links.count(), 120)):
                    text = (links.nth(i).text_content() or "").strip()
                    if text and words and any(w in text.lower() for w in words):
                        target = links.nth(i)
                        break
                if target is None:
                    raise RuntimeError("no matching product found")

                guard_click(target.text_content() or "")
                target.click()
                page.wait_for_load_state("domcontentloaded")

                add_button = page.get_by_text(re.compile(r"add to cart", re.I)).first
                guard_click(add_button.text_content() or "add to cart")
                page.once("dialog", lambda d: d.accept())
                add_button.click()
                page.wait_for_timeout(800)

                cart_link = page.get_by_text(re.compile(r"^cart$", re.I)).first
                cart_link.click()
                page.wait_for_load_state("domcontentloaded")
                # STOP. The human reviews price and address and pays.

                os.makedirs(settings.actions_dir, exist_ok=True)
                shot = os.path.join(settings.actions_dir, f"action-{action.id}.png")
                page.screenshot(path=shot)
                return {
                    "status": "ready_for_human",
                    "checkout_url": page.url,
                    "screenshot": shot,
                    "note": (
                        "The cart is ready — review the item, price, and address, "
                        "then pay yourself. I stop before any payment."
                    ),
                }
            finally:
                browser.close()
    except DoerSafetyError:
        raise
    except Exception:
        return manual
