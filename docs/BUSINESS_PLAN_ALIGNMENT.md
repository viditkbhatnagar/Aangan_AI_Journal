# Aangan × Business-Plan Alignment

> How Aangan's idea, concept, and codebase map onto the 20-section business-plan
> rubric in `Detailed Business Plan Structure.docx` — what we already evidence,
> what we must decide, and what we must build so every claim in the plan is
> honestly demonstrable in the product.
>
> The rubric is a template ("Include / Do not include" per section), not a
> filled plan. This document is the bridge: **Part A** gives Aangan's answer for
> each section, **Part B** is the codebase evidence & gap table, **Part C** is
> the engineering roadmap that closes the gaps, **Part D** is the non-code
> evidence workstream (research, testing, financials).

---

## Part A — Aangan's answers, section by section

### Section 1 — Executive summary (write it LAST)
| Rubric ask | Aangan's answer |
|---|---|
| Business name | **Aangan (आँगन)** — "courtyard": the shared open space at the heart of an Indian family home, where everyone gathers but each room stays private. Pronounceable in Hindi and English; directly reflects the product metaphor (private rooms = journals, courtyard = shared moments). A trademark/business-name search is still required before claiming availability. |
| Vision | A world where busy, scattered families never lose touch with the small things that matter about each other — where staying close is effortless and privacy is never the price of intimacy. |
| Mission | Aangan gives every family member a private voice journal and one warm AI Companion that shares only what each person chooses — so families notice, remember, and act on each other's everyday moments. |
| Values (each maps to a real safeguard in code) | 1) **Privacy by default** (visibility enforced in the retrieval code, not prompts); 2) **Author control** (only the Consent Guardian moves content, only for its author); 3) **Human agency** (no real-world action without explicit approval; the Doer never pays or sends); 4) **Warmth without deception** (the Companion is clearly an assistant, never medical, never fake-human); 5) **Grounded AI** (answers only from shared snippets, sources shown). |
| Product one-liner | A private family voice-journal app where one loving AI Companion answers questions about your family — only from what each member chose to share — and gently helps you act on it. |
| Main AI feature | Visibility-scoped retrieval-augmented answering: input = a family member's spoken/typed question + the shared journal snippets they are allowed to see; output = a warm grounded answer with sources and dates; human involvement = sharing is author-approved, actions are human-approved, alert triggers are author-defined. |
| Revenue model (recommended primary) | **Family-plan freemium subscription** (see Section 8 answer). |
| Funding | To be decided by the team; the financial model (Part D) should derive it from the cash-flow forecast, not ambition. |

### Section 2 — Business & problem description
- **Problem:** In busy, geographically scattered families (adult children working away from parents; NRI families; dual-income couples), members stop hearing each other's small daily moments. Consequences: missed early signals of a parent's health discomfort, forgotten gift wishes and dates, guilt and anxiety about "not calling enough", relationship drift. The desired state is knowing when to reach out and what matters — without surveillance and without forcing elders onto chat apps they find noisy.
- **Who experiences it:** Primary user = the "connector" adult (28–45, working, often living apart from parents); secondary users = spouse, parents (50–75, often more comfortable speaking Hindi than typing English), siblings. Payer = the connector adult.
- **Frequency:** Daily (missed check-ins) and event-driven (birthdays, illness, festivals) — validate with interviews (Part D).
- **Current alternatives:** Family WhatsApp groups (noisy, performative, no privacy gradient, nothing remembered), phone calls (synchronous, guilt-driven), private diary apps (Day One, Journey — single-player, nothing shared), reminder apps (no context), "do nothing".
- **Why insufficient:** Group chats force all-or-nothing sharing and remember nothing; diaries are private but isolated; none give a *consent-gradient* (share this one fact, keep the entry private) or a memory you can query ("what would Mumma want?").
- **Evidence to gather:** interviews/surveys (Part D); the rubric explicitly rejects fabricated statistics — do not invent market numbers.

