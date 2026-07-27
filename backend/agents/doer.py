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
import traceback
from datetime import datetime
from urllib.parse import quote

from sqlalchemy.orm import Session

from agents.llm import complete, complete_json
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

# journal phrases that read as "please make this happen"
_INTENT_RE = re.compile(
    r"\b(order|buy|purchase|book|send)\b.{0,80}", re.I
)
_DELEGATE_RE = re.compile(
    r"(you do it|please do it|can you (order|buy|get|send|book)|arrange it|करवा दो|मंगवा दो)", re.I
)
# A plain spoken command — a sentence that STARTS with a buy/book verb, e.g.
# "order some flowers", "please buy chocolates", "book a cab". Anchored at the
# start so past-tense reflections ("I ordered chocolates yesterday", "read a
# book") never match.
_IMPERATIVE_RE = re.compile(
    r"^\s*(?:please\s+|pls\s+|kindly\s+|can you\s+|could you\s+|"
    r"i\s+want\s+to\s+|i'?d\s+like\s+to\s+|i\s+would\s+like\s+to\s+)?"
    r"(order|buy|purchase|book|gift|arrange)\b",
    re.I,
)
_SENTENCES = re.compile(r"(?<=[.!?।])\s+")


def detect_action_intent(transcript: str) -> str | None:
    """If a journal entry asks for something to be DONE (not just felt), return
    the sentence to turn into a prepared action. The author still approves
    before anything runs — this only drafts. Catches both explicit delegations
    ('… you do it') and plain commands ('order some flowers')."""
    sentences = _SENTENCES.split(transcript.strip())
    # 1) explicit delegation markers anywhere in the entry
    if _DELEGATE_RE.search(transcript) or re.search(
        r"\bI want to (order|buy|send|book)\b", transcript, re.I
    ):
        for sentence in sentences:
            if _INTENT_RE.search(sentence):
                return sentence.strip()
        for sentence in sentences:  # e.g. Hindi: "मिठाई मंगवा दो।"
            if _DELEGATE_RE.search(sentence):
                return sentence.strip()
    # 2) a plain command to buy/book something, even without "you do it"
    for sentence in sentences:
        if _IMPERATIVE_RE.search(sentence):
            return sentence.strip()
    return None

DRAFT_SYSTEM = (
    "Draft a short, warm message from one family member to another based on the "
    "intent given. 1-3 sentences, plain words, no signature. Return only the message."
)


def _make_tracer(user_id: int | None, sink: list):
    """Return step(icon, label, detail='') that records a structured step onto
    `sink` (persisted on the action for the 'Behind the scenes' view) AND
    mirrors it to the live activity feed (the 'Agents at work' panel). One call
    → both places, so the pipeline is visible live and after the fact."""
    from services import activity

    def step(icon: str, label: str, detail: str = "") -> None:
        sink.append({"icon": icon, "label": label, "detail": detail})
        activity.emit(
            user_id, "Doer", f"{icon} {label}" + (f" — {detail}" if detail else "")
        )

    return step


