# D2 — Prototype Usability Testing Kit

> Evidence package for **business-plan Section 10 (Prototype & user testing)**.
> Rubric requirements this kit satisfies (see `docs/BUSINESS_PLAN_ALIGNMENT.md`,
> Part D2): **minimum three users**, at least one **Hindi-preferring elder**, a
> fixed task script, measured completion/time/errors/confusion, quotes with
> consent, and a documented **issue → change → retest** loop. It also closes
> the open B2-#15 question: is the "session lost on refresh" privacy trade
> acceptable to real users?
>
> Everything below matches the real UI (button labels verified against
> `frontend/src/screens/*` and `frontend/src/i18n.js` as of 2026-07-23).
> Run it as written — no adaptation needed.

---

## 1. Participant plan

### 1.1 Who we need (3 minimum, 5 ideal)

| # | Persona | Profile to recruit | Session language | Maps to plan section |
|---|---------|--------------------|------------------|----------------------|
| P1 | **Connector adult** (required) | 28–45, salaried, lives apart from parents (India-resident or NRI), organizes family gifts/calls today, comfortable with apps | English UI, English/Hinglish talk | §4 primary persona ("Aditya") |
| P2 | **Hindi-first elder** (required) | 55–75, prefers speaking Hindi over typing English, uses WhatsApp voice notes, smartphone daily but wary of new apps | **Hindi UI** (select हिन्दी at registration), Hindi facilitation | §4 secondary persona ("Mumma") |
| P3 | **Sibling / spouse** (required) | 25–40, family member who is *not* the organizer; joins things when invited, skeptical of "another family app" | English UI | §4 secondary users ("Deepa"/"Abhishek") |
| P4 | Second connector (optional) | Same as P1 but opposite residency (if P1 is India-based, recruit NRI, or vice versa) | English | §4 early adopters (NRI corridor) |
| P5 | Second elder (optional) | Same as P2, different comfort level with tech | Hindi | §4, strengthens the n=1 elder signal |

### 1.2 Recruiting notes

- **Do not recruit teammates or people who have seen Aangan.** Extended family,
  neighbours, colleagues' parents are fine. First-time eyes are the point.
- Screener (ask by phone/WhatsApp, 2 minutes):
  1. "Do you have close family you don't live with?" (must be yes)
  2. "When did you last find out late about something small but important in a
     family member's life?" (note the story — reusable for D1)
  3. For the elder slot: "आप फ़ोन पर लिखना पसंद करते हैं या बोलना?" (must prefer
     बोलना / speaking)
  4. "Would you be okay with us recording the screen and your voice for an
     hour, for a student business project?" (must be yes)
- Schedule 75 minutes per person (60 usable + buffer). Leave ≥45 minutes
  between sessions for reseed + notes.
- Thank-you: a small sweet box / ₹300–500 voucher is appropriate; state it up
  front so it isn't coercive.
- Elders: offer to run the session at their home on the facilitator's laptop;
  a familiar setting materially changes elder behaviour.

---

## 2. Session logistics

### 2.1 Format

- **Length:** 45–60 minutes (elder sessions: plan the full 60).
- **Setup:** facilitator's laptop, Chrome, external mouse for elders. One
  facilitator runs the script; one notetaker fills the measurement sheet
  (Section 5). If solo, record everything and fill the sheet from the video.
- **Think-aloud protocol:** ask the participant to say what they're looking at
  and expecting, out loud, the whole time. Hindi version for P2:
  "जो भी सोच रहे हैं, बोलते रहिए — सही-गलत कुछ नहीं है।"

### 2.2 Facilitator machine setup (exact commands)

Run from the repo root (`/Users/viditkbhatnagar/codes/Aangan` on the current
dev machine — adjust the path on another laptop).

```bash
# Terminal 1 — backend (Python 3.11/3.12 venv already at backend/.venv)
cd backend
.venv/bin/python seed.py        # wipes aangan.db + chroma_data, rebuilds demo family
.venv/bin/uvicorn app:app --reload --port 8000 \
  --reload-exclude 'chroma_data/*' --reload-exclude 'data/*'

# Terminal 2 — frontend
cd frontend
npm run dev                      # http://localhost:5173 (proxies /api → :8000)
```

