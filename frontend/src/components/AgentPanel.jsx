import { useEffect, useRef, useState } from 'react';
import { api } from '../api';

const AGENT_ICONS = {
  Conductor: '🧭',
  Companion: '🪔',
  Librarian: '📚',
  Transcriber: '🎙',
  Summarizer: '✍️',
  Extractor: '🔎',
  'Consent Guardian': '🛡️',
  Alerter: '🔔',
  Doer: '🎁',
  Interpreter: '🌐',
  Prompter: '🌱',
  Radar: '📡',
};

function timeAgo(ts) {
  const s = Math.max(0, Math.round(Date.now() / 1000 - ts));
  if (s < 5) return 'now';
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.round(s / 60)}m ago`;
  return `${Math.round(s / 3600)}h ago`;
}

// Right-hand panel: a live timeline of which agent is working and what it did
// while handling YOUR requests. (You never see anyone else's activity.)
export default function AgentPanel({ open, onClose }) {
  const [events, setEvents] = useState([]);
  const lastId = useRef(0);

  useEffect(() => {
    if (!open) return undefined;
    let alive = true;
    async function poll() {
      try {
        const { events: fresh } = await api.get(`/activity?after=${lastId.current}`);
        if (!alive || fresh.length === 0) return;
        lastId.current = fresh[fresh.length - 1].id;
        setEvents((prev) => [...fresh.reverse(), ...prev].slice(0, 80));
      } catch { /* quiet */ }
    }
    poll();
    const timer = setInterval(poll, 2000);
    return () => { alive = false; clearInterval(timer); };
  }, [open]);

  if (!open) return null;

  return (
    <aside className="agent-panel" aria-label="Agent activity">
      <div className="row between" style={{ marginBottom: 'var(--space-2)' }}>
        <h2 style={{ fontSize: '1.05rem' }}>Agents at work</h2>
        <button className="quiet" onClick={onClose} aria-label="Close panel">✕</button>
      </div>
      <p className="muted" style={{ fontSize: '0.8rem', marginBottom: 'var(--space-2)' }}>
        A live look behind the curtain — only for your own requests.
      </p>
      {events.length === 0 ? (
        <p className="muted">Quiet for now. Journal something or ask a question and watch this come alive.</p>
      ) : (
        <ol className="agent-feed">
          {events.map((e) => (
            <li key={e.id} className="agent-event">
              <span className="agent-event-icon" aria-hidden="true">
                {AGENT_ICONS[e.agent] ?? '⚙️'}
              </span>
              <div>
                <div className="row between">
                  <strong style={{ fontSize: '0.82rem' }}>{e.agent}</strong>
                  <span className="muted" style={{ fontSize: '0.72rem' }}>{timeAgo(e.ts)}</span>
                </div>
                <p style={{ fontSize: '0.85rem' }}>{e.message}</p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </aside>
  );
}