def prepare(db: Session, action: Action, plan_hint: dict | None = None) -> dict:
    """Build the plan and set the action to awaiting_approval. No browser runs
    here — nothing happens in the world until a human approves. Every decision
    is recorded in plan['trace'] so the whole pipeline is visible in the UI."""
    trace: list[dict] = []
    step = _make_tracer(action.created_by, trace)
    intent = action.intent.lower()
    hint = plan_hint or {}

    step("📝", "Received your request", action.intent)

    kind = hint.get("type")
    if kind in {"purchase", "message", "call"}:
        why = "you told me the type up front"
    elif any(w in intent for w in PURCHASE_WORDS):
        kind, why = "purchase", "the wording sounds like shopping"
    elif any(w in intent for w in MESSAGE_WORDS):
        kind, why = "message", "the wording sounds like a message"
    elif CALL_WORDS_RE.search(intent):
        kind, why = "call", "the wording sounds like a phone call"
    else:
        kind, why = "purchase", "no clear signal, so I default to a purchase"
    step("🧭", f"Understood this as a {kind}", why)

    if kind == "purchase":
        # Purchases go through a short back-and-forth so we buy the RIGHT thing
        # (a phone, not a phone case) at the right budget — never blindly grab
        # the first result. This asks the first question and waits.
        return _start_purchase(db, action, hint, trace, step)
    elif kind == "message":
        if hint.get("body"):
            body = hint["body"]
            step("💬", "Used the message you provided", body)
        else:
            step("✍️", "Writing a warm note", "asking the language model to draft it…")
            body = complete(
                f"Intent: {action.intent}",
                system=DRAFT_SYSTEM,
                fallback=lambda: f"Thinking of you! ({action.intent})",
                max_tokens=200,
                agent="Doer",
            )
            step("💬", "Draft ready", body)
        plan = {
            "type": "message",
            "channel": hint.get("channel", "whatsapp"),
            "to": hint.get("to", ""),
            "body": body,
        }
    else:
        note = hint.get("note") or action.intent
        plan = {"type": "call", "to": hint.get("to", ""), "note": note}
        step("📞", "Prepared a call note", note)

    step(
        "⏸️", "Plan ready — waiting for your approval",
        "Nothing runs until you approve. I never pay, send, or place a call on my own.",
    )

    plan["trace"] = trace
    action.plan = plan
    action.status = "awaiting_approval"
    db.commit()
    return plan


# ---------------------------------------------------------------------------
# Conversational purchase: clarify → suggest the best → (approve) → add to cart
# ---------------------------------------------------------------------------

SHOP_SYSTEM = (
    "You are a warm, concise shopping helper inside a family app. The user wants "
    "to buy a gift. Ask ONE short, friendly clarifying question at a time to pin "
    "down exactly what to buy — the specific kind/variant, a rough budget, and who "
    "it's for — and stop asking as soon as you could search a shop with confidence "
    "(usually after 1–2 questions). Never ask more than three questions. Reply in "
    "the user's language: {lang}."
)

SHOP_SCHEMA = {
    "type": "object",
    "properties": {
        "confident": {"type": "boolean"},
        "question": {"type": "string"},
        "refined_query": {"type": "string"},
        "budget_max": {"type": ["integer", "null"]},
        "recipient": {"type": ["string", "null"]},
        "note": {"type": "string"},
    },
    "required": ["confident"],
}

_ACCESSORY_RE = re.compile(
    r"\b(case|cover|pouch|screen protector|tempered glass|charger|cable|holder|"
    r"stand|skin|guard|protector|strap|band)\b",
    re.I,
)
_BUDGET_RE = re.compile(
    r"(?:under|below|upto|up to|around|about|max|budget|₹|rs\.?)\s*([\d,]{2,})", re.I
)
_RANGE_RE = re.compile(r"([\d,]{2,})\s*(?:-|–|to)\s*([\d,]{2,})")


def _user_language(db: Session, action: Action) -> str:
    u = db.get(User, action.created_by)
    return (getattr(u, "language", None) or "en") if u else "en"


def _recipient(intent: str) -> str | None:
    m = re.search(r"\bfor\s+(?:my\s+|our\s+)?([A-Za-z]+)", intent)
    return m.group(1) if m else None


def _parse_budget(text: str) -> int | None:
    m = _RANGE_RE.search(text)
    if m:
        return int(m.group(2).replace(",", ""))
    m = _BUDGET_RE.search(text)
    if m:
        return int(m.group(1).replace(",", ""))
    nums = re.findall(r"[\d,]{2,}", text)
    return int(nums[-1].replace(",", "")) if nums else None


