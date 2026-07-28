# Aangan — "Personal Standpoint" Improvement Report

**Session:** 28 July 2026 · Windows 11 · Python 3.11 venv · Node 22
**Scope:** `improvement.md` at the repo root, implemented end to end: My Thoughts
(Feature A), Personal Radar (Feature B), conversational Baithak + multilingual
voice chain (Feature C), plus localhost setup, automated tests, and the full
manual browser verification below.

---

## 1. What was built

### Feature A — "My Thoughts" screen (personal dashboard)

| Spec item | Delivered |
|---|---|
| `GET /thoughts` (auth required, current user only) | [backend/routes/thoughts_routes.py](../backend/routes/thoughts_routes.py) — `mirror` (reuses `mirror.reflect()`), `reflection`, `open_loops`, `upcoming` |
| New agent `reflector.py`, LLM agent name `Reflector`, metered, deterministic fallback | [backend/agents/reflector.py](../backend/agents/reflector.py) — warm 2–3 sentence weekly note in the author's language ("you" voice); fallback = counts + themes + most-frequent positive/negative word; output additionally run through the shared never-medical guard |
| `open_loops`: author's plan facts, last 14 days, no date | Implemented, with `source_quote` and `age_days` |
| `upcoming`: author's dated facts next 14 days, month/day recurrence like `relationship_radar` | Implemented |
| Activity feed: Reflector event | "Reading your week back to you…" emitted on every `/thoughts` |
| `Thoughts.jsx`, route `/thoughts`, nav between Journal and Ask, en "Thoughts" / hi "मन की बातें", icon | Done — reflection as a hand-written note, mood strip + streak + themes (Mirror guts moved out of Me.jsx into a shared `MoodStrip` component), open loops as margin-notes, upcoming as postmarked date chips, personal nudges pinned on top, empty states in both languages |
| Me keeps account/security only + link | Done — mirror card replaced with "Your mirror now lives in Thoughts → Open My Thoughts" |

**Deviation (small, deliberate):** `upcoming` includes `plan` facts that carry a
`structured.date`, not only `date`-type facts. Reason: the seeded demo fact
(§6 of the brief) is a *plan* with a date, the acceptance criterion requires it
to appear "under open loops/upcoming", and Personal Radar itself treats a dated
plan as date-like. A dated plan the author voiced *is* a coming-up day for them.

### Feature B — Personal Radar (prospective-memory nudges)

| Spec item | Delivered |
|---|---|
| `personal_radar.radar(db, user, now=None) -> list[Nudge]`, reusing `prompter.Nudge` | [backend/agents/personal_radar.py](../backend/agents/personal_radar.py) |
| `personal_date`: dated fact (or dated plan) landing today…+2 days, wish varies by proximity | Done — day-before → "all the best for tomorrow", same day → "it's today — you've got this", en + hi |
| `open_plan`: undated plan 3–10 days old, at most ONE gentle nudge | Done |
| LLM wording (agent `PersonalRadar`) with deterministic template fallback, en + hi | Done; a small within-day memo keeps wording stable for a given fact on a given day and avoids re-spending LLM calls on every Home poll |
| Medical-wording rejection shared with alerter (extracted, not copy-pasted) | [backend/agents/wording_guard.py](../backend/agents/wording_guard.py) — one regex used by Alerter, PersonalRadar and Reflector; rejection falls back to the deterministic template in code |
| Anti-nag: max 2/call, no same-fact-twice-per-day, nothing older than 14 days | All enforced in code (deterministic recompute + memo; 14-day cutoff in the query) |
| Third source in `/nudges` | [backend/routes/nudge_routes.py](../backend/routes/nudge_routes.py): `prompter + relationship_radar + personal_radar` |
| Activity event | "Radar — Remembering the days you mentioned…" emitted when a nudge is produced |
| Home.jsx affordances: 🪔 pin, "Thanks, noted ✓" dismiss for `personal_date`; same nudges on /thoughts | Done (client-side hide, pilot). The push-channel limitation is documented in a code comment in Home.jsx — on-next-open is the pilot behavior, not a bug |