Seeded accounts (password `aangan123` for all):
`aditya@ghar.family`, `deepa@ghar.family`, `mumma@ghar.family`,
`abhishek@ghar.family`. Seeded circle: **Ghar**, invite code **`GHAR-2026`**
(visible on Home as `Invite: GHAR-2026 ⧉` when logged in as a member).

**API keys matter for this test.** Check `backend/.env`:

- `DEEPGRAM_API_KEY` set → voice entries transcribe live. **Strongly
  recommended** — Task 3 is the heart of the product.
- No Deepgram key → voice upload returns a friendly 503 and the UI drops the
  participant into typing mode. If you must run keyless, keep Task 3 but
  treat the graceful failure itself as the observation, and note
  "keyless mode" on every measurement sheet.
- `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` optional — deterministic fallback
  answers are grounded and testable either way, just less warm. Note which
  mode you ran in; do not mix modes across participants if avoidable.

### 2.3 Reseed between participants (mandatory)

`seed.py` wipes the database — this is both hygiene and a privacy promise we
make in the consent form ("your entries are erased after your session").

```bash
# 1. Stop the backend (Ctrl+C in Terminal 1)
# 2. Reseed
cd backend && .venv/bin/python seed.py
# 3. Restart
.venv/bin/uvicorn app:app --reload --port 8000 \
  --reload-exclude 'chroma_data/*' --reload-exclude 'data/*'
```

Also clear the browser between participants: close all Aangan tabs (the JWT
is memory-only, so closing the tab logs out) and clear the mic permission if
you want to observe the permission prompt fresh (Chrome → site settings).

### 2.4 Pre-session checklist (10 minutes before each participant)

- [ ] Reseed done; backend and frontend both up; open http://localhost:5173
- [ ] Log in as `aditya@ghar.family` once: confirm Home shows
      "Your circle — Ghar" and `Invite: GHAR-2026 ⧉`; confirm the **Alerts**
      tab shows the seeded Mumma-knee alert (this is the Task 6 fallback);
      log out
- [ ] Record a 5-second test voice entry yourself — confirm transcription (or
      confirm the keyless 503 message if running keyless)
- [ ] Open the **⚙️ Agents** button (top right) — confirm the "Agents at
      work" panel slides in and fills with events after your test entry
- [ ] Screen recorder running (QuickTime or OBS): **full screen + microphone
      + system audio**. The screen capture must include the right side of the
      window so the Agents panel is on camera
- [ ] Consent form printed (or a signable PDF open), pen ready
- [ ] Second browser profile / incognito window ready for the Task 6 staging
      (Section 4, Task 6, Plan A)
- [ ] **Do not press refresh during the session** — the session token is
      memory-only and refresh logs the participant out. There is a deliberate
      refresh probe at the end (Task 7); don't trigger it early.

### 2.5 What to screen-record and why

| Capture | Why it matters for the plan |
|---|---|
| Full screen incl. bottom nav and **Agents panel** | Section 10 needs "user journey friction points"; the Agents panel makes normally-invisible AI work observable, so trust reactions are on tape |
| Participant audio (think-aloud) | Quote evidence (with consent) for §2 problem, §7 value proposition wording |
| Facilitator prompts | Proves prompts were neutral (rubric rejects led evidence) |
| Timestamps | Time-on-task comes from the recording, not a stopwatch |

During Tasks 3 and 5, **ask the participant to open the ⚙️ Agents panel**
("top right — the Agents button") while the app is thinking, and capture
their reaction to seeing Transcriber → Summarizer → Extractor → Librarian →
Companion work in real time. Two debrief questions hang on this.

---

## 3. Consent form (print/sign one per participant)

