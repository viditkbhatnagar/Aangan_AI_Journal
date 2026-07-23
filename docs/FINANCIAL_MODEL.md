# Aangan financial model — assumptions, provenance, and how to use it

The model lives in `backend/scripts/financial_model.py`. Run it from `backend/`:

```bash
cd backend
.venv/bin/python scripts/financial_model.py
# examples:
.venv/bin/python scripts/financial_model.py --price-inr 499
.venv/bin/python scripts/financial_model.py --tok-in 0.15 --tok-out 0.60 --stt-per-min 0.0092
```

It prints six numbered tables. This document says where every number comes
from and which business-plan section each table feeds (per
`docs/BUSINESS_PLAN_ALIGNMENT.md`, Part D3 and Sections 15–16).

## What is observed vs assumed

The script reads the real local database (`backend/aangan.db`) first and
labels every input `observed (…)` or `default (…)` in Table 1. Observed
today (2026-07-23, pre-pilot seed + smoke-test data):

- **Tokens per agent call** — from `llm_calls` (real metered OpenRouter
  calls): Summarizer ≈ 183 in / 57 out, Extractor ≈ 415 in / 112 out,
  Alerter ≈ 140 in / 36 out. Companion has only 1 metered call so far, so a
  default (450/60) is used — the single real call (445/35) confirms it.
- **LLM served rate 1.00** — all 13 metered calls hit a real provider
  (fallback calls cost ₹0, so a lower rate would only cut costs).
- **Members per circle 4.0** — the seeded family (4 users / 1 circle),
  which also matches the persona (2 parents + 2 adult children).

Everything below the thresholds (20 asks, 30 entries, 10 voice entries) is a
**stated default** until the pilot fills the tables. The script re-labels
automatically — no code change needed after the pilot.

## Assumption register

| # | Assumption | Default | Rationale / source | Override |
|---|---|---|---|---|
| 1 | LLM price in/out | $0.25 / $2.00 per 1M tokens | OpenAI gpt-5-mini (openai.com/api/pricing, checked Aug 2025) — the mini tier in `agents/llm.py` `OPENAI_CANDIDATES`. Cheaper fallbacks exist (gpt-4o-mini $0.15/$0.60, gpt-5-nano $0.05/$0.40), so this is conservative. | `--tok-in`, `--tok-out` |
| 2 | Speech-to-text | $0.0059 / audio min | Deepgram Nova-2 streaming pay-as-you-go (deepgram.com/pricing, checked 2025); Nova-2 supports Hindi (elder persona). Nova-3 multilingual ≈ $0.0092 — test with `--stt-per-min 0.0092`. | `--stt-per-min` |
| 3 | Hosting | $12/mo per slice, 500 circles/slice | One 2 vCPU/4 GB VPS (Hetzner/DO class, checked 2025) runs the single-container `docker compose` deploy. Capacity per slice is an engineering estimate — revisit at scale. | `--hosting-usd`, `--circles-per-host` |
| 4 | FX | ₹86 / USD | Approximate mid-2026 spot; all provider costs are USD, revenue is INR. | `--fx` |
| 5 | GST | 18%, price is GST-inclusive | Indian GST on digital services; consumer price candidates are quoted inclusive. | constant `GST_RATE` |
| 6 | Payment gateway | 2% of gross | Razorpay-class standard UPI/card rate. | constant `GATEWAY_FEE_RATE` |
| 7 | Fixed opex | ₹2,000/mo | Domain, email, error tracking, misc tooling. Team salaries are deliberately EXCLUDED (see note under Table 5). | `--fixed-opex` |
| 8 | Price candidates | ₹199 / ₹349 / ₹499 per circle/mo | Placeholder ladder to be validated by D1 willingness-to-pay interviews; ₹349 is the working default. | `--prices`, `--price-inr` |
| 9 | Usage per active family | 12 entries/member/mo, 15 asks/member/mo, 90 s voice, 70% voice share | "Active family" definition: ~3 entries/member/week; asks sized under the free cap (100/circle from `entitlements.py`, imported live so caps never drift from code). All replaced by observed values post-pilot. | defaults in script |
| 10 | Plus usage multiplier | 1.5× | Paying circles are uncapped and self-selected heavy users. | `--plus-mult` |
| 11 | Growth | 5 new circles in M1; +25%/mo Y1, +10%/mo Y2, +5%/mo Y3 | M1 = pilot families (Section 20 recommends a 3–5 family pilot); growth taper is a founder-marketing assumption, not evidence. Same curve for all scenarios — only conversion/churn vary. | `--m1-signups`, constants |
| 12 | Free→paid conversion (monthly, of free base) | 0.5% / 1.5% / 3.0% (pess/base/opt) | Consumer-freemium benchmarks put lifetime conversion at 2–5%; expressed here as a monthly rate on the active free base. | constants `SCENARIOS` |
| 13 | Paid churn (monthly) | 8% / 5% / 3% | Consumer-subscription range; family plans churn slower than individual ones. | constants `SCENARIOS` |
| 14 | Free churn (monthly) | 12% / 10% / 8% | Free circles going inactive; also keeps the free-rider cost base honest. | constants `SCENARIOS` |
| 15 | Funding contingency | +25% | Buffer on the modeled cash trough (Section 16 asks that funding be derived from the trough, not ambition). | `--contingency` |

