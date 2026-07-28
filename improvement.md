# Aangan — "Personal Standpoint" Improvement Session

> **You are implementing a planned product upgrade, end to end, in this repo.**
> This document is self-contained: read it fully, then read `CLAUDE.md`, then build.
> Do not stop at code — set up localhost, run everything, test everything (automated
> + manual browser flows), and finish by writing the report described at the end.
> The founder will review the running app against this document afterward.

---

## 1. Context — what Aangan is and what's wrong

Aangan is a private family voice-journal: FastAPI + SQLite + ChromaDB backend in
`backend/`, React + Vite frontend in `frontend/`. Each member journals by voice or
text; everything is **private by default**; an AI "Companion" answers a family
member's questions **only from what each person chose to share**. The privacy spine
(`backend/agents/librarian.py` + `consent_guardian.py`) and its tests
(`backend/tests/test_spine_*.py`) are sacred — see `CLAUDE.md` "Hard rules".

**The founder's observation (the reason for this session):** the product has no
standpoint as a *personal* journal. All value flows to the family; the author gets
nothing back day-to-day. The Mirror agent (mood/themes/streaks,
`backend/agents/mirror.py`) exists but is buried as a small card inside the Me
(settings) screen. There are no personal nudges. And "Ask" is stateless one-shot
Q&A — not a conversation.

**The vision to implement — one product, two loops:**
1. *Private diary that is useful to ME daily* — a first-class "My Thoughts" screen
   that makes sense of my ramblings, plus personal nudges like:
   *"Hey Adi — on Monday you said you have an important meeting on Friday.
   Hope you haven't forgotten. All the best!"*
2. *Family courtyard that is useful to US* — unchanged, but talking to the
   Companion becomes a natural multi-turn conversation (talk replied with talk),
   while journaling stays "I speak, the journal writes" (speech → refined text).

---

## 2. Non-negotiables (do not weaken)

1. All retrieval stays visibility-filtered in code (`librarian.is_visible` on every
   hit) — **including every turn of the new conversation mode**.
2. Only `consent_guardian` changes visibility, only for the author.
3. `doer.py` guards unchanged. Alert wording never medical — personal nudges must
   also never sound medical or diagnostic.
4. The spine tests are the gate. All existing tests must pass when you finish
   (`cd backend && .venv/Scripts/python -m pytest tests/ -q` — 140+ tests).
5. Every LLM call goes through `agents/llm.py` with a `fallback=` callable — the
   whole app must keep working with **zero API keys**.
6. New personal features read **only the author's own rows** (author-only data —
   assert this in tests anyway).
7. Frontend keeps the "Chitthi / Letters Home" design language
   (`frontend/src/styles/tokens.css`, existing screens as reference) and the JWT
   stays memory-only.
8. Schema changes ship as Alembic revisions (`backend/alembic/`), never by editing
   the baseline. `python scripts/migrate.py` must bring an existing DB current.

---

## 3. Feature A — "My Thoughts" screen (personal dashboard)

**Goal:** promote the personal layer to a first-class nav destination. Author-only.

### Backend
- New route file `backend/routes/thoughts_routes.py` → `GET /thoughts` (auth
  required), returning for the **current user only**:
  - `mirror`: the existing `mirror.reflect()` output (mood series, themes, streaks,
    total entries) — reuse, don't duplicate.
  - `reflection`: a warm weekly reflection over the last 7 days of the author's own
    entries: 2–3 sentences, "what you kept coming back to", written to the author
    ("you"), in the author's language. New agent `backend/agents/reflector.py`:
    LLM via `complete()` (agent name `"Reflector"`, metered) with a deterministic
    fallback (e.g. counts: "You wrote N times this week. Themes: X, Y." + the most
    frequent positive/negative words). Never clinical, never diagnostic.
  - `open_loops`: the author's recent `plan` facts (last 14 days) that have no
    associated `date` fact — "plans you voiced" with their `source_quote` and age.
  - `upcoming`: the author's own `date` facts within the next 14 days (reuse the
    month/day recurrence logic style from `relationship_radar.py`).
- Activity feed: emit `Reflector` events ("Reading your week back to you…") via
  `services/activity.py` so the Agents panel shows it.

