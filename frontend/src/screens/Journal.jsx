import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';
import { t } from '../i18n';
import HoldToTalk from '../components/HoldToTalk';
import ShareControls from '../components/ShareControls';
import UpgradeCard from '../components/UpgradeCard';

function SharePrompts({ capture, onDismiss, onShared }) {
  if (!capture?.share_suggestions?.length && !capture?.applied_rules?.length) return null;
  return (
    <section className="card stack" style={{ borderColor: 'var(--amber)' }}>
      {capture.applied_rules.map((rule) => (
        <p key={rule} className="muted">✨ Shared automatically because of your rule: “{rule}”.</p>
      ))}
      {capture.share_suggestions.map((s, i) => (
        <div key={i} className="stack">
          <p style={{ fontStyle: 'italic' }}>“{s.text}”</p>
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
    <div className="mnote">
      <div className="row between" style={{ marginBottom: 2 }}>
        <span className="k">{fact.type}</span>
        <span className="row" style={{ width: 'auto', gap: '0.2rem' }}>
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
        <span className="v">{fact.content}</span>
      )}
      <ShareControls entryId={entry.id} factId={fact.id} current={fact.visibility} onChanged={onChanged} />
    </div>
  );
}

// One journal entry as a sealed letter that unseals to ruled paper.
function EntryCard({ entry, onChanged }) {
  const [open, setOpen] = useState(false);
  const [confirming, setConfirming] = useState(false);

  async function remove() {
    await api.del(`/entries/${entry.id}`);
    onChanged();
  }

  const when = new Date(entry.created_at).toLocaleString(undefined, {
    day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit',
  });

  return (
    <article className={`letter ${open ? 'open' : ''}`}>
      <div className="env-flap" aria-hidden="true"><span className="wax-mini"><span lang="hi">आ</span></span></div>
      <button type="button" className="env-head" aria-expanded={open} onClick={() => setOpen(!open)}>
        <span className="postmark">{when}</span>
        <span className={`pill ${entry.visibility}`}>{entry.visibility}</span>
        <span className="unseal-hint">
          {open ? 'Open letter' : 'Tap to unseal'}
          {entry.facts?.length > 0 && ` · ${entry.facts.length} noted`}
          <span className="chev" aria-hidden="true">›</span>
        </span>
      </button>
      <div className="env-wrap">
        <div className="env-body">
          <div className="env-inner">
            <p className="prose">{entry.transcript}</p>
            {entry.summary && entry.summary !== entry.transcript && (
              <p className="muted" style={{ marginTop: 10, fontStyle: 'italic' }}>✍️ {entry.summary}</p>
            )}
            <div className="margin-notes">
              <ShareControls entryId={entry.id} current={entry.visibility} onChanged={onChanged} />
              {entry.facts?.length > 0 && (
                <>
                  <div className="mn-h" style={{ marginTop: 14 }}>In the margin · {entry.facts.length} note{entry.facts.length > 1 ? 's' : ''}</div>
                  {entry.facts.map((fact) => (
                    <FactCard key={fact.id} entry={entry} fact={fact} onChanged={onChanged} />
                  ))}
                </>
              )}
              <div className="row" style={{ marginTop: 12 }}>
                {confirming ? (
                  <>
                    <button className="quiet" style={{ color: 'var(--red-ink)' }} onClick={remove}>
                      Erase forever
                    </button>
                    <button className="quiet" onClick={() => setConfirming(false)}>Keep</button>
                  </>
                ) : (
                  <button className="quiet" onClick={() => setConfirming(true)} aria-label="Delete entry" title="Delete this entry everywhere">
                    🗑 Burn this letter
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
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
      <section className="screen-head">
        <div className="meta">Your diary</div>
        <h1>{t(lang, 'journal.title')}</h1>
        <p>{t(lang, 'journal.subtitle')}</p>
      </section>

      <section className="card">
        <div className="compose-cap"><span aria-hidden="true">✒</span> Pen a new letter to yourself</div>
        <div className="row" style={{ flexWrap: 'wrap' }}>
          <HoldToTalk onRecorded={onRecorded} disabled={busy} />
          <button className="quiet" onClick={() => setTyping(!typing)}>
            {typing ? t(lang, 'journal.type.cancel') : t(lang, 'journal.type')}
          </button>
        </div>
        {typing && (
          <form className="stack" style={{ marginTop: 14 }} onSubmit={onTyped}>
            <textarea
              rows={4}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={t(lang, 'journal.type.placeholder')}
            />
            <button disabled={busy || !text.trim()}>{t(lang, 'journal.type.submit')}</button>
          </form>
        )}
        <p className="meta" style={{ marginTop: 12, textTransform: 'none', letterSpacing: '0.03em' }}>
          Voice is transcribed by Deepgram · summaries use our AI provider ·{' '}
          <a href="/api/legal/privacy" target="_blank" rel="noreferrer">privacy</a>
        </p>
        {/* journaling stays scribe-mode; conversation lives in the Baithak */}
        <p className="muted" style={{ marginTop: 6 }}>
          <Link to="/ask">{t(lang, 'journal.baithak.hint')}</Link>
        </p>
      </section>

      {busy && (
        <article className="letter live-letter">
          <div className="row between" style={{ marginBottom: 10 }}>
            <span className="postmark meta">Just now</span>
            <span className="pill private">private</span>
          </div>
          <p className="prose live"><span>Listening back and making notes</span><span className="live-dots" aria-hidden="true"><i></i><i></i><i></i></span></p>
        </article>
      )}
      {!busy && capture?.entry?.status === 'enriching' && (
        <article className="letter live-letter" role="status">
          <div className="row between" style={{ marginBottom: 10 }}>
            <span className="postmark meta">Just now</span>
            <span className="pill private">private</span>
          </div>
          <p className="prose live"><span>Saved ✓ — making notes (watch the Agents panel)</span><span className="live-dots" aria-hidden="true"><i></i><i></i><i></i></span></p>
        </article>
      )}
      {notice && <p className="muted" role="status">{notice}</p>}

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
        <div className="stack-lg">
          {entries.map((entry) => <EntryCard key={entry.id} entry={entry} onChanged={refresh} />)}
        </div>
      )}
    </div>
  );
}
