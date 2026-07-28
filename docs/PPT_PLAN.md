# Aangan — Final Presentation Plan (research-backed, section by section)

> Working plan for the ~12–18 slide final presentation for the AI in Entrepreneurship class.
> Built from (a) the codebase and its evidence docs (`BUSINESS_PLAN_ALIGNMENT.md`,
> `FINANCIAL_MODEL.md`, the test suite), and (b) a six-stream web research pass
> (July 2026) in which **every statistic carries source + year + URL** and anything
> unverifiable is marked NOT FOUND. The rubric rejects fabricated statistics — this
> plan never needs any.

---

## Slide map (16 slides + appendix)

| # | Slide | Section |
|---|---|---|
| 1 | Title — business name & team | 1 |
| 2 | The problem — "the small things get lost" | 2 |
| 3 | The solution — one Companion, three sacred rules | 3 |
| 4–5 | Product demonstration (live demo or 2 screenshot slides) | 4 |
| 6 | Target market | 5 |
| 7 | Customer persona — the seeded family IS the persona | 6 |
| 8 | Market opportunity (bottom-up TAM/SAM/SOM) | 7 |
| 9 | Competitor analysis (matrix + positioning) | 8 |
| 10 | Business model — family freemium, enforced in code | 9 |
| 11 | Marketing strategy — channels ranked by evidence | 10 |
| 12 | Technology & AI model — privacy as architecture + why now | 11 |
| 13 | Financial projections — metered, not invented | 12 |
| 14 | Risks & ethical issues — risk register + ahead-of-the-curve compliance | 13 |
| 15 | Growth plan | 14 |
| 16 | Final recommendation — pilot first | 15 |
| — | Backup/appendix slides (see end) | — |

**Narrative arc:** families are scattering (problem) → money travels but daily life doesn't (emotion) → a private courtyard with a consent-gated Companion (solution) → it already works (demo) → the buyers exist and already pay for family bundles (market/model) → the economics are metered and honest (financials) → trust is designed in, not promised (risk) → so run the pilot (recommendation).

---

## Slide 1 — Business name and team

**Goal:** the name lands as the product thesis in one breath.

- **Aangan (आँगन)** = "courtyard" — the shared open space at the heart of an Indian family home, where everyone gathers **but each room stays private**. The name IS the architecture: private rooms = journals, courtyard = shared moments.
- One-liner: *"A private family voice journal where one loving AI Companion answers your questions about family — only from what each person chose to share."*
- Team table (rubric wants roles + contributions): CEO/PM, CTO (privacy spine + 140 tests), AI & Data Lead (LLM chain, extraction, bilingual eval), CMO, CFO (financial model), CX. **[FILL: actual team names/roles — Aditya Tripathi, Vidit K Bhatnagar, + others]**
- Footer honesty: "Working name — trademark search pending."

**Visual:** wordmark + a courtyard diagram (rooms = private journals, courtyard = shared).

---

## Slide 2 — Customer problem

**Goal:** the audience *feels* the missed-signal problem before seeing a single product screen.

**Open with the humanizing hook (qualitative, sourced):**
> "Many Indian parents have mastered the art of sounding 'fine'… What they do not mention are the skipped meals… the unopened medicine strips." — Samarth Elder Care, on NRI parents (2026, vendor content — attribute as such)

Or the muted-group quote: *"I've muted my family group for a year. I love them, but every morning starts with 20-odd messages."* — Deccan Chronicle, "Mute: The New Namaste" (Nov 2025)

**Then 4–5 hard stats (all verified, India-first):**
| Stat | Source |
|---|---|
| India's 60+ population: 149M (2022) → **347M by 2050**; elders outnumber children by 2046 | UNFPA India Ageing Report 2023 |
| **36% of Indian older parents already have a migrant child**; left-behind elders report worse health (20% vs 13% poor health) and more depression (17% vs 12%) | LASI 2017-18 via SSM–Population Health 2023 |
| **~1 in 4 Indian elders lives with no child in the house** (5.1% alone + 19.5% spouse-only); 41.8% of solo elders report low life satisfaction | LASI via BMC Geriatrics 2023 |
| **42% of Indians 45+ with hypertension don't know they have it** — the daily signals that would prompt a check-up are being missed | LASI via Int J Equity Health 2023 |
| **$129B remittances in 2024 — world's #1** … the money travels; the daily moments don't | World Bank 2024 |