### Section 3 — Proposed AI solution
- **How it works (already true end-to-end in the prototype):** register/join circle by invite code → hold-to-talk (or type) → Deepgram transcription → summary + private-by-default facts (LLM with deterministic fallback) → author's standing rules auto-apply → share prompts (author decides) → vector + relational memory → family members ask the Companion and get grounded, dated answers → author-set alert triggers notify chosen people → "you do it" delegations become actions that a human approves; the Doer prepares (cart at checkout / drafted message) and always stops before pay/send.
- **AI roles used:** NLP (transcription, summarization, extraction, Q&A), personalization (relationship labels, language), recommendation (gift hints from shared preference facts), automation with human control (Doer), decision support (alerts suggest, never diagnose).
- **Inputs:** voice/text entries (mandatory), language preference, sharing rules, triggers (optional). Sensitive handling: journals are the most intimate data class — see Section 14 alignment.
- **Outputs:** summaries, facts, grounded answers with source snippets + dates, alerts with suggested actions, prepared actions. Outputs show their sources in-product; confidence/limitation labeling is a gap (Part B).
- **Human review:** structural, not aspirational — author approves shares; recipient approves actions; triggers are author-authored. This satisfies the rubric's "which decisions are automated vs reviewed" with a real operating process.

### Section 4 — Target market & customer profile
- **Primary segment:** Indian urban + NRI "connector" adults, 28–45, salaried professionals, living apart from parents; smartphone-first; pay for 3–8 family subscriptions already (Netflix, Spotify Family).
- **Primary persona (evidence-based fiction to validate):** *Aditya, 34, product manager in Bengaluru; wife Deepa; mother in Lucknow speaking mostly Hindi; brother abroad.* Problem: guilt about missing Mumma's small health complaints and Deepa's hints; current solution: WhatsApp family group + memory; frustration: noise, forgetting, nagging feeling; desired outcome: "tell me when it matters and what she'd love"; objections: privacy of journals, another app for Mumma; channels: Instagram/YouTube, word of mouth; willingness to pay: family-plan range to be tested.
- **Early adopters:** NRI families (distance pain strongest), new caregivers of aging parents, couples in long-distance phases.
- **Secondary segments (later):** elder-care facilitators; close friend groups. Do NOT stretch to enterprise/all-consumers in the plan.
- The seeded demo family (Aditya/Deepa/Mumma/Abhishek) is deliberately the persona set — screenshots and demos automatically match the plan's persona section.

### Section 5 — Market & industry analysis (research workstream, Part D)
- Frame the market bottom-up: (Indian-origin households with split geography) × (family-plan subscription price), NOT "the global AI market". Distinguish TAM (all such families), SAM (English/Hindi, iOS/Android web, India+NRI corridors first), SOM (reachable via the chosen channels in year 1 with actual acquisition capacity).
- PESTLE/Porter/lifecycle: journaling apps = mature; family-tech + AI companions = emerging. Key forces: substitutes (WhatsApp = free), supplier power (LLM/API providers — mitigated in code by the provider-fallback chain), buyer power high (low switching costs today → build memory/network moat).
- Regulatory homework: India DPDP Act 2023, GDPR if NRI/EU, COPPA-like age rules if minors join circles — see Section 14.

### Section 6 — Competitor analysis
Minimum honest set: **Day One / Journey** (private journaling, no family layer), **Google Photos/“Memories”** (passive media, no consent gradient, no voice-first), **WhatsApp family groups** (the real incumbent; free; no privacy gradient, no memory, no nudges), **Life360** (family app but surveillance-posture — Aangan is its philosophical opposite), plus "do nothing/phone calls". Comparison factors: consent-gradient sharing, voice-first + Hindi, queryable family memory, care nudges, human-approved actions, price.
- **Differentiation that is hard to copy:** the consent-gradient data model enforced in code + accumulated private family memory (data moat with author permission) + trust posture (privacy as architecture, demonstrable in the spine tests). A single feature (e.g., "AI answers") is copyable; the trust architecture + memory accumulation is the defensible core.

### Section 7 — Value proposition
> For scattered families who fear losing touch with what matters, **Aangan** is a private family voice-journal with a loving AI Companion that remembers and shares only what each member chooses — unlike WhatsApp groups that force all-or-nothing sharing and remember nothing.

Advantage claims the plan may make **because code enforces them**: privacy-by-architecture (spine tests), human-AI service model (approval gates), local-market adaptation (Hindi voice-first, elder-tuned prompts), grounded answers with sources. Avoid claims of "better AI accuracy" — we use external models and have no benchmark yet.