def _clean_query(q: str) -> str:
    """Tighten a search query: drop budget words, numbers, and a trailing
    recipient so we search 'assorted chocolates', not the LLM's chatty
    'assorted chocolates gift for Deepa, budget around 800'."""
    q = _RANGE_RE.sub(" ", q)
    q = re.sub(r"\b(budget|under|below|upto|up to|around|about|approx(?:imately)?|max|rs\.?|inr)\b", " ", q, flags=re.I)
    q = re.sub(r"[₹]", " ", q)
    q = re.sub(r"\b\d[\d,]*\b", " ", q)
    q = re.sub(r"\bfor\s+[A-Z][a-z]+\b", " ", q)  # a trailing recipient name
    # filler adjectives that only dilute an Amazon search
    q = re.sub(r"\b(a|an|the|some|good|best|nice|great|lovely|quality|top)\b", " ", q, flags=re.I)
    q = re.sub(r"[,;]+", " ", q)
    return re.sub(r"\s+", " ", q).strip()


def _merge_query(item: str, pref_text: str) -> str:
    """Fold a preference reply ('assorted, under 500') into the search query,
    dropping budget words/numbers."""
    pref = _RANGE_RE.sub(" ", pref_text)
    pref = _BUDGET_RE.sub(" ", pref)
    pref = re.sub(r"[₹]|\brs\.?\b|\bunder\b|\bbelow\b|\baround\b|\babout\b|\bbudget\b|[\d,]{2,}", " ", pref, flags=re.I)
    words = [w for w in re.findall(r"[A-Za-z]+", pref) if len(w) > 2 and w.lower() not in item.lower()]
    extra = " ".join(words[:4])
    return f"{extra} {item}".strip() if extra else item


def _fallback_turn(intent: str, conversation: list) -> dict:
    """No-LLM path: ask exactly one budget/preference question, then commit."""
    item = _extract_item(intent)
    asked = [c for c in conversation if c["role"] == "agent"]
    if not asked:
        return {
            "confident": False,
            "question": "Happy to help! Roughly what's your budget, and any preference — brand, type, or colour?",
            "refined_query": item, "budget_max": None, "recipient": _recipient(intent), "note": "",
        }
    last_user = next((c["text"] for c in reversed(conversation) if c["role"] == "user"), "")
    budget = _parse_budget(last_user)
    refined = _merge_query(item, last_user)
    note = (f"I'll find the best “{refined}”" + (f" under ₹{budget}" if budget else "")
            + " and add it to your cart.")
    return {"confident": True, "question": "", "refined_query": refined,
            "budget_max": budget, "recipient": _recipient(intent), "note": note}


def _next_turn(intent: str, conversation: list, language: str) -> dict:
    convo_text = "\n".join(f"{c['role']}: {c['text']}" for c in conversation)
    return complete_json(
        f"Original request: {intent}\nConversation so far:\n{convo_text}",
        system=SHOP_SYSTEM.format(lang=language),
        schema=SHOP_SCHEMA,
        fallback=lambda: _fallback_turn(intent, conversation),
        agent="Doer",
    )


def _start_purchase(db: Session, action: Action, hint: dict, trace: list, step) -> dict:
    item = hint.get("item") or _extract_item(action.intent)
    step("🔎", "Worked out the gist", f"looks like you want: {item}")
    plan = {
        "type": "purchase",
        "stage": "clarifying",
        "item": item,
        "site": hint.get("site") or settings.doer_purchase_site,
        "conversation": [{"role": "user", "text": action.intent}],
        "slots": {"budget_max": None, "recipient": _recipient(action.intent)},
        "trace": trace,
    }
    turn = _next_turn(action.intent, plan["conversation"], _user_language(db, action))
    question = turn.get("question") or "Roughly what's your budget, and any preference?"
    plan["conversation"].append({"role": "agent", "text": question})
    plan["slots"]["refined_query"] = turn.get("refined_query") or item
    step("💬", "Asked a clarifying question", question)
    action.plan = plan
    action.status = "clarifying"
    db.commit()
    return plan


