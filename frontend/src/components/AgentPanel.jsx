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
  if (s < 5) return 'just now';
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

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <div className="scrim" onClick={onClose} aria-hidden="true"></div>
      <aside className="agent-panel" aria-label="Agent activity" role="dialog">
        <div className="row between" style={{ marginBottom: 'var(--space-1)', alignItems: 'flex-start' }}>
          <div>
            <div className="meta ap-kicker">Behind the curtain</div>
            <h2 style={{ fontSize: '1.4rem' }}>Agents at work</h2>
          </div>
          <button className="quiet" onClick={onClose} aria-label="Close panel">✕</button>
        </div>
        <p className="muted" style={{ fontSize: '0.9rem', marginBottom: 'var(--space-2)' }}>
          A live look behind the curtain — only for your own requests.
        </p>
        {events.length === 0 ? (
          <p className="muted" style={{ fontStyle: 'italic' }}>Quiet for now. Journal something or ask a question and watch this come alive.</p>
        ) : (
          <ol className="agent-feed">
            {events.map((e) => (
              <li key={e.id} className="agent-event">
                <span className="agent-event-icon" aria-hidden="true">
                  {AGENT_ICONS[e.agent] ?? '⚙️'}
                </span>
                <div>
                  <div className="ev-name">{e.agent}</div>
                  <p className="ev-msg">{e.message}</p>
                  <div className="ev-time">{timeAgo(e.ts)}</div>
                </div>
              </li>
            ))}
          </ol>
        )}
      </aside>
    </>
  );
}