## Output → business-plan mapping

| Table | Feeds | Use it for |
|---|---|---|
| 1. Unit inputs | Section 15 (unit economics), Section 11 (metrics) | Show that cost inputs are metered, not invented; cite the `observed (…)` labels. |
| 2. Cost per active family/month | Section 15 unit-economics table | Headline: **₹29.2/mo per active free family; ₹43.8/mo per Plus family** (at current observed token averages). STT is ~85% of variable cost — the cost lever is voice minutes, not tokens. |
| 3. Price → contribution → break-even | Sections 15 & 16, pricing discussion (with D1) | ₹349 nets ₹289 after GST+fees, contributes ₹245/circle; ~13 paying circles cover pilot-scale fixed costs (26 at ₹199, 9 at ₹499). |
| 4. Year-1 monthly per scenario | Section 15 (monthly Year-1 requirement) | Paste per-scenario; shows losses are hosting-dominated, not usage-dominated, at pilot scale. |
| 5. Three-year annual P&L | Section 15 (3-year requirement) | Gross margin turns positive in base Y3 (~2%) and optimistic Y2 (32%). Team salaries excluded — add them from Section 13 headcount when finalizing. |
| 6. Funding need | Section 16 (funding plan) | Funding = max cumulative shortfall + 25%: ₹744k pessimistic, ₹238k base, ₹52k optimistic (product-only, ex-salaries). Quote the base case; show the range. |
| Section 20 | Recommendation | Optimistic reaches monthly break-even M16 and cash-positive M23; pessimistic never does within 36 months — supports the "pilot first, then decide" recommendation. |

## Re-running after the pilot (do this)

1. Run the pilot with real families (instrumentation is already live:
   `llm_calls`, `asks`, `journal_entries.duration_sec`, `product_events`).
2. From `backend/`: `.venv/bin/python scripts/metrics.py` for the funnel,
   then `.venv/bin/python scripts/financial_model.py` for economics.
3. Check Table 1: every row that flips from `default` to `observed (…)`
   is a pilot deliverable. The thresholds are 2 metered calls per agent,
   20 asks, 30 entries, 10 voice entries.
4. Replace assumptions 8 and 12 with D1 interview findings (price ladder,
   willingness to pay) and adjust `SCENARIOS` in the script header.
5. Re-paste Tables 2–6 into Sections 15–16 and update the funding ask.

## Known limitations (say these out loud in the plan)

- Team salaries and marketing spend are excluded; the model prices the
  product engine only. Layer people costs from Section 13 before quoting
  net profit.
- Growth is an assumption curve, not a forecast; conversion/churn are
  benchmark ranges until the pilot produces real cohorts.
- Seed data slightly inflates "members per circle = observed" confidence
  (one circle). Treat it as persona-consistent, not statistically observed.
- Embeddings run locally (MiniLM) so they cost ₹0 marginal; if that ever
  moves to a paid API, add a line to `family_month_cost`.