def advance_purchase(db: Session, action: Action, message: str) -> dict:
    """A reply in the clarifying chat: either ask one more question, or (once
    confident) search the shop, pick the best product, and move to approval."""
    from sqlalchemy.orm.attributes import flag_modified

    plan = action.plan or {}
    trace = plan.setdefault("trace", [])
    step = _make_tracer(action.created_by, trace)
    convo = plan.setdefault("conversation", [])
    convo.append({"role": "user", "text": message})
    step("🗣️", "You replied", message)

    asked = [c for c in convo if c["role"] == "agent"]
    turn = _next_turn(action.intent, convo, _user_language(db, action))
    confident = bool(turn.get("confident")) or len(asked) >= 3

    if not confident:
        question = turn.get("question") or "Anything else — colour, brand, or budget?"
        convo.append({"role": "agent", "text": question})
        plan["slots"]["refined_query"] = turn.get("refined_query") or plan.get("item")
        step("💬", "Asked a follow-up", question)
        action.plan = plan
        flag_modified(action, "plan")
        db.commit()
        return plan

    return _finalize_purchase(db, action, plan, turn, step)


def _finalize_purchase(db: Session, action: Action, plan: dict, turn: dict, step) -> dict:
    from sqlalchemy.orm.attributes import flag_modified

    refined = _clean_query((turn.get("refined_query") or plan.get("item") or "").strip())
    if not refined:
        refined = _clean_query(plan.get("item", "")) or plan.get("item", "")
    budget = turn.get("budget_max")
    plan["item"] = refined
    plan["budget_max"] = budget
    plan["stage"] = "ready"
    convo = plan.setdefault("conversation", [])
    step("🧠", "Got what I need", f"searching for “{refined}”" + (f" under ₹{budget}" if budget else ""))

    candidate, shortlist = None, []
    if settings.doer_live_search:
        step("🔍", "Searching Amazon.in for real options", refined)
        candidates = _search_amazon_candidates(refined, budget)
        if not candidates:
            step("💡", "Amazon didn't cooperate — asking my own knowledge", "suggesting real products instead")
            candidates = _llm_suggest_products(refined, budget)
        if candidates:
            candidate, reason = _pick_best(candidates, action.intent, refined, budget)
            candidate = dict(candidate, reason=reason)
            shortlist = candidates[:4]
            step("⭐", "Picked the best match", f"{candidate['title'][:70]} — {candidate.get('price_text', '')}")
        else:
            step("⚠️", "Couldn't find options right now", "I'll search again when you approve.")
    else:
        step("🛍️", "Prepared the search", "I'll open the shop when you approve.")

    plan["candidate"] = candidate
    plan["shortlist"] = shortlist
    plan["search_url"] = f"https://www.amazon.in/s?k={quote(refined)}"

    if candidate:
        msg = (f"I found this for you: {candidate['title'][:90]} — "
               f"{candidate.get('price_text', 'price shown at checkout')}. "
               "Approve and I'll add it to your cart — you always pay.")
    else:
        msg = ((turn.get("note") or f"I'll find the best “{refined}”"
                + (f" under ₹{budget}" if budget else "") + " and add it to your cart.")
               + " Approve to go ahead — you always pay.")
    convo.append({"role": "agent", "text": msg})
    step("⏸️", "Ready — waiting for your approval", "nothing is bought until you approve; I never pay.")

    action.plan = plan
    flag_modified(action, "plan")
    action.status = "awaiting_approval"
    db.commit()
    return plan


def _safe_text(loc) -> str:
    try:
        return (loc.text_content(timeout=1500) or "").strip()
    except Exception:
        return ""


def _safe_attr(loc, name: str) -> str:
    try:
        return loc.get_attribute(name, timeout=1500) or ""
    except Exception:
        return ""