### Section 8 — Business model (recommended, to validate)
- **Canvas:** segments = connector adults (payer) + family members (users); channels = app stores/web, NRI communities, content; relationships = self-service + community; key resources = codebase, consent-gradient data model, brand trust; key activities = product, trust/compliance, support; key partners = LLM provider (OpenRouter/OpenAI — swappable by design), Deepgram, hosting, payment gateway; costs = AI usage (per-token), transcription (per-minute), hosting, team.
- **Primary revenue model — Family Freemium:** Free: 1 circle, N members, capped voice minutes/asks per month, deterministic-fallback features always free. **Aangan Plus (family plan, monthly/annual):** unlimited/high caps on transcription + Companion asks, actions/cart-prep, memory book "on this day", longer retention, priority support. Single payer per circle matches how families already buy plans. Justification per rubric: recurring value (daily journaling), costs scale with usage (AI per-token — caps protect margin), one payer/many users fits the segment.
- Explicitly rejected for the plan: advertising (poisons trust posture), selling data/insights (contradicts values; rubric flags it), transaction commissions on Doer purchases (conflict-of-interest with "suggest, never sell"; disclose if ever added).

### Sections 9–10 — AI/technology plan & prototype
Largely already true — see Part B evidence table. The technology-plan section of the report can describe the real stack (FastAPI, SQLite→Postgres path, Chroma, local MiniLM embeddings, provider-chain LLM, Deepgram, JWT auth, Playwright doer, 116 tests incl. adversarial privacy tests) and the real architecture diagram. Prototype section: real screenshots exist (login, home, alerts, agents panel); user-journey friction points and ≥3-user testing remain to be executed (Part D).