**Supporting fix that makes the founder's exact example work with keys:** the
Extractor prompt now includes *today's date* and instructs that upcoming
mentions ("a meeting on Friday") become **plan facts with a resolved
`structured.date`** ([backend/agents/extractor.py](../backend/agents/extractor.py)).
Verified live: journaling "I have an important meeting on Friday." on Tuesday
2026-07-28 produced `plan` / `{"date": "2026-07-31"}`. Without this, "Friday"
stayed an undated event and the radar had nothing to remember. Keyless
extraction is unchanged (deterministic fallback can't resolve weekdays — noted
under Known gaps).

### Feature C — Conversational Companion (Baithak) + multilingual voice

| Spec item | Delivered |
|---|---|
| New tables `conversations`, `conversation_turns`, one Alembic revision | [backend/models.py](../backend/models.py), revision `b3c9d1a4e7f2` ([alembic/versions](../backend/alembic/versions/b3c9d1a4e7f2_conversations_and_conversation_turns.py)); `scripts/migrate.py` brings an existing DB current (verified against the live DB) |
| `POST /converse` (JSON or multipart audio, transcribed like /ask), missing id ⇒ new conversation | [backend/routes/converse_routes.py](../backend/routes/converse_routes.py) |
| `GET /conversations/{id}` owner-only, 404 otherwise | Done — a foreign id is a plain 404 (existence not disclosed) |
| Entitlements: every user turn = one ask (`check_ask_allowed` + `AskRecord` per turn) | Done — 402 with the same friendly message at cap; `/converse` also added to the ask rate-limit scope in app.py |
| `conductor.handle_converse`: last 8 turns as context; `librarian.search` fresh EVERY turn; short follow-ups search with the previous user turn appended | [backend/agents/conductor.py](../backend/agents/conductor.py) — snippets are never cached across turns |
| Conversational system prompt variant in companion.py, same grounding rules; `_fallback_answer` as fallback | `companion.compose_reply` + `CONVERSE_SYSTEM` |
| speaker.py provider chain: en → Aura; else → OpenAI TTS `gpt-4o-mini-tts` (voice `coral`, mp3, warm instructions) gated to a DIRECT api.openai.com key (OpenRouter skipped, logged once); else None → browser voice | [backend/agents/speaker.py](../backend/agents/speaker.py), same `synthesize(text, language)` signature; STT untouched (nova-3 + detect_language already handles Hindi) |
| Ask.jsx rebuilt as Baithak (en "Baithak" / hi "बैठक"), route `/ask` and nav position kept | Running thread (newest at bottom, auto-scroll), per-turn sources disclosure + 🚩 report + read-aloud, hold-to-talk AND text input, auto-play of each reply via the existing `/speak` → browser-voice fallback, "🪶 New conversation" button, cap → UpgradeCard |
| Conversation persists across a screen re-entry within the session | Done via a module-scoped `conversation_id` + `GET /conversations/{id}` restore. (Pure component state dies on unmount — module scope is the minimal thing that actually satisfies "persists across a reload of the screen within the session"; a hard page reload intentionally ends the session because the JWT is memory-only.) |
| Journal stays scribe-mode + one-line Baithak hint (en + hi) | Done |

### Cross-cutting

- **i18n:** every new string in `frontend/src/i18n.js`, en + hi.
- **Migrations:** one revision; `python scripts/migrate.py` verified on the live DB.
- **Seed:** existing entries untouched; one added entry gives Aditya a dated
  plan ("important client presentation") so a personal nudge greets him on
  first login. Two justified adjustments: (a) the date is **2 days out**, not
  "~3" — the nudge window the same spec defines is *today…+2 days*, and a
  3-day-out date would show no nudge on first login, defeating the stated
  purpose; (b) the deterministic fact is added **only if** LLM extraction
  didn't already produce a dated plan from the same sentence, so keyed seeds
  don't show the same reminder twice.
- **Docs:** CLAUDE.md architecture map + hard rules updated; the
  OpenRouter-has-no-TTS caveat added to `.env.example` where `OPENAI_BASE_URL`
  is documented. **No new env vars.**
