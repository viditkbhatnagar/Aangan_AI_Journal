import { useCallback, useEffect, useState } from 'react';
import { api } from '../api';
import HoldToTalk from '../components/HoldToTalk';
import ShareControls from '../components/ShareControls';

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

function EntryCard({ entry, onChanged }) {
  const [open, setOpen] = useState(false);
  return (
    <article className="card stack">
      <div className="row between">
        <span className="muted">{new Date(entry.created_at).toLocaleString()}</span>
        <span className={`pill ${entry.visibility}`}>{entry.visibility}</span>
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
            <div key={fact.id} className="stack" style={{ background: 'var(--color-surface-sunken)', borderRadius: 'var(--radius-sm)', padding: 'var(--space-2)' }}>
              <div className="row between">
                <span className="pill">{fact.type}</span>
              </div>
              <p>{fact.content}</p>
              <ShareControls entryId={entry.id} factId={fact.id} current={fact.visibility} onChanged={onChanged} />
            </div>
          ))}
        </div>
      )}
    </article>
  );
}

export default function Journal() {
  const [entries, setEntries] = useState([]);
  const [capture, setCapture] = useState(null);
  const [typing, setTyping] = useState(false);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState(null);

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
      if (err.status === 503) {
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
        <h1>Your journal</h1>
        <p className="muted">Everything here is private until you choose to share it.</p>
      </section>

      <HoldToTalk onRecorded={onRecorded} disabled={busy} />
      {busy && <p className="muted" style={{ textAlign: 'center' }}>Listening back and making notes…</p>}
      {notice && <p className="muted" role="status">{notice}</p>}

      <div style={{ textAlign: 'center' }}>
        <button className="quiet" onClick={() => setTyping(!typing)}>
          {typing ? 'Never mind' : 'Prefer to type it?'}
        </button>
      </div>
      {typing && (
        <form className="card stack" onSubmit={onTyped}>
          <textarea
            rows={4}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="How was your day?"
          />
          <button disabled={busy || !text.trim()}>Keep this</button>
        </form>
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