### Section 11 — Marketing & customer acquisition
- Positioning: "the private family courtyard" — anti-surveillance, anti-noise family tech.
- Channels to test first: NRI community content (YouTube/Instagram reels of the demo), festival moments (Diwali/Raksha Bandhan campaigns), family-plan referral (invite codes exist in the schema, but surfacing them in-app is P0 item B2-#3 — the viral loop is not usable by real users until that ships).
- Funnel metrics (AARRR) require instrumentation — currently a gap (Part B/C).

### Section 12 — Operations plan
Map roles to the real agent architecture: AI processing = pipeline agents; support = human + in-product notices; QC = test suite + output sampling (gap: sampling process); complaints/appeals = gap (Part C). Automated-by-AI vs by-humans table falls directly out of the agent list.

### Section 13 — Team
Fill with the actual group; use the rubric's contribution table. Map roles: CEO/PM, CTO (owns spine + tests), AI & Data Lead (owns llm.py, extraction quality, bias testing), CMO (channels above), CFO (Part D model), CX Manager (support + user testing protocol).

### Section 14 — Ethical, legal, social
Aangan's story is unusually strong here **in architecture** (privacy spine, consent guardian, approval gates, non-medical alert wording, no localStorage tokens) but thin **in paperwork and controls** (no ToS/privacy policy, no consent records, no deletion/export, no audit trail UI, third-party data flows to Deepgram/OpenRouter undisclosed). Part B/C makes this the biggest compliance workstream.

### Sections 15–16 — Financial & funding plan (Part D)
The product must supply the unit-economics inputs: AI cost per entry/ask (token metering — gap), transcription minutes per user, hosting cost per circle. Three-year model: freemium conversion, family-plan ARPU, churn; break-even from contribution per paying circle. Funding ask derived from cash-flow trough, not vibes.

### Section 17 — Risk analysis (top candidates, each already partially mitigated in code)
1. **Privacy breach / trust collapse** (impact: existential) — mitigations: spine tests, minimal collection; gaps: encryption-at-rest story, incident response.
2. **AI usage costs outrun revenue** — mitigations: provider fallback, deterministic mode; gaps: per-user metering + caps (P1).
3. **Slow adoption / WhatsApp inertia** — mitigations: free tier, single-connector onboarding; validate via pilot.
4. **LLM/API provider dependence** — mitigated: OpenAI→OpenRouter→Anthropic→local chain in `llm.py`.
5. **Hallucinated/harmful outputs** — mitigations: grounded-only answering, never-medical wording tests; gaps: confidence labels, user reporting.

### Section 18 — Growth & scalability
Year 1: validate one corridor (India↔NRI), web app. Later: native mobile (voice-first argues for it), more languages (extraction/prompts already bilingual-ready), elder-care partnerships, family-archive exports. Technical scale path: SQLite→Postgres, Chroma→hosted vector DB, multi-circle tenancy (schema already supports circles; UI assumes one — gap), Docker/deploy story (gap).

### Section 19 — Implementation roadmap
Stage mapping in Part C (engineering) + Part D (research/report). The rubric's six stages map cleanly: problem research (D1) → model/features (done + A-sections) → prototype (done) → user testing (D2) → marketing+financial plan (D3, needs C2 instrumentation) → final report.

### Section 20 — Recommendation
The honest current recommendation the evidence supports: **launch a limited pilot** (3–5 real families, 4–6 weeks) using the working prototype, instrumented (C2) to produce activation/retention/willingness-to-pay evidence — then decide. Do not claim full-launch readiness in the plan.

---

## Part B — Codebase evidence & gap table

Result of a four-lens audit (product/monetization, ethics-legal-trust,
metrics/finance, ops/scalability) of the repo against the rubric.

### B1 — What the plan can already claim, with code as evidence

| Claim | Evidence |
|---|---|
| Privacy enforced in code, not prompts | `backend/agents/librarian.py` dual-store filter + authoritative relational re-check; adversarial spine tests incl. corrupted-vector-metadata leak test (`tests/test_spine_*.py`) |
| Author-only consent, all content private by default | `_vis_column()` defaults in `models.py`; `consent_guardian.set_visibility` is the only visibility-change path and refuses non-authors (tested) |
| Human-approved actions that never pay or send | `services/actions.py` approval gate; `agents/doer.py` `guard_fill`/`guard_click` refuse credential fields and pay buttons (unit-tested) |
| Author-authored alert triggers = recorded consent design | `AlertTrigger` rows are authored by the person the alert is about, timestamped, with audience chosen by them |
| Anti alert-fatigue controls | daily cap, per-fact dedupe, per-entry collapse in `agents/alerter.py` (tested) |
| Provider redundancy / no single AI supplier | `agents/llm.py`: OpenAI/OpenRouter → Anthropic → deterministic fallback, model-candidate fallback, auth-failure circuit breaker; `OPENAI_BASE_URL` portability |
| Honest free-tier basis | entire app runs keyless via deterministic fallbacks — a zero-marginal-cost free mode exists today |
| Family-plan billing unit already modeled | `FamilyCircle` + `Membership` (admin/member) + invite codes = "one payer, many members" schema |
| Voice-minutes cost input computable today | `JournalEntry.duration_sec` persisted per entry — Deepgram minutes per user is one SQL SUM |
| Cohort-capable core schema | `users.created_at` + author-keyed timestamped entries/facts/alerts/actions |
| Transparency UX | per-user agent-activity panel (`services/activity.py`) — scoped, never cross-user |
| Multilingual foundation | Hindi voice + extraction keywords + Companion replies; elder-tuned Hindi prompts |

### B2 — Gap table (deduplicated; each gap blocks a specific rubric claim)

**P0 — the plan cannot honestly describe an MVP until these close**

| # | Rubric § | Gap | Fix |
|---|---|---|---|
| 1 | 3, 10, 14 | **No deletion anywhere.** Author cannot delete an entry; no account deletion. Contradicts "your journal, your rules" and every retention/erasure requirement | `DELETE /entries/{id}` with full cascade (facts, share targets, referencing alerts, Chroma docs, audio file) + Journal UI affordance + spine test |
| 2 | 14, 9 | **No privacy policy / ToS / consent record**, and the "data stays on your machine" wording is false once keys are set (entries flow to Deepgram + OpenRouter/OpenAI) | Serve policy+ToS in-product; acceptance checkbox at registration persisted `(user_id, policy_version, accepted_at)`; first-run disclosure naming all three processors; correct README |
| 3 | 1, 11 | **Invite loop is broken for real users** — invite code shown only at creation, no UI ever displays it (Home even says "share your invite code") | `GET /circles/mine` + copy/share card on Home/Me |
| 4 | 10, 3 | **Doer cart-prep is demo-grade** (demo store default; Amazon path best-effort/ToS-risky) but could read as production commerce | Label as "simulated/best-effort demo" in the plan; keep live-retailer automation behind a setting; roadmap affiliate/official APIs |
| 5 | 9, 12 | **No hosted deployment** — no Docker, no prod config; "uptime/hosting" claims impossible | Dockerfile + compose (volumes for db/chroma/audio), deploy to one India-region VM/PaaS behind TLS; one-page hosting section |
| 6 | 9 | **Security floor below production**: default `change-me` JWT secret accepted, no password rules, no rate limiting | Refuse default secret outside dev; min password length; per-IP rate limits on auth + LLM endpoints; MFA = roadmap item |

**P1 — needed before monetization/viability claims (Sections 8, 11, 15, 20)**

| # | Rubric § | Gap | Fix |
|---|---|---|---|
| 7 | 15, 8 | **Zero AI usage metering** — no tokens, no cost per user, LLM-vs-fallback share unknown; `/ask` unmetered and unlimited (rubric's explicit "do not") | Instrument the `llm.py` chokepoint: `llm_calls` table (model, tokens, provenance llm/fallback, agent, latency, entry/ask context) + `asks` table + transcription minutes |
| 8 | 8, 11 | **No plans/tiers/caps/gating** — every "Plus" feature is free; no conversion mechanism exists | `plan` column on `FamilyCircle` + central `entitlements.py`; monthly caps (asks, voice minutes) with warm over-limit messages; gate 2–3 Plus features; gentle upgrade card + "Aangan Plus — notify me" fake-door (willingness-to-pay signal) |
| 9 | 11 | **No funnel measurement** — not one AARRR stage computable; activation undefined | `events` table + `record_event()` from existing routes (registered, first_entry, entry, share, ask, alert_seen, action_approved); `last_seen_at` on User via auth dependency; activation = "first entry within 7 days" (extend once asks persist); metrics CLI/endpoint |
| 10 | 8, 9 | **No payment integration** (none claimed yet — keep it that way until built) | Razorpay/Stripe behind entitlements when pilot pricing tests begin; mock pricing page clearly labeled until then |
| 11 | 3, 12 | **No support channel or correction tools** — no feedback route, no fact edit/delete, no "this looks wrong" | `/feedback` endpoint + Help section in Me; author-only fact PATCH/DELETE with re-index; report flag on answers/alerts |
| 12 | 14 | **No leave-circle / remove-member** — in the abuse worst-case, a victim can't leave | Leave + admin-remove endpoints purging ShareTargets/audiences + re-index; account recovery flow (pilot: admin one-time link) |
| 13 | 9, 12 | **No backups, no logging, no CI, no error visibility** (provider failures silently swallowed) | Nightly backup script + tested restore runbook; structured logging at `llm.py`/`transcriber.py` failure points incl. fallback-rate; GitHub Actions running pytest + build |
| 14 | 7, 4 | **Hindi UX is half-true** — Hindi voice/AI yes, but UI labels are English-only for the elder persona | Small i18n dictionary (~40 strings) keyed off `user.language`; until then phrase claims precisely |
| 15 | 11, 7 | Session lost on refresh (memory-only JWT) — deliberate privacy posture but a retention risk for elders; unlimited recording length conflicts with cost claims | Present as deliberate trade validated in user testing, or opt-in keep-me-signed-in; auto-stop recording at N minutes (Plus raises cap) |
| 16 | 18, 12 | Capture pipeline runs synchronously in-request — latency degrades under small concurrency | Move summarize/extract/index/alert to background tasks; activity panel already supports async UX |

**P2 — trust/compliance depth** | audit trail (`AuditEvent` append-only: visibility changes, consent, auth events, approvals — also feeds the agent panel durably) · code-level never-medical post-check on alert wording + test (today prompt-only) · `GET /me/export` + `DELETE /me` (portability/erasure) · encryption-at-rest posture (encrypted volumes; SQLCipher evaluation) + IR runbook · 18+ age policy for MVP (DPDP 2023) · model eval set (en/hi extraction precision, answer groundedness) — no accuracy claims until measured · mobile audit at 320/375/768 + iOS Safari MediaRecorder check · Alembic migrations.

**P3 — growth-section claims** | referral attribution (`source`/`invite_code` on registration → real K-factor) · multilingual embedding model eval (MiniLM is English-biased vs the Hindi core market — name language as the primary bias axis) · multi-circle membership + switcher (schema ready, UI assumes one) · load test then Postgres/pgvector migration path · official commerce/affiliate API before any transaction-revenue claim · API/enterprise/white-label stay roadmap-only.

---

### B3 — Status after the alignment execution (2026-07-23)

All P0 and P1 gaps above are **closed in code** (see commits `1c377cf`…): entry
deletion cascade (#1), legal/consent surfaces + corrected disclosure (#2),
invite loop (#3), Doer labeled honestly (#4), Docker deploy story (#5),
security floor + rate limiting (#6), usage metering + `scripts/metrics.py`
(#7, #9), entitlements + caps + fake-door (#8), support/corrections (#11),
leave/remove-member + reset links (#12), backups/logging/CI (#13), Hindi UI
strings (#14), 5-minute recording cap (#15). From P2: audit trail, code-level
never-medical enforcement, export + account erasure, ops/IR runbook
(docs/OPERATIONS.md), 18+ policy. From P3: referral `?ref=` attribution.

**Still open (deliberate):** live payment gateway (needs merchant account —
fake-door measures demand meanwhile), cloud deployment (needs an account —
one `docker compose up` away), MFA, async capture pipeline, Alembic,
multi-circle UI, multilingual embedding swap, official commerce APIs, and the
session-persistence trade (memory-only JWT kept as a privacy posture — to be
validated in D2 user testing).

## Part C — Engineering roadmap (four waves)

**Wave 1 — Truth & trust (P0, ~1 week).** Entry deletion cascade + UI + spine
test · legal/consent surfaces + processor disclosure + README correction ·
invite-code card (`GET /circles/mine`) · security floor (secret guard, password
rules, auth rate limits) · Docker + single-VM India deploy + TLS · relabel Doer
honestly. *Exit criterion: every sentence in the plan's product sections is
demonstrably true.*

**Wave 2 — Monetization & measurement (P1, ~2 weeks).** Unified usage metering
(`llm_calls`, `asks`, minutes; provenance flag) · entitlements + caps + Plus
gating + fake-door · event spine + activation metric + metrics report ·
support/feedback + fact corrections · leave/remove-member + account recovery ·
backups, logging, CI, background pipeline · Hindi UI strings. *Exit criterion:
the pilot can produce real activation/retention/unit-cost numbers for Sections
11/15/20.*

**Wave 3 — Trust depth (P2, parallel with pilot).** AuditEvent trail ·
never-medical code check · export/account-delete · encryption posture + IR
runbook · age policy · en/hi eval set · mobile audit · Alembic.

**Wave 4 — Growth claims (P3, post-pilot).** Referral attribution ·
multilingual embeddings · multi-circle · load test + Postgres path · commerce
APIs.

**Consistency fixes now:** ~~standardize the test count across docs~~ — done;
all docs quote the current suite size (116).

## Part D — Non-code evidence workstream

The rubric repeatedly rejects claims without evidence. These are the four
evidence packages the report needs that code alone can't produce.

### D1 — Problem & willingness-to-pay research (Sections 2, 4, 5, 20)
- 10–20 interviews with "connector" adults (mix India-resident + NRI). Ask about
  the last time they missed something that mattered (parent's health, a hint, a
  date); what they do today; what they'd pay for a family plan. Never leading
  questions; record consent.
- Short survey for frequency data ("how often do you learn late about a family
  member's small troubles?") to honestly fill the frequency subsection.
- Secondary sources: India DPDP context, journaling-app and family-app market
  reports, NRI remittance/communication statistics — every figure with source,
  year, currency, geography as the rubric demands.

### D2 — Prototype user testing (Section 10, minimum three users)
- Recruit ≥3 people matching the personas (at least one Hindi-preferring elder).
- Fixed task script: register → join circle → record an entry (voice, then typed
  fallback) → share one fact only → ask the Companion about another member →
  act on an alert. Measure completion, time, errors, confusion points; collect
  quotes with consent.
- Feed findings back: log original issue → change made → retest where possible
  (the rubric wants the before/after loop documented). The agent-activity panel
  makes "what the AI did" observable during tests — use it in sessions.

### D3 — Financial model inputs (Sections 15–16)
- Pull real unit costs from instrumentation (Part C): tokens per
  summarize/extract/ask, Deepgram minutes per entry, → cost per active family
  per month at observed usage.
- Model: free→paid conversion assumption (state it as assumption), family-plan
  price candidates from D1, churn scenario range, 3-year P&L + monthly Year 1,
  break-even circles count, funding need = max cumulative cash shortfall + contingency.

### D4 — Legal & policy pack (Section 14)
- Draft ToS + privacy policy (data categories, purposes, third-party processors
  — Deepgram, OpenRouter/OpenAI — retention, deletion, rights); jurisdiction
  research for India DPDP; age policy for minors in circles. In-product surfaces
  come from Part C; the documents themselves are this workstream.

---

*Generated as the working bridge between `Detailed Business Plan Structure.docx`
and the Aangan codebase. Keep this file updated as gaps close.*