def _parse_price(text: str) -> int | None:
    m = re.search(r"[\d,]{2,}", text or "")
    return int(m.group(0).replace(",", "")) if m else None


def _search_amazon_candidates(query: str, budget_max: int | None = None, limit: int = 6) -> list[dict]:
    """Scrape a handful of real Amazon.in results (title, price, url, image),
    filtering out accessories unless the query itself is for one. Best-effort:
    returns [] on any failure so the caller falls back gracefully."""
    q_is_accessory = bool(_ACCESSORY_RE.search(query))
    from playwright.sync_api import sync_playwright

    # Amazon intermittently serves a bot challenge (no result grid). A couple of
    # fresh-context retries turn that flaky ~50% into reliably getting the page.
    for _attempt in range(3):
        try:
            pw = sync_playwright().start()
            browser, page = _launch(pw, headless=True)  # scraping is always invisible
            try:
                _goto_with_retry(page, f"https://www.amazon.in/s?k={quote(query)}")
                try:
                    page.wait_for_selector(
                        'div[data-component-type="s-search-result"]', timeout=9000
                    )
                except Exception:
                    continue  # challenge page — retry with a fresh context
                cards = page.locator('div[data-component-type="s-search-result"]')
                good: list[dict] = []       # real products (accessories removed)
                any_product: list[dict] = []  # everything, as a last resort
                for i in range(min(cards.count(), 28)):
                    if len(good) >= limit:
                        break
                    card = cards.nth(i)
                    href = _safe_attr(card.locator('a[href*="/dp/"]').first, "href")
                    if not href:
                        continue
                    title = _safe_text(card.locator("h2 span, h2 a span").first) or _safe_text(
                        card.locator('a[href*="/dp/"]').first
                    )
                    if not title:
                        continue
                    price_text = _safe_text(card.locator("span.a-price span.a-offscreen").first)
                    item = {
                        "title": title,
                        "url": href if href.startswith("http") else f"https://www.amazon.in{href}",
                        "price": _parse_price(price_text),
                        "price_text": price_text or "price at checkout",
                        "image": _safe_attr(card.locator("img.s-image").first, "src"),
                    }
                    any_product.append(item)
                    if not q_is_accessory and _ACCESSORY_RE.search(title):
                        continue  # skip a case/cover when they asked for the real thing
                    good.append(item)
                # Budget shapes RANKING (in _pick_best), not availability.
                results = (good or any_product)[:limit]
                if results:
                    return results
            finally:
                browser.close()
                pw.stop()
        except Exception:
            traceback.print_exc()
    return []


def _llm_suggest_products(query: str, budget_max: int | None) -> list[dict]:
    """When live scraping keeps coming up empty, still recommend real, specific
    products via the LLM — each links to an Amazon search for that exact item,
    so the demo never dead-ends on a blank recommendation."""
    schema = {
        "type": "object",
        "properties": {
            "products": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}, "price_text": {"type": "string"}},
                    "required": ["title"],
                },
            }
        },
        "required": ["products"],
    }

    def _fb() -> dict:
        return {"products": [{"title": query, "price_text": (f"around ₹{budget_max}" if budget_max else "varies")}]}

    res = complete_json(
        f"Suggest 3 real, specific, popular products to buy for: {query}."
        + (f" Keep them around ₹{budget_max}." if budget_max else "")
        + " Use exact product names (brand + model/variant) a shopper would recognise.",
        system="You are a shopping expert. Recommend real, specific products people can actually buy.",
        schema=schema,
        fallback=_fb,
        agent="Doer",
    )
    out: list[dict] = []
    for p in (res.get("products") or [])[:4]:
        title = (p.get("title") or "").strip()
        if not title:
            continue
        out.append({
            "title": title,
            "url": f"https://www.amazon.in/s?k={quote(title)}",  # a search, not a /dp/ page
            "price": None,
            "price_text": p.get("price_text") or "see options",
            "image": None,
            "search_only": True,
        })
    return out


