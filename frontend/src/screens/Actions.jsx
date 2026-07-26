import { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';
import { t } from '../i18n';

function PlanDetails({ plan }) {
  if (!plan) return null;
  if (plan.type === 'message') {
    return <p className="muted">✉️ To {plan.to || 'them'}: “{plan.body}”</p>;
  }
  if (plan.type === 'call') {
    return <p className="muted">📞 {plan.to || 'number to confirm'} — {plan.note}</p>;
  }
  return null;
}

// The specific product the agent found and recommends — shown before you approve.
function ProductCard({ candidate }) {
  if (!candidate) return null;
  return (
    <div className="product-card">
      {candidate.image && <img src={candidate.image} alt="" className="product-img" />}
      <div className="stack-sm grow">
        <strong className="product-title">{candidate.title}</strong>
        <div className="row" style={{ gap: '0.5rem', flexWrap: 'wrap' }}>
          <span className="pill notable">{candidate.price_text}</span>
          {candidate.reason && <span className="muted product-reason">⭐ {candidate.reason}</span>}
        </div>
        {candidate.url && (
          <a className="muted product-link" href={candidate.url} target="_blank" rel="noreferrer">
            View on Amazon ↗
          </a>
        )}
      </div>
    </div>
  );
}

// "Behind the scenes": the ordered steps the agent took, gathered from the
// plan (preparation) and result (completion). Great for showing the whole
// pipeline live in a demo — nothing is hidden.
function Trace({ plan, result, open = false }) {
  const steps = [...(plan?.trace || []), ...(result?.trace || [])];
  if (steps.length === 0) return null;
  return (
    <details className="trace" open={open}>
      <summary className="trace-summary">
        🔬 Behind the scenes — how the agent handled this
        <span className="trace-count">{steps.length} steps</span>
      </summary>
      <ol className="trace-list">
        {steps.map((s, i) => (
          <li key={i} className="trace-step">
            <span className="trace-icon" aria-hidden="true">{s.icon || '•'}</span>
            <div className="trace-body">
              <strong>{s.label}</strong>
              {s.detail && <div className="muted trace-detail">{s.detail}</div>}
            </div>
          </li>
        ))}
      </ol>
    </details>
  );
}

function ResultDetails({ result }) {
  if (!result) return null;
  const url = result.checkout_url || result.url || result.deep_link;
  return (
    <div className="stack">
      <p>{result.note}</p>
      {result.item && <p className="muted">🛒 {result.item}</p>}
      {result.body && <p className="muted">“{result.body}”</p>}
      {url && (
        <a className="btn" href={url} target="_blank" rel="noreferrer" style={{ textDecoration: 'none', textAlign: 'center' }}>
          {result.status === 'ready_for_human' ? 'Open and finish it yourself' : 'Open the shop'}
        </a>
      )}
    </div>
  );
}

// The clarifying conversation — the agent asks, you answer, until it's sure.
function ChatCard({ action, onReply, thinking, autofocus }) {
  const [msg, setMsg] = useState('');
  const inputRef = useRef(null);
  useEffect(() => {
    if (autofocus && inputRef.current) inputRef.current.focus();
  }, [autofocus]);
  // skip the seeded first turn (your original request — already in the header)
  const convo = (action.plan?.conversation || []).filter(
    (c, i) => !(i === 0 && c.role === 'user'),
  );
  function send(e) {
    e.preventDefault();
    if (!msg.trim() || thinking) return;
    onReply(action.id, msg.trim());
    setMsg('');
  }
  return (
    <article className="card stack" style={{ borderColor: 'var(--color-accent)' }}>
      <div className="row between">
        <strong>{action.intent}</strong>
        <span className="pill gentle">let's confirm</span>
      </div>
      <div className="chat">
        {convo.map((c, i) => (
          <div key={i} className={`chat-bubble chat-${c.role}`}>{c.text}</div>
        ))}
        {thinking && <div className="chat-bubble chat-agent chat-thinking">🔎 Looking for the best options…</div>}
      </div>
      <form className="row" onSubmit={send}>
        <input
          ref={inputRef}
          className="grow"
          value={msg}
          onChange={(e) => setMsg(e.target.value)}
          placeholder="Type your answer…"
          aria-label="Your answer"
          disabled={thinking}
        />
        <button disabled={thinking || !msg.trim()}>{thinking ? '…' : 'Send'}</button>
      </form>
      <Trace plan={action.plan} result={action.result} />
    </article>
  );
}

function lastAgentMessage(action) {
  const convo = action.plan?.conversation || [];
  for (let i = convo.length - 1; i >= 0; i -= 1) {
    if (convo[i].role === 'agent') return convo[i].text;
  }
  return null;
}

export default function Actions() {
  const { user } = useAuth();
  const lang = user.language;
  const location = useLocation();
  const [actions, setActions] = useState([]);
  const [intent, setIntent] = useState('');
  const [busy, setBusy] = useState(false);
  const [replyingId, setReplyingId] = useState(null);
  const [error, setError] = useState(null);
  const fromAlert = location.state?.alertId ?? null;
  const focusActionId = location.state?.focusActionId ?? null;

  const refresh = useCallback(async () => setActions(await api.get('/actions')), []);
  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    if (location.state?.suggestion) setIntent(location.state.suggestion);
  }, [location.state]);

  async function createAction(e) {
    e.preventDefault();
    if (!intent.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api.post('/actions', { intent: intent.trim(), related_alert_id: fromAlert });
      setIntent('');
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function reply(id, message) {
    setReplyingId(id);
    setError(null);
    try {
      await api.post(`/actions/${id}/reply`, { message });
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setReplyingId(null);
    }
  }

  async function act(id, verb) {
    setBusy(true);
    setError(null);
    try {
      await api.post(`/actions/${id}/${verb}`);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const chatting = actions.filter((a) => a.status === 'clarifying');
  const pending = actions.filter((a) => a.status === 'awaiting_approval' || a.status === 'approved');
  const done = actions.filter((a) => a.status === 'completed' || a.status === 'cancelled');

  return (
    <div className="stack-lg">
      <section>
        <h1>{t(lang, 'actions.title')}</h1>
        <p className="muted">
          {t(lang, 'actions.subtitle')}
        </p>
      </section>

      <form className="card row" onSubmit={createAction}>
        <input
          className="grow"
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
          placeholder={t(lang, 'actions.placeholder')}
          aria-label="What should I prepare?"
        />
        <button disabled={busy || !intent.trim()}>{busy ? '…' : t(lang, 'actions.prepare')}</button>
      </form>
      {error && <p className="error-text" role="alert">{error}</p>}

      {chatting.length === 0 && pending.length === 0 && done.length === 0 && (
        <div className="empty-state">
          <span className="big" aria-hidden="true">🎁</span>
          Nothing waiting — ask me to prepare something kind.
        </div>
      )}

      {chatting.map((action) => (
        <ChatCard
          key={action.id}
          action={action}
          onReply={reply}
          thinking={replyingId === action.id}
          autofocus={action.id === focusActionId}
        />
      ))}

      {pending.map((action) => (
        <article key={action.id} className="card stack" style={{ borderColor: 'var(--color-accent)' }}>
          <div className="row between">
            <strong>{action.intent}</strong>
            <span className="pill notable">needs your OK</span>
          </div>
          {action.plan?.type === 'purchase' ? (
            <>
              {lastAgentMessage(action) && <p>{lastAgentMessage(action)}</p>}
              <ProductCard candidate={action.plan?.candidate} />
            </>
          ) : (
            <PlanDetails plan={action.plan} />
          )}
          <div className="row">
            <button disabled={busy} onClick={() => act(action.id, 'approve')}>
              {busy ? '…' : t(lang, 'actions.approve')}
            </button>
            <button className="quiet" disabled={busy} onClick={() => act(action.id, 'cancel')}>
              Cancel
            </button>
          </div>
          <Trace plan={action.plan} result={action.result} open />
        </article>
      ))}

      {done.map((action) => (
        <article key={action.id} className="card stack">
          <div className="row between">
            <strong>{action.intent}</strong>
            <span className="pill">{action.status}</span>
          </div>
          {action.status === 'completed' && <ResultDetails result={action.result} />}
          <Trace plan={action.plan} result={action.result} />
        </article>
      ))}
    </div>
  );
}
