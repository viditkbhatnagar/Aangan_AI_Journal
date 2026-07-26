import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';
import { t } from '../i18n';
import HoldToTalk from '../components/HoldToTalk';
import ShareControls from '../components/ShareControls';
import UpgradeCard from '../components/UpgradeCard';

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
  const navigate = useNavigate();
  const [entries, setEntries] = useState([]);
  const [capture, setCapture] = useState(null);
  const [typing, setTyping] = useState(false);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);
  const [capMessage, setCapMessage] = useState(null);

  const refresh = useCallback(async () => setEntries(await api.get('/entries')), []);
  useEffect(() => { refresh(); }, [refresh]);

  // A spoken/typed command ("order flowers") becomes an action — hop straight
  // into the Actions chat where the Doer is waiting with its first question.
  useEffect(() => {
    const act = capture?.suggested_action;
    if (!act) return;
    setCapture((c) => (c ? { ...c, suggested_action: null } : c));
    navigate('/actions', { state: { focusActionId: act.id } });
  }, [capture?.suggested_action, navigate]);

  // async capture: the save returns instantly with status 'enriching';
  // poll the enrichment endpoint until the background agents finish
  const pollTimer = useRef(null);
  const pollingFor = useRef(null); // entry id this poll belongs to
  useEffect(() => () => clearInterval(pollTimer.current), []);

  function pollEnrichment(entryId) {
    clearInterval(pollTimer.current);
    pollingFor.current = entryId;
    let attempts = 0;
    let errors = 0;
    const timer = setInterval(async () => {
      // a newer capture took over — this tick must not touch its state
      if (pollingFor.current !== entryId) {
        clearInterval(timer);
        return;
      }
      attempts += 1;
      try {
        const enriched = await api.get(`/entries/${entryId}/enrichment`);
        if (pollingFor.current !== entryId) return;
        if (enriched.entry.status === 'ready') {
          clearInterval(timer);
          pollingFor.current = null;
          setCapture(enriched);
          await refresh();
        } else if (attempts > 40) {
          clearInterval(timer);
          pollingFor.current = null;
          setNotice('Still finishing your notes — reopen the entry in a moment to see them.');
        }
      } catch {
        errors += 1;
        if (errors >= 3) {          // tolerate blips; give up only if persistent
          clearInterval(timer);
          pollingFor.current = null;
          setNotice('Saved ✓ — the notes are still being made; refresh the journal shortly.');
        }
      }
    }, 1500);
    pollTimer.current = timer;
  }

  async function submit(formData) {
    setBusy(true);
    setNotice(null);
    try {
      const result = await api.postForm('/entries', formData);
      setCapture(result);
      setText('');
      setTyping(false);
      await refresh();
      if (result.entry.status === 'enriching') pollEnrichment(result.entry.id);
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
      {!busy && capture?.entry?.status === 'enriching' && (
        <p className="muted" role="status" style={{ textAlign: 'center' }}>
          Saved ✓ — still making notes in the background (watch the Agents panel)…
        </p>
      )}
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