def _pick_best(candidates: list[dict], intent: str, query: str, budget_max: int | None):
    """LLM ranks the scraped candidates; heuristic fallback picks the best
    in-budget keyword match. Returns (candidate, reason)."""
    listing = "\n".join(
        f"{i}. {c['title']} — {c.get('price_text', '?')}" for i, c in enumerate(candidates)
    )
    words = [w for w in re.findall(r"[a-z]+", query.lower()) if len(w) > 2]

    def _fb() -> dict:
        def score(c: dict):
            title = c["title"].lower()
            match = sum(1 for w in words if w in title)
            price = c.get("price") or 10**9
            within = budget_max is None or price <= budget_max
            return (within, match, -price)
        best = max(range(len(candidates)), key=lambda i: score(candidates[i]))
        return {"index": best, "reason": "closest match within your budget"}

    res = complete_json(
        f"Shopper's request: {intent}\nBudget max (₹): {budget_max}\nCandidates:\n{listing}\n"
        "Choose the ONE that best matches the request and budget and is the actual "
        "product (not an accessory). Return {index, reason}.",
        system="You choose the single best product for a gift shopper. Be practical and match the budget.",
        schema={"type": "object", "properties": {"index": {"type": "integer"}, "reason": {"type": "string"}}, "required": ["index"]},
        fallback=_fb,
        agent="Doer",
    )
    idx = res.get("index", 0)
    if not isinstance(idx, int) or idx < 0 or idx >= len(candidates):
        idx = 0
    return candidates[idx], (res.get("reason") or "the best match for what you asked")


def _add_known_product(page, url: str) -> None:
    """Open a specific product page and add THAT product to the cart."""
    _goto_with_retry(page, url if url.startswith("http") else f"https://www.amazon.in{url}")
    page.wait_for_selector("#add-to-cart-button", timeout=15000)
    add_button = page.locator("#add-to-cart-button").first
    guard_click(add_button.get_attribute("value") or "Add to Cart")
    add_button.click(timeout=10000)
    page.wait_for_timeout(1500)
    _goto_with_retry(page, "https://www.amazon.in/gp/cart/view.html")
    try:
        page.wait_for_load_state("domcontentloaded", timeout=10000)
    except Exception:
        pass


def complete_action(db: Session, action: Action, user: User) -> dict:
    """Runs AFTER human approval only. Completes up to the safe handoff:
    cart ready to review, message drafted to send, number ready to dial."""
    plan = action.plan or {}
    kind = plan.get("type")
    trace: list[dict] = []
    step = _make_tracer(action.created_by, trace)
    step("✅", "You approved", "now completing — but only up to the safe handoff.")

    if kind == "purchase":
        result = _prepare_purchase(action, plan, step)
    elif kind == "message":
        body = quote(plan.get("body", ""))
        step("🔗", "Built a ready-to-send link", "prepared it, but I will NOT press send — that's yours.")
        result = {
            "status": "ready_for_human",
            "note": "Your message is drafted — read it once and press send yourself.",
            "deep_link": f"https://wa.me/{plan.get('to', '')}?text={body}"
            if plan.get("channel") == "whatsapp"
            else None,
            "body": plan.get("body", ""),
        }
    elif kind == "call":
        step("🔗", "Prepared the dial link", "the number is ready; you place the call yourself.")
        result = {
            "status": "ready_for_human",
            "note": "All set — place the call whenever you're ready.",
            "deep_link": f"tel:{plan.get('to', '')}" if plan.get("to") else None,
            "talking_note": plan.get("note", ""),
        }
    else:
        result = {"status": "manual", "note": "I wasn't sure how to prepare this — it's all yours."}

    step("✋", "Stopped at the safe handoff", "over to you to pay, send, or call — I never finish that step.")
    result["trace"] = trace
    action.result = result
    action.status = "completed"
    action.completed_at = datetime.utcnow()
    db.commit()
    return result


