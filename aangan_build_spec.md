# Aangan: Full Build Brief

*Working name. If the project is renamed (for example to Apnapan), replace the word "Aangan" throughout.*

## For the implementer (read this first)

You are building a complete, working application on **localhost**. Build the **entire system described here**, not a trimmed version and not a demo stub. Follow the build order in the last section so the pieces come together in the right sequence, but the target is the full system running locally with every feature wired up.

Three rules that must never be broken, because this app holds a real family's private journals:

1. **Private by default.** Every journal entry is private to its author unless the author explicitly shares it. The question layer must never return another person's private content. Enforce this as a hard filter in the retrieval code, not as a prompt instruction.
2. **The author is always in control of sharing.** The system may *suggest* sharing something, but nothing moves from private to shared without the author's explicit yes or a standing rule the author set up themselves.
3. **The human approves and completes any real-world action.** The action agent may prepare a purchase, message, or call, but it must stop before payment or sending and hand off to the human. It must never enter card or password details or complete a payment on its own.

When you finish, the app must run with the exact commands in the "Setup and run" section, and it must pass every item in "Acceptance criteria."

---

## 1. What we are building

Aangan is a private family app where each member keeps their own **voice journal**. They open it whenever they want and just talk, for ten seconds or ten minutes, as often as they like. On top of everyone's journals sits a single warm assistant, the **Companion**, that a family member can ask things like "How was Deepa's day?" or "What would Deepa want for her birthday?", and it answers only from what that person chose to share. The app also sends gentle care nudges (someone logs that they are unwell, the right family member is prompted to reach out) and can prepare small caring actions (order chocolates, draft a message) for a human to approve.

The feeling we are building for: in a busy, scattered life, staying close to the people who matter, and never forgetting the small things they said.

Audience: one real family (four members in the seed data: the user, spouse, mother, brother). Multiple family members, multiple languages (Hindi and English at least).

---

## 2. Non-negotiable principles

| Principle | What it means in code |
|---|---|
| Private by default | New entries and extracted facts have visibility `private`. Nothing is readable by others until explicitly shared |
| Author controls sharing | Sharing only happens through an explicit share action or a standing rule the author created. The AI may propose, never decide |
| Visibility is enforced at retrieval | The retriever filters by the asker's authorization on both the relational query and the vector search. Private content of others can never be returned, regardless of the prompt |
| One warm face | The user always talks to the Companion. All other agents work behind it |
| Human approves actions | The action agent prepares up to the point of payment or sending, then stops for human approval. It never enters credentials or completes payment |
| Nudges connect humans, they do not diagnose | Alerts prompt a person to call or check in. The app is not a medical or emergency service and must not present itself as one |
| Warm, plain, multilingual tone | Replies are gentle and simple, in the user's language |

---

## 3. Technology stack (localhost)

Use this cohesive stack so the whole thing can be built and run locally in one pass. Swappable items are noted, but pick these defaults.

| Layer | Choice | Notes |
|---|---|---|
| Backend | Python 3.11+ with FastAPI + Uvicorn | Matches an AI engineer's toolchain, easy local run |
| Relational database | SQLite via SQLAlchemy | Zero-config local file `aangan.db` |
| Vector store | ChromaDB (local, persistent) | Stores embeddings of entry summaries and facts with metadata for visibility filtering |
| Embeddings | `sentence-transformers` model `all-MiniLM-L6-v2` (local) | Fully local and free. Optional swap: a hosted embedding API |
| LLM (reasoning agents) | Anthropic API (Claude) via the official Python SDK | Used by the Companion, Extractor, Summarizer, Alerter wording, and others |
| Speech to text | Deepgram SDK | Transcribes uploaded audio |
| Text to speech | Browser `SpeechSynthesis` (client side) | Free and local for the Companion's spoken replies. Optional swap: a hosted TTS |
| Browser automation (action agent) | Playwright for Python | Prepares carts, messages, and calls. Stops before payment or send |
| Frontend | React with Vite (single page app) | Talks to the FastAPI backend over JSON. Records audio with the browser MediaRecorder |
| Auth | Local email plus password, JWT sessions (passlib for hashing, python-jose for tokens) | Real per-user login so visibility can be enforced |
| Agent orchestration | Plain Python: one module per agent with a clear function contract, plus a Conductor that routes | Easiest to build correctly in one pass and to debug. Optional swap: a graph framework later |

