# Aangan (आँगन) — a private family voice journal

Aangan is a quiet courtyard for one family. Each member keeps their own **voice
journal** — ten seconds or ten minutes, whenever they like. On top of everyone's
journals sits one warm **Companion** you can ask things like *"How was Deepa's
day?"* or *"What would Deepa want for her birthday?"* — and it answers **only
from what each person chose to share**. Gentle care nudges prompt the right
family member to reach out, and small caring actions (order the chocolates,
draft the message) are prepared for a human to approve and finish.

## Three sacred rules

1. **Private by default.** Every entry and every extracted fact starts private
   to its author. Visibility is enforced as a hard filter in the retrieval code
   — on both the relational store and the vector store, re-checked row by row —
   never as a prompt instruction.
2. **The author controls sharing.** The app may *suggest* sharing something;
   nothing moves from private to shared without the author's explicit yes or a
   standing rule the author created themselves.
3. **A human approves and completes every real-world action.** The action agent
   prepares up to the point of payment or sending, then stops. It never enters
   card or password details — a code-level guard refuses those fields outright.

## Setup and run

Requirements: Python 3.11 or 3.12, Node 18+.

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium         # optional — enables live cart preparation
python seed.py                       # creates the sample family and entries
uvicorn app:app --reload --port 8000
```

Notes for the first run:
- `seed.py` downloads the local embedding model (~90 MB, one time), then works
  fully offline.
- `--reload` tip: use `--reload-exclude 'chroma_data/*' --reload-exclude 'data/*'`
  to keep the vector store's own writes from re-triggering reloads.

### Frontend

```bash
cd frontend
npm install
npm run dev                          # Vite dev server, proxies /api → localhost:8000
```

Open the printed Vite URL (usually http://localhost:5173) and log in as one of
the seeded members.

### Environment variables (backend/.env — all optional)

```
DEEPGRAM_API_KEY=...     # speech-to-text for voice recording
OPENAI_API_KEY=...       # LLM for summaries, extraction, Companion replies
OPENAI_BASE_URL=         # optional: any OpenAI-compatible gateway, e.g.
                         # https://openrouter.ai/api/v1 (models: openai/gpt-5.4-mini)
OPENAI_MODEL=gpt-5.4-mini
ANTHROPIC_API_KEY=...    # alternative LLM provider (OpenAI wins if both set)
JWT_SECRET=change-me
DATABASE_URL=sqlite:///aangan.db
CHROMA_PATH=./chroma_data
```

**No keys? Everything still runs.** Without an LLM key the agents use warm
deterministic fallbacks (English + Hindi); without `DEEPGRAM_API_KEY` voice
upload returns a friendly note and the app offers typing instead. If the
configured `OPENAI_MODEL` isn't available to your account, the app falls back
through `gpt-5-mini` / `gpt-5-nano` / `gpt-4o-mini` automatically.

## The seeded family

Circle **Ghar** (invite code `GHAR-2026`), password `aangan123` for everyone:

| Member | Email | Language |
|---|---|---|
| Aditya (self) | aditya@ghar.family | en |
| Deepa (wife) | deepa@ghar.family | en |
| Mumma (mother) | mumma@ghar.family | hi |
| Abhishek (brother) | abhishek@ghar.family | en |

Ready on first login:
- Deepa's **black-dress moment** (shared ~3 months ago) — ask as Aditya:
  *"What would Deepa want for her birthday?"*
- Deepa's recent **private** entry — no phrasing of any question will surface it
  for anyone else.
- Mumma's Hindi knee entry — her own trigger has already alerted both sons,
  with a suggested caring action.
- Aditya's private reflection — visible only in his own Mirror.
- Deepa's standing rule (*share my gift ideas with the family*) and Mumma's
  knee trigger, both editable on the **Me** screen.

## How it's put together

```
backend/
  app.py                # FastAPI app and routes
  models.py             # users, circles, entries, facts, shares, rules,
                        # triggers, alerts, actions (SQLite via SQLAlchemy)
  memory/               # Chroma vector store + local MiniLM embeddings
  agents/               # one module per agent, plain Python:
    conductor           #   routes each ask through the agents below
    companion           #   the one warm face — answers only from returned snippets
    librarian           #   ALL retrieval; enforces visibility on both stores
    consent_guardian    #   the only private→shared code path
    transcriber         #   Deepgram speech-to-text (graceful without a key)
    summarizer/extractor#   summaries, snippets, and private-by-default facts
    alerter             #   author-set triggers, severity, daily rate limits
    prompter/relationship_radar  # gentle nudges, never pushy
    doer                #   Playwright actions with the human-approval gate
    interpreter         #   Hindi ⇄ English bridge
    keepsake/mirror     #   shared memory book / private reflection
  services/             # capture pipeline and action lifecycle
  seed.py               # the demo family
frontend/               # React + Vite; JWT held in memory only (no localStorage)
```

Run the test suite (81 tests, including leak-proofing of the visibility spine):

```bash
cd backend && .venv/bin/python -m pytest tests/ -q
```

## Privacy posture

- Family data stays on your machine (SQLite + local Chroma + local embeddings).
  The only outbound calls are transcription (Deepgram) and reasoning (Anthropic)
  — and only when you configure those keys.
- Another member's private content is never placed into any prompt.
- The Mirror is visible only to its owner; the memory book contains only shared
  moments.
- Aangan sends nudges so *people* connect. It is not a medical or emergency
  service and never presents itself as one.