> **Aangan prototype test — consent**
>
> Thank you for helping us test Aangan, a private family voice-journal app,
> as part of a student business project.
>
> 1. **What happens:** For about an hour you will try the app while we watch.
>    We will record the laptop screen and your voice.
> 2. **Your words:** With your permission we may quote things you say,
>    **anonymously** (e.g. "Participant 2, age 63"), in our project report.
>    Your name will never appear.
> 3. **Your entries:** Anything you record or type in the app during the test
>    is stored only on this laptop and is **erased after your session** when
>    we reset the test database. If you set API keys aside: audio is
>    transcribed by Deepgram and text may be processed by an AI provider
>    during the session, as disclosed in the app itself.
> 4. **Voluntary:** You can stop at any time, without giving a reason, and
>    you can ask us to delete the recording afterwards — no questions asked.
>    Contact: ______________________ (facilitator name + phone/email).
> 5. **Not a test of you:** We are testing the app. Nothing you do is wrong.
>
> ☐ I agree to the screen and voice recording.
> ☐ I agree to anonymous quotes in the project report.
>
> Name: ______________  Signature: ______________  Date: ____________

Hindi version for P2/P5 (read aloud as well — do not rely on reading):

> **आँगन प्रोटोटाइप टेस्ट — सहमति**
>
> 1. करीब एक घंटे आप ऐप आज़माएँगे; हम स्क्रीन और आपकी आवाज़ रिकॉर्ड करेंगे।
> 2. आपकी कही बातें रिपोर्ट में **बिना नाम के** इस्तेमाल हो सकती हैं।
> 3. टेस्ट में आपने जो भी रिकॉर्ड किया, वह सेशन के बाद **मिटा दिया जाएगा**।
> 4. आप कभी भी रुक सकते हैं और रिकॉर्डिंग हटवाने के लिए कह सकते हैं।
> 5. यह ऐप की परीक्षा है, आपकी नहीं — कुछ भी "गलत" नहीं होता।
>
> ☐ रिकॉर्डिंग की सहमति  ☐ बिना नाम के उद्धरण की सहमति
> नाम: ______  हस्ताक्षर: ______  तारीख: ______

---

## 4. Fixed task script

Read the same intro to everyone (Hindi in brackets for P2):