Do not use browser localStorage or sessionStorage for app data. Keep state in the backend database.

---

## 4. Repository layout

```
aangan/
  backend/
    app.py                 # FastAPI app, route registration
    config.py              # env vars, settings
    db.py                  # SQLAlchemy engine, session
    models.py              # all ORM models (Section 6)
    schemas.py             # Pydantic request/response models
    auth.py                # login, JWT, current-user dependency
    memory/
      store.py             # Chroma setup, upsert, query with visibility filter
      embeddings.py        # local embedding function
    agents/
      conductor.py         # routes a request to the right agents, holds context
      companion.py         # voice-facing dialogue agent
      transcriber.py       # Deepgram speech to text
      summarizer.py        # clean summary + shareable snippets
      extractor.py         # pulls facts (preference/event/state/plan/person/date)
      consent_guardian.py  # visibility rules, share prompts, redaction
      librarian.py         # retrieval scoped by visibility (uses memory/store.py)
      alerter.py           # evaluates triggers, severity, rate limit, wording
      prompter.py          # nudges people to journal, starter questions
      relationship_radar.py# "not in touch" and upcoming-date nudges
      doer.py              # Playwright actions with human approval gate
      interpreter.py       # language bridge and tone
      keepsake.py          # curates shared moments into a memory book
      mirror.py            # per-user private mood/theme reflection
    services/
      capture.py           # orchestrates the capture pipeline
      alerts.py            # alert creation and delivery
      actions.py           # action lifecycle
    routes/
      *.py                 # one file per route group (Section 14)
    seed.py                # creates the sample family and entries (Section 20)
    requirements.txt
  frontend/
    (Vite React app, screens in Section 15)
  README.md                # generated from Section 17
```

---

## 5. The people and the family circle

- A **User** is one family member with a login, a language, and an optional voice sample.
- A **Family Circle** is the shared group. In this build there is one circle. Members join by an invite code.
- **Relationships** describe how one member refers to another (spouse, mother, brother), used only to make the Companion's language warmer.

---

## 6. Data model

Relational tables (SQLAlchemy models). Types in parentheses. `visibility` is an enum: `private`, `circle`, `custom`.

**users**: id (int, pk), name (str), email (str, unique), password_hash (str), language (str, e.g. "hi" or "en"), voice_sample_path (str, nullable), created_at (datetime)

**family_circles**: id (int, pk), name (str), invite_code (str, unique), created_by (fk users), created_at

**memberships**: id (int, pk), circle_id (fk), user_id (fk), role (str: "member" or "admin"), joined_at

**relationships**: id (int, pk), circle_id (fk), from_user_id (fk), to_user_id (fk), label (str, e.g. "spouse"), (how from_user refers to to_user)

**journal_entries**: id (int, pk), author_id (fk users), circle_id (fk), audio_path (str), transcript (text), summary (text, nullable), language (str), duration_sec (int), visibility (enum, default `private`), created_at

**facts**: id (int, pk), entry_id (fk journal_entries), author_id (fk users), circle_id (fk), type (str: "preference" | "event" | "state" | "plan" | "person" | "date"), content (text, human readable), structured (json, e.g. {"item":"dress","brand":"H&M","sentiment":"loved"} or {"date":"2026-03-14"}), source_quote (text), visibility (enum, default `private`, inherits from entry but can be set independently), created_at

**share_targets**: id (int, pk), entry_id (fk, nullable), fact_id (fk, nullable), user_id (fk users). Lists exactly who can see an item whose visibility is `custom`. One row per allowed viewer.

**share_rules**: id (int, pk), user_id (fk, the author), circle_id (fk), description (str, human readable, e.g. "share my gift ideas with everyone"), match (json, e.g. {"type":"preference","tag":"gift"}), audience (json, either "all" or a list of user ids), active (bool), created_at

**alert_triggers**: id (int, pk), author_id (fk, the person this is about), circle_id (fk), description (str, e.g. "if I say I am unwell, tell Aditya"), match (json, e.g. {"type":"state","topic":"health"}), audience (json: list of user ids), severity_hint (str: "gentle" | "notable" | "urgent"), active (bool), created_at