### Frontend
- New screen `frontend/src/screens/Thoughts.jsx`, route `/thoughts`, nav item
  between Journal and Ask. Nav label: en "Thoughts", hi "मन की बातें" (add to
  `frontend/src/i18n.js`; pick a fitting icon in `icons.jsx` — an inkwell/mirror).
- Layout (Letters Home language): the weekly reflection as a hand-written note at
  top; mood strip + streak + themes (move the guts of the Mirror card out of
  `Me.jsx` — Me keeps account/security only, with a small link to /thoughts);
  "Open loops" as margin-notes with their source quotes; "Coming up" as small
  postmarked date chips.
- Empty states in both languages ("Your thoughts will gather here as you write.").

### Acceptance
- Log in as Aditya (seed data): /thoughts shows a reflection referencing his
  week, his "plan something special for Deepa's birthday" appears under open
  loops/upcoming, streak/mood render. Deepa's or Mumma's content NEVER appears.
- Works keyless (fallback reflection) and with keys (LLM reflection, metered in
  `llm_calls` with agent `Reflector`).

---

## 4. Feature B — Personal Radar (prospective-memory nudges)

**Goal:** the journal remembers for you. The founder's exact example: journal on
Monday "I have an important meeting on Friday" → around Thursday/Friday a warm
nudge: *"On Monday you mentioned an important meeting on Friday — all the best!"*

### Backend
- New agent `backend/agents/personal_radar.py`:
  - `radar(db, user, now=None) -> list[Nudge]` (reuse the `Nudge` dataclass from
    `prompter.py`).
  - Source: the **author's own** facts only. Two nudge kinds:
    1. `personal_date`: a `date`-type fact (or a `plan` fact whose
       `structured.date` exists) whose date is today or within the next 2 days →
       "On {weekday you said it} you mentioned {content} — {warm wish}." Wish
       varies by proximity: day before → "all the best for tomorrow"; same day →
       "it's today — you've got this".
    2. `open_plan`: a `plan` fact 3–10 days old with no date → at most ONE gentle
       "Still on your mind?" style nudge.
  - Wording: LLM via `complete()` (agent `"PersonalRadar"`, fallback = plain
    deterministic templates above, en + hi). Run the same medical-wording
    rejection regex used in `alerter.py` (extract it to a shared helper rather
    than copy-pasting).
  - Anti-nag rules (enforce in code): max 2 personal nudges per call; never nudge
    the same fact twice in one day (simplest: deterministic — recompute is fine,
    but keep output stable within a day); nothing for facts older than 14 days.
- Wire in as the third source in `backend/routes/nudge_routes.py`:
  `prompter.nudges() + relationship_radar.radar() + personal_radar.radar()`.