_ITEM_RE = re.compile(
    r"\b(?:order|buy|purchase|book|get)\s+(?:some\s+|a\s+|an\s+|the\s+)?(.+?)"
    r"(?:\s+for\s+\S.*)?$",  # strip a trailing "for <recipient>" (kept in slots)
    re.I,
)


def _extract_item(intent: str) -> str:
    """'I want to order chocolates for my husband.' -> 'chocolates'."""
    cleaned = intent.strip().rstrip(".!?।")
    match = _ITEM_RE.search(cleaned)
    if match:
        item = match.group(1).strip().rstrip(".!?।")
        if item:
            return item
    return cleaned


BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
# Amazon fingerprints headless Chromium and serves a bot challenge (which
# Chrome treats as a download). These launch args + context + the webdriver
# mask make the browser look like an ordinary user so the page actually loads.
_LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
]

# headful browsers stay open for the human to finish — keep refs so the
# driver process isn't garbage-collected out from under them
_open_browsers: list = []


def _launch(pw, headless: bool):
    """A browser + page tuned to pass as a real user (see _LAUNCH_ARGS)."""
    browser = pw.chromium.launch(headless=headless, args=_LAUNCH_ARGS)
    context = browser.new_context(
        user_agent=BROWSER_UA,
        locale="en-IN",
        viewport={"width": 1366, "height": 900},
        extra_http_headers={"Accept-Language": "en-IN,en;q=0.9"},
        accept_downloads=False,
    )
    context.add_init_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
    )
    return browser, context.new_page()


def _goto_with_retry(page, url: str, attempts: int = 3) -> None:
    last = None
    for _ in range(attempts):
        try:
            # "commit" returns as soon as the response lands — avoids Amazon's
            # bot-challenge "Download is starting" race on full-load waits.
            page.goto(url, timeout=30000, wait_until="commit")
            return
        except Exception as exc:  # bot-detection sometimes serves junk; retry
            last = exc
            page.wait_for_timeout(1200)
    raise last


