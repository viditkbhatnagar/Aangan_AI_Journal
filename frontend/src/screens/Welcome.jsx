import { useState } from 'react';
import { api } from '../api';
import { useAuth } from '../auth';

export default function Welcome() {
  const { login, register, refreshMembers } = useAuth();
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ name: '', email: '', password: '', language: 'en', accept_terms: false });
  const [circleChoice, setCircleChoice] = useState('join'); // after register: join | create
  const [circleValue, setCircleValue] = useState('');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === 'login') {
        await login(form.email, form.password);
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

  return (
    <main className="app-shell" style={{ paddingTop: 'var(--space-5)' }}>
      <div style={{ textAlign: 'center', marginBottom: 'var(--space-4)' }}>
        <h1 style={{ fontSize: 'var(--text-hero)', color: 'var(--color-primary-deep)' }}>
          Aangan <span style={{ color: 'var(--color-accent)' }}>आँगन</span>
        </h1>
        <p className="muted">A quiet courtyard for your family's voices.</p>
      </div>

      <form className="card stack" onSubmit={submit} aria-label={mode === 'login' ? 'Log in' : 'Create account'}>
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
            <label className="row" style={{ gap: '0.5rem', fontSize: '0.85rem', alignItems: 'flex-start' }}>
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
        <button disabled={busy}>{busy ? 'One moment…' : mode === 'login' ? 'Come in' : 'Join the courtyard'}</button>
        <button
          type="button"
          className="quiet"
          onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(null); }}
        >
          {mode === 'login' ? 'New here? Create your account' : 'Already have an account? Log in'}
        </button>
      </form>
    </main>
  );
}
