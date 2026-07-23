import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import { useAuth } from '../auth';

function MoodStrip({ series }) {
  if (!series.length) return <p className="muted">Your moods will appear here as you journal.</p>;
  return (
    <div className="row" style={{ alignItems: 'flex-end', gap: '3px', minHeight: '3.5rem', overflowX: 'auto' }} aria-label="Mood over time">
      {series.slice(-30).map((p, i) => {
        const height = 12 + Math.round((p.score + 1) * 20);
        const color = p.score > 0.1 ? 'var(--color-accent)' : p.score < -0.1 ? 'var(--color-rose)' : 'var(--color-line)';
        return (
          <div
            key={i}
            title={`${p.date}: ${p.summary}`}
            style={{ width: '10px', height: `${height}px`, background: color, borderRadius: '4px 4px 0 0', flexShrink: 0 }}
          />
        );
      })}
    </div>
  );
}

function PlusFakeDoor() {
  const [reply, setReply] = useState(null);
  if (reply) return <p className="muted">{reply}</p>;
  return (
    <button onClick={async () => setReply((await api.post('/plus/interest')).message)}>
      Aangan Plus — notify me
    </button>
  );
}

export default function Me() {
  const { user, members, logout } = useAuth();
  const others = members.filter((m) => m.id !== user.id);
  const [mirror, setMirror] = useState(null);
  const [rules, setRules] = useState([]);
  const [triggers, setTriggers] = useState([]);
  const [ruleText, setRuleText] = useState('');
  const [triggerText, setTriggerText] = useState('');
  const [triggerAudience, setTriggerAudience] = useState([]);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    const [m, r, t] = await Promise.all([
      api.get('/mirror'),
      api.get('/share-rules'),
      api.get('/alert-triggers'),
    ]);
    setMirror(m);
    setRules(r);
    setTriggers(t);
  }, []);
  useEffect(() => { refresh().catch((e) => setError(e.message)); }, [refresh]);

  async function addRule(e) {
    e.preventDefault();
    await api.post('/share-rules', {
      description: ruleText.trim(),
      match: { type: 'preference', tag: 'gift' },
      audience: 'all',
    });
    setRuleText('');
    refresh();
  }

  async function addTrigger(e) {
    e.preventDefault();
    await api.post('/alert-triggers', {
      description: triggerText.trim(),
      match: { type: 'state', topic: 'health' },
      audience: triggerAudience,
      severity_hint: 'notable',
    });
    setTriggerText('');
    setTriggerAudience([]);
    refresh();
  }

  async function setLanguage(language) {
    await api.post('/me/settings', { language });
    window.location.reload();
  }

  return (
    <div className="stack-lg">
      <section className="row between">
        <div>
          <h1>{user.name}</h1>
          <p className="muted">Your private mirror, your rules. Only you see this page.</p>
        </div>
        <button className="ghost" onClick={logout}>Log out</button>
      </section>

      {error && <p className="error-text">{error}</p>}

      <section className="card stack">
        <h2>🪞 Mirror</h2>
        {mirror && (
          <>
            <div className="row" style={{ gap: 'var(--space-4)' }}>
              <div><strong style={{ fontSize: '1.4rem' }}>{mirror.total_entries}</strong><p className="muted">entries</p></div>
              <div><strong style={{ fontSize: '1.4rem' }}>{mirror.streak_days}</strong><p className="muted">day streak</p></div>
            </div>
            <MoodStrip series={mirror.mood_series} />
            {mirror.themes.length > 0 && (
              <div className="row" style={{ flexWrap: 'wrap' }}>
                {mirror.themes.map((t) => (
                  <span key={t.name} className="pill">{t.name} · {t.count}</span>
                ))}
              </div>
            )}
          </>
        )}
      </section>

      <section className="card stack">
        <h2>✨ My sharing rules</h2>
        <p className="muted">Standing yes-es you set up yourself — e.g. gift ideas go to everyone.</p>
        {rules.map((r) => (
          <div key={r.id} className="row between">
            <span>{r.description}</span>
            <span className="pill circle">{r.active ? 'active' : 'off'}</span>
          </div>
        ))}
        <form className="row" onSubmit={addRule}>
          <input
            className="grow"
            value={ruleText}
            onChange={(e) => setRuleText(e.target.value)}
            placeholder="e.g. share my gift ideas with the family"
          />
          <button disabled={!ruleText.trim()}>Add</button>
        </form>
      </section>

      <section className="card stack">
        <h2>🔔 My alert triggers</h2>
        <p className="muted">About you, by you — who should be told when you note something.</p>
        {triggers.map((t) => (
          <div key={t.id} className="row between">
            <span>{t.description}</span>
            <span className={`pill ${t.severity_hint}`}>{t.severity_hint}</span>
          </div>
        ))}
        <form className="stack" onSubmit={addTrigger}>
          <input
            value={triggerText}
            onChange={(e) => setTriggerText(e.target.value)}
            placeholder="e.g. if I say I'm unwell, tell…"
          />
          <div className="row" style={{ flexWrap: 'wrap' }}>
            {others.map((m) => (
              <label key={m.id} className="row" style={{ width: 'auto', gap: '0.3rem' }}>
                <input
                  type="checkbox"
                  style={{ width: 'auto' }}
                  checked={triggerAudience.includes(m.id)}
                  onChange={(e) =>
                    setTriggerAudience(
                      e.target.checked
                        ? [...triggerAudience, m.id]
                        : triggerAudience.filter((id) => id !== m.id),
                    )
                  }
                />
                {m.name}
              </label>
            ))}
            <button disabled={!triggerText.trim() || triggerAudience.length === 0}>Add</button>
          </div>
        </form>
      </section>

      <section className="card stack">
        <h2>✨ Aangan Plus</h2>
        <p className="muted">
          Unlimited voice minutes and Companion questions, the full memory book,
          and first access to new features — one plan for the whole family.
        </p>
        <PlusFakeDoor />
      </section>

      <section className="card stack">
        <h2>⚙️ Settings</h2>
        <div>
          <label htmlFor="lang">Language</label>
          <select id="lang" value={user.language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="en">English</option>
            <option value="hi">हिन्दी (Hindi)</option>
          </select>
        </div>
        <p className="muted">
          Everything you record starts private. Sharing is always your explicit choice.
        </p>
      </section>
    </div>
  );
}