**alerts**: id (int, pk), source_entry_id (fk), author_id (fk, the person the alert is about), recipient_id (fk, who receives it), circle_id (fk), severity (str), message (text), suggested_action (text), status (str: "new" | "seen" | "acted" | "dismissed"), created_at

**actions**: id (int, pk), created_by (fk users, the human who will approve), related_alert_id (fk, nullable), intent (text, e.g. "order Deepa's chocolates"), plan (json, one of the shapes below), status (str: "draft" | "awaiting_approval" | "approved" | "completed" | "cancelled"), result (json, nullable), created_at, completed_at (nullable)

Action `plan` shapes:
- purchase: {"type":"purchase","item":"...","site":"...","url":"...","price":"...","deliver_to":"..."}
- message: {"type":"message","channel":"whatsapp|sms|email","to":"...","body":"..."}
- call: {"type":"call","to":"...","note":"..."}

**Vector store (Chroma)**: one collection, `family_memory`. Each document is the text of an entry summary or a fact. Metadata on each: {entry_id, fact_id (nullable), author_id, circle_id, visibility, custom_viewer_ids (list), type, created_at}. This metadata is what makes visibility-filtered search possible.

---

## 7. The consent and visibility model (the spine)

This is the most important part. Build it first and test it hard.

**Visibility of an item** (an entry or a fact) authored by A, when member U asks:

U may see the item if any of these is true:
- `item.author_id == U.id` (your own content, always visible to you), or
- `item.visibility == "circle"` and U is in the same circle, or
- `item.visibility == "custom"` and there is a `share_targets` row linking that item to U.

Otherwise (the default `private`), only the author sees it.

**How sharing happens:**
- When the author records an entry, the Extractor produces facts, all `private`.
- The Consent Guardian looks at the new entry and facts and, if something looks shareable (a gift idea, a plan, a happy update), it asks the author through the app: "Share this with your family?" with the specific item shown. The author can share the whole entry, or just a specific fact, to everyone (`circle`) or to chosen people (`custom` plus `share_targets` rows).
- Standing rules (`share_rules`) let the author pre-approve a category, for example "share my gift ideas with everyone." When a new fact matches an active rule, the Consent Guardian applies that rule's visibility automatically. This is still the author's choice, because the author created the rule.

**Redaction by granularity:** Because facts have their own visibility, an author can share one fact (the black dress) while the surrounding entry and its private feelings stay `private`. Sharing a fact never exposes its parent entry.

**Hard enforcement:** The Librarian (Section 8) applies the visibility test above on every relational query and passes the same filter to Chroma (`where` on `visibility` and `custom_viewer_ids` and `author_id`). There must be no code path where the Companion can read another member's `private` content.

---

## 8. The agents

Each agent is a Python module with a clear function contract. The Conductor decides which to call for a given request and passes context between them. The Companion is the only agent the user talks to.

| Agent | When it runs | Reads | Returns or writes | Must |
|---|---|---|---|---|
| Conductor | On every user request | The request, current user, context | A plan of which agents to call, in order | Hold context so it feels like one helper |
| Companion | On every "ask" and as the reply voice | The Librarian's grounded snippets | A warm, spoken and written answer in the user's language | Never invent facts; only use what the Librarian returned |
| Transcriber | On new audio upload | The audio file | transcript text, detected language, duration (Deepgram) | Store transcript on the entry |
| Summarizer | After transcription | The transcript | A clean summary plus 0 to 3 short shareable snippets | Keep the author's meaning and voice |
| Extractor | After summarization | The transcript and summary | facts rows (preference, event, state, plan, person, date) each with a source_quote | Tag every fact `private` by default |
| Consent Guardian | After extraction, and on any share action | New facts, the author's share_rules | Share prompts for the author, and visibility writes | Only path from private to shared. AI proposes, author decides |
| Librarian | On every "ask" | Relational tables and the Chroma collection | Grounded snippets with dates and sources, filtered to what the asker may see | Apply the Section 7 visibility test on both stores |
| Alerter | On new entry or new fact | alert_triggers for that author, recipient rate limits | alerts rows with severity, message, suggested_action | Only fire triggers the author set. Respect rate limits. Never medical |
| Prompter | On a schedule or when a member has not journaled in a while | Last entry time per member | A gentle nudge and a starter question | Tuned for elders. Never pushy |
| Relationship Radar | On a schedule | Last contact and upcoming dates | A nudge to reach out or prepare for a date | Suggest, do not act |
| Doer | When a human asks for an action or acts on an alert | The intent and needed details | A prepared action awaiting approval, then completion after approval | Stop before payment or send. Never enter credentials |
| Interpreter | Inside capture and ask when languages differ | Text and target language | Translated or tone-adjusted text | Log in Hindi, ask in English, and back |
| Keepsake | On a schedule and on request | Shared entries and facts | A memory book view and "on this day" resurfacing | Only shared content, never private |
| Mirror | On request, private to the user | The user's own full journal | The user's mood and theme patterns over time | Visible only to that user |

