import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { t } from '../i18n';
import { useAuth } from '../auth';
import MfaCard from '../components/MfaCard';

function DataControls({ onDeleted }) {
  const [confirming, setConfirming] = useState(false);

  async function exportData() {
    const data = await api.get('/me/export');
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'aangan-export.json';
    link.click();
    URL.revokeObjectURL(url);
  }

  async function deleteAccount() {
    await api.del('/me');
    onDeleted();
  }

  return (
    <div className="row" style={{ flexWrap: 'wrap' }}>
      <button className="ghost" onClick={exportData}>Export my data</button>
      {confirming ? (
        <>
          <button style={{ background: 'var(--color-danger)' }} onClick={deleteAccount}>
            Yes, erase everything forever
          </button>
          <button className="quiet" onClick={() => setConfirming(false)}>Keep my account</button>
        </>
      ) : (
        <button className="quiet" style={{ color: 'var(--color-danger)' }} onClick={() => setConfirming(true)}>
          Delete my account…
        </button>
      )}
    </div>
  );
}

function HelpForm() {
  const [message, setMessage] = useState('');
  const [reply, setReply] = useState(null);

  async function send(e) {
    e.preventDefault();
    const res = await api.post('/feedback', { kind: 'feedback', message: message.trim() });
    setReply(res.message);
    setMessage('');
  }

  return (
    <form className="stack" onSubmit={send}>
      <textarea
        rows={2}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Something confusing? Something you wish existed?"
      />
      <div className="row">
        <button disabled={!message.trim()}>Send</button>
        {reply && <span className="muted">{reply}</span>}
      </div>
    </form>
  );
}

function AnotherCircle() {
  const { refreshMembers } = useAuth();
  const [choice, setChoice] = useState('join'); // join | create
  const [value, setValue] = useState('');
  const [notice, setNotice] = useState(null);
  const [error, setError] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setError(null);
    try {
      const circle = choice === 'join'
        ? await api.post('/circles/join', { invite_code: value.trim() })
        : await api.post('/circles', { name: value.trim() });
      await refreshMembers();
      setNotice(`You're in "${circle.name}" — switch circles from the top bar.`);
      setValue('');
    } catch (err) { setError(err.message); }
  }

  return (
    <form className="stack" onSubmit={submit}>
      <div className="row">
        <button type="button" className={choice === 'join' ? '' : 'ghost'} onClick={() => setChoice('join')}>
          Join with code
        </button>
        <button type="button" className={choice === 'create' ? '' : 'ghost'} onClick={() => setChoice('create')}>
          Start a new one
        </button>
      </div>
      <div className="row">
        <input
          placeholder={choice === 'join' ? 'Invite code' : 'Circle name, e.g. Sasural'}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          required
        />
        <button disabled={!value.trim()}>{choice === 'join' ? 'Join' : 'Create'}</button>
      </div>
      {notice && <p className="muted" role="status">{notice}</p>}
      {error && <p className="error-text" role="alert">{error}</p>}
    </form>
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
  const [rules, setRules] = useState([]);
  const [triggers, setTriggers] = useState([]);
  const [ruleText, setRuleText] = useState('');
  const [triggerText, setTriggerText] = useState('');
  const [triggerAudience, setTriggerAudience] = useState([]);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    const [r, t] = await Promise.all([
      api.get('/share-rules'),
      api.get('/alert-triggers'),
    ]);
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
      <section className="row between" style={{ alignItems: 'flex-start' }}>
        <div className="screen-head" style={{ marginBottom: 0 }}>
          <div className="meta">Private · sealed</div>
          <h1>{user.name}</h1>
          <p>{t(user.language, 'me.subtitle')}</p>
          <div className="desk-tools" aria-hidden="true">
            <svg width="26" height="18" viewBox="0 0 26 18" fill="none"><path d="M3 15l3-1 15-15 2 2-15 15-4 1z" transform="translate(0,1) scale(.9)" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" /></svg>
            <svg width="22" height="18" viewBox="0 0 22 18" fill="none"><path d="M5 8h12v4a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3z" stroke="currentColor" strokeWidth="1.3" /><ellipse cx="11" cy="8" rx="6" ry="2" stroke="currentColor" strokeWidth="1.3" /></svg>
            <span className="meta" style={{ textTransform: 'none', letterSpacing: '0.02em', fontSize: '0.66rem' }}>nib · inkwell · a quiet corner</span>
          </div>
        </div>
        <button className="ghost" onClick={logout}>{t(user.language, 'me.logout')}</button>
      </section>

      {error && <p className="error-text">{error}</p>}

      {/* the mirror's guts moved to /thoughts — Me keeps account & security */}
      <section className="card stack">
        <p className="muted" style={{ marginBottom: 0 }}>{t(user.language, 'me.mirror.moved')}</p>
        <Link className="btn" to="/thoughts" style={{ borderBottom: 'none', width: 'fit-content' }}>
          {t(user.language, 'me.mirror.link')}
        </Link>
      </section>

      <section className="card stack">
        <h2>Sharing rules</h2>
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
        <h2>Alert triggers</h2>
        <p className="muted">About you, by you — who should be told when you note something.</p>
        {triggers.map((t) => (
          <div key={t.id} className="care-eg row between">
            <span>“{t.description}”</span>
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
        <h2>Help & feedback</h2>
        <p className="muted">A human reads every message — usually within a day or two.</p>
        <HelpForm />
      </section>

      <section className="card stack">
        <h2>Aangan Plus</h2>
        <p className="muted">
          Unlimited voice minutes and Companion questions, the full memory book,
          and first access to new features — one plan for the whole family.
        </p>
        <PlusFakeDoor />
      </section>

      <MfaCard user={user} />

      <section className="card stack">
        <h2>Another circle</h2>
        <p className="muted">
          Family comes in many shapes — join or start a second circle, and
          switch between them from the top bar. Each circle only ever sees
          what you share with it.
        </p>
        <AnotherCircle />
      </section>

      <section className="card stack">
        <h2>Settings</h2>
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
        <DataControls onDeleted={logout} />
      </section>
    </div>
  );
}
