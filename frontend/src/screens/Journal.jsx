import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';
import { t } from '../i18n';
import HoldToTalk from '../components/HoldToTalk';
import ShareControls from '../components/ShareControls';
import UpgradeCard from '../components/UpgradeCard';

// When an entry clearly asks for something to be DONE ("order chocolates —
// you do it"), the Doer drafts it. Nothing runs until the author approves.
function ActionPrompt({ action, onDone }) {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  if (!action) return null;

  async function approve() {
    setBusy(true);
    try {
      const approved = await api.post(`/actions/${action.id}/approve`);
      setResult(approved.result);
    } finally {
      setBusy(false);
    }
  }

  if (result) {
    const url = result.checkout_url || result.url || result.deep_link;
    return (
      <section className="card stack" style={{ borderColor: 'var(--color-accent)' }}>
        <p>🎁 {result.note}</p>
        {url && (
          <a className="btn" href={url} target="_blank" rel="noreferrer" style={{ textDecoration: 'none', textAlign: 'center' }}>
            Open it
          </a>
        )}
        <button className="quiet" onClick={onDone}>Done</button>
      </section>
    );
  }

  return (
    <section className="card stack" style={{ borderColor: 'var(--color-accent)' }}>
      <p>🎁 I heard something to do: <strong>“{action.intent}”</strong></p>
      <p className="muted">I've prepared it — nothing happens until you say yes. You'll finish any payment yourself.</p>
      <div className="row">
        <button disabled={busy} onClick={approve}>{busy ? 'Preparing…' : 'Yes, go ahead'}</button>
        <button className="ghost" disabled={busy} onClick={() => navigate('/actions')}>Review first</button>
        <button className="quiet" disabled={busy} onClick={async () => { await api.post(`/actions/${action.id}/cancel`); onDone(); }}>
          No, leave it
        </button>
      </div>
    </section>
  );
}

function SharePrompts({ capture, onDismiss, onShared }) {
  if (!capture?.share_suggestions?.length && !capture?.applied_rules?.length) return null;
  return (
    <section className="card stack" style={{ borderColor: 'var(--color-accent)' }}>
      {capture.applied_rules.map((rule) => (
        <p key={rule} className="muted">✨ Shared automatically because of your rule: “{rule}”.</p>
      ))}
      {capture.share_suggestions.map((s, i) => (
        <div key={i} className="stack">
          <p>“{s.text}”</p>
          <p className="muted">{s.reason}</p>
          <div className="row">
            <button
              onClick={async () => {
                await api.post(`/entries/${capture.entry.id}/share`, {
                  fact_id: s.fact_id,
                  visibility: 'circle',
                });
                onShared();
              }}
            >
              Yes, share it
            </button>
            <button className="ghost" onClick={onDismiss}>Keep it private</button>
          </div>
        </div>
      ))}
    </section>
  );
}

function FactCard({ entry, fact, onChanged }) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(fact.content);

  async function save() {
    await api.patch(`/facts/${fact.id}`, { content: text.trim() });
    setEditing(false);
    onChanged();
  }

  async function remove() {
    await api.del(`/facts/${fact.id}`);
    onChanged();
  }

  return (
    <div className="stack" style={{ background: 'var(--color-surface-sunken)', borderRadius: 'var(--radius-sm)', padding: 'var(--space-2)' }}>
      <div className="row between">
        <span className="pill">{fact.type}</span>
        <span className="row" style={{ width: 'auto' }}>
          <button className="quiet" onClick={() => setEditing(!editing)} title="Correct this note">✏️</button>
          <button className="quiet" onClick={remove} title="Remove this note">🗑</button>
        </span>
      </div>
      {editing ? (
        <div className="row">
          <input className="grow" value={text} onChange={(e) => setText(e.target.value)} />
          <button disabled={!text.trim()} onClick={save}>Save</button>
        </div>
      ) : (
        <p>{fact.content}</p>
      )}
      <ShareControls entryId={entry.id} factId={fact.id} current={fact.visibility} onChanged={onChanged} />
    </div>
  );
}