---

## 9. The main flows

**Capture flow** (service `capture.py`):
1. Client records audio, uploads to `POST /entries`.
2. Create a `journal_entries` row (`private`), save audio.
3. Transcriber fills transcript and language.
4. Summarizer fills summary and snippets.
5. Extractor creates facts (`private`).
6. Consent Guardian applies any matching `share_rules`, then returns share suggestions for the author to confirm in the app.
7. Librarian upserts the summary and each fact into Chroma with visibility metadata.
8. Alerter checks the author's triggers and creates any alerts.

**Ask flow** (route `POST /ask`):
1. Conductor receives the question and current user.
2. Librarian searches (relational plus vector), filtered to what the user may see, and returns grounded snippets with dates.
3. Interpreter adjusts language if needed.
4. Companion composes a warm answer using only those snippets, and the client speaks it with browser TTS.
5. If nothing is visible, the Companion says so kindly.

**Alert flow:**
1. Alerter creates an `alerts` row for each permitted recipient.
2. Recipient sees it in the Alerts screen with a suggested action.
3. Recipient can dismiss, or turn it into an action (opens the Doer flow).

**Action flow** (service `actions.py`):
1. From an alert or a direct ask, create an `actions` row (`draft`).
2. Doer prepares the plan (finds the item and builds a cart with Playwright, or drafts a message, or lines up a call), sets status `awaiting_approval`.
3. Human reviews in the Actions screen and calls `POST /actions/{id}/approve`.
4. On approval, the Doer completes up to the safe handoff point (cart ready at checkout for the human to pay, message ready to send, call ready to place). It never pays or sends by itself. Status becomes `completed`, result stored.

---

## 10. Voice pipeline

- **Record:** Browser MediaRecorder captures audio (webm or wav), uploaded as multipart to `POST /entries`.
- **Transcribe:** Deepgram via the Python SDK, with language auto-detection. Store transcript and detected language.
- **Speak (Companion replies):** The client uses the browser `SpeechSynthesis` API to read answers aloud in the user's language. Provide a text fallback always.
- Optional: store the audio file path so entries can be replayed.

---

## 11. Memory and retrieval

- On capture, embed the entry summary and each fact with `all-MiniLM-L6-v2` and upsert into Chroma with the visibility metadata from Section 7.
- On ask, the Librarian:
  1. Builds the visibility filter for the asker (own, or `circle`, or `custom` with the asker in `custom_viewer_ids`).
  2. Runs a vector search with that `where` filter, and a structured lookup for exact things (dates, named people, gift tags).
  3. Returns the top grounded snippets, each with its date and a short source reference, so the Companion can say "back in January, ...".
- Never return a snippet the filter excluded. Re-check visibility on the relational row before returning, as a second guard.

---

## 12. Alert engine

- **Triggers:** Authored by the person the alert is about (`alert_triggers`). Example: Deepa creates "if I say I am unwell, tell Aditya" with audience [Aditya], severity_hint "notable".
- **Matching:** When a new fact of the matching type and topic appears in that author's journal, create alerts for the listed audience.
- **Severity tiers:** `gentle` (a small heads up), `notable` (worth reaching out today), `urgent` (call now). The wording of the message is written by the Alerter through the LLM, kept warm and human, and it prompts a person to connect. It must never phrase itself as medical advice or a diagnosis, and the app must not claim to detect emergencies reliably.
- **Rate limiting (anti alert-fatigue):** Cap alerts per recipient per day (default 5) and never send two alerts about the same fact. Collapse similar alerts.
- **Delivery on localhost:** In-app, shown in the Alerts screen with a badge. (Email or push can be added later.)