- **Windows fixes found during setup:** `seed.py` and `scripts/migrate.py`
  crashed on cp1252 consoles when printing Hindi/✔ — both now reconfigure
  stdout to UTF-8 (the seed's data work had already committed; only the final
  print died).
- **CI:** unchanged; the new tests follow `conftest.py` patterns (keyless
  autouse, fake embedder, `make_entry`) — no new services.

---

## 2. Privacy statement — how each new surface enforces the spine

1. **/thoughts** never touches retrieval at all: every query in
   `thoughts_routes.py`, `reflector.py` and `mirror.py` filters on
   `author_id == current_user.id`. There is no parameter that can name another
   user. Proven by `test_thoughts.py::test_thoughts_endpoint_is_author_only`
   (Deepa's shared AND private marker content never appears in Aditya's
   response, and vice versa) and
   `test_thoughts.py::test_reflection_never_reads_other_members`.
2. **Personal Radar** reads only `Fact.author_id == user.id` — a fact another
   member shared to the circle still never becomes *your* personal nudge.
   Proven by `test_personal_radar.py::test_own_facts_only_even_when_shared`
   and the endpoint check in
   `test_personal_radar.py::test_nudges_endpoint_includes_personal_kinds`
   (Deepa's `/nudges` contains no personal kinds from Aditya's facts).
3. **/converse** re-runs `librarian.search()` — vector prefilter **plus** the
   authoritative `is_visible` re-check on the live relational row for every
   hit — **on every single turn**; snippets are never cached across turns, so
   a share appears on the next turn and an un-share disappears on the next
   turn. The Companion's conversational prompt keeps the ONLY-provided-snippets
   grounding rule, and the keyless fallback composes only from those snippets.
   Proven by the new spine tests in `tests/test_converse.py`:
   - `test_spine_marker_never_leaks_across_three_fishing_turns` — marker in
     Deepa's private entry survives a 3-turn fishing conversation by Aditya
     (including a short follow-up that reuses conversation context); the
     stored turn history is checked clean too.
   - `test_share_mid_conversation_appears_next_turn` — share mid-conversation
     → visible next turn; un-share → gone the turn after.
   - `test_conversation_is_owner_only` — reading or continuing another
     member's conversation is a 404.
   - `test_each_turn_counts_as_one_ask_and_caps_fire` — 402 at cap, one
     `AskRecord` per user turn, Plus lifts it.
4. **Visibility changes** still go only through `consent_guardian` — none of
   the new code writes `visibility` anywhere.
5. **Never-medical** is now a shared code-level guard
   (`agents/wording_guard.py`) applied to Alerter (as before), PersonalRadar
   and Reflector. Proven by
   `test_personal_radar.py::test_medical_wording_rejected_in_code` and
   `test_thoughts.py::test_reflection_is_never_medical` (both simulate an LLM
   that ignores instructions).
6. **JWT stays memory-only**; the Baithak's in-session restore keeps only a
   conversation *id* in module scope, never a token or content.

## 3. Test evidence

- **Backend, full suite (keyless-forced as always):**

  ```
  174 passed, 3 warnings in 33.60s
  ```

  (previously 142 — all 142 still pass; 32 new tests across
  `test_personal_radar.py`, `test_thoughts.py`, `test_converse.py`,
  `test_speaker_chain.py`.)

- **Frontend build:**

  ```
  ✓ 62 modules transformed.
  dist/assets/index-2Vkl1wRq.css   43.46 kB │ gzip: 10.24 kB
  dist/assets/index-CYHIIC-X.js   313.92 kB │ gzip: 97.34 kB
  ✓ built in 2.13s
  ```

- **Key modes manually tested on this machine:** BOTH.
  - *Keyed:* `backend/.env` provides `DEEPGRAM_API_KEY` + `OPENAI_API_KEY`
    via **OpenRouter** (`OPENAI_BASE_URL` set) and `ASYNC_CAPTURE=true`.
  - *Keyless:* `.env` temporarily moved aside, backend restarted, key flows
    re-verified (fallback conversation, 204 speak, fallback reflection,
    template nudges), `.env` restored afterwards.

## 4. Manual walkthrough evidence