- Emit an activity event when a personal nudge is produced ("Radar — remembering
  Friday for you…").

### Frontend
- `Home.jsx` already renders nudges as sticky notes — give `personal_date` /
  `open_plan` kinds their own affordance: personal ones get a 🪔 pin and, for
  `personal_date`, a "Thanks, noted ✓" dismiss (client-side hide is acceptable
  for the pilot). Also surface the same personal nudges at the top of /thoughts.
- Note in code comments: real scheduled delivery (Thursday-night push) needs a
  push channel that doesn't exist yet — on-next-open is the pilot behavior,
  documented, not a bug.

### Acceptance
- Seeded/manual test: as Aditya, journal "I have an important meeting on Friday."
  on a simulated Monday (tests may pass `now=`), then GET /nudges with
  `now=Thursday` → the personal nudge appears with warm non-medical wording; it
  references only Aditya's own facts. Deepa never sees it.
- Unit tests in `backend/tests/test_personal_radar.py`: date proximity windows,
  anti-nag caps, own-facts-only, medical-wording rejection, keyless fallback.

---

## 5. Feature C — Conversational Companion + multilingual voice

**Goal:** journaling stays dictation (unchanged). Asking about family becomes a
natural conversation — talk replied with talk, multi-turn, with memory of the
conversation — while the privacy spine re-checks visibility **on every turn**.

### Backend
- **New tables** (one Alembic revision): `conversations`
  (id, user_id FK, circle_id FK, started_at, last_at) and `conversation_turns`
  (id, conversation_id FK, role `user|companion`, text, snippet_count, created_at).
- New route file `backend/routes/converse_routes.py`:
  - `POST /converse` — body `{conversation_id?: int, message?: str}` or multipart
    with `audio` (transcribe first, exactly like `/ask` does). Missing
    `conversation_id` ⇒ create a new conversation. Returns
    `{conversation_id, reply, language, snippets: [...]}`.
  - `GET /conversations/{id}` — the turn history (owner-only, 404 otherwise).
  - Entitlements: **each user turn counts as one ask** — call
    `entitlements.check_ask_allowed` and write an `AskRecord` per turn (same as
    `/ask`), so the freemium caps and unit economics stay truthful.
- Conductor: add `handle_converse(db, user, conversation_id, message)`:
  - Load the last 8 turns as conversation context.
  - `librarian.search(db, user, message)` fresh **every turn** (never cache
    snippets across turns — a re-share/un-share must take effect immediately).
    If the message is a short follow-up ("what else?", "और?"), also search with
    the previous user turn appended so retrieval has a topic.
  - Companion: add a conversational system prompt variant in `companion.py`
    (same grounding rules — ONLY provided snippets, say-so-kindly when nothing is
    shared — but conversational: reacts to the prior turn, short spoken-style
    sentences, no lists, warmth per the existing SYSTEM). Deterministic fallback:
    the existing `_fallback_answer` is fine.
- **Voice replies (this is where Mumma's Hindi gets fixed).** Rework
  `backend/agents/speaker.py` into a provider chain, keeping the current
  signature (`synthesize(text, language) -> bytes | None`):
  1. If language is English → Deepgram Aura (current behavior, keep).
  2. Else (Hindi and other non-Aura languages) → **OpenAI TTS**
     (`POST https://api.openai.com/v1/audio/speech`, model `gpt-4o-mini-tts`,
     a warm voice e.g. `coral`, `response_format: "mp3"`, and an
     `instructions` field asking for a warm, gentle, family tone). OpenAI TTS
     speaks Hindi. **Gating:** use it only when `settings.openai_api_key` is set
     AND `settings.openai_base_url` is unset or points to `api.openai.com` —
     OpenRouter does NOT proxy the audio/speech endpoint, so if the key is an
     OpenRouter key, skip this hop (log once, don't error).
  3. Else return `None` → the frontend falls back to the browser voice (existing
     behavior, keep).
  - STT needs **no change**: `transcriber.py` already uses Deepgram `nova-3`
    with `detect_language=True`, which handles Hindi (and code-switching).
- Metering: conversational LLM calls go through `llm.py` as usual (agent
  `"Companion"`); nothing new needed.

### Frontend
- Rebuild `Ask.jsx` as a conversation ("Baithak — sit and talk with the
  Companion"; hi: "बैठक"). Keep the route `/ask` and nav position:
  - A running thread (newest at bottom, auto-scroll), each companion turn with
    the existing sources-disclosure ("From N shared moments") and 🚩 report.
  - Hold-to-talk per turn (existing `HoldToTalk`) AND a text input. After each
    reply: auto-play the voice via the existing `/speak`→`speak()` path (now the
    reply itself comes from `/converse`; keep using `postBlob('/speak', ...)` for
    audio, or return audio inline — your choice, but browser-voice fallback must
    survive).
  - "🪶 New conversation" button; conversation persists across a reload of the
    screen within the session via `conversation_id` in component state.
- The Journal screen is NOT made conversational — it stays scribe-mode. Add a
  one-line hint under the Journal composer: "Want to talk *with* someone? Visit
  the Baithak." (i18n both languages.)

### Acceptance
- Multi-turn works: "What would Deepa want for her birthday?" → black-dress
  answer → follow-up "when did she say that?" answers from context with the
  date, without re-asking the full question.
- **Spine test (mandatory, add to `backend/tests/test_converse.py`):** marker
  string in Deepa's private entry; 3-turn conversation as Aditya trying to fish
  for it (incl. follow-ups) → marker never appears in any reply. Also: a fact
  shared mid-conversation becomes visible on the next turn; un-shared mid-
  conversation disappears on the next turn.
- Caps: with a circle at its ask cap, /converse returns the same friendly 402.
- Keyless: conversation still works with deterministic fallback replies; /speak
  returns 204 and the browser voice takes over.
- Hindi: as Mumma (hi), a reply's TTS uses OpenAI TTS when a direct OpenAI key
  is configured; otherwise browser voice — never silence, never a crash.

---

## 6. Cross-cutting requirements

- **i18n:** every new user-facing string in `frontend/src/i18n.js` in en + hi.
- **Migrations:** one Alembic revision for the new tables; `seed.py` untouched
  except: add one seeded plan fact for Aditya with a date ~3 days out so the
  demo shows a personal nudge on first login (keep the existing seed entries
  exactly as they are — the business-plan demo depends on them).
- **Docs:** update `CLAUDE.md` architecture map (new agents/routes/tables, the
  speaker chain) and `README`/`SETUP.md` if any new env var is introduced
  (avoid new env vars if possible). Add the OpenRouter-has-no-TTS caveat where
  `OPENAI_BASE_URL` is documented in `.env.example`.
- **Tests:** everything existing stays green; new tests for reflector (fallback
  determinism), personal radar, converse spine + caps + ownership (another
  user's conversation_id → 404). Follow `conftest.py` patterns (keyless
  autouse, fake embedder, `make_entry`).
- **CI:** `.github/workflows/ci.yml` must pass as-is (no new services in tests).

## 7. Localhost setup & full manual verification (required, not optional)

This machine is **Windows 11** (PowerShell/Git Bash). Gotchas:

- Python: needs **3.11 or 3.12** (3.13+ breaks passlib). Check `py -0` first; if
  neither is present: `winget install Python.Python.3.12`, then from `backend/`:
  `py -3.12 -m venv .venv`, `.venv\Scripts\pip install -r requirements.txt`.
- First `python seed.py` downloads the ~470MB multilingual embedding model once —
  let it finish. `uvicorn` must run from `backend/`:
  `.venv\Scripts\uvicorn app:app --reload --port 8000 --reload-exclude chroma_data/* --reload-exclude data/*`
- Frontend: `cd frontend && npm install && npm run dev` → http://localhost:5173.
- API keys: check whether `backend/.env` exists and has keys. Run the manual
  pass **both** ways if keys exist (with keys, then `AANGAN_ENV`/keys unset for
  keyless) — at minimum run keyless; note in the report which modes you ran.
- Seeded logins: `aditya|deepa|mumma|abhishek@ghar.family` / `aangan123`.

Manual script (do all of it in a real browser, e.g. via the preview/browser
tooling; screenshot each numbered step for the report):

1. Seed fresh (`python seed.py`). Log in as Aditya.
2. **Thoughts:** open /thoughts — reflection, mood strip, streak, open loops
   (Deepa's-birthday plan), upcoming dates all render; nothing from other members.
3. **Personal nudge:** journal "I have an important meeting on Friday." Confirm a
   personal nudge appears (Home + Thoughts) with warm wording. Confirm Deepa
   (log in separately) sees none of it.
4. **Baithak:** 3-turn conversation incl. the birthday question, a follow-up, and
   a fishing attempt at Deepa's private entry (must stay sealed). Voice reply
   plays (or browser voice keyless). New-conversation button works.
5. **Regression sweep:** Journal capture + share suggestion; Mumma Hindi entry →
   knee alert for the sons; Actions chocolates flow to the approval receipt;
   Memory book; Me → export JSON downloads; Agents panel shows Reflector/Radar/
   Companion events.
6. `cd backend && .venv\Scripts\python -m pytest tests/ -q` → all green.
   `cd frontend && npm run build` → clean.

## 8. The report (final deliverable)

Write `docs/IMPROVEMENT_REPORT.md` containing:

1. **What was built** — feature-by-feature vs sections 3–5, with any deviations
   and their reasons (deviations from the vision need strong justification).
2. **Privacy statement** — exactly how each new surface enforces the spine, and
   the new spine tests proving it (file:test names).
3. **Test evidence** — full pytest summary line (count must be ≥ previous 140,
   all passing), frontend build output, and which key-modes were manually tested.
4. **Manual walkthrough evidence** — the numbered script above with a screenshot
   per step and one line on what it proves.
5. **Voice matrix** — reply-voice behavior for en/hi × keys/keyless on this
   machine (Aura / OpenAI TTS / browser fallback).
6. **Known gaps & follow-ups** — e.g. push-channel for timed nudge delivery,
   anything deferred.
7. **Demo script** — 90 seconds: the founder logs in as Aditya and sees the new
   personal loop end to end.

Then stop. The founder will review the app against this document.