**Why current alternatives fail (one line each):** WhatsApp family groups = one visibility level, everything to everyone, meaningful moments drown in forwards (peer-reviewed: Digital Journalism 2023 on Indian family groups as noisy misinformation spaces); private diary apps = single-player; phone calls = synchronous + guilt-driven; elders answer "sab theek hai" (geriatric literature calls it "dependency anxiety", JFMPC 2021).

**Honesty note:** no rigorous NRI call-frequency survey exists (NOT FOUND) — frequency claims come from D1 interviews, not invented numbers.

**Visual:** map graphic (parents in Lucknow, son in Bengaluru, brother abroad) + the stat band.

---

## Slide 3 — Proposed AI solution

**Goal:** one flow diagram + three rules the audience can repeat.

**The flow (all real, end-to-end today):**
speak/type → Deepgram transcribes (Hindi/English auto-detect) → AI summarizes + extracts **private-by-default** facts → author's own standing rules apply → share suggestions (author decides) → family asks the **Companion** → answers grounded ONLY in consented snippets, with sources + dates → author-set care triggers alert chosen people → "order some flowers" becomes a **human-approved** action.

**Three sacred rules (enforced in code, not prompts):**
1. **Private by default** — visibility is a hard filter in retrieval, on both stores, re-checked row by row.
2. **The author controls sharing** — one code path (Consent Guardian) can ever widen visibility, only for the author.
3. **A human approves every action** — the Doer never pays or sends; code-level guards refuse credential fields and pay buttons.

**AI roles line (rubric asks):** NLP (STT, summarization, extraction, RAG Q&A) · personalization (relationship labels, language) · recommendation (gift hints from shared preferences) · automation with human control (Doer) · decision support (alerts that never diagnose).

**Visual:** pipeline diagram with the 12 agents as small icons (Conductor, Companion, Librarian, Transcriber, Summarizer, Extractor, Consent Guardian, Alerter, Prompter, Radar, Doer, Interpreter) — same icons as the in-app "Agents at work" panel.

---

## Slides 4–5 — Product demonstration

**Goal:** prove it's a working system, not a mockup — and make the privacy spine *visible*.

**Live demo script (seeded family, runs keyless/offline — zero demo risk):**
1. Log in as **Aditya** → Home: lit diya, family register, gentle nudges.
2. Ask: *"What would Deepa want for her birthday?"* → black-dress answer **with source snippet + date**, read aloud (Aura TTS).
3. The kill shot: show Deepa's recent **private** entry never surfaces, for any phrasing. (Optionally: open the Agents panel while asking — "Librarian: found N snippets you're allowed to see — private ones stayed sealed.")
4. Alerts: Mumma journaled knee pain **in Hindi** → both sons got a gentle, never-medical alert with a suggested action.
5. Actions: "order chocolates for Deepa" → Doer's clarifying chat (budget?) → errand receipt with a real product → **stamp to approve** → cart prepared, safe handoff, "you always pay."
6. Close on the **"Behind the scenes" trace** — every step the AI took, visible.

**Fallback screenshots (if no live demo):** Home · Ask answer with sources · Alert telegram · Action receipt + trace · Agents panel · Journal letter with share controls.

**Design language callout:** "Chitthi / Letters Home" — entries are sealed letters, alerts are telegrams, actions are errand receipts. Warmth is the brand.

**Rubric tie-in:** user testing with ≥3 persona-matched users (incl. one Hindi-preferring elder) is the D2 workstream — present completed sessions if done by presentation day, else show the D2 protocol as "scheduled."

---

## Slide 6 — Target market

**Goal:** a specific, reachable buyer — not "everyone with a family."

- **Primary segment:** the "connector" adult — 28–45, salaried, urban India or NRI, living apart from parents, already pays for 3–8 family subscriptions. **They are the payer; the family are the users.**
- **Early adopters:** NRI families (distance pain strongest), new caregivers of aging parents, long-distance couples.
- **Secondary (later):** elder-care facilitators, close friend groups. (Explicitly NOT enterprise.)

