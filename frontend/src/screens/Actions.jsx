import { useCallback, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { api } from '../api';

function PlanDetails({ plan }) {
  if (!plan) return null;
  if (plan.type === 'purchase') {
    return (
      <p className="muted">
        🛍 {plan.item} · {plan.price} · deliver: {plan.deliver_to}
      </p>
    );
  }
  if (plan.type === 'message') {
    return <p className="muted">✉️ To {plan.to || 'them'}: “{plan.body}”</p>;
  }
  if (plan.type === 'call') {
    return <p className="muted">📞 {plan.to || 'number to confirm'} — {plan.note}</p>;
  }
  return null;
}

function ResultDetails({ result }) {
  if (!result) return null;
  const url = result.checkout_url || result.url || result.deep_link;
  return (
    <div className="stack">
      <p>{result.note}</p>
      {result.body && <p className="muted">“{result.body}”</p>}
      {url && (
        <a className="btn" href={url} target="_blank" rel="noreferrer" style={{ textDecoration: 'none', textAlign: 'center' }}>
          {result.status === 'ready_for_human' ? 'Open and finish it yourself' : 'Open the shop'}
        </a>
      )}
    </div>
  );
}

export default function Actions() {
  const location = useLocation();
  const [actions, setActions] = useState([]);
  const [intent, setIntent] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const fromAlert = location.state?.alertId ?? null;

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

  const pending = actions.filter((a) => a.status === 'awaiting_approval' || a.status === 'approved');
  const done = actions.filter((a) => a.status === 'completed' || a.status === 'cancelled');

  return (
    <div className="stack-lg">
      <section>
        <h1>Actions</h1>
        <p className="muted">
          I prepare — you approve and finish. I never pay or send anything myself.
        </p>
      </section>

      <form className="card row" onSubmit={createAction}>
        <input
          className="grow"
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
          placeholder="e.g. order Deepa's chocolates"
          aria-label="What should I prepare?"
        />
        <button disabled={busy || !intent.trim()}>Prepare</button>
      </form>
      {error && <p className="error-text" role="alert">{error}</p>}

      {pending.length === 0 && done.length === 0 && (
        <div className="empty-state">
          <span className="big" aria-hidden="true">🎁</span>
          Nothing waiting — ask me to prepare something kind.
        </div>
      )}

      {pending.map((action) => (
        <article key={action.id} className="card stack" style={{ borderColor: 'var(--color-accent)' }}>
          <div className="row between">
            <strong>{action.intent}</strong>
            <span className="pill notable">needs your OK</span>
          </div>
          <PlanDetails plan={action.plan} />
          <div className="row">
            <button disabled={busy} onClick={() => act(action.id, 'approve')}>
              {busy ? 'Preparing…' : 'Approve — prepare it'}
            </button>
            <button className="quiet" disabled={busy} onClick={() => act(action.id, 'cancel')}>
              Cancel
            </button>
          </div>
        </article>
      ))}

      {done.map((action) => (
        <article key={action.id} className="card stack">
          <div className="row between">
            <strong>{action.intent}</strong>
            <span className="pill">{action.status}</span>
          </div>
          {action.status === 'completed' && <ResultDetails result={action.result} />}
        </article>
      ))}
    </div>
  );
}