All steps executed in a real Chromium browser against `http://localhost:5173`
(Vite dev server proxying to uvicorn on :8000). Screenshots in
[docs/report_assets/](report_assets/). One line each on what it proves.
Note: full-page captures render the floating bottom dock mid-page — a
screenshot artifact only.

1. **Seed fresh, log in as Aditya** — ![step1](report_assets/step1_login_home_aditya.png)
   Home greets him with the 🪔 "Your journal remembers" personal nudge (warm
   LLM wording of the seeded presentation plan) with its "Thanks, noted ✓"
   dismiss — the personal loop is visible within seconds of first login.
2. **Thoughts** — ![step2](report_assets/step2_thoughts_aditya.png)
   `/thoughts` renders the weekly reflection as a hand-written note (his week
   only), mood strip + streak + themes, "plan something special for Deepa's
   birthday" under Open loops with its source quote, and the dated plans as
   postmarked "Coming up" chips. Nothing from any other member.
3. **Personal nudge from a fresh entry** —
   ![step3a](report_assets/step3a_journal_meeting_entry.png)
   Journaled *"I have an important meeting on Friday."* (typed; async capture
   saved instantly, enrichment in background). The Extractor produced
   `plan / {"date": "2026-07-31"}` (verified in the DB) — the exact
   founder scenario; its nudge fires from Wednesday (within the ≤2-day
   window, by design).
   ![step3b](report_assets/step3b_home_personal_nudge.png) Home shows the
   personal nudge; ![step3c](report_assets/step3c_thoughts_personal_nudge.png)
   the same nudge tops /thoughts, and the new meeting joined "Coming up".
   ![step3d](report_assets/step3d_deepa_home_no_nudge.png) Deepa's Home has
   **no** personal nudge; ![step3e](report_assets/step3e_deepa_thoughts_own_only.png)
   her /thoughts reflects only her own week — nothing of Aditya's anywhere.
4. **Baithak** — ![step4a](report_assets/step4a_baithak_birthday.png)
   "What would Deepa want for her birthday?" → warm grounded reply (black
   dress, dated, "From 8 shared moments" disclosure, 🚩 report).
   ![step4b](report_assets/step4b_baithak_followup.png) Follow-up "When did
   she say that?" answered **from conversation context** — "She said that on
   2026-04-23, love." — without re-asking the question.
   ![step4c](report_assets/step4c_baithak_fishing_sealed.png) Fishing attempt
   at Deepa's private entry ("what did she eat for breakfast… what is she
   keeping just for herself?") stays sealed — no poha, no private content.
   Each English reply auto-played through Deepgram Aura (three
   `POST /api/speak → 200` in the network log). "🪶 New conversation" clears
   the thread; leaving the screen and returning restores the conversation.