> "This is Aangan, an app where each family member keeps a private voice
> diary, and one AI Companion shares only what each person chooses. I'll give
> you small tasks. Please think out loud. I can't answer questions during a
> task, but I'll help if you're truly stuck."
> (हिंदी: "यह आँगन है — हर सदस्य की अपनी निजी बोलने वाली डायरी, और एक साथी जो
> सिर्फ़ वही बताता है जो आपने साझा किया हो। मैं छोटे-छोटे काम दूँगा/दूँगी।
> सोचते हुए बोलते रहिए।")

**Facilitator ground rules (all tasks):** never point at the screen, never
name a button before the participant finds it. Escalate neutrally: prompt 1 →
prompt 2 → if still stuck after ~2 minutes past budget, assist and mark the
task **Assisted** (counts as failure for the completion metric, but continue
so later tasks aren't blocked). Log every wrong tap and every "confusion
point" (visible hesitation >10s, or a wrong guess said aloud).

Scenario card handed to the participant (EN / HI on one card):

> "Imagine your family — including [family member's real name they mentioned
> in the screener] — uses this app. During the test, talk about your real
> day, and somewhere mention **one thing you'd genuinely like as a gift**."
> (हिंदी: "अपने असली दिन के बारे में बोलिए, और कहीं यह भी बताइए कि **आपको
> तोहफ़े में क्या पसंद आएगा**।")

(The gift mention is deliberate: the Extractor reliably produces a
preference fact from it, which makes Task 4's "share exactly one fact" real
rather than staged.)

---

### Task 1 — Create an account (target: 4 min)

> "Set up your own account in this app. Use this email: `test1@family.test`
> and any password you'll remember."
> (हिंदी: "इस ऐप में अपना खाता बनाइए। ईमेल यह लीजिए: `test1@family.test`।")

- **UI path:** Welcome screen → **"New here? Create your account"** → name,
  email, password → **Language** dropdown (P2/P5 must be observed choosing
  **हिन्दी (Hindi)** — if they don't notice it, that's a finding; after one
  neutral prompt you may say "there is a language choice on this page") →
  tick the 18+/privacy checkbox.
- **Success criteria:** registration form fully filled including language and
  the consent checkbox, without facilitator naming any field.
- **Watch for:** Do they read the consent line ("Voice is transcribed by
  Deepgram…")? Do they click the privacy policy link? Does the elder find
  the language dropdown unaided?
- **Neutral prompts:** "What would you do first?" / "What do you expect that
  checkbox does?" (हिंदी: "सबसे पहले क्या करेंगे?" / "आपको क्या लगता है यह
  किसलिए है?")

### Task 2 — Join the family circle with an invite code (target: 3 min)

> "Your family already has a circle in this app. Their invite code is
> **GHAR-2026**. Join them."
> (हिंदी: "आपके परिवार का ग्रुप पहले से है। उनका कोड है **GHAR-2026**। उनसे
> जुड़िए।")

- **UI path:** same registration form, **Family circle** section →
  **"Join with code"** (vs "Start a new one") → type `GHAR-2026` → press
  **"Join the courtyard"**.
- **Success criteria:** lands on Home; Home shows **"Your circle — Ghar"**
  with Aditya, Deepa, Mumma, Abhishek listed.
- **Watch for:** confusion between "Join with code" and "Start a new one";
  whether they verify on Home that they're actually in ("who are these
  people?" reactions are gold — note them).
- **Neutral prompts:** "Where would a code like that go?" (हिंदी: "यह कोड
  कहाँ डालेंगे?")

### Task 3 — Record a voice entry, then a typed one (target: 10 min)

> Part A: "Tell the app about your day — out loud, like a voice message.
> Remember the card: mention that gift you'd like."
> Part B (after A completes): "Now add one more small note, but this time
> without speaking."
> (हिंदी A: "अब ऐप को अपने दिन के बारे में बोलकर बताइए — जैसे वॉइस मैसेज।
> कार्ड वाली बात — तोहफ़ा — ज़रूर बताइए।"
> हिंदी B: "अब एक और छोटी बात जोड़िए, पर इस बार बिना बोले।")

- **UI path A:** bottom nav **Journal** (📓 / डायरी) — or the big
  **"Talk to me" / "मुझसे बोलिए"** button on Home → **press and hold**
  **"Hold to talk" / "दबाकर बोलिए"** (label changes to "Listening…" /
  "सुन रही हूँ…") → speak 20–60s → release. Browser mic permission prompt
  will appear on first use — observing how they handle it is part of the task.
  While "Listening back and making notes…" shows, ask them to open
  **⚙️ Agents** (top right) and say what they think is happening.
- **UI path B:** **"Prefer to type it?" / "लिखना चाहेंगे?"** → textarea
  ("How was your day?" / "आज का दिन कैसा रहा?") → **"Keep this" /
  "सहेज लीजिए"**.
- **Success criteria:** (A) an entry card appears with a summary and today's
  timestamp and a `private` pill; (B) a second entry appears via typing. The
  hold-to-record interaction is completed without the facilitator
  demonstrating it.
- **Watch for:** do they understand **hold** (vs tap-to-toggle — the #1
  expected friction, especially for WhatsApp-voice-note users who know
  hold-to-record but also know tap-to-lock)? Reaction to the mic permission
  dialog. Do they notice the `private` pill and the line "Everything here is
  private until you choose to share it"? Reaction to the Agents panel:
  reassuring or creepy? (quote it verbatim). If keyless: reaction to the
  friendly failure + fallback to typing.
- **Neutral prompts:** "How do you think you talk to it?" / "What do you
  think the app just did with what you said?" (हिंदी: "आपको क्या लगता है,
  इससे बात कैसे करते हैं?" / "आपकी बात का ऐप ने क्या किया होगा?")

### Task 4 — Share exactly ONE fact from the entry (target: 5 min)

> "The app noticed some things in what you said. Share **only the gift
> idea** with your family — and nothing else."
> (हिंदी: "ऐप ने आपकी बातों में कुछ नोट किया है। सिर्फ़ **तोहफ़े वाली बात**
> परिवार से साझा कीजिए — बाकी कुछ नहीं।")

- **UI paths (both count as success):**
  (a) the post-entry share suggestion card — quote + reason →
  **"Yes, share it"** (the other option is "Keep it private"); or
  (b) on the entry card → **"Details · N noted"** → find the fact card with
  the `preference` pill → **"Share with everyone"** (other options:
  "Make private", "Share with chosen…" with member checkboxes).
- **Success criteria:** exactly one fact's pill turns `circle`; the entry
  itself and all other facts stay `private`. Verify on screen before moving
  on.
- **Watch for:** THE core comprehension test of the product. Afterwards ask
  the check question (record the answer verbatim):
  **"Right now, what can your family see — and what can't they see?"**
  (हिंदी: "अभी आपका परिवार क्या देख सकता है — और क्या नहीं?")
  Wrong answers here are Severity-1 findings regardless of task completion.
- **Neutral prompts:** "Where might the app have kept what it noticed?"
  (हिंदी: "ऐप ने जो नोट किया, वह कहाँ मिलेगा?")

### Task 5 — Ask the Companion about another member (target: 7 min)

> "Deepa is in your circle and her birthday is coming. Ask the app what she
> might want."
> (हिंदी: "दीपा आपके परिवार में हैं, उनका जन्मदिन आने वाला है। ऐप से पूछिए
> कि उन्हें क्या पसंद आएगा।")

- **UI path:** bottom nav **Ask** (💬 / पूछें) — title "Ask the Companion" /
  "साथी से पूछिए" → type in the box (placeholder "e.g. How was Deepa's day?"
  / "जैसे: दीपा का दिन कैसा था?") → **"Ask" / "पूछें"** — or hold-to-talk to
  ask by voice (elders should be nudged to try voice if they typed:
  "बोलकर भी पूछ सकते हैं").
- **Success criteria:** a grounded answer appears (seeded data ensures Deepa
  has a shared gift preference); participant can point to where the answer
  came from — the **"From N shared moment(s)"** expandable sources.
- **Watch for:** do they open the sources? Do they trust the answer ("how
  does it know that?")? Reaction to the spoken reply (the answer is read
  aloud — is that delightful or startling, especially for the elder?); do
  they find 🔊 replay or "Stop speaking"? Do they notice the 🚩 report
  button? Ask: **"Could the Companion tell Deepa what YOU recorded today?"**
  (correct answer: only the one fact you shared) (हिंदी: "क्या यह साथी दीपा
  को बता सकता है कि आपने आज क्या रिकॉर्ड किया?")
- **Neutral prompts:** "Where would you ask a question here?" (हिंदी: "यहाँ
  सवाल कहाँ पूछेंगे?")

### Task 6 — Act on an alert (target: 7 min)

**Staging — Plan A (live, preferred).** While the participant does Task 5,
the facilitator, in the second browser window, logs in as
`mumma@ghar.family` / `aangan123` → **Me (मैं)** → **"🔔 My alert triggers"**
→ add trigger: text "अगर मैं तबियत की बात करूँ, तो बताना", tick the
**participant's name** in the audience checkboxes → **Add** → go to
**Journal (डायरी)** → "लिखना चाहेंगे?" → type "आज घुटने का दर्द फिर बढ़ गया है,
सीढ़ियाँ मुश्किल हो रही हैं" → "सहेज लीजिए". The Alerter fires an alert to the
participant within seconds (Alerts badge appears on the 🔔 tab).

**Staging — Plan B (fallback, zero-risk).** If Plan A misfires, say: "Let's
switch to Aditya's account — imagine you are him." Close the tab, log in as
`aditya@ghar.family` / `aangan123`: the seeded alert about Mumma's knee is
already waiting in Alerts.

> "Someone in your family wanted you to know something. Find it and do
> something about it."
> (हिंदी: "परिवार में किसी ने चाहा था कि आपको एक बात पता चले। उसे ढूँढिए और
> कुछ कीजिए।")

- **UI path:** bottom nav **Alerts** (🔔 / सूचना, with badge) → alert card
  shows severity pill, message, and a 💡 suggested action → buttons:
  **"Act on this" / "कुछ कीजिए"** (navigates to the Actions screen with the
  suggestion pre-filled), "Mark seen" / "देख लिया", "Dismiss" / "हटाइए", 🚩.
- **Success criteria:** participant opens Alerts unaided (badge → tab),
  reads the alert correctly (ask: "what happened, and why are YOU seeing
  this?"), and taps **"Act on this"**, landing on Actions. (Completing an
  action there is beyond scope — stop once they can say what they'd do
  next: "call Mumma" is a perfect answer.)
- **Watch for:** tone check — does the alert feel caring or clinical or
  alarming? (§14 requires never-medical wording; capture their word for it).
  Do they understand Mumma *chose* to have them told? That consent framing
  ("जिन्होंने आपको बताने के लिए कहा था" / "the people who asked you to be
  told") is a plan-level differentiator — probe it: **"Who decided that you
  should be told this?"** (हिंदी: "यह किसने तय किया कि आपको बताया जाए?")
- **Neutral prompts:** "Anything on this screen calling for attention?"
  (हिंदी: "स्क्रीन पर कुछ ध्यान खींच रहा है?")

### Task 7 — Refresh probe + debrief (target: 8 min)

Last, deliberately: "Please refresh the page." The app logs out (memory-only
token — the deliberate privacy trade from B2-#15). Ask: "What just happened?
How do you feel about logging in again each time, if the trade is that your
diary can't be left open by accident?" (हिंदी: "हर बार दोबारा लॉगिन करना
पड़े, लेकिन डायरी कभी खुली न रह जाए — यह सौदा ठीक लगता है?") Record verdict:
**acceptable / annoying / dealbreaker**.

Debrief questions (verbatim answers onto the sheet):

1. "In one sentence, what would you tell your family this app is?"
2. "What would stop you from using it weekly?"
3. Agents panel: "Did seeing the agents work make you trust it more, less,
   or no change? Why?"
4. Show **Me → ✨ Aangan Plus → "Aangan Plus — notify me"**: "This will be a
   paid family plan — unlimited voice and questions, full memory book. Would
   your family pay for something like this? Roughly what per month feels
   fair for the whole family?" (record the number; do not anchor). Invite
   them to press the button if genuinely interested — every press is a
   logged willingness-to-pay signal for §8/§15.
5. Elder only: "क्या आप इसमें हफ़्ते में कुछ बार बोलेंगे? क्यों / क्यों नहीं?"

---

## 5. Measurement sheet (one per participant)

Header: `Participant ID: P_   Persona: _______   Date: ____   UI language:
EN/HI   Mode: keys / keyless   Facilitator: ____   Recording file: ____`

| Task | Completed (Y / Assisted / N) | Time (m:ss) | Errors (wrong taps / dead ends) | Confusion points (what + where) | SEQ 1–7 | Verbatim quote |
|---|---|---|---|---|---|---|
| 1 Register | | | | | | |
| 2 Join circle (GHAR-2026) | | | | | | |
| 3a Voice entry | | | | | | |
| 3b Typed entry | | | | | | |
| 4 Share ONE fact | | | | | | |
| 5 Ask Companion | | | | | | |
| 6 Act on alert | | | | | | |

**SEQ (Single Ease Question)** — ask immediately after each task:
"Overall, how difficult or easy was that? 1 = very difficult, 7 = very easy."
(हिंदी: "यह काम कितना मुश्किल या आसान लगा? 1 = बहुत मुश्किल, 7 = बहुत आसान।")

**Definitions (apply consistently):**
- *Completed*: success criteria met with zero facilitator assists beyond the
  two scripted neutral prompts. *Assisted* = facilitator had to reveal a
  location/label. Assisted counts as **not completed** in the report.
- *Error*: any tap that moves away from the success path, or a stated wrong
  expectation acted upon.
- *Confusion point*: silence/hesitation >10 seconds while visibly searching,
  or a wrong guess spoken aloud. Log as `screen → element → what they said`.
- *Time*: from end of task instruction to success criteria visible on
  screen (read off the recording).

**Comprehension checks (Y/N + verbatim):**
- [ ] After T4: correctly stated what family can/can't see
- [ ] After T5: correctly stated Companion can't reveal their private entries
- [ ] After T6: correctly stated the alert subject chose the audience
- [ ] T7 refresh trade verdict: acceptable / annoying / dealbreaker
- [ ] Plus price point volunteered: ₹______/month · pressed notify-me: Y/N

**Per-session cross-task observations:** mic permission reaction · hold vs
tap on the talk button · Agents panel reaction (trust up/down/neutral) ·
spoken-answer reaction · any Hindi string that confused the elder (log the
exact string from `i18n.js`).

---

## 6. Findings loop — issue → change → retest

This is the rubric's required before/after loop. Keep one shared table in
`docs/research/D2_findings.md` (create on first finding); every row must end
with a retest result or an explicit "accepted, not fixing — reason".

### 6.1 Severity scale

| Sev | Meaning | Rule |
|---|---|---|
| S0 | Blocker — task cannot be completed, or a privacy comprehension failure (participant believed private content was shared or vice versa) | Fix before the **next participant** if <1 hour of work; otherwise script a workaround and disclose in the report |
| S1 | Major — task completed only with assist, or SEQ ≤ 3, or ≥2 participants hit it | Fix before pilot (feeds §19 roadmap) |
| S2 | Minor — completed with friction/detour | Batch; fix opportunistically |
| S3 | Cosmetic / preference | Log only |

### 6.2 Findings log format

| # | Session/Task | Issue (what happened, quote) | Sev | Root cause (screen/element/copy) | Change made (commit) | Retested with | Retest result |
|---|---|---|---|---|---|---|---|
| F1 | P1/T3 | *(example)* Tapped "Hold to talk" once and waited; "I pressed it, why is nothing happening?" | S1 | Hold affordance not obvious to tap-first users (`HoldToTalk.jsx` label) | e.g. animate + "press **and hold**" microcopy `abc1234` | P3, P4 | P3 succeeded unaided, 0:40 |

Rules: one row per **distinct** issue (repeat hits increment a tally column,
not a new row). Fixes between sessions must be small and committed
individually so the report can cite commit hashes as before/after evidence.
If a fix can't be retested with a later participant, retest with one fresh
person (even 10 minutes, task-only) or mark "unretested" honestly.

### 6.3 Where the results feed the business plan

| Output of this kit | Business-plan destination |
|---|---|
| Completion %, times, SEQ per task, findings log with before/after | **Section 10** — prototype user testing & friction points (the core deliverable) |
| Comprehension-check results (private-by-default understood or not) | **Section 7** value proposition wording; **Section 14** informed-consent claims |
| Elder session results (Hindi UI, voice-first behaviour) | **Section 4** persona validation; **Section 6** "Hindi voice-first" differentiator — only claimable if the elder actually succeeded |
| Agents-panel trust reactions | **Section 3** human-oversight story; **Section 17** hallucination/trust risk mitigation evidence |
| Alert tone reactions ("caring vs clinical") | **Section 14** never-medical posture; **Section 17** risk 5 |
| Plus fake-door presses + volunteered price points | **Section 8** pricing hypothesis; **Section 15** willingness-to-pay input (alongside D1) |
| Refresh-trade verdicts (T7) | Closes **B2-#15**: keep memory-only JWT (if ≥majority "acceptable") or move "keep me signed in" up the roadmap (§19) |
| Screener stories (screener Q2) | **Section 2** problem evidence (merge into D1 corpus) |
| Reseed/setup friction you experienced as facilitator | **Section 12** operations plan (support & onboarding reality check) |

### 6.4 Reporting thresholds (write these numbers into Section 10)

- Report per task: completion n/N, median time, mean SEQ, top confusion point.
- A task "passes" for the plan if ≥2 of 3 (or ≥4 of 5) completed unaided
  **and** mean SEQ ≥ 5. Anything below that is reported as an open friction
  point with its planned fix — the rubric rewards honesty over polish.
- Never average across personas silently: report the elder's numbers
  separately. One elder is n=1 — present it as a case study, not a statistic.
