import { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../auth';
import { t } from '../i18n';
import {
  CartIcon, EnvelopeIcon, FlaskIcon, GiftIcon, PhoneIcon, SearchIcon, StarIcon, TickIcon, TraceGlyph,
} from '../icons';

function PlanDetails({ plan }) {
  if (!plan) return null;
  if (plan.type === 'message') {
    return <p className="muted"><EnvelopeIcon /> To {plan.to || 'them'}: “{plan.body}”</p>;
  }
  if (plan.type === 'call') {
    return <p className="muted"><PhoneIcon /> {plan.to || 'number to confirm'} — {plan.note}</p>;
  }
  return null;
}

// The found product, as a line on an errand receipt you stamp to approve.
function Receipt({ action, busy, stamping, onApprove, onCancel }) {
  const candidate = action.plan?.candidate;
  const shortlist = (action.plan?.shortlist || []).filter(
    (c) => c.title !== candidate?.title,
  ).slice(0, 2);
  return (
    <div className={`receipt ${stamping ? 'stamped' : ''}`}>
      <div className={`stamp-approve ${stamping ? 'press' : ''}`} aria-hidden="true">
        <span className="mark">Approved ✓<small>Ghar · you always pay</small></span>
      </div>
      <div className="receipt-head">
        <div className="rh-store">Aangan General Store</div>
        <div className="rh-sub">Errand receipt · No. GHAR-{String(action.id).padStart(4, '0')}</div>
        <svg className="barcode" viewBox="0 0 180 24" width="150" height="20" aria-hidden="true">
          {[2, 6, 12, 15, 20, 25, 32, 35, 41, 45, 51, 54, 58, 65, 69, 74, 77, 83, 88, 91, 96, 103, 106, 110, 116, 120, 123, 128, 133, 140, 143, 149, 153, 159, 162, 166, 173, 177].map((x, i) => (
            <rect key={x} x={x} y="0" width={[2, 4, 1, 3, 2, 5][i % 6]} height="24" />
          ))}
        </svg>
      </div>
      {candidate ? (
        <div className="prod-main">
          <div className="prod-thumb" aria-hidden="true">
            {candidate.image ? <img src={candidate.image} alt="" /> : <span className="thumb-fallback"><GiftIcon /></span>}
          </div>
          <div className="prod-body">
            <h3>{candidate.title}</h3>
            {candidate.reason && (
              <div className="prod-meta">
                <span className="reason"><StarIcon /> {candidate.reason}</span>
              </div>
            )}
            <div className="meta store-meta">
              Amazon.in
              {candidate.url && (
                <> · <a href={candidate.url} target="_blank" rel="noreferrer">view ↗</a></>
              )}
            </div>
          </div>
          <span className="pill price">{candidate.price_text || 'price at checkout'}</span>
        </div>
      ) : (
        <div className="prod-main">
          <div className="prod-body">
            <h3>{action.plan?.item}</h3>
            <div className="meta store-meta">I'll find the best match when you approve.</div>
          </div>
        </div>
      )}
      <div className="prod-actions">
        <button disabled={busy || stamping} onClick={onApprove}>
          {stamping ? 'Stamping…' : busy ? '…' : 'Stamp to approve'}
        </button>
        <button className="ghost" disabled={busy || stamping} onClick={onCancel}>Cancel</button>
      </div>
      {shortlist.length > 0 && (
        <div className="shortlist">
          <span className="meta">Also on the shelf</span>
          {shortlist.map((c, i) => (
            <div key={i} className="alt">
              <span className="an">{c.title.slice(0, 60)}{c.title.length > 60 ? '…' : ''}</span>
              <span className="lead" aria-hidden="true"></span>
              <span className="ap">{c.price_text}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// "Behind the scenes": the doer's itemized ledger — every step it took,
// from the plan (preparation) and result (completion). Nothing is hidden.
function Trace({ plan, result, open = false }) {
  const steps = [...(plan?.trace || []), ...(result?.trace || [])];
  if (steps.length === 0) return null;
  return (
    <details className="trace" open={open}>
      <summary className="trace-summary">
        <FlaskIcon /> Behind the scenes — the doer’s ledger
        <span className="trace-count">{steps.length} steps</span>
      </summary>
      <ol className="trace-list">
        {steps.map((s, i) => (
          <li key={i} className="trace-step" style={{ '--i': i }}>
            <span className="trace-icon" aria-hidden="true"><TraceGlyph emoji={s.icon} /></span>
            <div className="trace-body">
              <strong>{s.label}</strong>
              {s.detail && <div className="trace-detail">{s.detail}</div>}
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
    <div className="handoff" style={{ padding: '14px 6px 4px', textAlign: 'left' }}>
      <p>{result.note}</p>
      {result.item && <p className="muted iconline" style={{ marginTop: 6 }}><CartIcon /> {result.item}</p>}
      {result.body && <p className="muted" style={{ marginTop: 6, fontStyle: 'italic' }}>“{result.body}”</p>}
      {url && (
        <div style={{ marginTop: 12 }}>
          <a className="btn" href={url} target="_blank" rel="noreferrer" style={{ borderBottom: 'none' }}>
            {result.status === 'ready_for_human' ? 'Open and finish it yourself' : 'Open the shop'}
          </a>
          <span className="safe-stamp" style={{ marginLeft: 12 }}>Safe handoff</span>
        </div>
      )}
    </div>
  );
}

// The clarifying conversation — little paper notes between you and the doer.
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
    <article className="card">
      <div className="card-title">
        <h3>{action.intent}</h3>
        <span className="pill gentle">let's confirm</span>
      </div>
      <div className="chat">
        {convo.map((c, i) => (
          <div key={i} className={`chat-bubble ${c.role === 'user' ? 'chat-user' : 'chat-agent'}`}>
            <span className="who">{c.role === 'user' ? 'You' : 'The doer'}</span>
            {c.text}
          </div>
        ))}
        {thinking && (
          <div className="chat-bubble chat-agent chat-thinking">
            <span className="who">The doer</span>
            <SearchIcon /> Looking for the best options…
          </div>
        )}
      </div>
      <form className="ask-bar" style={{ marginTop: 14 }} onSubmit={send}>
        <span className="inp">
          <input
            ref={inputRef}
            value={msg}
            onChange={(e) => setMsg(e.target.value)}
            placeholder="Write your answer…"
            aria-label="Your answer"
            disabled={thinking}
          />
        </span>
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
  const [stampingId, setStampingId] = useState(null);
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

  // Approving is a rubber stamp: press the stamp, then complete for real.
  async function approve(id) {
    setStampingId(id);
    setError(null);
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    await new Promise((r) => setTimeout(r, reduce ? 0 : 650));
    try {
      await api.post(`/actions/${id}/approve`);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setStampingId(null);
    }
  }

  async function cancel(id) {
    setBusy(true);
    setError(null);
    try {
      await api.post(`/actions/${id}/cancel`);
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
      <section className="screen-head">
        <div className="meta">The doer</div>
        <h1>{t(lang, 'actions.title')}</h1>
        <p>{t(lang, 'actions.subtitle')}</p>
      </section>

      <section className="card">
        <form className="ask-bar" onSubmit={createAction}>
          <span className="inp">
            <input
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              placeholder={t(lang, 'actions.placeholder')}
              aria-label="What should I prepare?"
            />
          </span>
          <button disabled={busy || !intent.trim()}>{busy ? '…' : t(lang, 'actions.prepare')}</button>
        </form>
      </section>
      {error && <p className="error-text" role="alert">{error}</p>}

      {chatting.length === 0 && pending.length === 0 && done.length === 0 && (
        <div className="empty-state">
          <span className="big" aria-hidden="true"><GiftIcon /></span>
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
        <article key={action.id} className="card">
          <div className="card-title">
            <h3>{action.intent}</h3>
            <span className="pill notable">needs your stamp</span>
          </div>
          {action.plan?.type === 'purchase' ? (
            <>
              {lastAgentMessage(action) && (
                <div className="chat">
                  <div className="chat-bubble chat-agent">
                    <span className="who">The doer</span>
                    {lastAgentMessage(action)}
                  </div>
                </div>
              )}
              <Receipt
                action={action}
                busy={busy}
                stamping={stampingId === action.id}
                onApprove={() => approve(action.id)}
                onCancel={() => cancel(action.id)}
              />
            </>
          ) : (
            <>
              <PlanDetails plan={action.plan} />
              <div className="row" style={{ marginTop: 12 }}>
                <button disabled={busy || stampingId === action.id} onClick={() => approve(action.id)}>
                  {stampingId === action.id ? 'Stamping…' : t(lang, 'actions.approve')}
                </button>
                <button className="ghost" disabled={busy} onClick={() => cancel(action.id)}>Cancel</button>
              </div>
            </>
          )}
          <Trace plan={action.plan} result={action.result} open />
        </article>
      ))}

      {done.map((action) => (
        <article key={action.id} className="card">
          <div className="done-action">
            <span className="tick" aria-hidden="true"><TickIcon /></span>
            <div>
              <span className="meta" style={{ display: 'block' }}>{action.status === 'completed' ? 'Ready for you' : 'Set aside'}</span>
              <span style={{ fontSize: '1.08rem' }}>{action.intent}</span>
            </div>
            <span className="ready-stamp" aria-hidden="true">
              {action.status === 'completed' ? 'Prepared ✓' : 'Cancelled'}
            </span>
          </div>
          {action.status === 'completed' && <ResultDetails result={action.result} />}
          <Trace plan={action.plan} result={action.result} />
        </article>
      ))}
    </div>
  );
}