**Segment-sizing facts:**
| Fact | Source |
|---|---|
| 37.28M overseas Indians — world's largest diaspora (US 6.1M, UAE 4.3M, Canada 3.2M, UK 1.3M) | MEA, Govt of India, retrieved 2026 |
| Indian-American median household income **$145,000** — premium willingness-to-pay segment | Pew Research (2022 data) |
| 958M active internet users in India (2025) | IAMAI-Kantar |
| **58.2% of Indian households are nuclear**; ~402M internal migrants | NFHS-5 (2019-21); EAC-PM (2023) |
| 98% of Indian internet users consume Indic-language content → Hindi voice-first is a requirement, not a feature | IAMAI-Kantar 2024 |

**Visual:** two concentric audiences (India-urban + NRI corridors on a map), payer vs users called out.

---

## Slide 7 — Customer persona

**Goal:** make the demo family and the persona the same people — screenshots then automatically match the persona section (rubric loves internal consistency).

**Persona: Aditya, 34, product manager, Bengaluru.** Wife Deepa; mother ("Mumma") in Lucknow, more comfortable in Hindi; brother Abhishek abroad.
- **Problem:** guilt about missing Mumma's small health complaints and Deepa's hints; WhatsApp group is noise; memory fails.
- **Desired outcome:** "Tell me when it matters and what she'd love."
- **Objections:** privacy of journals ("who reads this?"), "another app for Mumma?"
- **Channels:** Instagram/YouTube, NRI communities, word of mouth.
- **Willingness to pay:** family-plan range — to be tested in D1 interviews (say "to validate", don't invent).

**Ground each pain in one stat:** Mumma → 1-in-4 elders with no child at home + only 20% of urban Indian elders comfortable with a digital device (HelpAge India 2024 → hence *voice*-first, hold-to-talk); Aditya → 36% of parents have a migrant child (LASI); Abhishek → NRI "disenfranchised grief" framing (Dr. Prerna Kohli) + 50% of NRIs prioritize elderly family wellbeing (Policybazaar Jan 2025 — label as industry survey).

**Visual:** the four seeded faces with speech bubbles — then the actual app screenshot of the same four in the family register.

---

## Slide 8 — Market opportunity

**Goal:** a bottom-up, sourced TAM/SAM/SOM — the anti-"1% of a $100B market" slide.

**Category comparables (cite verbatim, footnote conflicts):**
- Digital journal apps: **$5.7–6.1B (2025), ~10–11.5% CAGR** (Straits Research; Market Research Future — figures conflict across firms; both quoted).
- Mental health apps: $7.48B (2024) → $17.52B (2030), 14.6% CAGR; **India slice $498M (2024) → $1.41B (2030), 18.5% CAGR** (Grand View Research).
- AI companion apps: 220M downloads, ~$120M revenue in 2025, +88% YoY downloads (Appfigures/TechCrunch) — people already pay to talk to AI.

**Bottom-up construction (label derivations as own calculations):**
- **TAM:** 37.28M-person diaspora (MEA) + urban nuclear India (535M urban × 58.2% nuclear share, ÷ 4.4 household size).
- **SAM:** India households that already pay for digital subscriptions — **143M households hold 216M paid OTT subscriptions; digital subscription revenue ₹16,300 crore in 2025, +60% YoY** (FICCI-EY 2026) — × family-separation propensity; NRI corridor households (US/UAE/UK/Canada/Australia).
- **SOM (year 1):** what the chosen channels can actually reach — pilot → hundreds of circles; anchored to the financial model's growth curve (5 circles in M1, +25%/mo Y1 — stated as assumption).

**Why now (one line):** Apple launched Journal (Dec 2023) and expanded it to iPad/Mac (2025) — journaling is platform-mainstream; voice AI funding grew $315M → $2.1B (2022→2024, CB Insights).

**Visual:** funnel TAM→SAM→SOM with the sources printed inside each band.

---

## Slide 9 — Competitor analysis

**Goal:** one matrix that shows a documented empty slot — then say the honest caution out loud.

**Comparison matrix (verified July 2026):**
| | Consent-gradient sharing | Voice-first | Hindi | Ask AI about *family* | Care nudges | Human-approved actions | Price |
|---|---|---|---|---|---|---|---|
| Day One (Automattic) | ✗ whole-journal, ≤30 people | ~ | ✗ | ~ own journal only | ✗ | ✗ | $49.99–74.99/yr |
| Journey | ✗ | ~ | ✗ | ~ | ✗ | ✗ | $6.99/mo |
| Apple Journal | ✗ no sharing at all | ~ | ~ | ✗ | ✗ | ✗ | free |
| StoryWorth / Remento / Storii | ✗ broadcast-by-design | ~/✓ | ✗ (En+Es) | ✗ | ✗ | ✗ | $69–199 |
| Life360 | ✗ | ✗ | ✗ | ✗ | ~ safety only | ✗ | free–$24.99/mo |
| WhatsApp | ✗ everyone sees everything | ~ | ✓ | ✗ | ✗ | ✗ | free |
| Google Photos | ✗ | ✗ | ~ | ~ own photos | ✗ | ✗ | free |
| AI journals (Rosebud…) | ✗ single-user | ✓ | ✗ | ~ own notes | ✗ | ✗ | ~$10/mo |
| Khyaal / Samarth (India eldercare) | ✗ logistics, not memory | ✗ | ✓ | ✗ | ~ human services | ✗ | ₹999/yr–₹15k/mo |
| **Aangan** | **✓ per-entry, in code** | **✓** | **✓** | **✓ consent-filtered** | **✓ never-medical** | **✓ code-gated** | ₹349/mo family |

**Story beats:**
- **The incumbent is free:** WhatsApp, ~535M India users — but it's a firehose, not a memory ("mute is the new namaste").
- **The cautionary incumbent proves payment:** Life360 — **95.8M MAU, $489.5M FY2025 revenue, 2.8M paying circles** — families demonstrably pay for family apps… and it was caught selling precise location data of tens of millions incl. children (The Markup 2021). Aangan is its philosophical opposite: care signals **without surveillance**.
- **The honest caution (say it before they ask):** Day One is the closest structural competitor and could add consent tiers. The durable moat is the **combination**: consent-gradient retrieval architecture + Hindi voice + care nudges + gated actions + accumulated consented family memory.
- **Documented whitespace:** no India-built, Hindi-first, consent-based family voice-journal was found (search sweep, July 2026).

**Visual:** the matrix + a 2×2 (x: individual ↔ family; y: surveillance/broadcast ↔ consent) with Aangan alone in the family+consent quadrant.

---

## Slide 10 — Business model

**Goal:** "the freemium is already enforced in code, priced inside a proven band."

- **Family Freemium.** Free: 1 circle, 100 Companion asks + 60 voice-min/month, 90-day memory book (typed entries always unlimited) — *enforced today in `entitlements.py`, not a pricing-page fiction*. **Aangan Plus ₹349/circle/month:** uncapped asks/voice, full memory book, priority support. One payer per circle — how families already buy plans.
- **The pricing story (evidence-backed):** ₹349 sits exactly inside India's proven family-bundle band — **YouTube Premium Family ₹299** and **Apple One Family ₹365** bracket it (verified live, July 2026); Netflix Standard is ₹499. Per member ≈ ₹58/mo. For an NRI payer ≈ **$4/month against a $129B remittance flow**. Ladder to test in D1: ₹199 / ₹349 / ₹499.
- **Unit economics (metered):** cost ≈ ₹29/free family/month, ₹44/Plus family; ₹349 nets ₹289 after 18% GST + gateway → **contribution ≈ ₹245/circle/month**.
- **Conversion realism:** RevenueCat 2026 (115k apps): median download→paid 2.0% global, **1.4% India/SEA**; India/SEA Y1 LTV $14/payer — a ₹349 family plan beats the regional median in ~3.4 retained months. Our scenarios (0.5/1.5/3.0%/mo) straddle these benchmarks.
- **Rejected models & why (rubric asks):** advertising (poisons trust), selling data/insights (contradicts values — and see Life360), commerce commissions on Doer purchases (conflict with "suggest, never sell").
- **Willingness-to-pay instrument already live:** the "Aangan Plus — notify me" fake-door logs interest events.

**Visual:** free-vs-Plus table + price-anchor band graphic (₹299 YT — **₹349 Aangan** — ₹365 Apple One — ₹499 Netflix).

---

## Slide 11 — Marketing strategy

**Goal:** channels ranked by evidence strength, with the viral loop built into the product.

1. **The family invite loop (product-led, strongest evidence):** the paying unit *is* a circle that must invite 3–6 members. Spotify's SEC F-1: family plans drove **31–32% of gross new Premium subscribers** (2017–18). Invite codes + `?ref=` attribution are already in the product → real K-factor measurable from day 1.
2. **UPI Autopay-first checkout:** Autopay volumes ~doubled YoY (926M txns Nov 2025, NPCI-derived); overtook cards since Sep 2024; ₹349 clears the ₹15,000 AFA-free mandate limit frictionlessly.
3. **Micro-influencers in family/parenting/NRI niches:** ₹1k–10k/post (India, 2026 rate cards); budgets shifting to micro (+28% YoY) — cheap enough to measure true CAC in the pilot.
4. **"Gift a family circle" Diwali campaign (NRI → India):** festive e-commerce GMV ₹1.15 lakh crore, +20–25% (Redseer 2025); ~2/3 of annual gifting concentrated around Diwali; Raksha Bandhan as second moment.
5. **NRI communities (experimental):** r/nri ~42k members (+67%/yr), r/ABCDesis ~122k, diaspora YouTube — position as test channel, not forecast driver.

**Positioning line:** *"The anti-surveillance, anti-noise family app — the private courtyard."*

**Measurement (rubric: AARRR):** every stage instrumented in code today — `product_events` (registered → first_entry → share → ask → alert_seen → action_approved), activation = first entry ≤7 days, `scripts/metrics.py` prints the funnel.

**Honesty note:** official Meta/Google India CPI figures don't exist publicly (NOT FOUND) — CAC will come from the pilot, not from blog estimates.

**Visual:** channel table with an "evidence grade" column (A/B/C) — the grading itself demonstrates rigor.

---

## Slide 12 — Technology and AI model

**Goal:** privacy as *architecture*, plus "why now" tailwinds.

- **Stack:** React+Vite → FastAPI → SQLite + ChromaDB; local multilingual embeddings (₹0 marginal); Deepgram Nova-3 STT (Hindi + code-switching) + Aura-2 TTS; LLM chain **OpenAI/OpenRouter → Anthropic → deterministic fallback** (the whole app runs keyless — a zero-marginal-cost free mode exists); Playwright Doer with `guard_fill`/`guard_click`.
- **The privacy spine (the slide's centerpiece):** every retrieval passes the Librarian — Chroma metadata is only a prefilter; **every hit is re-checked against the live SQL row**. 140 automated tests, including an adversarial test that *corrupts the vector store's metadata and proves nothing leaks*. "We don't ask the AI to respect privacy — the code makes it impossible not to."
- **Security floor:** JWT in memory only, optional TOTP MFA, per-IP + per-account rate limits, append-only audit trail, full export + erasure, production refuses default secrets. Docker deploy + CI + backup/IR runbook.

**Why now (pick 3 of 5):**
1. **LLMflation:** GPT-3.5-class inference fell **280×** in 2 years ($20 → $0.07/1M tokens, Stanford HAI AI Index 2025); ~10×/year (a16z) → COGS falls every year we operate.
2. **A Hindi voice note now costs <1¢ to understand** (Nova-3 multilingual streaming $0.0058/min, Hindi + auto language detection, 2026).
3. **Trust is the moat:** 71% of Americans say AI makes personal data *less* secure (Pew, Feb 2026); only 46% of 48k people across 47 countries trust AI (KPMG/Melbourne 2025); Apple markets exactly this ("aware of your personal information without collecting it") — Aangan makes the promise enforceable in code for families.
4. **RAG is de-risked:** enterprise adoption 31%→51% in a year (Menlo Ventures) — proven pattern, unserved domain.
5. **Voice AI is inflecting:** funding $315M → $2.1B (2022→2024); ElevenLabs $3.3B → $11B valuation in 12 months.

**Honest footnote:** Deepgram Aura-2 has **no Hindi TTS voice yet** — Hindi spoken replies use the browser voice fallback (roadmap: alternative Hindi TTS).

**Visual:** architecture diagram with the Librarian highlighted as a gate; small "why now" stat strip.

---

## Slide 13 — Financial projections

**Goal:** "metered, not invented" — the credibility slide.

- **Unit economics from real metered usage** (`llm_calls`, `asks`, `duration_sec` tables): **₹29.2/month per active free family; ₹43.8 per Plus family.** STT ≈ 85% of variable cost → the cost lever is voice minutes, not tokens (and caps exist).
- **Contribution:** ₹349 → ₹289 net of 18% GST + gateway → **≈ ₹245/circle/month** → **~13 paying circles cover pilot-scale fixed costs** (26 @ ₹199, 9 @ ₹499).
- **Three scenarios** (conversion 0.5/1.5/3.0%/mo of free base; paid churn 8/5/3% — benchmark ranges, consistent with RevenueCat medians): optimistic reaches monthly break-even **M16**, cash-positive **M23**; pessimistic never within 36 months.
- **Funding ask = max cumulative cash trough + 25% contingency:** **₹744k pess / ₹238k base / ₹52k opt** (product engine only — team salaries and marketing spend excluded; say so on the slide and layer Section-13 headcount when finalizing).
- **2026 price re-verification (fresh):** assumptions *hold or improve* — current nano-tier LLM ($0.20/$1.25 per 1M) is ~31% cheaper per call than modeled; Nova-3 multilingual streaming ($0.0058/min) matches the modeled rate with Hindi included; hosting $12/mo remains a fair midpoint. Stress case available: `financial_model.py --tok-in 0.75 --tok-out 4.50`.
- **Assumption register on backup slide** — all 15 assumptions with provenance labels (`observed (…)` vs `default (…)`), auto-relabeled by the script after the pilot.

**Visual:** unit-economics waterfall (₹349 → GST → gateway → COGS → ₹245) + 3-scenario cash curve with the trough marked.

---

## Slide 14 — Risks and ethical issues

**Goal:** the risk slide that *increases* confidence — each risk has a shipped mitigation.

**Risk register:**
| Risk | L / I | Mitigation (shipped, not promised) |
|---|---|---|
| Privacy breach / trust collapse | M / Severe | Code-enforced visibility on every retrieval; no ad-tech, no data sale; audit trail; IR runbook aligned to DPDP's 72-hour breach report |
| Regulatory — DPDP full compliance due **14 May 2027** | Certain / High | Consent records at registration; export + erasure live; 18+ policy today; DigiLocker verifiable parental consent on roadmap for minors |
| AI cost overrun | M / M | Metered per-call costs; caps in `entitlements.py`; keyless fallback = ₹0 floor |
| Provider dependence | M / M | OpenAI→OpenRouter→Anthropic→local chain; local embeddings; swappable base URL |
| Hallucination / harmful output | M / H | Grounded-only answers with visible sources; code-level never-medical filter (rejected wording is audited); 🚩 report loop with weekly human review |
| WhatsApp inertia / slow adoption | H / M | Free tier; position on what WhatsApp cannot do; pilot metrics gate scaling |

**Regulatory context (fresh, verified):** DPDP Rules notified 13 Nov 2025; penalties up to **₹250 crore**; children's data = verifiable parental consent (under-18). EU AI Act Art. 50 (AI must disclose itself) applies from Aug 2026 — a companion app is **limited-risk**, not high-risk. California SB 243 companion-chatbot law live Jan 2026.

**Three ahead-of-the-curve claims:**
1. Aangan implements DPDP's hardest requirements (consent-first, erasure, security) ~10 months before the May 2027 deadline.
2. It already meets the EU AI Act Art. 50 / SB 243 norms that became enforceable in 2026 (disclosed AI, human approval, non-medical wording).
3. "Never diagnose" is a **regulatory moat** — it keeps Aangan outside CDSCO medical-device scope (India) and inside FDA's general-wellness exemption (US).

**Cautionary tales (why trust-by-architecture):** Life360 (location data of tens of millions sold to brokers, The Markup 2021), BetterHelp (FTC $7.8M, 2023), Flo Health (FTC 2021) — intimate-data apps monetizing via ad-tech is the failure mode Aangan's architecture rejects.

**Ethics mapping (one line):** design maps to NITI Aayog Responsible AI principles / MeitY's 7 AI Sutras (Nov 2025): consent → accountability, approval gate → safety, agents panel → transparency.

**Visual:** risk-register table + a small "compliance timeline" bar (Nov 2025 → Nov 2026 → May 2027) with Aangan's shipped features plotted before the deadlines.

---

## Slide 15 — Growth plan

**Goal:** staged, capital-light, each stage gated by evidence.

- **Now → pilot (weeks):** 3–5 real families, 4–6 weeks, instrumented end-to-end (activation, retention, shares, alert→action rate, fake-door conversion, real unit costs).
- **Year 1 — validate one corridor:** India ↔ NRI (US/UAE first — 10.4M of the diaspora), web app, Diwali gifting moment, referral loop measured via `?ref=`.
- **Year 2 — deepen:** native mobile (voice-first argues for it), more Indic languages (extraction/prompts already bilingual; embeddings already multilingual), Hindi TTS, elder-care partnerships (Samarth-type services do logistics; Aangan adds the emotional layer), payment gateway + real Plus billing.
- **Scale path (technical, already prepared):** SQLite→Postgres, Chroma→pgvector/hosted, multi-circle membership **already shipped**, Docker deploy one command away.
- **Growth math honesty:** growth curve is an assumption (+25%/mo Y1 tapering), not a forecast — the pilot's measured K-factor and retention replace it.

**Visual:** three-stage roadmap with a "gate" icon between stages (pilot evidence → corridor evidence → scale).

---

## Slide 16 — Final recommendation

**Goal:** end on discipline, not hype — the rubric's Section 20 explicitly rewards this.

> **Recommendation: launch a limited pilot — 3–5 families, 4–6 weeks — then decide with evidence.**

- The prototype is real: 140 passing tests, adversarial privacy proofs, live unit-economics metering, deployable in one `docker compose up`.
- The pilot produces exactly the numbers the plan currently states as assumptions: activation, retention, willingness-to-pay (fake-door + D1 interviews), true CAC, real cost per family.
- Funding ask derived from the modeled cash trough, not ambition: **≈ ₹238k base case** (+ pilot costs; ex-salaries).
- Decision gates after the pilot: proceed to corridor launch / iterate / stop — pre-committed criteria, e.g. activation ≥ X%, W4 retention ≥ Y%, fake-door interest ≥ Z%.
- Close by returning to the name: *"Every family deserves a courtyard — where nothing is shared without consent, and nothing that matters is lost."*

---

## Appendix / backup slides (have ready, don't present)

1. **Assumption register** — all 15 financial assumptions with sources and override flags.
2. **Privacy spine test evidence** — the corrupted-metadata leak test, in code.
3. **Full competitor fact sheets** (pricing pages, dates, URLs).
4. **DPDP compliance detail** — phased timeline vs shipped features.
5. **NOT FOUND register** — statistics we searched for and refused to invent: NRI call-frequency survey; % of elders hiding health problems; India sandwich-generation prevalence; India dual-income %; official Meta/Google India CPI; family-plan invite→paid conversion; cross-border gifting market size. *(Showing this list is itself a rubric win.)*
6. **Geography labels** — AARP caregiver stats (63M caregivers, 2025) and Pew sandwich stats are US-geography; Policybazaar 50%/70% NRI figures are unpublished industry research — always attributed as such.
7. **Demo video** (30–60s screen capture) as insurance against live-demo failure.

## Follow-ups surfaced by this research (repo hygiene, before the deck is final)

- `docs/FINANCIAL_MODEL.md` rows 1–2 cite delisted models (gpt-5-mini, Nova-2) → repin to gpt-5.4-nano ($0.20/$1.25) and Nova-3 streaming ($0.0058/min); note June 2026 Hetzner repricing.
- Gateway fee: model assumes 2%; Razorpay recurring is effectively ~3% (2% + 0.99% add-on + GST on fee) → adjust or footnote.
- Aura-2 has no Hindi voice → risk-slide footnote + roadmap line.
- Don't cite Spotify Family as a current India anchor (discontinued after Nov 2025 restructure) — use YouTube ₹299 / Apple One ₹365.
- DPDP children's-data: family circles + minors → add verifiable-parental-consent to roadmap (18+ policy holds for pilot).
- Team slide needs real names/roles/contributions filled in.
