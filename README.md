# Aangan (आँगन) — AI Journal for the family courtyard

A private family app where each member keeps their own voice journal, and one warm
Companion answers questions only from what each person chose to share.

Full setup and run instructions land with the final polish commit; for now:

```bash
# backend
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000

# frontend
cd frontend
npm install
npm run dev
```

Three sacred rules:
1. **Private by default** — nothing is readable by others until its author shares it.
2. **The author controls sharing** — the AI proposes, the author decides.
3. **A human approves and completes every real-world action** — the app never pays or sends on its own.