Examples the build should handle:
- Deepa logs she is in pain on her first day, Aditya (permitted) gets: "Deepa is having a rough day, a call or her favourite chocolates might help." with a suggested action to order chocolates.
- Mumma logs her knee hurts, her sons (permitted) get: "Mumma's knee is bothering her, good time to call and remind her about her calcium."

---

## 13. The action agent (Doer)

- Uses Playwright for Python to prepare real-world actions.
- **Purchase:** search a site, add the item to the cart, bring it to the checkout page, and stop. The human reviews price and address and pays. The Doer never fills payment or login credentials and never clicks the final pay button.
- **Message:** draft the text and open or prepare the send, the human sends.
- **Call:** prepare the number and a short note, the human places the call.
- Always create the action as `awaiting_approval` first, complete only after `POST /actions/{id}/approve`.
- Practical note for the implementer: third party sites may require the human to log in or clear a check first. That is expected and correct, hand those steps to the human. Store the outcome in `actions.result`, and log completed actions so the Companion can later say "you sent Deepa chocolates last month."

---

## 14. API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | /auth/register | Create a family member |
| POST | /auth/login | Log in, return JWT |
| GET | /me | Current user profile |
| POST | /circles | Create the family circle |
| POST | /circles/join | Join by invite code |
| GET | /circles/members | List members and relationships |
| POST | /entries | Upload audio, run the capture pipeline, return the entry with share suggestions |
| GET | /entries | List the current user's own entries |
| GET | /entries/{id} | Get one own entry |
| POST | /entries/{id}/share | Set entry or fact visibility (circle or custom with viewer ids) |
| POST | /ask | Ask the Companion a question, return a grounded, visibility-scoped answer |
| GET | /alerts | Alerts for the current user |
| POST | /alerts/{id}/status | Mark seen, acted, or dismissed |
| POST | /share-rules | Create a standing sharing rule |
| GET | /share-rules | List my sharing rules |
| POST | /alert-triggers | Create a trigger about me |
| GET | /alert-triggers | List my triggers |
| POST | /actions | Create an action from an intent or an alert |
| GET | /actions | List actions awaiting my approval and my past actions |
| POST | /actions/{id}/approve | Approve, Doer completes to the safe handoff |
| POST | /actions/{id}/cancel | Cancel an action |
| GET | /keepsake | The memory book (shared moments, on this day) |
| GET | /mirror | My own private patterns over time |

All routes except register and login require a valid JWT and operate as the current user. Visibility is enforced server side using the current user's identity.

---

## 15. Frontend screens

- **Welcome / setup:** register or log in, create or join the family circle by code, set language and record a short voice sample.
- **Home:** a big "hold to talk" button to journal, and a list of recent nudges.
- **Journal:** record a new entry, see your own past entries, and share toggles (share whole entry, or specific extracted facts, to everyone or chosen people). Share prompts from the Consent Guardian appear here after recording.
- **Ask:** talk or type to the Companion, answers shown as text and read aloud.
- **Alerts:** incoming nudges with a suggested action and an "act on this" button.
- **Actions:** items awaiting your approval (with price, address, or message body) and past actions.
- **Memory book:** the Keepsake view, shared moments and "a year ago today".
- **Me:** the Mirror (your private patterns), plus your sharing rules and your alert triggers.
- **Settings:** language, voice, and your default privacy.

Keep the visual tone warm and calm. Simple, rounded, friendly.

---

## 16. Auth and security

- Per-user login with hashed passwords (passlib) and JWT sessions (python-jose).
- Every data route resolves the current user from the token and enforces visibility using that identity.
- Store the SQLite file and audio locally. Do not send any family data to third parties except the transcription (Deepgram) and the reasoning calls (Anthropic), and never send another member's private content into a prompt when answering someone else.
- Keep all API keys in environment variables, never in code or in the frontend.