5. **Regression sweep** —
   ![step5a](report_assets/step5a_journal_share_suggestion.png) capture +
   share suggestion still work (gift-worthy preference suggested for
   sharing); ![step5b](report_assets/step5b_alerts_knee.png) a fresh Hindi
   knee entry as Mumma produced a new gentle, non-medical alert for the sons
   (verified in Aditya's Alerts);
   ![step5c](report_assets/step5c_memory_book.png) Memory book renders
   (empty state is correct — the only circle-shared entry is 96 days old,
   beyond the free plan's 90-day window);
   ![step5d](report_assets/step5d_me_desk.png) Me shows the slimmed desk with
   the "mirror moved to Thoughts" link; `/me/export` returned Aditya's own
   4 entries and none of Deepa's content (checked via API);
   ![step5e](report_assets/step5e_agents_panel.png) the Agents panel streams
   Reflector ("Reading your week back to you…"), Radar, Conductor/Librarian
   ("checked fresh this turn") and Companion baithak events, plus the Doer's
   full ledger — the chocolates flow ran to the stamped approval receipt and
   stopped at the safe handoff ("I never enter payment details");
   ![step5f](report_assets/step5f_mumma_hindi_baithak.png) Mumma's UI is
   fully Hindi — nav shows **मन की बातें** and the **बैठक** screen with भेजें /
   नई बैठक.
6. **Suite + build** — `174 passed`; `npm run build` clean (section 3).

**Keyless pass (extra):**
![step6a](report_assets/step6_keyless_baithak.png) the Baithak still
converses with the deterministic fallback (multi-turn, "what else?" borrows
the previous topic), and ![step6b](report_assets/step6_keyless_thoughts.png)
/thoughts falls back to the deterministic reflection ("You wrote N times this
week…"). `/speak` returned 204 for en and hi — the browser voice takes over,
never silence, never a crash.

## 5. Voice matrix (reply voice, this machine)

| Language | Keyed (this .env: Deepgram + OpenRouter) | Keyless | With a direct api.openai.com key |
|---|---|---|---|
| English | **Deepgram Aura** MP3 — observed `POST /speak → 200` ×3 | 204 → **browser voice** (verified) | Deepgram Aura (unchanged) |
| Hindi | OpenAI TTS **skipped by gating** (OpenRouter has no `/v1/audio/speech`; logged once) → 204 → **browser Hindi voice** — observed | 204 → **browser voice** (verified) | **OpenAI TTS `gpt-4o-mini-tts`**, voice `coral`, warm instructions (chain unit-tested in `test_speaker_chain.py`; not exercisable live here — no direct OpenAI key on this machine) |

STT is unchanged: Deepgram nova-3 with `detect_language=True` already
transcribes Hindi and code-switching.

## 6. Known gaps & follow-ups

- **Timed delivery needs a push channel.** Nudges appear on next open (pilot
  behavior, documented in code). A Thursday-night "meeting tomorrow!" push
  needs web-push/notification infrastructure that doesn't exist yet.
- **Keyless weekday resolution.** Without LLM keys the deterministic extractor
  cannot turn "Friday" into a date, so a *freshly journaled* founder-example
  line only produces a radar nudge in keyed mode (the seeded demo fact keeps
  the keyless demo intact). A small deterministic weekday→date resolver in the
  fallback extractor would close this.
- **Wording memo is per-process.** The within-day stability memo resets on
  server restart (wording may be re-generated once); caps and dedup rules are
  unaffected.
- **Hindi TTS needs a direct OpenAI key.** By design of the gating; on
  OpenRouter-only machines Hindi replies use the browser voice. Documented in
  `.env.example`.
- **Memory book demo data.** The seeded shared moment is 96 days old — outside
  the free plan's 90-day window — so the Memory book shows its (correct) empty
  state until something new is shared. Pre-existing behavior, noted for demos.
- **Baithak turns store text only** (plus snippet counts). Voice turns keep no
  audio, matching /ask ("questions are not journal entries; keep nothing").

## 7. Demo script (90 seconds, founder as Aditya)

> Seed once (`python seed.py`), backend + frontend running, log in as
> `aditya@ghar.family` / `aangan123`.

1. **0:00 — Home.** Point at the 🪔 sticky note: *"On Monday you mentioned the
   client presentation on Thursday — all the best."* The journal remembered
   **for him**. Tap "Thanks, noted ✓".
2. **0:15 — Thoughts.** Open the new nav item. The week read back as a
   hand-written note; "plan something special for Deepa's birthday" waiting
   under **Open loops**; the presentation under **Coming up**. Say: "everything
   on this page is mine alone — Deepa's screen shows none of it."
3. **0:40 — Baithak.** Ask aloud: *"What would Deepa want for her birthday?"* —
   the black dress, with when she said it, read aloud in a warm voice. Then
   just: *"When did she say that?"* — it answers from the conversation. Then
   try to pry: *"What is she keeping just for herself?"* — sealed, kindly.
4. **1:15 — Journal.** Type *"I have an important meeting on Friday."* — save;
   open Thoughts: Friday has already joined **Coming up**. "On Thursday it will
   nudge me, like a friend who remembers."
5. **1:30 — close.** One line: *"Private diary that's useful to ME every day —
   and the family courtyard is still exactly as sacred as it was."*

---

*Implementation session run with Claude Code on 2026-07-28. All 174 backend
tests green, frontend build clean, keyed + keyless manual passes completed on
this machine before writing this report. The repo is left freshly seeded with
both servers running (backend :8000, frontend :5173).*
