import { useEffect, useRef, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../auth';
import { PostageStamp } from '../icons';

const HERO = "A quiet courtyard for your family's voices.";

// The landing reads like a letter home: a dateline types itself, the
// headline is written out stroke by stroke, and the page settles in.
function useLetterReveal() {
  const [dateline, setDateline] = useState('');
  const [typed, setTyped] = useState('');
  const [heroDone, setHeroDone] = useState(false);
  const [revealed, setRevealed] = useState({});
  const cancelled = useRef(false);

  useEffect(() => {
    cancelled.current = false;
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const now = new Date();
    const dl = `GHAR — ${now.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}`;
    const show = (k) => setRevealed((r) => ({ ...r, [k]: true }));

    if (reduce) {
      setDateline(dl);
      setTyped(HERO);
      setHeroDone(true);
      ['stamp', 'salut', 'sub', 'cta', 'sign'].forEach(show);
      return undefined;
    }

    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    (async () => {
      show('stamp');
      await sleep(250);
      for (let i = 0; i < dl.length; i += 1) {
        if (cancelled.current) return;
        setDateline(dl.slice(0, i + 1));
        await sleep(24);
      }
      await sleep(200);
      show('salut');
      await sleep(480);
      for (let j = 0; j < HERO.length; j += 1) {
        if (cancelled.current) return;
        setTyped(HERO.slice(0, j + 1));
        const c = HERO.charAt(j);
        await sleep(c === ' ' ? 32 : c === '.' ? 110 : 40);
      }
      setHeroDone(true);
      await sleep(160);
      show('sub');
      await sleep(400);
      show('cta');
      await sleep(280);
      show('sign');
    })();
    return () => { cancelled.current = true; };
  }, []);

  return { dateline, typed, heroDone, revealed };
}

export default function Welcome() {
  const { login, verifyMfa, register, refreshMembers } = useAuth();
  const [mode, setMode] = useState('login'); // login | register | mfa
  const [form, setForm] = useState({ name: '', email: '', password: '', language: 'en', accept_terms: false });
  const [circleChoice, setCircleChoice] = useState('join'); // after register: join | create
  const [circleValue, setCircleValue] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const loginRef = useRef(null);
  const rulesRef = useRef(null);
  const { dateline, typed, heroDone, revealed } = useLetterReveal();

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === 'mfa') {
        await verifyMfa(mfaCode.trim());
      } else if (mode === 'login') {
        const result = await login(form.email, form.password);
        if (result?.mfaRequired) {
          setMode('mfa');
          setMfaCode('');
        }
      } else {
        const source = new URLSearchParams(window.location.search).get('ref');
        await register({ ...form, source });
        if (circleChoice === 'create' && circleValue.trim()) {
          await api.post('/circles', { name: circleValue.trim() });
        } else if (circleChoice === 'join' && circleValue.trim()) {
          await api.post('/circles/join', { invite_code: circleValue.trim() });
        }
        await refreshMembers();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const scrollTo = (ref) => ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });

  return (
    <main className="landing">
      <div className="land-top">
        <div className="wordmark">Aangan <span className="dev" lang="hi">आँगन</span></div>
        <div className="meta">A letter home · est. 2026</div>
      </div>

      {/* the letter sheet — the hero */}
      <section className="sheet" aria-label="Welcome">
        <div className={`stampwrap reveal-block ${revealed.stamp ? 'in' : ''}`} aria-hidden="true">
          <PostageStamp />
          <span className="pm">
            <span className="top">GHAR</span>
            <b>{new Date().getDate()}</b>
            <i>{new Date().toLocaleDateString('en-IN', { month: 'short' }).toUpperCase()} '{String(new Date().getFullYear()).slice(2)}</i>
          </span>
        </div>

        <div className="sheet-in">
          <p className="dateline" aria-hidden="true">{dateline}</p>
          <p className={`salut reveal-block ${revealed.salut ? 'in' : ''}`}>Dear family,</p>
          <h1 className={`hero-h ${heroDone ? 'done' : ''}`}>
            <span className="sr-only" style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)' }}>{HERO}</span>
            <span aria-hidden="true">{typed}</span>
            <span className="cursor" aria-hidden="true">▍</span>
          </h1>
          <p className={`hero-sub reveal-block ${revealed.sub ? 'in' : ''}`}>
            Everyone's journal stays <b>private</b>. One warm Companion answers only what
            each of you has <b>chosen to share</b> — no more, no less.
          </p>
          <div className={`cta-row reveal-block ${revealed.cta ? 'in' : ''}`}>
            <button type="button" onClick={() => scrollTo(loginRef)}>Enter the courtyard</button>
            <button type="button" className="ghost" onClick={() => scrollTo(rulesRef)}>See how it works</button>
          </div>
          <p className={`sign reveal-block ${revealed.sign ? 'in' : ''}`}>— yours, always · <span className="nm" lang="hi">आँगन</span></p>
        </div>
      </section>

      {/* three sacred rules */}
      <section className="land-section" ref={rulesRef}>
        <div className="sec-kicker">
          <div className="meta">The three promises</div>
          <h2>Three things we will never bend</h2>
        </div>
        <div className="rules">
          <article className="rule">
            <div className="no">Rule one</div>
            <h3>Private by default</h3>
            <p>Every entry starts private to its author. Nothing is shared the moment you speak it.</p>
          </article>
          <article className="rule">
            <div className="no">Rule two</div>
            <h3>You control sharing</h3>
            <p>Nothing leaves you without your yes. You choose each moment that becomes a shared memory.</p>
          </article>
          <article className="rule">
            <div className="no">Rule three</div>
            <h3>A human finishes</h3>
            <p>It prepares an action up to the moment of payment — but never pays and never sends. That is always you.</p>
          </article>
        </div>
      </section>

      {/* how it feels */}
      <section className="land-section">
        <div className="sec-kicker"><div className="meta">How it feels</div><h2>Three unhurried steps</h2></div>
        <div className="feels">
          <div className="feel"><div className="n">01</div><h4>Speak</h4><p>Ten seconds or ten minutes. Just talk, like writing in a diary.</p></div>
          <div className="feel-arrow" aria-hidden="true">→</div>
          <div className="feel"><div className="n">02</div><h4>Share what you choose</h4><p>Keep it to yourself, or seal it into the family's memory.</p></div>
          <div className="feel-arrow" aria-hidden="true">→</div>
          <div className="feel"><div className="n">03</div><h4>Remembered, kindly</h4><p>The Companion holds it gently, and answers only from what was shared.</p></div>
        </div>
      </section>

      {/* login / register */}
      <section className="land-section" ref={loginRef}>
        <div className="login-wrap">
          <div className="login-copy">
            <h3>Come in.</h3>
            <p>
              {mode === 'register'
                ? 'Sign the register — your journal starts private from the very first word.'
                : 'Welcome back to your courtyard. Your letters are where you left them.'}
            </p>
            <p className="demo-note">Demo login · <b>aditya@ghar.family</b> · <b>aangan123</b></p>
          </div>

          {mode === 'mfa' ? (
            <form className="stack" onSubmit={submit} aria-label="Two-factor code">
              <div>
                <label htmlFor="mfa-code">Code from your authenticator app</label>
                <input
                  id="mfa-code"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  autoFocus
                  placeholder="123456"
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value)}
                  required
                />
              </div>
              {error && <p className="error-text" role="alert">{error}</p>}
              <button disabled={busy || mfaCode.trim().length < 6}>{busy ? 'One moment…' : 'Verify'}</button>
              <button type="button" className="quiet" onClick={() => { setMode('login'); setError(null); }}>
                Back to login
              </button>
            </form>
          ) : (
            <form className="stack" onSubmit={submit} aria-label={mode === 'login' ? 'Log in' : 'Create account'}>
              {mode === 'register' && (
                <div>
                  <label htmlFor="name">Your name</label>
                  <input id="name" value={form.name} onChange={set('name')} required />
                </div>
              )}
              <div>
                <label htmlFor="email">Email</label>
                <input id="email" type="email" value={form.email} onChange={set('email')} required />
              </div>
              <div>
                <label htmlFor="password">Password</label>
                <input id="password" type="password" value={form.password} onChange={set('password')} required />
              </div>
              {mode === 'register' && (
                <>
                  <div>
                    <label htmlFor="language">Language</label>
                    <select id="language" value={form.language} onChange={set('language')}>
                      <option value="en">English</option>
                      <option value="hi">हिन्दी (Hindi)</option>
                    </select>
                  </div>
                  <label className="row" style={{ gap: '0.5rem', alignItems: 'flex-start', textTransform: 'none', letterSpacing: 'normal', fontFamily: 'var(--serif)', fontSize: '0.85rem' }}>
                    <input
                      type="checkbox"
                      style={{ width: 'auto', marginTop: '0.2rem' }}
                      checked={form.accept_terms}
                      onChange={(e) => setForm({ ...form, accept_terms: e.target.checked })}
                      required
                    />
                    <span>
                      I'm 18+ and accept the{' '}
                      <a href="/api/legal/privacy" target="_blank" rel="noreferrer">privacy policy</a> and{' '}
                      <a href="/api/legal/terms" target="_blank" rel="noreferrer">terms</a>.
                      Voice is transcribed by Deepgram; summaries and replies use our AI provider.
                    </span>
                  </label>
                  <div>
                    <label>Family circle</label>
                    <div className="row">
                      <button type="button" className={circleChoice === 'join' ? '' : 'ghost'} onClick={() => setCircleChoice('join')}>
                        Join with code
                      </button>
                      <button type="button" className={circleChoice === 'create' ? '' : 'ghost'} onClick={() => setCircleChoice('create')}>
                        Start a new one
                      </button>
                    </div>
                    <input
                      style={{ marginTop: 'var(--space-1)' }}
                      placeholder={circleChoice === 'join' ? 'Invite code' : 'Circle name, e.g. Ghar'}
                      value={circleValue}
                      onChange={(e) => setCircleValue(e.target.value)}
                    />
                  </div>
                </>
              )}
              {error && <p className="error-text" role="alert">{error}</p>}
              <button disabled={busy}>{busy ? 'One moment…' : mode === 'login' ? 'Enter the courtyard' : 'Join the courtyard'}</button>
              <button
                type="button"
                className="quiet"
                onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(null); }}
              >
                {mode === 'login' ? 'New here? Create your account' : 'Already have an account? Log in'}
              </button>
            </form>
          )}
        </div>
      </section>

      <footer className="land-foot">
        <p className="meta">Family data stays on the server you run. &nbsp;·&nbsp; Not a medical service.</p>
      </footer>
    </main>
  );
}
