# Aangan operations runbook

Pilot-scale operations for a single-node deployment. Written to back the
business plan's Sections 9 (technology), 12 (operations), and 14 (safeguards)
with real, executable procedures.

## Hosting

Single container, one small VM (recommended region: Mumbai for the India
launch market — data-residency claim in the plan should match the region you
actually pick).

```bash
docker compose build
JWT_SECRET="$(openssl rand -hex 32)" AANGAN_ENV=production docker compose up -d
```

- The backend refuses to start in production with the default JWT secret.
- Terminate TLS at the host (Caddy/nginx/PaaS default) — encryption in transit.
- At-rest posture: enable disk/volume encryption on the host; SQLCipher is a
  future consideration. Do not claim more than this in the plan.
- Volumes: `aangan-db` (SQLite), `aangan-chroma` (vectors), `aangan-media`
  (audio + action screenshots), `aangan-models` (embedding-model cache).
- First boot downloads the embedding model (~90 MB) into the models volume.

## Backups

```bash
backend/scripts/backup.sh            # consistent sqlite .backup + chroma + media
```

Run nightly (cron). Keeps the last 14. **Restore:** stop the server, copy
`aangan.db` back, untar `chroma_data.tgz` and `media.tgz`, restart. Test the
restore quarterly — a backup that has never been restored is a hope, not a plan.

## Monitoring & logs

- `backend/logs/aangan.log` (rotating): provider failures (LLM, Deepgram) with
  agent context.
- LLM health metric: `scripts/metrics.py` → `llm_served_rate` (share of calls
  answered by a real model vs deterministic fallback). Corrective threshold:
  if it drops below 0.9 with keys configured, check provider keys/limits.
- Uptime: point any external pinger at `GET /health` once hosted.

## Account recovery (pilot)

```bash
backend/scripts/reset_link.py member@email   # prints a one-time /reset link, 24h
```

## Support & complaints

- In-app: Me → Help & feedback (stored in the `feedback` table), plus 🚩
  report flags on Companion answers and alerts.
- Process: a named human reviews the feedback table **weekly** (pilot cadence);
  reports about wrong AI output get a reply and, where needed, a fact
  correction or deletion using the in-app tools. No automated rejections.

## Incident response (one page)

1. **Detect** — log review, member report, or anomalous audit events
   (`audit_events` table: logins, visibility changes, membership changes).
2. **Contain** — rotate `JWT_SECRET` (invalidates all sessions), revoke
   affected API keys, take the service offline if data exposure is suspected.
3. **Assess** — which members, which data classes (audio, transcripts, facts),
   using the audit trail.
4. **Notify** — affected members without undue delay; follow DPDP Act 2023
   timelines for the India market.
5. **Learn** — write up cause and fix; add a test where possible.

## Data retention (current policy)

| Data | Retention |
|---|---|
| Journal entries, facts, vectors, audio | Until the author deletes them (per-entry or full account) |
| Backups | 14 days rolling |
| Audit events | Pilot: retained; revisit before public launch |
| Password-reset tokens | 24 h validity, single use |

## Release process

- CI (GitHub Actions) runs the full backend suite and the frontend build on
  every push.
- Schema changes during the pilot require re-running `seed.py` (wipes data) or
  a manual migration — Alembic is deliberately deferred until after the pilot.
- Rollback: previous image + last night's backup.
