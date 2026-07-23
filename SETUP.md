# Aangan — developer setup, end to end

This gets you from a fresh clone to the running app with seeded demo data.
If you use Claude Code, you can just say *"set up and run this project"* —
[CLAUDE.md](CLAUDE.md) tells it how to do everything below for you.

## 0. Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | **3.11 or 3.12** | Not 3.9 (too old), not 3.13 (breaks passlib). `brew install python@3.12` |
| Node.js | 18+ | `brew install node` |
| ~2.5 GB disk | | torch + chromadb + the local embedding model |

No API keys are required to run everything — see step 3.

## 1. Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt      # takes a few minutes (torch is large)
playwright install chromium          # OPTIONAL — enables live cart preparation
                                     # for the actions feature; skip freely
```

## 2. Environment file

```bash
cp .env.example .env
```

Open `backend/.env` and fill in what you have. **Everything is optional** —
with no keys the app uses warm deterministic fallbacks (typed entries instead
of voice, template answers instead of LLM prose):

| Variable | What it unlocks | Where to get it |
|---|---|---|
| `DEEPGRAM_API_KEY` | live voice transcription | console.deepgram.com (free tier) |
| `OPENAI_API_KEY` | natural summaries, extraction, Companion replies | platform.openai.com — or an OpenRouter key |
| `OPENAI_BASE_URL` | use any OpenAI-compatible gateway | e.g. `https://openrouter.ai/api/v1` |
| `OPENAI_MODEL` | model choice | `gpt-5.4-mini` (direct) / `openai/gpt-5.4-mini` (OpenRouter) |
| `ANTHROPIC_API_KEY` | alternative LLM provider | console.anthropic.com |
| `DOER_PURCHASE_SITE` | shop the action agent prepares carts on | default demo store; set `https://www.amazon.in` for real cart prep |
| `DOER_HEADLESS` | `false` opens a visible browser that stays open at the cart for you | default `true` |

`.env` is gitignored. Never commit keys.

## 3. Seed the demo family

```bash
python seed.py
```

First run downloads the local embedding model (~90 MB), then everything is
offline except the optional key-backed features. The seed **wipes and
rebuilds** `aangan.db` and `chroma_data/` — rerun it whenever you want a clean
demo. It creates circle **Ghar** with four members (password `aangan123`):

| Login | Who | Language |
|---|---|---|
| `aditya@ghar.family` | self | en |
| `deepa@ghar.family` | wife | en |
| `mumma@ghar.family` | mother | hi |
| `abhishek@ghar.family` | brother | en |

## 4. Run it

Terminal 1 — backend:

```bash
cd backend && source .venv/bin/activate
uvicorn app:app --reload --port 8000 --reload-exclude 'chroma_data/*' --reload-exclude 'data/*'
```

Terminal 2 — frontend:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**, log in as `aditya@ghar.family` / `aangan123`.

A five-minute tour that exercises everything:
1. **Alerts** — Mumma's knee alert is waiting (her own trigger fired; note the
   severity pill and suggested action). Tap **Act on this**.
2. **Actions** — approve the prepared action; the Doer completes to the safe
   handoff and always stops before payment/sending.
3. **Ask** — "What would Deepa want for her birthday?" → the shared black-dress
   moment, with its date, spoken aloud. Ask about anything unshared → a kind
   "nothing shared" answer. Nothing private ever crosses members.
4. **Journal** — hold-to-talk (or type), watch facts get extracted private-by-
   default with share prompts; share one fact while its entry stays private.
   Say something like *"order chocolates for my husband — you do it"* and the
   Doer drafts an action you can approve on the spot (with `DOER_HEADLESS=false`
   a browser opens, adds to cart, and stays open for you to pay).
5. **⚙️ Agents** (top right) — a live side panel showing which agent is working
   on your requests and what each one did.
6. **Me** — your private Mirror, your sharing rules, your alert triggers.
6. Log in as `mumma@ghar.family` and ask in Hindi — दीपा को जन्मदिन पर क्या पसंद आएगा?

## 5. Tests and build

```bash
cd backend && .venv/bin/python -m pytest tests/ -q    # 81 tests — the privacy
                                                       # spine is the gate
cd frontend && npm run build
```

Tests pin themselves to keyless mode: deterministic, no API spend.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `pip install` fails on passlib/crypt | You're on Python 3.13 — use 3.11/3.12 |
| Voice button says transcription isn't set up | Add `DEEPGRAM_API_KEY` to `backend/.env`, restart uvicorn |
| Answers sound template-y | No (or invalid) LLM key — check `OPENAI_API_KEY`; watch uvicorn logs |
| `seed.py` looks stuck on first run | It's downloading the embedding model (~90 MB, one time) |
| Port already in use | `lsof -nP -iTCP:8000 -sTCP:LISTEN` (or `:5173`) and kill it |
| Purchase actions return a manual link | Chromium not installed — `playwright install chromium`, or just use the link (that's the graceful fallback) |
| Uvicorn restart loop | You forgot the `--reload-exclude` flags — Chroma's writes retrigger reload |

## What you must not break

1. **Privacy is enforced in code, not prompts** — every read goes through
   `backend/agents/librarian.py`, which re-checks visibility on the live
   relational row for every vector hit. `tests/test_spine_*.py` prove a private
   entry can't leak even with corrupted vector metadata.
2. **Only `consent_guardian.py` changes visibility**, and only for the author.
3. **The Doer never pays or sends** — `guard_fill`/`guard_click` refuse
   credential fields and pay/send buttons; every action needs explicit human
   approval first.
