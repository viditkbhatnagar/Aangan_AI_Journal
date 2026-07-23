# Aangan — instructions for Claude Code

Aangan is a private family voice-journal app: FastAPI + SQLite + ChromaDB
backend in `backend/`, React + Vite frontend in `frontend/`. Everyone's journal
is private by default; one warm "Companion" answers questions only from what
each member chose to share.

## If the user asks you to set up or run this project

Follow [SETUP.md](SETUP.md) end to end. The short version you can execute:

```bash
# backend (Python 3.11 or 3.12 — NOT 3.9, NOT 3.13)
cd backend
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium        # optional: live cart-prep for actions
cp .env.example .env                          # then ask the user for their API keys (see below)
.venv/bin/python seed.py                      # demo family; downloads ~90MB embedding model once
.venv/bin/uvicorn app:app --reload --port 8000 --reload-exclude 'chroma_data/*' --reload-exclude 'data/*'

# frontend (Node 18+), separate terminal
cd frontend
npm install
npm run dev                                   # http://localhost:5173 (proxies /api → :8000)
```

API keys are **optional** — the app runs fully without them using deterministic
fallbacks. Ask the user whether they have keys and put them in `backend/.env`
(gitignored — never commit it, never hardcode keys):

- `DEEPGRAM_API_KEY` — live voice transcription
- `OPENAI_API_KEY` (+ optional `OPENAI_BASE_URL` for OpenRouter and
  `OPENAI_MODEL`, e.g. `openai/gpt-5.4-mini`) — natural LLM replies
- `ANTHROPIC_API_KEY` — alternative LLM provider

Seeded logins after `seed.py`: `aditya|deepa|mumma|abhishek@ghar.family`,
password `aangan123`. Good first demo: log in as Aditya, ask
"What would Deepa want for her birthday?", check the Alerts tab.

## Verification

```bash
cd backend && .venv/bin/python -m pytest tests/ -q     # full suite, must all pass
cd frontend && npm run build                            # must compile clean
```

Tests force keyless mode automatically, so they never spend API credits and
stay deterministic even when `.env` has keys.

## Architecture map

- `backend/app.py` — FastAPI app; routes live in `backend/routes/*.py`
- `backend/models.py` — all ORM tables (visibility enum: private/circle/custom)
- `backend/agents/` — one plain-Python module per agent:
  - `librarian.py` — **the privacy spine.** ALL retrieval goes through it; it
    enforces visibility on both SQLite and Chroma and re-checks every vector
    hit against the live relational row.
  - `consent_guardian.py` — the ONLY code path that moves content from private
    to shared (explicit share or the author's own standing rule).
  - `companion.py` (answers), `conductor.py` (routing), `transcriber.py`
    (Deepgram), `summarizer.py`/`extractor.py`, `alerter.py` (rate-limited
    triggers), `doer.py` (Playwright actions with human-approval gate),
    `prompter.py`/`relationship_radar.py` (nudges), `keepsake.py`/`mirror.py`
  - `llm.py` — provider chain: OpenAI/OpenRouter → Anthropic → deterministic
    fallback. Every LLM call must pass a `fallback=` callable.
- `backend/services/capture.py` — the entry pipeline (also detects "you do it"
  delegations and drafts an action awaiting approval); `services/actions.py` —
  action lifecycle with the approval gate; `services/activity.py` — per-user
  agent-activity feed shown in the UI's right-hand "Agents" panel
- `frontend/src/screens/` — one file per screen; `src/api.js` keeps the JWT in
  memory only (never localStorage)

## Hard rules — do not weaken these

1. Retrieval must stay visibility-filtered in code (`librarian.is_visible` on
   every hit). Never rely on prompts for privacy.
2. Only `consent_guardian` may change visibility, and only for the author.
3. `doer.py` must never fill credential/payment fields or click pay/send —
   `guard_fill`/`guard_click` enforce this; actions always require explicit
   human approval before completing.
4. The spine tests (`tests/test_spine_*.py`) are the gate: if a change makes
   any of them fail, the change is wrong.
5. Alert wording must never sound medical or diagnostic.

## Useful scripts & ops

- `backend/scripts/metrics.py` — pilot funnel/unit-economics report
- `backend/scripts/reset_link.py <email>` — one-time password-reset link
- `backend/scripts/backup.sh` — consistent backup (see docs/OPERATIONS.md)
- `docker compose up` — single-container deploy (backend serves built frontend)
- Entitlements/caps live in `backend/entitlements.py`; plan column on FamilyCircle

## Gotchas

- macOS system `python3` is 3.9 — always use `python3.11`/`python3.12`.
  Python 3.13 breaks passlib.
- `uvicorn` must run from `backend/` (paths resolve relative to it).
- `seed.py` wipes `aangan.db` + `chroma_data` and rebuilds them — that's
  intentional; run it any time you want a clean demo.
- First `seed.py`/embedding call downloads `all-MiniLM-L6-v2` (~90 MB, once).
- If port 8000/5173 is busy: `lsof -nP -iTCP:8000 -sTCP:LISTEN`.