function EntryCard({ entry, onChanged }) {
  const [open, setOpen] = useState(false);
  const [confirming, setConfirming] = useState(false);

  async function remove() {
    await api.del(`/entries/${entry.id}`);
    onChanged();
  }

  return (
    <article className="card stack">
      <div className="row between">
        <span className="muted">{new Date(entry.created_at).toLocaleString()}</span>
        <span className="row" style={{ width: 'auto' }}>
          <span className={`pill ${entry.visibility}`}>{entry.visibility}</span>
          {confirming ? (
            <>
              <button className="quiet" style={{ color: 'var(--color-danger)' }} onClick={remove}>
                Erase forever
              </button>
              <button className="quiet" onClick={() => setConfirming(false)}>Keep</button>
            </>
          ) : (
            <button className="quiet" onClick={() => setConfirming(true)} aria-label="Delete entry" title="Delete this entry everywhere">
              🗑
            </button>
          )}
        </span>
      </div>
      <p>{entry.summary || entry.transcript}</p>
      <button className="quiet" onClick={() => setOpen(!open)}>
        {open ? 'Hide details' : `Details${entry.facts?.length ? ` · ${entry.facts.length} noted` : ''}`}
      </button>
      {open && (
        <div className="stack" style={{ borderTop: '1px solid var(--color-line)', paddingTop: 'var(--space-2)' }}>
          <p className="muted" style={{ whiteSpace: 'pre-wrap' }}>{entry.transcript}</p>
          <ShareControls entryId={entry.id} current={entry.visibility} onChanged={onChanged} />
          {entry.facts?.map((fact) => (
            <FactCard key={fact.id} entry={entry} fact={fact} onChanged={onChanged} />
          ))}
        </div>
      )}
    </article>
  );
}

export default function Journal() {
  const { user } = useAuth();
  const lang = user.language;
  const [entries, setEntries] = useState([]);
  const [capture, setCapture] = useState(null);
  const [typing, setTyping] = useState(false);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const [capMessage, setCapMessage] = useState(null);

  const refresh = useCallback(async () => setEntries(await api.get('/entries')), []);
  useEffect(() => { refresh(); }, [refresh]);

  async function submit(formData) {
    setBusy(true);
    setNotice(null);
    try {
      const result = await api.postForm('/entries', formData);
      setCapture(result);
      setText('');
      setTyping(false);
      await refresh();
    } catch (err) {
      if (err.status === 402) {
        setCapMessage(err.message);
        setTyping(true); // typed entries stay free
      } else if (err.status === 503) {
        setNotice(err.message);
        setTyping(true);
      } else {
        setNotice(err.message);
      }
    } finally {
      setBusy(false);
    }
  }

  function onRecorded(blob) {
    const formData = new FormData();
    const ext = blob.type.includes('mp4') ? 'm4a' : 'webm';
    formData.append('audio', blob, `entry.${ext}`);
    submit(formData);
  }

  function onTyped(e) {
    e.preventDefault();
    if (!text.trim()) return;
    const formData = new FormData();
    formData.append('transcript', text.trim());
    submit(formData);
  }

  return (
    <div className="stack-lg">
      <section>
        <h1>{t(lang, 'journal.title')}</h1>
        <p className="muted">{t(lang, 'journal.subtitle')}</p>
      </section>

      <HoldToTalk onRecorded={onRecorded} disabled={busy} />
      <p className="muted" style={{ textAlign: 'center', fontSize: '0.75rem' }}>
        Voice is transcribed by Deepgram · summaries use our AI provider ·{' '}
        <a href="/api/legal/privacy" target="_blank" rel="noreferrer">privacy</a>
      </p>
      {busy && <p className="muted" style={{ textAlign: 'center' }}>Listening back and making notes…</p>}
      {notice && <p className="muted" role="status">{notice}</p>}

      <div style={{ textAlign: 'center' }}>
        <button className="quiet" onClick={() => setTyping(!typing)}>
          {typing ? t(lang, 'journal.type.cancel') : t(lang, 'journal.type')}
        </button>
      </div>
      {typing && (
        <form className="card stack" onSubmit={onTyped}>
          <textarea
            rows={4}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={t(lang, 'journal.type.placeholder')}
          />
          <button disabled={busy || !text.trim()}>{t(lang, 'journal.type.submit')}</button>
        </form>
      )}

      {capMessage && <UpgradeCard message={capMessage} onDismiss={() => setCapMessage(null)} />}

      {capture?.suggested_action && (
        <ActionPrompt
          action={capture.suggested_action}
          onDone={() => setCapture({ ...capture, suggested_action: null })}
        />
      )}

      <SharePrompts
        capture={capture}
        onDismiss={() => setCapture(null)}
        onShared={() => { setCapture(null); refresh(); }}
      />

      {entries.length === 0 ? (
        <div className="empty-state">
          <span className="big" aria-hidden="true">🪔</span>
          अभी यहाँ कुछ नहीं है — nothing here yet.<br />Hold the button and just talk.
        </div>
      ) : (
        entries.map((entry) => <EntryCard key={entry.id} entry={entry} onChanged={refresh} />)
      )}
    </div>
  );
}