---

## 17. Setup and run

Environment variables (backend `.env`):

```
ANTHROPIC_API_KEY=...
DEEPGRAM_API_KEY=...
JWT_SECRET=change-me
DATABASE_URL=sqlite:///aangan.db
CHROMA_PATH=./chroma_data
```

Backend:

```
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt      # fastapi, uvicorn, sqlalchemy, anthropic,
                                     # deepgram-sdk, chromadb, sentence-transformers,
                                     # playwright, passlib[bcrypt], python-jose, python-multipart
playwright install chromium
python seed.py                       # creates the sample family and entries
uvicorn app:app --reload --port 8000
```

Frontend:

```
cd frontend
npm install
npm run dev                          # Vite dev server, proxy /api to http://localhost:8000
```

Then open the Vite URL, log in as one of the seeded members, and use the app.

---

## 18. Build order (full build, sequenced)

Build all of it. This is the order to build it in so each layer rests on a working one.

1. **Scaffold:** backend and frontend skeletons, config, database engine, auth (register, login, JWT), circle create and join, members list.
2. **The spine (Section 7):** the visibility model, share_rules, share_targets, and the Librarian's enforcement. Write tests proving a private entry never appears for another member. Do not move on until these pass.
3. **Capture pipeline:** audio upload, Transcriber (Deepgram), Summarizer, Extractor, Consent Guardian share prompts and rule application, Chroma upsert with metadata.
4. **Memory and ask:** embeddings, visibility-scoped Librarian retrieval, Conductor, Companion, Interpreter, and the Ask screen with voice in and spoken out.
5. **Alerts:** alert_triggers, the Alerter with severity and rate limiting, the Alerts screen.
6. **Actions:** the Doer with Playwright and the approval gate, the Actions screen.
7. **Enrichment:** Prompter, Relationship Radar.
8. **Keepsake and Mirror:** the memory book and the private reflection view.
9. **Polish:** warm empty states, tone pass on all Companion and Alerter wording, the seed data, and the run scripts, so it works from a clean clone.

---

## 19. Acceptance criteria

The build is done when all of these are true on localhost:

- Four seeded family members can each log in.
- Any member can record a voice entry and see it transcribed, summarized, and turned into facts, all private by default.
- A member can share a whole entry or a single fact, to everyone or to chosen people, and can create a standing sharing rule.
- Asking "What would Deepa want for her birthday?" returns the shared black-dress moment with its date. Asking about something Deepa did not share returns a kind "nothing shared" answer.
- A member's **private** entry never appears in any other member's ask, by any phrasing. (Covered by the spine tests.)
- An alert fires only when the author set a matching trigger, only to the permitted recipients, with the right severity, and respects the daily rate limit.
- Creating an action always requires human approval before completion, and the Doer never enters payment or login details or completes a payment.
- A member can log in Hindi and another can ask in English and get a sensible answer, and back.
- The memory book shows only shared moments, and the Mirror view is visible only to its owner.
- The whole app runs using the commands in Section 17 from a fresh clone.

---

## 20. Seed data

Create one circle named "Ghar" with four members (use simple passwords for local testing):

- Aditya (self), language en
- Deepa (spouse), language en
- Mumma (mother), language hi
- Abhishek (brother), language en

Relationships set so the Companion can say "your wife", "your mother", "your brother".

A few entries so the app demos immediately:
- Deepa, dated a few months ago, shared: "Saw a beautiful black dress at H&M today, I could not stop thinking about it." (Extractor: preference, {item: dress, brand: H&M, sentiment: loved}, shared to circle.)
- Deepa, recent, private: a normal day entry (stays private, to prove the ask layer excludes it).
- Mumma, recent, with a trigger "if I say my knee hurts, tell my sons": "My knee has been paining a little today." (Alerter creates a notable alert for Aditya and Abhishek with a suggested "call and remind about calcium".)
- Aditya, private: a reflection entry (feeds the Mirror, invisible to others).

Set up one sharing rule for Deepa ("share my gift ideas with the family") and one alert trigger for Mumma (the knee example) so both features are demonstrable on first run.

---

*End of brief. Build the whole thing, keep the three rules at the top sacred, and make it feel warm.*