def _prepare_purchase(action: Action, plan: dict, step=None) -> dict:
    """Best-effort Playwright cart prep. Stops at the cart/checkout page — the
    human reviews and pays. In headful mode the browser window STAYS OPEN so
    the human can finish right there. Any failure still hands the human a
    useful link, so approval always ends in something actionable. `step` is the
    tracer from complete_action so the browser work shows up in the trace."""
    if step is None:
        step = lambda *a, **k: None  # noqa: E731 — no-op when called directly
    item = plan.get("item", "")
    site = plan.get("site") or settings.doer_purchase_site
    candidate = plan.get("candidate") or {}
    search_url = plan.get("search_url") or (
        f"https://www.amazon.in/s?k={quote(item)}" if "amazon" in site else site
    )
    manual = {
        "status": "manual",
        "url": candidate.get("url") or search_url,
        "item": candidate.get("title") or item,
        "note": (
            "I couldn't finish preparing the cart automatically — here's the shop "
            "with the details, you can do it in one tap. I never enter payment details."
        ),
        "plan": plan,
    }
    # Offline/test path: no real browser — hand over a ready link, deterministically.
    if not settings.doer_live_search:
        step("🛍️", "Prepared your shopping link", "(live browser is off in this environment)")
        return {
            "status": "manual",
            "url": candidate.get("url") or search_url,
            "item": candidate.get("title") or item,
            "note": "Here's the shop, ready for you — review and pay yourself. I never enter payment details.",
        }
    step(
        "🛡️", "Safety guards armed",
        "for the whole browser session I refuse any card/CVV/password field and any pay/place-order button.",
    )
    try:
        from playwright.sync_api import sync_playwright

        mode = "a visible window you can watch" if not settings.doer_headless else "a headless (invisible) browser"
        step("🌐", "Opening a browser", mode)
        pw = sync_playwright().start()
        browser, page = _launch(pw, headless=settings.doer_headless)
        try:
            if candidate.get("url") and "/dp/" in candidate.get("url", ""):
                step("🎯", "Opening the exact product you approved", candidate.get("title", "")[:70])
                _add_known_product(page, candidate["url"])
            elif candidate.get("title"):
                # an LLM-suggested product (no direct URL) — search its exact name
                step("🎯", "Finding the product you approved", candidate["title"][:70])
                _amazon_cart(page, candidate["title"])
            elif "amazon" in site:
                step("🔍", "Searching Amazon.in", f"for “{item}”")
                _amazon_cart(page, item)
            else:
                step("🔍", f"Searching {site}", f"for “{item}”")
                _generic_cart(page, site, item)
            # STOP. The human reviews price and address and pays.
            step("🛒", "Added it to the cart", (candidate.get("title") or item)[:70])
            step("🛡️", "No payment or credential field was ever touched", "the guards stayed green the whole time.")

            os.makedirs(settings.actions_dir, exist_ok=True)
            shot = os.path.join(settings.actions_dir, f"action-{action.id}.png")
            page.screenshot(path=shot)
            step("📸", "Saved a screenshot of the cart", "so you can review before paying.")
            result = {
                "status": "ready_for_human",
                "checkout_url": page.url,
                "screenshot": shot,
                "item": candidate.get("title") or item,
                "note": (
                    "The cart is ready — review the item, price, and address, "
                    "then pay yourself. I stop before any payment."
                ),
            }
            if settings.doer_headless:
                browser.close()
                pw.stop()
            else:
                # leave the window open at the cart for the human
                _open_browsers.append((pw, browser))
                result["note"] += " The browser window is open for you."
                step("🖐️", "Left the browser open at the cart", "finish the payment there yourself.")
            return result
        except DoerSafetyError:
            step("🛡️", "Refused an unsafe step", "hit a payment/credential action and stopped immediately.")
            browser.close()
            pw.stop()
            raise
        except Exception:
            traceback.print_exc()  # server log only — the user gets the kind note
            browser.close()
            pw.stop()
            step("⚠️", "Couldn't finish the cart automatically", "handing you a direct shop link instead — still no payment from me.")
            return manual
    except DoerSafetyError:
        raise
    except Exception:
        traceback.print_exc()
        step("⚠️", "Couldn't open the browser", "handing you a direct shop link instead.")
        return manual


def _amazon_cart(page, item: str) -> None:
    """Search fallback (when we don't already have a chosen product URL): pick
    the first real product, skipping accessories, then add it."""
    _goto_with_retry(page, f"https://www.amazon.in/s?k={quote(item)}")
    try:
        page.wait_for_selector('div[data-component-type="s-search-result"]', timeout=15000)
    except Exception:
        pass
    item_is_accessory = bool(_ACCESSORY_RE.search(item))
    cards = page.locator('div[data-component-type="s-search-result"]')
    href = None
    for i in range(min(cards.count(), 20)):
        card = cards.nth(i)
        candidate_href = _safe_attr(card.locator('a[href*="/dp/"]').first, "href")
        if not candidate_href:
            continue
        title = _safe_text(card.locator("h2 span, h2 a span").first)
        if not item_is_accessory and title and _ACCESSORY_RE.search(title):
            continue  # don't buy a case when they asked for a phone
        href = candidate_href
        break
    if not href:  # nothing passed the filter — take the very first result
        href = _safe_attr(
            page.locator('div[data-component-type="s-search-result"] a[href*="/dp/"]').first,
            "href",
        )
    if not href:
        raise RuntimeError("no search results")
    _add_known_product(page, href)


def _generic_cart(page, site: str, item: str) -> None:
    words = [w for w in re.findall(r"[a-z0-9]+", item.lower()) if len(w) > 2]
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
