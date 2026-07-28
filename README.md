<div align="center">

# आँगन · Aangan

### A private family voice-journal — with one warm **Companion** that answers *only* from what each person chose to share.

**Built by · Vidit Bhatnagar · Aditya · Sumith Swaroop**

`FastAPI` &nbsp;·&nbsp; `SQLite` &nbsp;·&nbsp; `ChromaDB + local multilingual embeddings` &nbsp;·&nbsp; `React + Vite`
`Deepgram (STT + Aura TTS)` &nbsp;·&nbsp; `OpenRouter / OpenAI / Anthropic` &nbsp;·&nbsp; **174 tests · privacy-first**

</div>

---

*Aangan* (आँगन) means **courtyard** — the warm inner heart of a family home. Each
member keeps their own **voice journal**: ten seconds or ten minutes, whenever
they like. On top of everyone's journals sits one gentle Companion you can ask
things like *"How was Deepa's day?"* or *"What would Deepa want for her
birthday?"* — and it answers **only from what each person chose to share**.
Gentle care nudges prompt the right person to reach out, and small caring
actions (order the chocolates, draft the message) are prepared for a human to
approve and finish.

## Contents

- [Three sacred rules](#three-sacred-rules)
- [What's inside](#whats-inside)
- [System architecture](#system-architecture)
- [The privacy spine](#the-privacy-spine)
- [The capture pipeline](#the-capture-pipeline)
- [Asking the Companion](#asking-the-companion)
- [The conversational Doer](#the-conversational-doer)
- [The agent cast](#the-agent-cast) · [The eight screens](#the-eight-screens)
- [Setup and run](#setup-and-run) · [The seeded family](#the-seeded-family)
- [Privacy posture](#privacy-posture) · [The team](#the-team)

## Three sacred rules

1. **Private by default.** Every entry and every extracted fact starts private
   to its author. Visibility is enforced as a hard filter **in the retrieval
   code** — on both the relational store and the vector store, re-checked row
   by row — never as a prompt instruction.
2. **The author controls sharing.** The app may *suggest* sharing something;
   nothing moves from private to shared without the author's explicit yes, or a
   standing rule the author created themselves.
3. **A human approves and completes every real-world action.** The action agent
   prepares up to the point of payment or sending, then stops. It never enters
   card or password details — a code-level guard refuses those fields outright.

## What's inside

| | Feature | |
|---|---|---|
| <img src="docs/icons/mic.svg" width="20" alt=""> | **Voice journal** | hold-to-talk (Deepgram) or type; entries are private the instant they're spoken |
| <img src="docs/icons/lamp.svg" width="20" alt=""> | **The Companion** | one warm face that answers only from shared memories, grounded in real snippets |
| <img src="docs/icons/teapot.svg" width="20" alt=""> | **Baithak** | a multi-turn conversation with the Companion, remembered across turns |
| <img src="docs/icons/thoughts.svg" width="20" alt=""> | **My Thoughts + Personal Radar** | your own open loops, plans and gentle self-nudges — visible only to you |
| <img src="docs/icons/bell.svg" width="20" alt=""> | **Care alerts** | author-set triggers ("tell my sons if I mention my knee") — warm, never medical |
| <img src="docs/icons/gift.svg" width="20" alt=""> | **Conversational Doer** | clarifies, finds the right product on Amazon, and stops at the cart for you to pay |
| <img src="docs/icons/camera.svg" width="20" alt=""> | **Memory book** | the moments the family *chose* to share, kept together |
| <img src="docs/icons/globe.svg" width="20" alt=""> | **Bilingual** | English + हिन्दी throughout — content, replies, and the interface |
| <img src="docs/icons/lock.svg" width="20" alt=""> | **Real auth** | JWT in memory only, optional TOTP two-factor, multi-circle membership |

## System architecture

Everything runs on the server *you* run. The frontend never touches the stores
directly; every read flows through the **Librarian**, the one code path that
enforces who-can-see-what.

```mermaid
flowchart TB
 subgraph FE["Frontend — React + Vite · JWT kept in memory only"]
 S["8 screens<br/>Home · Journal · Ask · Alerts<br/>Actions · Memory · Thoughts · Me"]
 end

 subgraph BE["FastAPI · rate-limited · JWT + optional TOTP MFA"]
 RT["17 route modules<br/>/entries · /ask · /converse · /actions<br/>/alerts · /thoughts · /keepsake · /speak"]
 end

 subgraph AG["Agent layer — one plain-Python module each"]
 COND["Conductor"]
 LIB["Librarian — the privacy spine"]
 CG["Consent Guardian"]
 COMP["Companion / Baithak"]
 DOER["Doer — human-approval gate"]
 MORE["Transcriber · Summarizer · Extractor<br/>Alerter · Personal Radar · Reflector<br/>Speaker (Aura) · Interpreter · Prompter"]
 end

 subgraph ST["Local stores — on your machine"]
 DB[("SQLite<br/>relational source of truth")]
 VS[("ChromaDB + local MiniLM<br/>multilingual embeddings")]
 end

 subgraph EX["Optional providers — only what the asker may see ever leaves"]
 DG["Deepgram<br/>speech-to-text + Aura TTS"]
 AI["OpenAI · OpenRouter · Anthropic<br/>deterministic fallback if absent"]
 end

 S -->|"/api → :8000"| RT
 RT --> COND
 RT --> CG
 RT --> DOER
 RT --> MORE
 COND --> LIB
 LIB --> COMP
 LIB --> DB
 LIB --> VS
 CG --> DB
 COMP --> AI
 MORE --> DG
 MORE --> AI
 DOER --> AI

 classDef fe fill:#FBF4E7,stroke:#C9B58E,color:#22303a;
 classDef be fill:#EFE5D2,stroke:#8E2C22,color:#22303a;
 classDef ag fill:#F4ECDD,stroke:#3E6E70,color:#22303a;
 classDef spine fill:#B23A2E,stroke:#8E2C22,color:#FBF3E6;
 classDef st fill:#EAF0EA,stroke:#565633,color:#22303a;
 classDef ex fill:#E9EEF0,stroke:#3E6E70,color:#22303a;
 class S fe;
 class RT be;
 class COND,CG,COMP,DOER,MORE ag;
 class LIB spine;
 class DB,VS st;
 class DG,AI ex;
```

## The privacy spine

The single most important guarantee in Aangan: **another member's private
content is never placed into any prompt.** It isn't a request to the model —
it's enforced in code, and the spine tests (`tests/test_spine_*.py`) prove a
private entry can't leak even with corrupted vector metadata.

```mermaid
flowchart LR
 Q["A member asks a question"] --> COND["Conductor"]
 COND --> LIB["Librarian"]
 LIB --> E1["1 · Embed the question<br/>locally, multilingual"]
 E1 --> E2["2 · Vector search in Chroma<br/>scoped to the asker's circle"]
 E2 --> E3{"3 · For EVERY hit, re-check the<br/>LIVE SQLite row's visibility<br/>against THIS asker"}
 E3 -->|"visible to the asker"| KEEP["keep the snippet"]
 E3 -->|"private · not shared with them"| DROP["drop — it never reaches a prompt"]
 KEEP --> COMP["Companion answers<br/>ONLY from the kept snippets"]
 COMP --> A["Grounded answer + spoken reply"]

 classDef spine fill:#B23A2E,stroke:#8E2C22,color:#FBF3E6;
 classDef drop fill:#EFE5D2,stroke:#8E2C22,color:#8E2C22;
 class LIB,E3 spine;
 class DROP drop;
```

## The capture pipeline

A new entry is saved **private and instantly**; enrichment (summary, facts,
rules, indexing, alerts, action-detection) then runs — synchronously by
default, or in a background task when `ASYNC_CAPTURE=true` (the UI polls
`/entries/{id}/enrichment`).

```mermaid
flowchart LR
 V["voice / typed entry"] --> T["Transcriber<br/>Deepgram → text"]
 T --> SV["saved PRIVATE<br/>status: enriching"]
 SV --> SUM["Summarizer"]
 SUM --> EX["Extractor<br/>facts · private by default"]
 EX --> CR["Consent Guardian<br/>apply the author's OWN rules"]
 CR --> IDX["Librarian<br/>index with visibility tags"]
 IDX --> AL["Alerter<br/>author-set care triggers"]
 AL --> DO{"a command? e.g.<br/>'order flowers'"}
 DO -->|yes| DR["Doer drafts an Action<br/>awaiting your approval"]
 DO -->|no| DONE["ready "]

 classDef step fill:#F4ECDD,stroke:#3E6E70,color:#22303a;
 classDef save fill:#EFE5D2,stroke:#8E2C22,color:#22303a;
 class T,SUM,EX,CR,IDX,AL step;
 class SV,DR save;
```

## Asking the Companion

```mermaid
sequenceDiagram
 autonumber
 actor U as Family member
 participant API as FastAPI (ask · baithak)
 participant C as Conductor
 participant L as Librarian
 participant DB as SQLite + Chroma
 participant K as Companion
 participant TTS as Deepgram Aura

 U->>API: "What would Deepa want for her birthday?"
 API->>C: route the ask
 C->>L: retrieve relevant memories
 L->>DB: vector search + per-row visibility re-check
 DB-->>L: only snippets the asker may see
 L-->>C: safe snippets (no private content)
 C->>K: compose a warm answer from these
 K-->>API: grounded answer + sources
 API->>TTS: speak it — Aura voice "Helena"
 TTS-->>U: text + voice
```

## The conversational Doer

The Doer never blindly buys the first result. It **chats to get it right**,
recommends the best in-budget match, and — only after you approve — adds *that*
item to the cart and stops. A code-level guard makes the "never pays, never
sends" promise real.

```mermaid
flowchart TD
 I["'order chocolates for Deepa'"] --> CLR["Clarify<br/>kind? budget? — chat until sure"]
 CLR --> SRCH["Search Amazon.in live<br/>rank with the LLM · filter out accessories"]
 SRCH --> BEST["Recommend the best in-budget match<br/>+ a shortlist"]
 BEST --> APP{"Human approval<br/>stamp to approve"}
 APP -->|cancel| STOP["nothing happens"]
 APP -->|approve| CART["add THAT item to the cart"]
 CART --> HAND["safe hand-off<br/>cart ready — YOU review and pay"]
 GUARD["guard_fill / guard_click<br/>refuse card · CVV · password<br/>and any pay / place-order button"] -. enforces .-> CART
 GUARD -. enforces .-> HAND

 classDef doer fill:#F4ECDD,stroke:#3E6E70,color:#22303a;
 classDef guard fill:#B23A2E,stroke:#8E2C22,color:#FBF3E6;
 classDef stop fill:#EFE5D2,stroke:#8E2C22,color:#22303a;
 class I,CLR,SRCH,BEST,CART,HAND doer;
 class GUARD guard;
 class STOP stop;
```

## The agent cast

Each agent is a small, plain-Python module — easy to read, test, and reason
about.

| Agent | Role |
|---|---|
| <img src="docs/icons/compass.svg" width="20" alt=""> **Conductor** | routes every ask through the agents below |
| <img src="docs/icons/book.svg" width="20" alt=""> **Librarian** | **all** retrieval; enforces visibility on both stores, row by row |
| <img src="docs/icons/shield.svg" width="20" alt=""> **Consent Guardian** | the only code path that moves content private → shared |
| <img src="docs/icons/lamp.svg" width="20" alt=""> **Companion** | the one warm face — answers only from returned snippets |
| <img src="docs/icons/mic.svg" width="20" alt=""> **Transcriber** | Deepgram speech-to-text (graceful without a key) |
| <img src="docs/icons/feather.svg" width="20" alt=""> **Summarizer** / <img src="docs/icons/search.svg" width="20" alt=""> **Extractor** | summaries, snippets, and private-by-default facts |
| <img src="docs/icons/bell.svg" width="20" alt=""> **Alerter** | author-set triggers, severity, daily rate limits |
| <img src="docs/icons/gift.svg" width="20" alt=""> **Doer** | Playwright actions with the human-approval gate |
| <img src="docs/icons/radar.svg" width="20" alt=""> **Personal Radar** / <img src="docs/icons/mirror.svg" width="20" alt=""> **Reflector** | your own open loops and gentle self-nudges |
| <img src="docs/icons/speaker.svg" width="20" alt=""> **Speaker** | Deepgram Aura text-to-speech (warm neural voice) |
| <img src="docs/icons/globe.svg" width="20" alt=""> **Interpreter** | Hindi ⇄ English bridge |
| <img src="docs/icons/sprout.svg" width="20" alt=""> **Prompter** / **Relationship Radar** | gentle nudges, never pushy |
| <img src="docs/icons/book.svg" width="20" alt=""> **Keepsake** / <img src="docs/icons/mirror.svg" width="20" alt=""> **Mirror** | shared memory book / private reflection |
| <img src="docs/icons/shieldcheck.svg" width="20" alt=""> **Wording Guard** | keeps alert wording warm — never medical or diagnostic |
|  **LLM** | provider chain OpenAI/OpenRouter → Anthropic → deterministic fallback |

## The eight screens

**Home** · **Journal** · **Ask** · **Alerts** · **Actions** · **Memory** ·
**Thoughts** · **Me** — one file each under `frontend/src/screens/`, styled as a
family diary of letters home (warm paper, ink serif, wax seals, postmarks).

## Setup and run

Requirements: **Python 3.11 or 3.12** (not 3.9, not 3.13), **Node 18+**.

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium          # optional — enables live cart preparation
cp .env.example .env                 # then fill in any keys you have (all optional)
python seed.py                       # the demo family + rich, presentation-ready data
uvicorn app:app --reload --port 8000 --reload-exclude 'chroma_data/*' --reload-exclude 'data/*'
```

First run downloads the local embedding model
(`paraphrase-multilingual-MiniLM-L12-v2`, ~470 MB) once, then works offline.

### Frontend

```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173 (proxies /api → :8000)
```

### Verify

```bash
cd backend && .venv/bin/python -m pytest tests/ -q     # 174 tests — the privacy spine is the gate
cd frontend && npm run build                            # must compile clean
```

### Environment variables — `backend/.env`, all optional

```
DEEPGRAM_API_KEY=...     # live voice transcription + Aura text-to-speech
OPENAI_API_KEY=...       # LLM for summaries, extraction, Companion replies
OPENAI_BASE_URL=         # any OpenAI-compatible gateway, e.g. https://openrouter.ai/api/v1
OPENAI_MODEL=gpt-5.4-mini
ANTHROPIC_API_KEY=...    # alternative LLM provider (OpenAI wins if both set)
DEEPGRAM_TTS_MODEL=aura-2-helena-en   # the Companion's spoken voice
JWT_SECRET=change-me
```

**No keys? Everything still runs** on warm deterministic fallbacks (English +
Hindi); without `DEEPGRAM_API_KEY` the app offers typing instead of voice, and
the Companion uses the browser voice.

## The seeded family

Circle **Ghar** (invite code `GHAR-2026`), password `aangan123` for everyone:

| Member | Email | Language |
|---|---|---|
| Aditya (self) | `aditya@ghar.family` | en |
| Deepa (wife) | `deepa@ghar.family` | en |
| Mumma (mother) | `mumma@ghar.family` | hi |
| Abhishek (brother) | `abhishek@ghar.family` | en |

`python seed.py` builds a **full, presentation-ready portal** — 22 journal
entries across ~8 weeks, a 9-photo memory book, prepared & completed actions,
care alerts, and personal thoughts — so every dashboard, for every login, is
alive. The canonical demo still holds: log in as **Aditya**, ask
*"What would Deepa want for her birthday?"* → the Companion surfaces Deepa's
**shared** black-dress wish, while her private notes never surface for anyone.

## Privacy posture

- Family data is stored on the server you run (SQLite + local Chroma + local
  embeddings). With keys configured, only two things leave that server: audio
  goes to **Deepgram**, and questions + **only the snippets the asker may see**
  go to the LLM provider. With no keys, nothing leaves the machine. See
  `backend/legal/privacy.md`.
- Another member's private content is never placed into any prompt.
- The Mirror and My Thoughts are visible only to their owner; the memory book
  contains only shared moments.
- Aangan sends nudges so *people* connect. It is **not** a medical or emergency
  service and never presents itself as one.

## The team

<div align="center">

Designed and built with care by

### **Vidit Bhatnagar** &nbsp;·&nbsp; **Aditya** &nbsp;·&nbsp; **Sumith Swaroop**

*A private courtyard for families — built to be real, not a demo.*

</div>
